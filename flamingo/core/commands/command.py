from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flamingo.core.commands.parser import ArgParser
    from flamingo.core.kernel import FlamingoKernel


class FlamingoCommand:
    def __init__(self, name, description, aliases, arg_parser):
        self.name: str = name
        self.description: str = description
        self.aliases: tuple[str] = aliases
        self.arg_parser: ArgParser = arg_parser

    def execute(self, kernel: FlamingoKernel,
                args: list):
        raise NotImplementedError

    def suggest(self, kernel: FlamingoKernel,
                current_word: str, previous_words: list[str]):
        """Returns list of (completion, meta) tuples."""
        return [self.name]