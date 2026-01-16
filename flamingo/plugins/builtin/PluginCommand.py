from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, StaticCompleter, PluginNameCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.debug.error import CommandExecutionError
from flamingo.core.vars.var_validators_builtin import LiteralValidator
from flamingo.interface.text import FmtBuilder
from flamingo.plugins.builtin.HelpCommand import build_commands_list


class PluginCommand(FlamingoCommand):
    def __init__(self):
        action_arg = FlamingoArg(
            name="action",
            validator=LiteralValidator(("list", "load", "unload", "reload", "restart", "commands")),
            completer=StaticCompleter(["list", "load", "unload", "reload", "restart", "commands"]),
            default="list",
            help_text="Action to perform"
        )

        target_arg = FlamingoArg(
            name="target",
            required=False,
            completer=PluginNameCompleter(),  # Default to names
            help_text="Plugin name or path"
        )

        save_flag = FlamingoArg(name="save", is_flag=True, help_text="Persist changes to $plugins.paths")
        all_flag = FlamingoArg(name="all", is_flag=True, help_text="Reload all plugins")

        parser = ArgParser() \
            .add_arg(action_arg) \
            .add_arg(target_arg) \
            .add_flag("save", save_flag) \
            .add_flag("all", all_flag)

        super().__init__("plugin", "Manage system plugins.", ("pl",), parser)

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        action = parsed['action']
        target = parsed['target']
        save = parsed['save']

        if action == "list":
            self._list(kernel)
        elif action == "load":
            if not target:
                raise CommandExecutionError("Load requires a path.")
            self._load(kernel, target, save)
        elif action == "unload":
            if not target:
                raise CommandExecutionError("Unload requires a plugin name.")
            if target == "core":
                raise CommandExecutionError("Cannot unload flamingo core")
            self._unload(kernel, target, save)
        elif action == "reload":
            if parsed['all']:
                self._reload_all(kernel)
            else:
                if not target:
                    raise CommandExecutionError("Reload requires a plugin name.")
                self._reload(kernel, target)
        elif action == "restart":
            for plugin_loader in kernel.plugin_manager.plugin_loaders:
                if plugin_loader is kernel.core_plugin:  # Never gonna do it
                    continue
                kernel.plugin_manager.unload_plugin(plugin_loader)
            kernel.load_startup_plugins()
            kernel.commands = kernel.plugin_manager.build_command_list()
        elif action == "commands":
            if not target:
                raise CommandExecutionError("Commands requires a plugin name.")

            loader = kernel.plugin_manager.get_plugin_loader(target)
            if loader:
                kernel.out(build_commands_list(loader.plugin.commands).build())
            else:
                kernel.out(f"Plugin '{target}' not found.")

    @staticmethod
    def _list(kernel):
        b = FmtBuilder.from_kernel(kernel)
        b.surface2(f"Active Plugins ({len(kernel.plugin_manager.plugins)})\n")
        b.text("   " + "-" * 60).raw("\n")

        for loader in kernel.plugin_manager.plugin_loaders:
            p = loader.plugin
            b.flamingo(f"   {p.name:<15}")
            b.surface2(f" v{p.version:<8}")
            b.overlay1(f" {p.author:<15}")

            # Show path relative to cwd if possible for brevity
            path_display = loader.path
            if len(path_display) > 30:
                path_display = "..." + path_display[-27:]

            b.subtext0(f" {path_display}").raw("\n")

        kernel.out(b.build())

    @staticmethod
    def _load(kernel, path, save):
        loaded = kernel.plugin_manager.load_plugin_path(path)

        if not loaded:
            return  # Manager handles errors

        msg = f"Loaded {len(loaded)} plugins."
        kernel.out(msg)

        if save:
            paths_var = kernel.resolve_var_path("$plugins.paths")
            current_paths = paths_var.value
            if path not in current_paths:
                current_paths.append(path)
                kernel.save_state()  # Persist immediate
                kernel.out(FmtBuilder().green(" [Persisted]").build())

    @staticmethod
    def _unload(kernel, name, save):
        if name == "core":
            kernel.out("Can't unload core.")
            return  # Still don't want to reload core

        success = kernel.plugin_manager.unload_plugin(name)
        if success:
            kernel.out(f"Unloaded '{name}'.")

            if save:
                paths_var = kernel.resolve_var_path("#plugins.paths")
                # TODO: Removing a plugin by name, but the list stores paths. Cheeky. Use warning
                kernel.out(FmtBuilder().yellow(
                    "Warning: --save on unload not fully implemented (path resolution needed).").build())
        else:
            kernel.out(f"Plugin '{name}' not found.")

    @staticmethod
    def _reload(kernel, name):
        if name == "core":
            kernel.out("Can't reload core.")
            return  # Still don't want to reload core

        kernel.plugin_manager.reload_plugin(name)
        kernel.out(f"Reloaded {name}.")

    @staticmethod
    def _reload_all(kernel):
        count = 0
        # Snapshot names because list might change (unlikely but safe)
        names = [p.name for p in kernel.plugin_manager.plugins]
        for name in names:
            if name == "core":
                continue  # Still don't want to reload core

            if kernel.plugin_manager.reload_plugin(name):
                count += 1
        kernel.out(f"Reloaded {count} plugins.")
