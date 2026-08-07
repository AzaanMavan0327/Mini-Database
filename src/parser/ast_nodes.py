from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class Condition:
    column: str
    operator: str
    value: Union[int, str]


@dataclass
class SelectStatement:
    table_name: str
    where: Optional[Condition] = None


@dataclass
class InsertStatement:
    table_name: str
    key: int
    value: str
