"""가계부 값 객체. 값 검증은 validators에서 수행한다."""
from dataclasses import dataclass, field
from datetime import date as Date


@dataclass
class Transaction:
    id: str
    type: str
    date: Date
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class Category:
    name: str


@dataclass
class Budget:
    month: str
    amount: int
