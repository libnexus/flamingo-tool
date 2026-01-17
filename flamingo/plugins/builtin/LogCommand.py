from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.logging import get_recent_logs
from flamingo.core.vars.var_validators_builtin import TypeValidator, IntValidator
from flamingo.interface.text import FmtBuilder


class LogCommand(FlamingoCommand):
    def __init__(self):
        count_arg = FlamingoArg(
            name="count",
            validator=IntValidator(minimum=1),
            default=20,
            help_text="Number of lines to show"
        )

        parser = ArgParser().add_arg(count_arg)

        super().__init__("log", "Show recent system logs.", ("dmesg",), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        count = int(parsed['count'])

        raw_lines = get_recent_logs(count)

        if not raw_lines:
            kernel.out(FmtBuilder.from_kernel(kernel).overlay1("No logs recorded.").build())
            return

        b = FmtBuilder.from_kernel(kernel)
        b.surface2(f"Displaying last {len(raw_lines)} events:\n")
        b.text("-" * 60).raw("\n")

        for line in raw_lines:
            self._format_line(b, line)

        kernel.out(b.build())

    @staticmethod
    def _format_line(b: FmtBuilder, line: str):
        # Format: '%(asctime)s | %(name)-10s | %(levelname)-7s | %(message)s'
        parts = line.split("|")

        if len(parts) < 4:
            # Just in case, for unformatted lines
            b.text(line).raw("\n")
            return

        timestamp = parts[0].strip()
        module = parts[1].strip()
        level = parts[2].strip()
        msg = "|".join(parts[3:]).strip()  # Rejoin msg in case it had pipes

        b.overlay0(f"{timestamp} ")

        b.overlay1(f"[{module}] ")

        if level == "INFO":
            b.blue(f"{level:<7}")
        elif level == "WARNING":
            b.yellow(f"{level:<7}")
        elif level == "ERROR":
            b.red(f"{level:<7}", bold=True)
        elif level == "CRITICAL":
            b.maroon(f"{level:<7}", bold=True)
        elif level == "DEBUG":
            b.surface2(f"{level:<7}")
        else:
            b.text(f"{level:<7}")

        b.text(f" {msg}").raw("\n")
