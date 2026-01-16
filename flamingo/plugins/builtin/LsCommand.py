import os

from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, PathCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError
from flamingo.core.vars.var_validators_builtin import TypeValidator
from flamingo.interface.text import FmtBuilder


class LsCommand(FlamingoCommand):
    def __init__(self):
        path_arg = FlamingoArg(
            name="path",
            validator=TypeValidator(str),
            completer=PathCompleter(),
            default=None,
            required=False,
            help_text="Directory to list"
        )

        long_flag = FlamingoArg(
            name="long",
            is_flag=True,
            help_text="Detailed View"
        )

        parser = ArgParser() \
            .add_arg(path_arg) \
            .add_flag("l", long_flag)

        super().__init__(
            name="ls",
            description="List files.",
            aliases=["dir"],
            arg_parser=parser
        )

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        target = parsed['path']

        if target is None:
            target = kernel.resolve_var_path_fmt("$cwd")

        if not os.path.exists(target):
            raise CommandExecutionError(f"Path not found: {target}")

        files = os.listdir(target)
        if parsed['long']:
            kernel.out(f"Directory: {os.path.abspath(target)}")
            kernel.out("-" * 20)
            for f in files:
                kernel.out(f"- {f}")
        else:
            b = FmtBuilder()
            for f in files:
                b.lavender(f) if os.path.isdir(f) else b.rosewater(f)
            kernel.out(b.join("  ").build())
