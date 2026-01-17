import os
import datetime
import math

import flamingo
from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, PathCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.kernel import FlamingoKernel
from flamingo.core.vars.var_validators_builtin import IntValidator, PathValidator
from flamingo.interface.text import FmtBuilder
from flamingo.plugins.plugin import FlamingoPlugin


class EssentialsDevPlugin(FlamingoPlugin):
    def load(self, kernel) -> tuple[int, int]:
        return 0, 0

    def unload(self, kernel) -> tuple[int, int]:
        return 0, 0

    def __init__(self):
        super().__init__("essentials-dev", "shaun",
                         "Potentially essential additions, in a plugin for easy development before escalation to core",
                         "0.1")


edv = EssentialsDevPlugin()


@edv.add_command
class LastCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("last", "Re-displays the previous output from a command", (),
                         ArgParser())
        self.arg_parser.add_arg(
            FlamingoArg(name="n", required=False, default=None, validator=IntValidator(minimum=1, maximum=100),
                        help_text="Previous n output (kernel stores up to 100)"))

    def execute(self, kernel: FlamingoKernel, args: list):
        args = self.arg_parser.parse(args)

        if not kernel.command_history:
            kernel.out("No previous outputs.")
            return

        n = args['n']
        if n is None:
            n = len(kernel.command_history)

        idx = len(kernel.command_history) - int(n) - 1

        if idx >= len(kernel.command_history):
            kernel.out(f"Can't get output {idx} with a buffer of {len(kernel.command_history)}")
            return

        last_command = kernel.command_history[idx]

        b = FmtBuilder.from_kernel(kernel).surface2("Command ").flamingo(last_command.command.name).peach(
            " " + " ".join(last_command.args)).surface2(":\n").text(
            "-" * (len(f"Command {last_command.name}:")) + "\n\n").extend(last_command.output)

        if not len(last_command.output):
            b.surface2("No output.")

        kernel.out(b.build())


@edv.add_command
class HistoryCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("history", "Displays a list of previous commands used", (),
                         ArgParser())
        self.arg_parser.add_arg(
            FlamingoArg(name="n", required=False, default=None, validator=IntValidator(minimum=1, maximum=100),
                        help_text="Number of previous commands to display (kernel stores up to 100)"))

    def execute(self, kernel: FlamingoKernel, args: list) -> bool:
        args = self.arg_parser.parse(args)
        n = args['n']
        if n is None:
            n = 10
        else:
            n = int(n)

        command_history = kernel.command_history.copy()
        command_history_len = len(command_history)

        b = FmtBuilder.from_kernel(kernel)
        b.surface2(f"Command History ({n if n < command_history_len else command_history_len})\n")
        b.overlay1(f"   {"Num":<7}")
        b.flamingo(f"{"Name":<25}")
        b.peach(f"{"Arguments":<25}\n")
        b.text("   " + "-" * 50 + "\n")
        for i in range(n):
            if i >= command_history_len:
                break
            command_history_entry = command_history[command_history_len - 1 - i]
            b.overlay1(f"   {i + 1:<7}")
            b.flamingo(f"{command_history_entry.command.name:<20}")
            b.peach(f"    {" ".join(command_history_entry.args)}\n")
        kernel.out(b.build())
        return True


@edv.add_command
class WhatIsCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("whatis", "Displays metadata about a path", ("info", "stat"),
                         flamingo.core.commands.parser.ArgParser())
        self.arg_parser.add_arg(
            FlamingoArg(name="path", required=False, default=None, 
                        validator=PathValidator(must_exist=True),
                        completer=PathCompleter(),
                        help_text="The path to show info on"))

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        target = parsed['path']

        if target is None:
            target = kernel.resolve_var_path_fmt("$cwd")

        abs_path = os.path.abspath(target)
        
        stat_info = os.stat(abs_path)
        last_modified = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        created = datetime.datetime.fromtimestamp(stat_info.st_birthtime).strftime('%Y-%m-%d %H:%M:%S')
        
        is_dir = os.path.isdir(abs_path)
        name = os.path.basename(abs_path) or os.path.basename(os.path.dirname(abs_path)) # Handle root/trailing slash

        b = FmtBuilder.from_kernel(kernel)
        b.surface2("Metadata of: ").flamingo(name).raw("\n")
        b.text("-" * 40).raw("\n")
        
        b.surface2(f"{'Path':<15}").text(abs_path).raw("\n")
        b.surface2(f"{'Type':<15}").mauve("Directory" if is_dir else "File").raw("\n")
        b.surface2(f"{'Last Write':<15}").text(last_modified).raw("\n")
        b.surface2(f"{'Created':<15}").text(created).raw("\n")

        if is_dir:
            try:
                items = os.listdir(abs_path)
                file_count = 0
                dir_count = 0
                
                for item in items:
                    full_item_path = os.path.join(abs_path, item)
                    if os.path.isdir(full_item_path):
                        dir_count += 1
                    else:
                        file_count += 1
                
                b.surface2(f"{'Content':<15}")
                b.text(f"{file_count} Files, {dir_count} Directories").raw("\n")
                
            except PermissionError:
                b.red(f"{'Content':<15}Permission Denied").raw("\n")

        else:
            human_size = self.convert_size(stat_info.st_size)
            b.surface2(f"{'Size':<15}").text(f"{human_size} ({stat_info.st_size} bytes)").raw("\n")

        kernel.out(b.build())

    @staticmethod
    def convert_size(size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"