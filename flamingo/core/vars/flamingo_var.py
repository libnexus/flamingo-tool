from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from flamingo.core.debug.error import ReadOnlyError, FlamingoException
from flamingo.core.debug.logging import logger

if TYPE_CHECKING:
    from flamingo.core.vars.var_validator import Validator


class FlamingoWrapper(ABC):
    @abstractmethod
    def show_as_string(self, max_size: int) -> str:
        ...


def show_as_string(value: str | int | float | bool | list | tuple | dict | FlamingoWrapper, max_size=40):
    if isinstance(value, (str, int, float, bool, FlamingoWrapper)):
        if isinstance(value, FlamingoWrapper):
            string = value.show_as_string(max_size)
        else:
            string = str(value)
        if len(string) > max_size:
            string = string[:max_size - 3] + "..."
        return string
    elif isinstance(value, (list, tuple)):
        components = []
        for item in value:
            string = show_as_string(item)
            if len(", ".join(components)) + len(string) > max_size:
                components.append("...")
                break
        if isinstance(value, list):
            return f"L({", ".join(components)})"
        else:
            return f"T({", ".join(components)}"
    elif isinstance(value, dict):
        return "{...}"
    else:
        return "{%s}" % value.__class__.__name__


class FlamingoVar:
    def __init__(self,
                 value: str | int | float | bool | list | tuple | dict | FlamingoWrapper,
                 validator: Validator = None,
                 readonly=False,
                 recursive=False):
        """

        :param value: value of the variable
        :param validator: optional validator for the shape of a variable (e.g. the case of reserved variable slots)
        :param readonly: if the variable can even be overwritten
        :param recursive: if the variable will re-format itself after being formatted
        """

        self.value = value
        self.validator = validator
        self.readonly = False
        self.recursive = recursive

        self.set(value)

        self.readonly = readonly

    def set(self, new_value: object):
        if not isinstance(new_value, (str, int, float, bool, list, tuple, dict, FlamingoWrapper)):
            raise FlamingoException("Custom values must implement FlamingoWrapper interface")

        if self.readonly:
            logger.warning(f"Write rejected: Variable is read-only.")
            raise ReadOnlyError("Variable is read-only")

        if self.validator:
            self.validator.validate(new_value)

        self.value = new_value

    def get(self):
        return self.value

    def to_string_for_env(self, resolver_func=None, depth: int = 0) -> str:
        """
        Returns string representation.
        Handles nested recursion: {@user.config.{@user.selection}}

        Supports:

        >>> "{@user.path}"      # -> User Pool
        >>> "{$env.path}"       # -> Environment Pool
        >>> "{#system.path}"    # -> System Pool

        :param resolver_func: Function(path) -> FlamingoVar
        :param depth: Recursion limiter
        """
        raw = str(self.get())

        if resolver_func:
            if depth > 10:  # Safety break
                return raw

            # Iterative inside out solver
            # Match '{' followed by one of [@, $, #], then any chars not containing { or }, ending with '}'
            pattern = re.compile(r'\{([@$#][^{}]+)}')

            current_str = raw
            iteration = 0

            while iteration < 20:  # Prevent infinite loops
                match = pattern.search(current_str)
                if not match:
                    break  # No more variables to resolve

                full_token = match.group(0)  # e.g. {@user.name}
                path = match.group(1)  # e.g. @user.name


                try:
                    target_var = resolver_func(path)

                    # Pass depth + 1 to prevent infinite variable reference loops
                    resolved_val_str = target_var.to_string_for_env(resolver_func, depth + 1)
                    current_str = current_str.replace(full_token, resolved_val_str, 1)

                except Exception as e:
                    logger.debug(f"Failed to resolve {path}: {e}")
                    break

                iteration += 1

            return current_str

        return raw


class DynamicVar(FlamingoVar):
    def __init__(self, obj, *args):
        super().__init__(0, readonly=True)
        self.obj = obj
        self.args = args

    def get(self):
        value = self.obj
        for arg in self.args:
            value = getattr(value, arg)
        return str(value)
