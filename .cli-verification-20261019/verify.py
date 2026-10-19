import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).resolve().parent
DATA = BASE / 'cases'
LOG = []
ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}

def run(label, args, inputs=(), code=0, contains=(), data=DATA):
    cmd = [sys.executable, '-m', 'budget_app', '--data-dir', str(data), *args]
    result = subprocess.run(cmd, input='\n'.join(inputs) + ('\n' if inputs else ''), capture_output=True, encoding='utf-8', env=ENV, cwd=ROOT, timeout=20)
    output = result.stdout + result.stderr
    ok = result.returncode == code and all(t in output for t in contains)
    if code:
        ok = ok and '[오류]' in result.stderr and '[힌트]' in result.stderr and 'Traceback' not in output
    entry = dict(label=label, args=args, inputs=list(inputs), data=str(data), expected_code=code, code=result.returncode, stdout=result.stdout, stderr=result.stderr, passed=ok)
    LOG.append(entry)
    return result

def check(label, value):
    LOG.append(dict(label=label, passed=bool(value), code=None))

def snapshot():
    return {p.name:p.read_bytes() for p in DATA.glob('*.csv')}

def source(name, rows, fields=None, encoding='utf-8'):
    path=BASE/name
    with path.open('w',encoding=encoding,newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or ['date','type','category','amount','memo','tags'])
        w.writeheader(); w.writerows(rows)
    return path

run('초기 목록', ['list'], contains=['거래 없음'])
check('저장 CSV 네 개', set(snapshot()) == {'transactions.csv','categories.csv','budgets.csv','metadata.csv'})
run('카테고리 추가', ['category','add'], ['검증분류'], contains=['완료'])
run('재실행 카테고리 유지', ['category','list'], contains=['검증분류'])
run('지출 추가', ['add'], ['2026-10-19','expense','검증분류','120000','점심 검증','Meal,friend'], contains=['TX-000001'])
run('수입 추가', ['add'], ['2026-10-01','income','급여','300000','월급',''], contains=['TX-000002'])
run('재실행 거래 유지', ['list'], contains=['TX-000001','TX-000002','120,000원'])
r=run('조건 AND 검색', ['search','--from','2026-10-19','--to','2026-10-19','--category','검증분류','--type','expense','--q','점심','--tags','meal,FRIEND'], contains=['TX-000001'])
check('검색 불일치 거래 제외', 'TX-000002' not in r.stdout)
run('미설정 예산 요약', ['summary','--month','2026-10'], contains=['총 수입: 300,000원','총 지출: 120,000원','잔액: 180,000원','예산 미설정'])
run('예산 설정', ['budget','set','--month','2026-10'], ['100000'])
run('재실행 예산 유지', ['budget','get','--month','2026-10'], contains=['100,000원'])
run('사용률 및 초과', ['summary','--month','2026-10'], contains=['120.0%','예산 초과'])
run('0원 예산 설정', ['budget','set','--month','2026-11'], ['0'])
run('0원 예산 요약', ['summary','--month','2026-11'], contains=['계산 불가','예산 0원'])
before=snapshot()
run('사용 중 카테고리 삭제 차단', ['category','delete'], ['검증분류'], code=3, contains=['사용 중인 카테고리','해당 거래'])
check('카테고리 삭제 실패 원본 유지', snapshot()==before)
run('미사용 카테고리 추가', ['category','add'], ['삭제대상'])
run('미사용 카테고리 삭제', ['category','delete'], ['삭제대상'])
r=run('카테고리 삭제 재확인', ['category','list'])
check('미사용 카테고리 제거 확인', '삭제대상' not in r.stdout)
run('remove 명령 지원 여부', ['category','remove'], ['삭제대상'], code=2)
run('거래 수정', ['update','--id','TX-000001'], ['','','','125000','수정 메모','','y'], contains=['수정 완료'])
run('수정 재실행 확인', ['list'], contains=['125,000원','수정 메모'])

row=dict(date='2026-10-20',type='expense',category='식비',amount='1234',memo='한글, "따옴표"\n여러 줄 메모',tags='태그,Meal')
path=source('special.csv',[row])
run('특수문자 CSV import', ['import','--file',str(path)], contains=['imported=1'])
out=BASE/'export.csv'
run('월 CSV export', ['export','--month','2026-10','--file',str(out)], contains=['exported=3'])
raw=out.read_bytes(); parsed=list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
check('UTF-8 및 정확한 export 헤더', raw.decode('utf-8').splitlines()[0]=='date,type,category,amount,memo,tags')
check('한글 쉼표 따옴표 여러 줄 보존', row in parsed)
OTHER=BASE/'roundtrip'
run('왕복 대상 카테고리 준비', ['category','add'], ['검증분류'], data=OTHER)
run('export 결과 재import', ['import','--file',str(out)], contains=['imported=3'], data=OTHER)
out2=BASE/'roundtrip.csv'
run('재import 결과 export', ['export','--from','2026-10-01','--to','2026-10-31','--file',str(out2)], data=OTHER)
parsed2=list(csv.DictReader(io.StringIO(out2.read_text(encoding='utf-8'))))
check('왕복 거래 내용 동일(ID 및 순서 제외)', sorted(map(lambda x:json.dumps(x,sort_keys=True),parsed))==sorted(map(lambda x:json.dumps(x,sort_keys=True),parsed2)))
minimal={k:row[k] for k in ('date','type','category','amount')}
p=source('minimal.csv',[minimal],fields=list(minimal))
run('선택 열 생략 import', ['import','--file',str(p)], contains=['imported=1'])
p=source('bom-extra.csv',[{**row,'extra':'ignored'}],fields=[*row,'extra'],encoding='utf-8-sig')
run('BOM 및 추가 열 허용', ['import','--file',str(p)], contains=['imported=1'])

for label,changes,code in [('잘못된 날짜',{'date':'2026-02-30'},2),('잘못된 금액',{'amount':'-1'},2),('미등록 카테고리',{'category':'미등록'},3)]:
    values=dict(date='2026-10-19',type='expense',category='식비',amount='100',memo='',tags='');values.update(changes)
    before=snapshot(); run(label,['add'],list(values.values()),code=code);check(label+' 원본 유지',snapshot()==before)
for label,args,code in [('잘못된 ID',['delete','--id','bad'],2),('없는 ID',['delete','--id','TX-999999'],3),('잘못된 인자',['list','--unknown'],2),('잘못된 limit',['list','--limit','0'],2),('없는 파일',['import','--file',str(BASE/'missing.csv')],4)]:
    run(label,args,code=code)
before=snapshot()
run('수정 검증 실패',['update','--id','TX-000001'],['','','','-1','',''],code=2)
check('실패 update 원본 유지',snapshot()==before)
before=snapshot();run('없는 거래 삭제 실패',['delete','--id','TX-999999'],code=3);check('실패 delete 원본 유지',snapshot()==before)
for name,p in [('깨진 값',source('bad-value.csv',[row,{**row,'amount':'bad'}])),('필수 헤더 누락',source('bad-header.csv',[],fields=['date','amount']))]:
    before=snapshot();run(name,['import','--file',str(p)],code=5);check(name+' import 전체 롤백',snapshot()==before)
bad=BASE/'bad-utf8.csv';bad.write_bytes(b'\xff\xfeinvalid')
before=snapshot();run('잘못된 UTF-8',['import','--file',str(bad)],code=5);check('인코딩 오류 원본 유지',snapshot()==before)
# Real Windows file-handle lock: deny write/delete access to only our test CSV.
import ctypes
from ctypes import wintypes
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
k.CreateFileW.restype=wintypes.HANDLE
k.CloseHandle.argtypes=[wintypes.HANDLE]
handle=k.CreateFileW(str(DATA/'transactions.csv'),0x80000000,1,None,3,0,None)
if handle==wintypes.HANDLE(-1).value:
    LOG.append(dict(label='실제 파일 잠금 저장 실패',passed=None,reason=str(ctypes.get_last_error())))
else:
    try:
        for label,args,inputs in [('잠금 update',['update','--id','TX-000001'],['','','','130000','','','y']),('잠금 delete',['delete','--id','TX-000001'],['y']),('잠금 import',['import','--file',str(path)],[])]:
            old=(DATA/'transactions.csv').read_bytes();run(label,args,inputs,code=4);check(label+' 거래 원본 보존',(DATA/'transactions.csv').read_bytes()==old)
    finally:k.CloseHandle(handle)
run('거래 삭제',['delete','--id','TX-000001'],['y'],contains=['삭제 완료'])
r=run('삭제 재실행 확인',['list']);check('삭제 거래 없음','TX-000001' not in r.stdout)
report=BASE/'results.json'
report.write_text(json.dumps(LOG,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(total=len(LOG),passed=sum(x['passed'] is True for x in LOG),failed=[x for x in LOG if x['passed'] is False],unverified=[x for x in LOG if x['passed'] is None],report=str(report)),ensure_ascii=False,indent=2))
