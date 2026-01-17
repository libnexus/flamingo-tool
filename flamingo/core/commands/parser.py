from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from prompt_toolkit import HTML

from flamingo.core.commands.completer import FlamingoArg
from flamingo.core.debug.error import CommandExecutionError
from flamingo.interface.text import FmtBuilder

if TYPE_CHECKING:
    from flamingo.core.kernel import FlamingoKernel


class ArgParser:
    def __init__(self):
        self.positionals: list[FlamingoArg] = []
        self.flags: dict[str, FlamingoArg] = {}

    def add_arg(self, arg: FlamingoArg):
        if self.positionals and self.positionals[-1].greedy:
            raise CommandExecutionError("Cannot add argument after a greedy argument.")
        self.positionals.append(arg)
        return self

    def add_flag(self, flag_name: str, arg: FlamingoArg):
        self.flags[flag_name] = arg
        return self

    def parse(self, raw_args: list[str]) -> dict:
        """
        Parses the arguments based on the internal specification

        Note: This does not do automatic type conversions. Validators provide checking before getting
        to execution which allows for safe casting, but casting has to be manual.

        :param raw_args: The user's arguments, pre-shlexed / split etc.
        :return: a dictionary of values put into the names based on built arg spec
        """
        result = {}

        for arg in self.positionals:
            result[arg.name] = arg.default
        for name, arg in self.flags.items():
            result[arg.name] = arg.default

        # Re-group ((1, 2) split by shlex)
        tokens = self._reconcile_groups(raw_args)

        pos_idx = 0
        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.startswith('--'):
                flag_name = token.lstrip('-')
                if flag_name in self.flags:
                    arg_def = self.flags[flag_name]
                    if arg_def.is_flag:
                        result[arg_def.name] = True
                        i += 1
                    else:
                        if i + 1 >= len(tokens):
                            raise CommandExecutionError(f"Flag {token} requires value.")
                        val = self._parse_value(tokens[i + 1])
                        arg_def.validate(val)
                        result[arg_def.name] = val
                        i += 2
                    continue

            if pos_idx >= len(self.positionals):
                raise CommandExecutionError(f"Unexpected argument: {token}")

            arg_def = self.positionals[pos_idx]

            if arg_def.greedy:
                rest_tokens = tokens[i:]
                parsed_rest = [self._parse_value(t) for t in rest_tokens]

                # Greedy args just gonna be a list of strings.
                arg_def.validate(parsed_rest)
                result[arg_def.name] = parsed_rest
                break

            val = self._parse_value(token)
            arg_def.validate(val)
            result[arg_def.name] = val

            pos_idx += 1
            i += 1

        # Required check in-case args are starving command
        if pos_idx < len(self.positionals):
            next_arg = self.positionals[pos_idx]
            if next_arg.required and not next_arg.greedy:
                # Greedy required means at least 1 item
                # If default is None and required is true, throw error
                pass
            if next_arg.required and result[next_arg.name] is None:
                raise CommandExecutionError(f"Missing required argument: {next_arg.name}")

        return result

    def _parse_value(self, token_str: str):
        # Handle (1, 2) tuples
        if token_str.startswith('(') and token_str.endswith(')'):
            try:
                return ast.literal_eval(token_str)
            except:
                pass

        # Shlex handles all top-level quotes
        return token_str

    def _reconcile_groups(self, raw_args: list[str]) -> list[str]:
        """
        Reconstructs tokens split by shlex that are part of a tuple structure.
        Input: ['(1,', '2)', '"quoted"']
        Output: ['(1, 2)', '"quoted"']
        """
        clean = []
        buffer = []
        depth = 0

        for token in raw_args:
            start_count = token.count('(')
            end_count = token.count(')')

            if depth == 0 and start_count == 0:
                clean.append(token)
                continue

            buffer.append(token)
            depth += (start_count - end_count)

            if depth == 0:
                # Merge buffer space-separated to reconstruct the tuple string
                # e.g. "(1," + " " + "2)"
                clean.append(" ".join(buffer))
                buffer = []

        if depth > 0:
            raise CommandExecutionError("Unmatched parentheses in arguments.")

        return clean

    def get_signature(self) -> str:
        parts = []
        for arg in self.positionals:
            # Format: <name> or [name]
            name = arg.name
            if arg.help_text:
                # TODO decide whether to include help text
                pass

            fmt = f"<{name}>" if arg.required else f"[{name}]"
            parts.append(fmt)

        # Flags
        for name, arg in self.flags.items():
            if arg.is_flag:
                parts.append(f"[--{name}]")
            else:
                parts.append(f"[--{name} <val>]")

        return " ".join(parts)

    def get_signature_highlighted(self, kernel: FlamingoKernel) -> FmtBuilder:
        b = FmtBuilder.from_kernel(kernel)
        for arg in self.positionals:
            name = arg.name
            if arg.help_text:
                # TODO: Tooltip style?
                pass

            b.green(f"<{name}>") if arg.required else b.yellow(f"[{name}]")

        # Flags
        for name, arg in self.flags.items():
            if arg.is_flag:
                b.blue(f"[--{name}]")
            else:
                b.red(f"[--{name} <val>]")

        return b
