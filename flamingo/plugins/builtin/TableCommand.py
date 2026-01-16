from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, StaticCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError, FlamingoException
from flamingo.core.vars.var_table import VarTable
from flamingo.interface.text import FmtBuilder


class TableCommand(FlamingoCommand):
    def __init__(self):
        path_arg = FlamingoArg(
            name="path",
            required=True,
            completer=StaticCompleter(["@", "$", "#"]),
            help_text="Table path (e.g. @, $env, #system)"
        )

        raw_flag = FlamingoArg(name="raw", is_flag=True, help_text="Show raw values/types")

        parser = ArgParser().add_arg(path_arg).add_flag("raw", raw_flag)

        super().__init__("table", "Inspect variable tables.", ("lsvar", "vars"), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        path = parsed['path']
        show_raw = parsed['raw']

        target_table = self.resolve_table(kernel, path)

        if not target_table:
            raise CommandExecutionError(f"Could not resolve table: {path}")

        b = FmtBuilder.from_kernel(kernel)
        b.surface2(f"Table: {target_table.name} ").overlay0(f"({path})").raw("\n")
        b.text("   " + "-" * 40).raw("\n")

        if target_table.values:
            for key, var in target_table.values.items():
                b.flamingo(f"   {key:<15}")

                if show_raw:
                    val_preview = str(var.value)[:30]
                    b.overlay1(f" {type(var.value).__name__}: {val_preview}")
                else:
                    try:
                        val_str = var.to_string_for_env(resolver_func=kernel.resolve_var_path)
                        if len(val_str) > 40:
                            val_str = val_str[:37] + "..."
                        b.text(f" {val_str}")
                    except RecursionError:
                        b.red(" <Error resolving>")

                b.raw("\n")
        else:
            b.overlay1("  (No variables)\n")

        if target_table.children:
            b.raw("\n").surface2("   Sub-Tables:\n")
            for key in target_table.children.keys():
                b.blue(f"      {key}/").raw("\n")

        kernel.out(b.build())

    @staticmethod
    def resolve_table(kernel, path: str) -> VarTable | None:
        # Manual resolution matching Kernel logic but stopping at Table
        if path == "@":
            return kernel.current_user.var_table
        if path == "$":
            return kernel.env_vars
        if path == "#":
            return kernel.system_vars

        # Handle dot paths: #system.shell
        parts = path.split(".")
        root_char = parts[0][0]

        if root_char == "@":
            current = kernel.current_user.var_table
        elif root_char == "$":
            current = kernel.env_vars
        elif root_char == "#":
            current = kernel.system_vars
        else:
            return None

        clean_parts = []
        for p in parts:
            if p.startswith(("@", "$", "#")):
                p = p[1:]
            if p:
                clean_parts.append(p)

        for part in clean_parts:
            if part in current.children:
                current = current.children[part]
            else:
                return None

        return current
