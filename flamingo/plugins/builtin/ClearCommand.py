import os

from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.parser import ArgParser


class ClearCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("clear", "Clear the terminal screen.", ("cls",), ArgParser())

    def execute(self, kernel, args):
        self.arg_parser.parse(args)
        os.system('cls' if os.name == 'nt' else 'clear')
