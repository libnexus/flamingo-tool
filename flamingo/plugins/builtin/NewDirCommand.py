import os

from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, PathCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError
from flamingo.core.vars.var_validators_builtin import TypeValidator


class NewDirCommand(FlamingoCommand):
    def __init__(self):
        path_arg = FlamingoArg(
            name="path",
            validator=TypeValidator(str),
            completer=PathCompleter(),
            required=True,
            help_text="Directory to create"
        )

        # Strictness is annoying.

        parser = ArgParser().add_arg(path_arg)

        super().__init__("newdir", "Create a directory.", ("mkdir",), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        path = parsed['path']

        cwd = kernel.resolve_var_path_fmt("$cwd")
        full_path = os.path.join(cwd, path)

        if os.path.exists(full_path):
            raise CommandExecutionError(f"Path already exists: {path}")

        try:
            os.makedirs(full_path, exist_ok=True)
            kernel.out(f"Created: {path}")
        except Exception as e:
            raise CommandExecutionError(f"Failed to create directory: {e}")
