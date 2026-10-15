"""터미널 입출력. 업무 규칙은 BudgetService에 위임한다."""
import argparse
from collections.abc import Iterable

from .errors import AppError, handle_errors
from .models import Transaction, parse_tags, positive
from .repository import Repository
from .service import BudgetService


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise AppError(message, f"{self.prog} --help로 옵션을 확인하세요.")


def parser() -> argparse.ArgumentParser:
    root = Parser(description="파일 기반 용돈 기입장 (Python 표준 라이브러리)")
    root.add_argument("--data-dir", default="./data", help="저장 폴더 (서브명령 앞에 지정, 기본: ./data)")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("add", help="대화형 거래 추가")
    listing = commands.add_parser("list", help="최신순 거래 조회")
    listing.add_argument("--limit", type=positive, default=10, help="표시할 건수 (기본: 10)")
    search = commands.add_parser("search", help="조건 검색 (AND 결합)")
    for flag in ("from", "to", "category", "tag"):
        search.add_argument("--" + flag, dest={"from": "start", "to": "end"}.get(flag, flag))
    search.add_argument("--type", choices=("income", "expense"))
    search.add_argument("-q", "--query", help="메모 부분 검색 (대소문자 무시)")
    summary = commands.add_parser("summary", help="월별 요약과 예산 사용률")
    summary.add_argument("--month", required=True)
    summary.add_argument("--top", type=positive, default=3)
    budget = commands.add_parser("budget", help="월 예산 관리")
    setter = budget.add_subparsers(dest="action", required=True).add_parser("set", help="예산 설정/갱신")
    setter.add_argument("--month", required=True)
    setter.add_argument("--amount", required=True, type=positive)
    category = commands.add_parser("category", help="카테고리 관리")
    actions = category.add_subparsers(dest="action", required=True)
    for action in ("add", "list", "remove"):
        actions.add_parser(action)
    update = commands.add_parser("update", help="옵션형 거래 수정")
    update.add_argument("--id", required=True)
    for field in ("date", "type", "category", "amount", "memo", "tags"):
        options = {"type": positive} if field == "amount" else {}
        if field == "type":
            options["choices"] = ("income", "expense")
        update.add_argument("--" + field, **options)
    delete = commands.add_parser("delete", help="ID로 거래 삭제")
    delete.add_argument("--id", required=True)
    importing = commands.add_parser("import", help="CSV 전체 성공/실패 방식 가져오기")
    importing.add_argument("--from", dest="source", required=True)
    exporting = commands.add_parser("export", help="월 또는 기간 CSV 내보내기")
    exporting.add_argument("--out", required=True)
    exporting.add_argument("--month")
    exporting.add_argument("--from", dest="start")
    exporting.add_argument("--to", dest="end")
    return root


def show_transactions(transactions: Iterable[Transaction]) -> None:
    count = 0
    for tx in transactions:
        print(f"{tx.id} | {tx.date} | {tx.type} | {tx.category} | {tx.amount:,}원 | {tx.memo} | {','.join(tx.tags)}")
        count += 1
    if not count:
        print("데이터 없음")


@handle_errors
def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    service = BudgetService(Repository(args.data_dir))
    if args.command == "add":
        values = {}
        for field, label in (("date", "날짜 (YYYY-MM-DD)"), ("type", "종류 (income/expense)"),
                             ("category", "카테고리"), ("amount", "금액"), ("memo", "메모 (선택)"),
                             ("tags", "태그 (쉼표 구분, 선택)")):
            values[field] = input(label + ": ").strip()
        tx = Transaction.create(**values)
        service.add(tx)
        print(f"[저장 완료] id={tx.id}")
    elif args.command == "list":
        show_transactions(service.select(limit=args.limit))
    elif args.command == "search":
        show_transactions(service.select(start=args.start, end=args.end, category=args.category,
                                         type=args.type, query=args.query, tag=args.tag))
    elif args.command == "summary":
        result = service.summary(args.month, args.top)
        if not result["count"]:
            print("데이터 없음")
        print(f"총 수입: {result['income']:,}원\n총 지출: {result['expense']:,}원\n잔액: {result['balance']:,}원")
        if result["budget"] is not None:
            print(f"예산: {result['budget']:,}원 (사용률 {result['expense'] / result['budget'] * 100:.1f}%)")
            if result["expense"] > result["budget"]:
                print("[경고] 예산 초과")
        print(f"지출 TOP {args.top}")
        for rank, (name, amount) in enumerate(result["top"], 1):
            print(f"{rank}) {name}: {amount:,}원")
    elif args.command == "budget":
        service.set_budget(args.month, args.amount)
        print(f"[저장 완료] {args.month} 예산 {args.amount:,}원")
    elif args.command == "category":
        if args.action == "list":
            for name in sorted(service.repo.category_names()):
                print("- " + name)
        else:
            name = input("카테고리 이름: ")
            service.category(args.action, name)
            print(f"[완료] category {args.action}: {name.strip()}")
    elif args.command == "update":
        changes = {key: getattr(args, key) for key in ("date", "type", "category", "amount", "memo", "tags")
                   if getattr(args, key) is not None}
        if "tags" in changes:
            changes["tags"] = parse_tags(changes["tags"])
        service.change(args.id, changes)
        print(f"[수정 완료] id={args.id}")
    elif args.command == "delete":
        service.change(args.id)
        print(f"[삭제 완료] id={args.id}")
    elif args.command == "import":
        count = service.import_csv(args.source)
        print(f"[완료] imported={count}")
    elif args.command == "export":
        count = service.export_csv(args.out, month=args.month, start=args.start, end=args.end)
        print(f"[완료] {args.out} ({count} records)")
    return 0
