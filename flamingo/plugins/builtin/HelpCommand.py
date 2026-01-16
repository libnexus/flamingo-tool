from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, CommandNameCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.interface.text import FmtBuilder


class HelpCommand(FlamingoCommand):
    def __init__(self):
        cmd_arg = FlamingoArg(
            name="command",
            required=False,
            completer=CommandNameCompleter(),
            help_text="Show details for specific command"
        )

        parser = ArgParser().add_arg(cmd_arg)

        super().__init__("help", "List commands or show usage.", ["?"], parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        target = parsed['command']

        # TODO include aliases

        if target:
            if target not in kernel.commands:
                kernel.out(f"Unknown command: {target}")
                return

            cmd = kernel.commands[target]

            b = FmtBuilder()

            (b.surface2("   Name: ")
             .flamingo(cmd.name).raw("\n")
             .surface2(f"       {cmd.description}\n")
             .surface2(f"   Usage: {cmd.name} ")
             .extend(cmd.arg_parser.get_signature_highlighted(kernel).join(" ").segments).raw("\n"))

            if cmd.arg_parser.positionals:
                b.surface2("\n   Arguments:\n")
                for arg in cmd.arg_parser.positionals:
                    b.surface2(f"     {arg.name:<15}")

                    if arg.required:
                        b.green(f"{"Required":<10}")
                    else:
                        b.yellow(f"{"Optional":<10}")

                    b.surface2(f" {arg.help_text}\n")

            if cmd.arg_parser.flags:
                b.surface2("   Options:\n")
                for name, arg in cmd.arg_parser.flags.items():
                    b.surface2(f"     --{name:<13}").surface1(arg.help_text).raw("\n")

            kernel.out(b.build())
            return

        kernel.out(build_commands_list(kernel.commands).build())


def build_commands_list(commands: dict[str, FlamingoCommand]):
    b = FmtBuilder()

    (b.surface2("Available Commands:\n")
     .flamingo(f"   {"Name":<20}")
     .peach(f"{"Signature":<50}")
     .surface2(f"{"Description"}\n")
     .text("   " + "-" * 90)
     .raw("\n"))

    for name in sorted(commands.keys()):
        cmd = commands[name]
        if name != cmd.name:
            continue

        sig = cmd.arg_parser.get_signature()
        desc = cmd.description
        if len(desc) > 50:
            desc = desc[:47] + "..."

        b.flamingo(f"   {name:<20}").peach(f"{sig:<50}").surface2(desc).raw("\n")
    return b
