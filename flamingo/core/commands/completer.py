from __future__ import annotations

from re import Pattern
from typing import TYPE_CHECKING, Optional

from flamingo.core.vars.var_validator import Validator

if TYPE_CHECKING:
    from flamingo.core.kernel import FlamingoKernel


class ArgCompleter:
    """Base class for autocomplete logic."""

    def complete(self, kernel: FlamingoKernel, prefix: str, full_args: list[str] = None, arg_index: int = 0) -> list[
        tuple[str, str]]:
        return []


class StaticCompleter(ArgCompleter):
    """Completes from a fixed list (e.g. ['latte', 'mocha'])."""

    def __init__(self, options: list[str]):
        self.options = options

    def complete(self, kernel, prefix, full_args=None, arg_index=None):
        return [(o, "Option") for o in self.options if o.startswith(prefix)]


class UserCompleter(ArgCompleter):
    """Completes Flamingo Users."""

    def complete(self, kernel, prefix, full_args=None, arg_index=None):
        return [(u, "User") for u in kernel.users.keys() if u.startswith(prefix)]


class PathCompleter(ArgCompleter):
    """Completes Filesystem Paths."""

    def __init__(self, must_be_dir: Optional[bool] = None, must_be_file: Optional[bool] = None, re_filter: Optional[Pattern] = None):
        super().__init__()
        self.must_be_dir = must_be_dir
        self.must_be_file = must_be_file
        self.re_filter = re_filter

    def complete(self, kernel, prefix, full_args=None, arg_index=None):
        import os
        directory = os.path.dirname(prefix) or "."
        base = os.path.basename(prefix)
        try:
            ret = []
            for f in os.listdir(directory):
                if self.must_be_dir and not os.path.isdir(f):
                    continue 

                if self.must_be_file and os.path.isdir(f):
                    continue

                if self.re_filter and not self.re_filter.match(f):
                    continue

                if f.startswith(base):
                    ret.append((f, "Dir" if os.path.isdir(f) else "Flamingo Script" if f.endswith(".fgo") else "file"))
            return ret
        except (NotADirectoryError, FileNotFoundError):
            return []


class CommandNameCompleter(ArgCompleter):
    def complete(self, kernel, prefix, full_args=None, arg_index=None):
        return [(name, cmd.description) for name, cmd in kernel.commands.items() if name.startswith(prefix)]


class PluginNameCompleter(ArgCompleter):
    def complete(self, kernel, prefix, full_args=None, arg_index=None):
        return [(p.name, f"v{p.version}") for p in kernel.plugin_manager.plugins if p.name.startswith(prefix)]


class FlamingoArg:
    def __init__(self, name: str, validator: Validator = None, completer: ArgCompleter = None,
                 default=None, required=True, is_flag=False, greedy=False, help_text=""):
        self.name = name
        self.validator = validator
        self.completer = completer or ArgCompleter()
        self.default = default
        self.required = required
        self.is_flag = is_flag
        self.greedy = greedy
        self.help_text = help_text

    def validate(self, value):
        if self.validator:
            self.validator.validate(value)
        return value
