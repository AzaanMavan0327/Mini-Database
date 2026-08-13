from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class Condition:
    column: str
    operator: str
    value: Union[int, str]


# A WHERE clause is a list of AND-groups, OR'd together:
#   [[cond1, cond2], [cond3]]  means  (cond1 AND cond2) OR cond3
# This mirrors how AND binds tighter than OR in real SQL.
WhereClause = List[List[Condition]]


@dataclass
class SelectStatement:
    table_name: str
    where: Optional[WhereClause] = None


@dataclass
class InsertStatement:
    table_name: str
    key: int
    value: str