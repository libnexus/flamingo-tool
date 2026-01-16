from __future__ import annotations

import shlex
from typing import TYPE_CHECKING

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle

from flamingo.core.debug.error import ContextScope, FlamingoExit, FlamingoException
from flamingo.core.debug.logging import logger
from flamingo.interface.theme import FlamingoStyle

if TYPE_CHECKING:
    from flamingo.core.kernel import FlamingoKernel


class FlamingoCompleter(Completer):
    def __init__(self, kernel):
        self.kernel: FlamingoKernel = kernel

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        if not text.strip():
            yield from self._complete_commands("")
            return

        parts = text.split()
        is_new_arg = text.endswith(' ')
        if is_new_arg:
            parts.append("")

        # If parts is empty (handled by step 0) or on the first word
        if not parts or (len(parts) == 1 and not is_new_arg):
            current_word = parts[0]
            yield from self._complete_commands(current_word)
            return

        # Check if in a variable by looking at the last word
        raw_words = text.split()
        if raw_words and raw_words[-1][0] in "$@#":
            word = raw_words[-1]
            yield from self._complete_variables(word)
            return

        # Trailing space means new arg
        parts = text.split()

        is_new_arg = text.endswith(' ')
        if is_new_arg:
            parts.append("")  # Dummy slot for the new arg

        if not parts:
            return

        if len(parts) == 1:
            current_word = parts[0]
            yield from self._complete_commands(current_word)
            return

        cmd_name = parts[0]
        if cmd_name in self.kernel.commands:
            command = self.kernel.commands[cmd_name]

            # The last item in 'parts' is the one the cursor is on
            raw_args = parts[1:]
            cursor_token_index = len(raw_args) - 1
            cursor_token_val = raw_args[-1]

            parser = command.arg_parser
            positional_idx = 0
            target_arg_def = None

            i = 0
            while i < len(raw_args):
                token = raw_args[i]
                is_cursor = (i == cursor_token_index)

                if token.startswith('-') and token != "-":
                    flag_clean = token.lstrip('-')

                    # Are we typing the flag name?
                    if is_cursor:
                        yield from self._complete_flags(parser, token)
                        return

                    if flag_clean in parser.flags:
                        flag_def = parser.flags[flag_clean]
                        if not flag_def.is_flag:
                            # Is the cursor on the value?
                            if i + 1 == cursor_token_index:
                                target_arg_def = flag_def
                                # Set value to what's typing so logic below uses it
                                cursor_token_val = raw_args[i + 1]
                                break
                            i += 1  # Skip value in sim
                    i += 1
                    continue

                if is_cursor:
                    if positional_idx < len(parser.positionals):
                        target_arg_def = parser.positionals[positional_idx]
                    break

                positional_idx += 1
                i += 1

            if target_arg_def and target_arg_def.completer:
                logger.debug(f"Completing arg '{target_arg_def.name}' with '{cursor_token_val}'")
                suggestions = target_arg_def.completer.complete(self.kernel, cursor_token_val)

                for val, meta in suggestions:
                    yield Completion(
                        val,
                        start_position=-len(cursor_token_val),
                        display=val,
                        display_meta=meta
                    )

    def _complete_variables(self, word):
        ctx = 0
        if word[0] == "#":
            ctx = "#"
        elif word[0] == "@":
            ctx = "@"
        elif word[0] == "$":
            ctx = "$"
        clean = word[1:]
        u = self.kernel.current_user
        if not u:
            return
        for pool_name, pool_content in u.var_table.full_table().items():
            base_path = f"{ctx}{pool_name}"
            if pool_name.startswith(clean) or base_path.startswith(clean):
                yield Completion(base_path, start_position=-len(word), display=base_path,
                                 display_meta="Pool")
            if isinstance(pool_content, dict):
                for key, var_obj in pool_content.items():
                    full_path = f"{base_path}.{key}"
                    preview = "Locked"
                    try:
                        resolved = self.kernel.resolve_var_path(full_path)
                        preview = str(resolved)[:30].replace('\n', ' ')
                    except:
                        pass
                    if key.startswith(clean) or full_path.startswith(clean):
                        yield Completion(full_path, start_position=-len(word), display=full_path,
                                         display_meta=preview)

    def _complete_commands(self, word):
        for name, cmd in self.kernel.commands.items():
            if name.startswith(word):
                sig = cmd.arg_parser.get_signature()

                # e.g. "Switch User | <username> [password]"
                meta = f"{cmd.description} | {sig}" if sig else cmd.description

                yield Completion(
                    name,
                    start_position=-len(word),
                    display=name,
                    display_meta=meta
                )

    def _complete_flags(self, parser, word):
        clean = word.lstrip('-')
        for flag, arg in parser.flags.items():
            if flag.startswith(clean):
                yield Completion(f"--{flag}", start_position=-len(word), display=f"--{flag}",
                                 display_meta=arg.help_text)


def run_shell(kernel: FlamingoKernel):
    session = PromptSession(
        completer=FlamingoCompleter(kernel),
        style=FlamingoStyle,
        complete_style=CompleteStyle.COLUMN,
        complete_while_typing=True
    )

    while True:
        try:
            prompt_str = kernel.resolve_var_path_fmt("#shell.prompt")

            text = session.prompt(HTML(f"<prompt.symbol>{prompt_str}</prompt.symbol>"))
            if not text.strip():
                continue

            ContextScope.GLOBAL_CONTEXT.clear()
            ContextScope.GLOBAL_CONTEXT.append(f"Input: {text}")

            cmd_name, args = command_shlex(text)
            if not cmd_name:
                continue

            kernel.execute_command(cmd_name, args)

        except KeyboardInterrupt:
            continue
        except FlamingoException as e:
            kernel.out(e.message)
        except FlamingoExit:
            break
        except Exception as e:
            kernel.out(f"[!] Error: {e}")
            raise e


def command_shlex(command: str):
    try:
        parts = shlex.split(command)
    except ValueError:
        return None, None

    cmd_name = parts[0]
    args = parts[1:]

    return cmd_name, args
