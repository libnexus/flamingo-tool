from dataclasses import dataclass
from typing import Optional

from flamingo.scripting.token.token_types import Token


@dataclass(slots=True, frozen=True)
class ASTNode:
    """Base class for all nodes to ensure they are slotted/frozen."""
    token: Token


@dataclass(slots=True, frozen=True)
class Expr(ASTNode):
    pass


@dataclass(slots=True, frozen=True)
class Stmt(ASTNode):
    pass


@dataclass(slots=True, frozen=True)
class Literal(Expr):
    """Primitive values: 1, 1.5, "hello", True, None"""
    value: int | float | str | bool | None


@dataclass(slots=True, frozen=True)
class Identifier(Expr):
    """Standard logic names: x, my_var, width (in macros)"""
    name: str


@dataclass(slots=True, frozen=True)
class Variable(Expr):
    """The {...} syntax: {user_id}, {context_ref}"""
    name: str


@dataclass(slots=True, frozen=True)
class ListExpr(Expr):
    """Syntax: [1, 2, x]"""
    elements: tuple[Expr, ...]


@dataclass(slots=True, frozen=True)
class TupleExpr(Expr):
    """Syntax: (1, 2, x)"""
    elements: tuple[Expr, ...]


@dataclass(slots=True, frozen=True)
class Binary(Expr):
    """Syntax: x + y, a && b"""
    left: Expr
    op: int
    right: Expr


@dataclass(slots=True, frozen=True)
class Unary(Expr):
    """Syntax: -x, !y"""
    op: int
    right: Expr


@dataclass(slots=True, frozen=True)
class Block(Stmt):
    statements: tuple[Stmt, ...]


@dataclass(slots=True, frozen=True)
class Command(Stmt):
    """A raw line of text that didn't trigger logic mode."""
    text: str


@dataclass(slots=True, frozen=True)
class SetStmt(Stmt):
    """!set name = value"""
    target: str
    value: Expr


@dataclass(slots=True, frozen=True)
class IfStmt(Stmt):
    """!if expr"""
    condition: Expr
    then_branch: Block
    else_branch: Optional[Stmt] = None  # Can be Block or IfStmt (elif)


@dataclass(slots=True, frozen=True)
class WhileStmt(Stmt):
    """!while expr"""
    condition: Expr
    body: Block


@dataclass(slots=True, frozen=True)
class ForStmt(Stmt):
    """!for x in list"""
    target: str
    iterable: Expr
    body: Block


@dataclass(slots=True, frozen=True)
class MacroDef(Stmt):
    """!macro name(arg1, arg2)"""
    name: str
    params: tuple[str, ...]
    body: Block


@dataclass(slots=True, frozen=True)
class MacroCall(Stmt):
    """!do name(val1, val2) - Placeholder for Compiler Expansion"""
    name: str
    args: tuple[Expr, ...]
