import os
import time
from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, PathCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError


class TouchCommand(FlamingoCommand):
    def __init__(self):
        path_arg = FlamingoArg(
            name="path",
            completer=PathCompleter(),
            required=True,
            help_text="File to create/update"
        )

        parser = ArgParser().add_arg(path_arg)
        super().__init__("touch", "Update timestamp or create file.", ("new",), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        path = os.path.expanduser(parsed['path'])

        try:
            if os.path.exists(path):
                os.utime(path, None)
            else:
                with open(path, 'a'):
                    os.utime(path, None)
        except Exception as e:
            raise CommandExecutionError(f"Touch failed: {e}")