import flamingo
from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.kernel import FlamingoKernel
from flamingo.interface.text import FmtBuilder
from flamingo.plugins.plugin import FlamingoPlugin


class PingPlugin(FlamingoPlugin):
    def load(self, kernel) -> tuple[int, int]:
        return 0, 0

    def unload(self, kernel) -> tuple[int, int]:
        return 0, 0

    def __init__(self):
        super().__init__("ping", "shaun", "It's a pinging plugin!", "0.1")


ping_plugin = PingPlugin()


@ping_plugin.add_command
class MyCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("ping", "Ping", (), flamingo.core.commands.parser.ArgParser())

    def execute(self, kernel: FlamingoKernel, args: list):
        _ = self.arg_parser.parse(args)
        kernel.out(FmtBuilder.from_kernel(kernel).surface2("pong!").build())
