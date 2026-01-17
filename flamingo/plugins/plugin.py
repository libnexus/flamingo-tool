from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Type, TYPE_CHECKING, Tuple

from flamingo.core.debug.logging import logger

if TYPE_CHECKING:
    from flamingo.core.commands.command import FlamingoCommand
    from flamingo.core.kernel import FlamingoKernel


class FlamingoPlugin(ABC):
    """
    Abstract Base Class for all Flamingo Extensions.
    Enforces identity and lifecycle handling.
    """

    def __init__(self, name: str, author: str, description: str = "", version: str = "0.1"):
        self.name = name
        self.author = author
        self.description = description
        self.version = version

        self.commands: dict[str, FlamingoCommand] = {}
        self.command_aliases: dict[str, tuple[str]] = {}

    @abstractmethod
    def load(self, kernel: FlamingoKernel) -> tuple[int, int]:
        """
        Called when the plugin is loaded (file load - added to plugin manager).

        :return a tuple of number of warnings and number of errors while loading.
        """

    @abstractmethod
    def unload(self, kernel: FlamingoKernel) -> tuple[int, int]:
        """
        Called before the plugin is unloaded (file unload - removed from plugin manager).

        :return a tuple of number of warnings and number of errors while unloading.
        """

    def add_command(self, cls: Type[FlamingoCommand]) -> FlamingoCommand:
        # All flamingo command subclasses are built to be singletons
        # TODO consider either catching bad singletons or continue to let it propagate
        command = cls()
        self.commands[command.name] = command
        for alias in command.aliases:
            self.commands[alias] = command
        self.command_aliases[command.name] = command.aliases
        return command

    def remove_command(self, name: str):
        command = self.commands[name]
        del self.commands[name]
        del self.command_aliases[name]

        for alias in command.aliases:
            del self.commands[alias]

    def get_command(self, name: str):
        return self.commands[name]

    def log(self, what: str, level=logging.INFO):
        logger.log(level, f"[{self.name}] {what}")