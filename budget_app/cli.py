"""명령 파싱과 대화형 입출력. 저장 작업은 서비스에 위임한다."""
import argparse
import sys
from contextlib import closing
from .decorators import handle_errors
from .errors import AppError
from .repositories import CsvRepository
from .services import BudgetService
from .validators import validate_amount


class Parser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['add_help'] = False
        super().__init__(*args, **kwargs)
        self.add_argument('--help', action='help', help='사용법 표시')

    def error(self, message):
        raise AppError(message, f'{self.prog} --help로 사용법을 확인하세요.')


def create_parser() -> argparse.ArgumentParser:
    root = Parser(description='CSV 콘솔 가계부 (Python 표준 라이브러리)')
    root.add_argument('--data-dir', default='./data', help='저장 폴더, 명령 앞에 지정')
    commands = root.add_subparsers(dest='command', required=True)
    for name, handler, help_text in (
        ('add', handle_add, '대화형 거래 추가'), ('list', handle_list, 'ID 내림차순 목록'),
        ('search', handle_search, '조건 AND 검색'), ('update', handle_update, '대화형 수정·확인'),
        ('delete', handle_delete, '거래 삭제·확인'), ('summary', handle_summary, '월별 요약'),
        ('budget', handle_budget, '월 예산'), ('category', handle_category, '카테고리'),
        ('import', handle_import, 'CSV 일괄 가져오기'), ('export', handle_export, 'CSV 내보내기')):
        command = commands.add_parser(name, help=help_text)
        command.set_defaults(handler=handler)
        if name == 'list':
            command.add_argument('--limit', type=validate_amount, default=20)
        elif name == 'search':
            for flag, dest in [('from', 'start'), ('to', 'end'), ('category', 'category'),
                               ('type', 'type'), ('q', 'q'), ('tags', 'tags')]:
                command.add_argument('--' + flag, dest=dest, default='' if flag == 'tags' else None)
        elif name in ('update', 'delete'):
            command.add_argument('--id', required=True)
        elif name == 'summary':
            command.add_argument('--month', required=True)
            command.add_argument('--top', type=validate_amount, default=5)
        elif name in ('budget', 'category'):
            actions = command.add_subparsers(dest='action', required=True)
            for action in (('set', 'get') if name == 'budget' else ('add', 'list', 'delete')):
                child = actions.add_parser(action)
                if name == 'budget':
                    child.add_argument('--month', required=True)
        elif name in ('import', 'export'):
            command.add_argument('--file', required=True)
            if name == 'export':
                command.add_argument('--month')
                command.add_argument('--from', dest='start')
                command.add_argument('--to', dest='end')
    return root


def show_transaction(tx) -> None:
    print(f'{tx.id} | {tx.date} | {tx.type} | {tx.category} | {tx.amount:,}원 | {tx.memo} | {",".join(tx.tags)}')


def show_transactions(transactions) -> None:
    count = 0
    try:
        with closing(transactions):
            for tx in transactions:
                show_transaction(tx)
                count += 1
    except AppError:
        if count:
            print('[주의] 이미 출력된 목록은 불완전한 결과입니다.', file=sys.stderr)
        raise
    if not count:
        print('거래 없음 (0건)')


@handle_errors
def handle_add(args, service) -> int:
    print('카테고리: ' + ', '.join(c.name for c in service.list_categories()))
    if not service.list_categories():
        raise AppError('카테고리가 없습니다.', 'category add로 먼저 등록하세요.', 3)
    values = {key: input(label + ': ') for key, label in (
        ('date', '날짜 (YYYY-MM-DD)'), ('type', '종류 (income/expense)'), ('category', '카테고리'),
        ('amount', '금액'), ('memo', '메모 (선택)'), ('tags', '태그 (쉼표 구분, 선택)'))}
    tx = service.add_transaction(**values)
    print(f'[저장 완료] {tx.id}')
    return 0


@handle_errors
def handle_list(args, service) -> int:
    show_transactions(service.list_transactions(args.limit))
    return 0


@handle_errors
def handle_search(args, service) -> int:
    show_transactions(service.search_transactions(**{k: getattr(args, k) for k in ('start', 'end', 'category', 'type', 'q', 'tags')}))
    return 0


def confirm() -> bool:
    return input('저장할까요? (y/yes): ').strip().casefold() in ('y', 'yes')


@handle_errors
def handle_update(args, service) -> int:
    old = service.get_transaction(args.id)
    print('수정 전:')
    show_transaction(old)
    changes = {}
    for field in ('date', 'type', 'category', 'amount', 'memo', 'tags'):
        current = getattr(old, field)
        shown = ','.join(current) if field == 'tags' else current
        clear_hint = ', :clear로 비우기' if field in ('memo', 'tags') else ''
        raw = input(f'{field} [{shown}] (Enter 유지{clear_hint}): ')
        if raw:
            changes[field] = '' if field in ('memo', 'tags') and raw == ':clear' else raw
    new = service.preview_update(args.id, **changes)
    if new == old:
        print('변경 없음')
        return 0
    print('수정 후:')
    show_transaction(new)
    if not confirm():
        print('취소')
        return 0
    service.update_transaction(args.id, **changes)
    print('[수정 완료] ' + args.id)
    return 0


@handle_errors
def handle_delete(args, service) -> int:
    show_transaction(service.get_transaction(args.id))
    if not confirm():
        print('취소')
        return 0
    service.delete_transaction(args.id)
    print('[삭제 완료] ' + args.id)
    return 0


def show_budget(amount, expense=None) -> None:
    if amount is None:
        print('예산 미설정')
    else:
        print(f'예산: {amount:,}원')
        if expense is not None:
            print('계산 불가 — 예산 0원' if amount == 0 else f'사용률 {expense / amount * 100:.1f}%')
            if expense > amount:
                print('[경고] 예산 초과')


@handle_errors
def handle_summary(args, service) -> int:
    result = service.get_monthly_summary(args.month, args.top)
    if not result['count']:
        print('거래 없음')
    print(f"총 수입: {result['income']:,}원\n총 지출: {result['expense']:,}원\n잔액: {result['balance']:,}원")
    show_budget(result['budget'], result['expense'])
    print(f'지출 TOP {args.top}')
    for name, amount in result['top']:
        print(f'{name}: {amount:,}원')
    return 0


@handle_errors
def handle_budget(args, service) -> int:
    if args.action == 'set':
        old, new = service.set_budget(args.month, input('예산 금액 (0 이상 정수): '))
        print(f"[예산 변경] {'미설정' if old is None else str(old.amount) + '원'} → {new.amount}원")
    else:
        budget = service.get_budget(args.month)
        show_budget(budget.amount if budget is not None else None)
    return 0


@handle_errors
def handle_category(args, service) -> int:
    if args.action == 'list':
        categories = service.list_categories()
        print('\n'.join(c.name for c in categories) if categories else '카테고리 없음')
    else:
        name = input('카테고리 이름: ')
        if args.action == 'add':
            service.add_category(name)
        else:
            service.delete_category(name)
        print('[완료] category ' + args.action)
    return 0


@handle_errors
def handle_import(args, service) -> int:
    print(f'[완료] imported={service.import_transactions(args.file)}')
    return 0


@handle_errors
def handle_export(args, service) -> int:
    count = service.export_transactions(args.file, month=args.month, start=args.start, end=args.end)
    print(f'[완료] exported={count} ({args.file})')
    return 0


@handle_errors
def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    repository = CsvRepository(args.data_dir)
    repository.initialize_files()
    return args.handler(args, BudgetService(repository))
