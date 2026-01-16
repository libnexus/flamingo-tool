from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flamingo.core.vars.var_table import VarTable


@dataclass
class User:
    name: str
    var_table: VarTable
