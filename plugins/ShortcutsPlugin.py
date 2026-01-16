import os
from logging import WARN

from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError
from flamingo.core.kernel import FlamingoKernel
from flamingo.interface.shell import command_shlex
from flamingo.interface.text import FmtBuilder
from flamingo.plugins.plugin import FlamingoPlugin

path = os.path.dirname(os.path.abspath(__file__))


class AdvancedShortcutsPlugin(FlamingoPlugin):
    def __init__(self):
        super().__init__("shortcuts", "shaun", "a simple plugin to add easily configurable, advanced shortcuts", "0.1")
        self.shortcuts: list[tuple[tuple[str, ...], tuple[str, ...]]] = []

    def load(self, kernel) -> tuple[int, int]:
        if not os.path.exists(path + "/shortcuts.conf"):
            with open(path + "/shortcuts.conf", "w+") as file:
                file.write("")
        else:
            with open(path + "/shortcuts.conf", "r") as file:
                self.read(file.read())

        for shortcuts, aliased in self.shortcuts:
            if kernel.commands.get(aliased[0], None) is None:
                self.log(f"{aliased[0]} doesn't exist. Skipping.", WARN)
                continue

            @advanced_shortcuts.add_command
            class C(FlamingoCommand):
                def __init__(self):
                    super().__init__(shortcuts[0],
                                     f"Alias of: {" ".join(aliased)}",
                                     tuple(shortcuts[1:]),
                                     ArgParser())

                def execute(self, _k: FlamingoKernel, args: list):
                    kernel.execute_command(aliased[0], list(aliased[1:]) + args)

        return 0, 0

    def unload(self, kernel) -> [int, int]:
        return 0, 0

    def read(self, source: str):
        self.shortcuts.clear()
        lines = source.split("\n")
        for line in lines:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            _shortcuts = line.split("=")
            if len(_shortcuts) < 2:  # must look at least like X=Y
                raise CommandExecutionError("Aliases must have at least one alias and one command")

            _cmd_shortcuts = map(lambda s: s.lstrip().rstrip(), _shortcuts[:-1])
            _cmd, _args = command_shlex(_shortcuts[-1])
            self.shortcuts.append((tuple(_cmd_shortcuts), (_cmd, *_args)))


advanced_shortcuts = AdvancedShortcutsPlugin()


@advanced_shortcuts.add_command
class CheckShortcutsCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("shortcuts", "Checks the current shortcuts from the plugin and in the kernel", ("alls",),
                         ArgParser())

    def execute(self, kernel: FlamingoKernel, args: list) -> bool:
        b = FmtBuilder()
        b.surface2(f"Shortcuts ({len(advanced_shortcuts.shortcuts)})\n")
        b.text("   " + "-" * 70 + "\n")
        for shortcuts, command in advanced_shortcuts.shortcuts:
            b.flamingo(f"   {shortcuts[0]:<20}")
            b.surface2(f"    {" ".join(command)}\n")
            for alias in shortcuts[1:]:
                b.flamingo(f"   {alias:<20}\n")
        kernel.out(b.build())
        return True
