from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import FlamingoExit


class ExitCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("exit", "Exits the shell.", ("quit",), ArgParser())

    def execute(self, kernel, args):
        self.arg_parser.parse(args)
        raise FlamingoExit
