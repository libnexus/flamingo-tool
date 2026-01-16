from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Any

from flamingo.core.debug.error import FlamingoException

if TYPE_CHECKING:
    from flamingo.core.vars.flamingo_var import FlamingoVar


class VarTable:
    def __init__(self, name: str, parent: Optional['VarTable'] = None):
        self.name = name
        self.parent = parent
        self.children: dict[str, 'VarTable'] = {}
        self.values: dict[str, FlamingoVar] = {}

    def child(self, name: str) -> VarTable:
        if name not in self.children:
            self.children[name] = VarTable(name, parent=self)
        return self.children[name]

    def resolve(self, path: list[str], sentinel: object) -> FlamingoVar | object:
        if len(path) == 0:
            raise FlamingoException("Empty path passed to variable resolution")
        elif len(path) == 1:  # Resolve a variable
            if path[0] in self.values:
                return self.values[path[0]]
            else:
                return sentinel
        elif path[0] in self.children:
            return self.children[path[0]].resolve(path[1:], sentinel)
        return sentinel

    def set_variable(self, key: str, value: Any, as_reference: bool = False):
        """
        Smart Setter.
        If key exists: Tries to set the value INSIDE the existing FlamingoVar (Enforcing validators).
        If key missing: Creates a new FlamingoVar.

        :param as_reference: If True, 'value' must be a FlamingoVar, and it's linked directly
        """
        if as_reference:
            from flamingo.core.vars.flamingo_var import FlamingoVar
            if not isinstance(value, FlamingoVar):
                value = FlamingoVar(value)

            self.values[key] = value
            return

        if key in self.values:
            self.values[key].set(value)
        else:
            # Create new (Default behavior)
            from flamingo.core.vars.flamingo_var import FlamingoVar
            # If the value passed is already a FlamingoVar (from a lookup), unwrap it
            if isinstance(value, FlamingoVar):
                value = value.value

            self.values[key] = FlamingoVar(value)

    def full_table(self):
        values = self.values.copy()
        for child in self.children.values():
            values.update(child.full_table())
        return values
