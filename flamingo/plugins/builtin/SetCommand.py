from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, StaticCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError
from flamingo.core.vars.var_validators_builtin import LiteralValidator


class SetCommand(FlamingoCommand):
    def __init__(self):
        path_arg = FlamingoArg(
            name="path",
            required=True,
            completer=StaticCompleter(["@", "$", "#"]),  # TODO: A VarPathCompleter would be better
            help_text="Variable path (e.g. @theme)"
        )

        to_arg = FlamingoArg(
            name="to",
            required=True,
            validator=LiteralValidator(("to",)),
            completer=StaticCompleter(["to"]),
            help_text="A haughty syntactic necessity. Egad.",
        )

        val_arg = FlamingoArg(
            name="value",
            greedy=True,
            required=True,
            help_text="Value to set"
        )

        ref_flag = FlamingoArg(name="ref", is_flag=True, help_text="Store as reference to another variable")

        parser = (ArgParser()
                  .add_arg(path_arg)
                  .add_arg(to_arg)
                  .add_arg(val_arg)
                  .add_flag("r", ref_flag))

        super().__init__("set", "Set variable value.", ("let", "var"), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        raw_path = parsed['path']
        value_tokens = parsed['value']
        is_ref = parsed['ref']

        # TODO implement listing logic

        final_value = " ".join(value_tokens)

        if is_ref:
            if not isinstance(final_value, str) or not final_value.startswith(("@", "$", "#")):
                raise CommandExecutionError("Reference (-r) target must be a variable path (e.g. @other).")

            source_var = kernel.resolve_var_path(final_value)
            final_value = source_var  # Pass the actual flamingo var

        target_table, target_key = self._resolve_target(kernel, raw_path)

        try:
            target_table.set_variable(target_key, final_value, as_reference=is_ref)
        except Exception as e:
            raise CommandExecutionError(f"Failed to set variable: {e}")

    @staticmethod
    def _infer_type(val: str):
        # TODO for later on when inference is permitted

        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val

    @staticmethod
    def _resolve_target(kernel, raw_path: str):
        # This mirrors Kernel.resolve_var_path but stops one step short
        if not raw_path.startswith(("@", "$", "#")):
            raise CommandExecutionError(f"Invalid path '{raw_path}'. Must start with @, $, or #")

        parts = raw_path[1:].split(".")
        root_char = raw_path[0]

        if root_char == "@":
            current = kernel.current_user.var_table
        elif root_char == "$":
            current = kernel.env_vars
        elif root_char == "#":
            current = kernel.system_vars

        key = parts[-1]

        parents = parts[:-1]
        for p in parents:
            if p in current.children:
                current = current.children[p]
            else:
                current = current.child(p)

        return current, key
