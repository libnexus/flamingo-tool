from __future__ import annotations

import os
import shelve
from dataclasses import dataclass
from typing import Optional

from prompt_toolkit import print_formatted_text, HTML

from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.debug.error import VariableNotFoundError, ContextScope, FlamingoException, PluginError
from flamingo.core.debug.logging import logger
from flamingo.core.user import User
from flamingo.core.vars.flamingo_var import FlamingoVar, DynamicVar
from flamingo.core.vars.var_table import VarTable
from flamingo.core.vars.var_validators_builtin import TypeValidator, PathValidator, LiteralValidator, ListValidator
from flamingo.plugins.builtin import core
from flamingo.plugins.plugin_manager import PluginManager, FlamingoPluginLoader
from collections import deque


@dataclass(frozen=True, slots=True)
class CommandHistory:
    command: FlamingoCommand
    name: str
    args: list[str]
    output: list[str | HTML]


class FlamingoKernel:
    """
    The main object to run the flamingo environment. The main delegator and manager.
    """

    DB_PATH = ".flamingo.db"

    def __init__(self):
        self.users: dict[str, User] = {}
        self.current_user: User = ...
        self.system_vars = VarTable("system")  # define behaviour of the system (where everything lives)
        self.env_vars = self.system_vars.child("env")  # communal variable pool
        self.user_vars = self.system_vars.child("users")  # user pools
        self.plugin_manager = PluginManager(self)

        self.command_history: deque[CommandHistory] = deque(maxlen=100)
        self.out_buffer: list[str | HTML] = []

        self.commands: dict[str, FlamingoCommand] = {}
        self.core_plugin = FlamingoPluginLoader(core, "builtin", "__int_flamingo")
        self.plugin_manager.plugin_loaders.append(self.core_plugin)
        self.commands.update(self.plugin_manager.build_command_list())

        with ContextScope("Initializing Kernel"):
            self.load_state()
            self.load_startup_plugins()

        self.commands.update(self.plugin_manager.build_command_list())

    def load_state(self):
        try:
            with shelve.open(self.DB_PATH) as db:
                if 'users' not in db:
                    logger.info("No state found. Bootstrapping.")
                    self._bootstrap()
                else:
                    self.users = db['users']
                    # Restore session or default
                    self.current_user = self.users.get('admin') or self.users.get('guest')
                    logger.info(f"State loaded. Logged in as: {self.current_user.name}")
        except Exception as e:
            logger.critical(f"State load failed: {e}")
            self._bootstrap()

    def save_state(self):
        with shelve.open(self.DB_PATH) as db:
            db['users'] = self.users
        logger.debug("State persisted to disk.")

    def load_startup_plugins(self):
        try:
            paths_var = self.resolve_var_path("#plugins.paths")
            paths = paths_var.value

            if not paths:
                return

            logger.info(f"Loading {len(paths)} startup plugin paths...")
            for path in paths:
                self.plugin_manager.load_plugin_path(path)

        except PluginError as e:
            logger.error(f"Startup plugin load error: {e}")

    def _bootstrap(self):
        flamingo = User("flamingo", self.user_vars.child("flamingo"))
        self.setup_user_variables(flamingo)
        self.users["flamingo"] = self.current_user = flamingo

        # System variables

        self.system_vars.child("shell").values["prompt"] = FlamingoVar(
            value="({#current_user} @ {$cwd}) ",
            validator=TypeValidator(str))
        self.system_vars.values["current_user"] = DynamicVar(self, "current_user", "name")

        self.system_vars.child("plugins").values["paths"] = FlamingoVar(
            value=[os.path.expanduser("./plugins")],
            validator=ListValidator(TypeValidator(str)),
            recursive=False
        )

        # Environment variables

        self.env_vars.values["cwd"] = FlamingoVar(
            value=os.path.abspath("."),
            validator=PathValidator(must_exist=True, must_be_dir=True)
        )

    def setup_user_variables(self, user: User):
        self.user_vars.children[user.name].values["theme"] = FlamingoVar(
            value="frappe",
            validator=LiteralValidator(("latte", "frappe", "macchiato", "macchiato"))
        )

    def resolve_var_path(self, path: str) -> FlamingoVar:
        """
        Resolves a variable path to a flamingo variable
        """

        with (ContextScope(f"Resolving '{path}'")):
            if not self.current_user or self.current_user is ...:
                raise FlamingoException("No active user.")

            path_split = path[1:].split(".")  # Pre-emptively removing any namespace indicator

            no_var = object()

            if path[0] == "@":
                # User pool relative path
                table = self.current_user.var_table
            elif path[0] == "$":
                # Environment pool path
                table = self.env_vars
            elif path[0] == "#":
                # System pool path
                table = self.system_vars
            else:
                raise VariableNotFoundError(f"Invalid variable prefix '{path[0]}', try @, $ or #")

            result = table.resolve(path_split, no_var)

            if result is no_var:
                raise FlamingoException(f"No variable at <{path}>")

            return result

    def resolve_var_path_fmt(self, path: str, depth: int = 0) -> str:
        """
        Resolve a variable path to a flamingo variable, formatted as a string
        """
        var = self.resolve_var_path(path)

        return var.to_string_for_env(resolver_func=self.resolve_var_path, depth=depth)

    def execute_command(self, cmd_name: str, cmd_args: list[str],
                        extra_commands: Optional[dict[str, FlamingoCommand]] = None,
                        extra_plugins: Optional[PluginManager] = None):
        if extra_commands is None:
            extra_commands = {}
        if extra_plugins is not None:
            extra_commands.update(extra_plugins.build_command_list())

        if cmd_name in self.commands:
            command = self.commands[cmd_name]
        elif extra_commands and cmd_name in extra_commands:
            command = extra_commands[cmd_name]
        else:
            self.out(f"Unknown command: {cmd_name}")
            return

        try:
            self.out_buffer.clear()
            with ContextScope(f"Executing '{cmd_name}'"):
                command.execute(self, cmd_args)
        finally:
            self.command_history.append(CommandHistory(command, cmd_name, cmd_args, self.out_buffer[:]))
            self.out_buffer.clear()

    def out(self, text: str | HTML):
        self.out_buffer.append(text)
        print_formatted_text(text)
