import os
import shutil
from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, PathCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError


class CopyCommand(FlamingoCommand):
    def __init__(self):
        src_arg = FlamingoArg(name="src", completer=PathCompleter(), required=True, help_text="Source")
        dest_arg = FlamingoArg(name="dest", completer=PathCompleter(), required=True, help_text="Destination")
        rec_flag = FlamingoArg(name="recursive", is_flag=True, help_text="Recursive copy")

        parser = ArgParser().add_arg(src_arg).add_arg(dest_arg).add_flag("r", rec_flag)
        super().__init__("copy", "Copy files or directories.", ("cp",), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        src = os.path.expanduser(parsed['src'])
        dest = os.path.expanduser(parsed['dest'])
        recursive = parsed['recursive']

        if not os.path.exists(src):
            raise CommandExecutionError(f"Source not found: {src}")

        try:
            if os.path.isdir(src):
                if not recursive:
                    # Unix fails. We fail.
                    raise CommandExecutionError(f"Source is directory. Use -r.")
                shutil.copytree(src, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dest)

            kernel.out(f"Copied {src} -> {dest}")
        except Exception as e:
            raise CommandExecutionError(f"Copy failed: {e}")