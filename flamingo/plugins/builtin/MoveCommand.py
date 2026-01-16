import os
import shutil

from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, PathCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError


class MoveCommand(FlamingoCommand):
    def __init__(self):
        src_arg = FlamingoArg(name="src", completer=PathCompleter(), required=True, help_text="Source")
        dest_arg = FlamingoArg(name="dest", completer=PathCompleter(), required=True, help_text="Destination")

        parser = ArgParser().add_arg(src_arg).add_arg(dest_arg)
        super().__init__("move", "Move or rename files.", ("mv", "rename"), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        src = os.path.expanduser(parsed['src'])
        dest = os.path.expanduser(parsed['dest'])

        if not os.path.exists(src):
            raise CommandExecutionError(f"Source not found: {src}")

        try:
            shutil.move(src, dest)
            kernel.out(f"Moved {src} -> {dest}")
        except Exception as e:
            raise CommandExecutionError(f"Move failed: {e}")
