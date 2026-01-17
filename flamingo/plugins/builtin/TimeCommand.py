import time

from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, CommandNameCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.interface.text import FmtBuilder


class TimeCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("time", "Measure execution time.", (), ArgParser())
        self.arg_parser.add_arg(FlamingoArg(name="cmd", greedy=True, required=True, completer=CommandNameCompleter()))

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        cmd_parts = parsed['cmd']

        target_cmd = cmd_parts[0]
        target_args = cmd_parts[1:]

        start = time.perf_counter()
        kernel.execute_command(target_cmd, target_args)
        end = time.perf_counter()

        kernel.out(FmtBuilder.from_kernel(kernel).overlay1(f"Real: {format_duration(end - start)}").build())


def format_duration(seconds: float) -> str:
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f}µs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    else:
        return f"{seconds:.2f}s"
