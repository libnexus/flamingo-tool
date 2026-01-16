from __future__ import annotations
from typing import Any, List, TYPE_CHECKING

from flamingo.core.debug.error import FlamingoException
from flamingo.core.vars.flamingo_var import FlamingoVar
from flamingo.core.vars.var_table import VarTable
from flamingo.interface.shell import command_shlex
from flamingo.interface.text import FmtBuilder
from flamingo.scripting.token.token_types import *
from flamingo.scripting.parse.ast import (
    Expr, Stmt, Literal, Identifier, Variable, ListExpr, TupleExpr,
    Binary, Unary, Block, Command, SetStmt, IfStmt, WhileStmt, ForStmt, ASTNode
)

if TYPE_CHECKING:
    from flamingo.core.kernel import FlamingoKernel


class FlamingoScriptError(FlamingoException):
    def __init__(self, token: Token, message: str):
        super().__init__(message)
        self.token = token


class ReturnSignal(Exception):
    """
    Control flow exception to unwind the stack when returning from a block/macro.
    Much faster than passing state flags through every recursive call.
    """
    __slots__ = ('value',)

    def __init__(self, value: Any):
        self.value = value


class Interpreter:
    __slots__ = ('kernel', 'name', 'source', 'local_vars', 'environment')

    def __init__(self, kernel: FlamingoKernel, name: str, source: str = None,
                 local_vars: dict[str, FlamingoVar] = None):
        self.kernel = kernel
        self.name = name
        self.source = source
        self.local_vars = kernel.current_user.var_table.child("script")
        local_vars and self.local_vars.values.update(local_vars)
        self.environment: List[VarTable] = [self.local_vars]

    def get_local(self, name: str) -> Any:
        return self.get_var("{@script.%s}" % name)

    def get_var(self, name: str) -> Any:
        var = self.kernel.resolve_var_path(name)
        return var.get()

    def set_var(self, name: str, value: Any):
        """Sets variable. Defaults to current scope."""
        self.local_vars.set_variable(name, value)

        # TODO elaborate on setting logic, include !varset or varset command

    def push_scope(self):
        self.environment.append(self.local_vars.child("__scope"))

    def pop_scope(self):
        self.environment.pop()

    def evaluate(self, expr: Expr) -> Any:
        """
        The hot path. Uses structural pattern matching for dispatch.
        """
        match expr:
            case Literal(_, value):
                return value

            case Identifier(_, name):
                return self.get_local(name)

            case Variable(_, name):
                return self.get_var(name)

            case Binary(_, left, op, right):
                l_val = self.evaluate(left)
                r_val = self.evaluate(right)

                # TODO type checking

                try:
                    if op == T_PLUS:
                        return l_val + r_val
                    elif op == T_MINUS:
                        return l_val - r_val
                    elif op == T_STAR:
                        return l_val * r_val
                    elif op == T_SLASH:
                        return l_val / r_val
                    elif op == T_DOUBLE_EQUALS:
                        return l_val == r_val
                    elif op == T_BANG_EQUALS:
                        return l_val != r_val
                    elif op == T_MORE_THAN:
                        return l_val > r_val
                    elif op == T_LESS_THAN:
                        return l_val < r_val
                    elif op == T_MORE_THAN_EQUALS:
                        return l_val >= r_val
                    elif op == T_LESS_THAN_EQUALS:
                        return l_val <= r_val
                    elif op == T_KEYWORD:
                        pass
                except TypeError:
                    raise FlamingoScriptError(expr.token,
                                              f"Unsupported operand type(s) for: {type(l_val)} and {type(r_val)}")

            case Unary(_, op, right):
                r_val = self.evaluate(right)
                if op == T_MINUS:
                    return -r_val
                elif op == T_BANG:
                    return not r_val

            case ListExpr(_, elements):
                return [self.evaluate(e) for e in elements]

            case TupleExpr(_, elements):
                return tuple(self.evaluate(e) for e in elements)

        raise FlamingoScriptError(expr.token, f"Unknown Expression Node: {expr}")

    def execute(self, stmt: Stmt):
        """
        The Statement Runner.
        """
        match stmt:
            case Command(_, text):
                self.handle_command(text)

            case SetStmt(_, target, value):
                val = self.evaluate(value)
                self.set_var(target, val)

            case IfStmt(_, condition, then_branch, else_branch):
                if self.evaluate(condition):
                    self.execute(then_branch)
                elif else_branch:
                    self.execute(else_branch)

            case WhileStmt(_, condition, body):
                while self.evaluate(condition):
                    self.execute(body)

            case ForStmt(_, target, iterable, body):
                iter_val = self.evaluate(iterable)
                # Optimization by direct iteration without creating an iterator object if possible
                for item in iter_val:
                    self.environment[-1].set_variable(target, item)
                    self.execute(body)

            case Block(_, statements):
                try:
                    for s in statements:
                        self.execute(s)
                finally:
                    pass

    def interpret(self, node: Stmt | Expr) -> Any:
        try:
            if isinstance(node, Stmt):
                self.execute(node)
            else:
                return self.evaluate(node)
        except FlamingoScriptError as e:
            if self.source is not None:
                location = highlight_location(self.source, e.token)

                b = FmtBuilder.from_kernel(self.kernel)
                b.red(f"Error at ").yellow(str(e.token.line)).red(", ").yellow(str(e.token.col)) \
                    .red(f":\n{location}\n{e.message}")

                self.kernel.out(b.build())
        finally:
            self.local_vars.values.clear()  # Tidy up

    def handle_command(self, text: str):
        cmd_name, cmd_args = command_shlex(text)
        self.kernel.execute_command(cmd_name, cmd_args)
