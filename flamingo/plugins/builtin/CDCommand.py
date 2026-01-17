import os

from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, PathCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError
from flamingo.core.vars.var_validators_builtin import PathValidator


class CDCommand(FlamingoCommand):
    def __init__(self):
        path_arg = FlamingoArg(
            name="path",
            validator=PathValidator(must_exist=True, must_be_dir=True),
            completer=PathCompleter(must_be_dir=True),
            required=True,
            help_text="Target directory"
        )

        parser = ArgParser().add_arg(path_arg)
        super().__init__("cd", "Change current directory.", ("goto",), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        target = parsed['path']

        # cd ~
        target = os.path.expanduser(target)

        # cd .
        cwd_var = kernel.resolve_var_path("$cwd")
        current_abs = cwd_var.value

        final_path = os.path.abspath(os.path.join(current_abs, target))

        if not os.path.isdir(final_path):
            raise CommandExecutionError(f"Not a directory: {final_path}")

        try:
            cwd_var.set(final_path)
            os.chdir(final_path)
        except Exception as e:
            raise CommandExecutionError(f"Failed to change directory: {e}")
