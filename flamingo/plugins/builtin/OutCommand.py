from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg
from flamingo.core.commands.parser import ArgParser
from flamingo.core.vars.flamingo_var import FlamingoVar


class OutCommand(FlamingoCommand):
    def __init__(self):
        text_arg = FlamingoArg(
            name="text",
            greedy=True,  # Consumes all remaining args
            required=True,
            help_text="Text to display"
        )

        raw_flag = FlamingoArg(name="raw", is_flag=True, help_text="Do not resolve variables")

        parser = ArgParser().add_arg(text_arg).add_flag("raw", raw_flag)

        super().__init__("out", "Print text to the console.", ("echo", "print"), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        raw_text = " ".join(map(str, parsed['text']))
        is_raw = parsed['raw']

        if is_raw:
            kernel.out(raw_text)
        else:
            temp_var = FlamingoVar(raw_text)
            resolved = temp_var.to_string_for_env(resolver_func=kernel.resolve_var_path)
            kernel.out(resolved)
