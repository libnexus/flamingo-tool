from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from flamingo.core.debug.error import PluginError
from flamingo.core.debug.logging import logger

if TYPE_CHECKING:
    from flamingo.plugins.plugin import FlamingoPlugin
    from flamingo.core.kernel import FlamingoKernel
    from flamingo.core.commands.command import FlamingoCommand


@dataclass
class FlamingoPluginLoader:
    """

    :ivar plugin: The actual plugin it's wrapping
    :ivar path: The path to the module source
    :ivar module_name: The internal module name of the source
    """

    plugin: FlamingoPlugin
    path: str | None
    module_name: str  # Track the internal module name to purge it later


class PluginManager:
    def __init__(self, kernel: FlamingoKernel):
        self.kernel = kernel
        self.plugin_loaders: list[FlamingoPluginLoader] = list()

    @property
    def plugins(self) -> list[FlamingoPlugin]:
        return [pl.plugin for pl in self.plugin_loaders]

    def load_plugin_path(self, path: str) -> list[FlamingoPlugin]:
        """
        Loads a path. If it's a directory, loads all .py files inside.
        Returns a list of successfully loaded plugins.
        """
        path = os.path.abspath(os.path.expanduser(path))
        loaded = []

        if not os.path.exists(path):
            msg = f"Plugin path not found: {path}"
            logger.warning(msg)
            self.kernel.out(f"[!] {msg}")
            return []

        if os.path.isdir(path):
            logger.info(f"Scanning plugin directory: {path}")
            for f in os.listdir(path):
                if f.endswith(".py") and not f.startswith("__"):
                    full_path = os.path.join(path, f)
                    loaded.extend(self._load_single_file(full_path))
        else:
            loaded.extend(self._load_single_file(path))

        return loaded

    def _load_single_file(self, path: str) -> list[FlamingoPlugin]:
        try:
            # Generate unique internal module name to avoid conflicts with standard libs
            filename = os.path.basename(path).replace('.py', '')
            internal_name = f"__flamingo_ext_{filename}"

            spec = importlib.util.spec_from_file_location(internal_name, path)
            if not spec or not spec.loader:
                raise PluginError(f"Could not create spec for {path}")

            module = importlib.util.module_from_spec(spec)

            # Inject Flamingo API
            import flamingo
            module.__dict__["flamingo"] = flamingo

            original_modules = sys.modules.copy()

            # Add to sys.modules or relative imports inside the plugin will fail
            sys.modules[internal_name] = module
            try:
                spec.loader.exec_module(module)
            finally:
                # House-keeping to go back to normal
                sys.modules.clear()
                sys.modules.update(original_modules)

            from flamingo.plugins.plugin import FlamingoPlugin

            found_plugins = []
            for attr_name, attr in module.__dict__.items():
                if isinstance(attr, FlamingoPlugin):
                    if plug_ld := self.get_plugin_loader(attr.name):
                        logger.warning(f"Plugin '{attr.name}' already loaded as {plug_ld.plugin.name} {plug_ld.plugin.version}. Skipping.")
                        continue

                    found_plugins.append(attr)

            if not found_plugins:
                logger.warning(f"No FlamingoPlugin instance found in {path}")
                del sys.modules[internal_name]
                return []

            if len(found_plugins) > 1:
                logger.warning(f"Multiple plugins in {path}. Loading all.")

            for plug in found_plugins:
                try:
                    warnings, errors = plug.load(self.kernel)
                except Exception as e:
                    logger.error(f"Plugin '{plug.name}' crashed during load: {e}")
                    del sys.modules[internal_name]
                    continue

                for cmd_name, cmd in plug.commands.items():
                    if cmd_name in self.kernel.commands:
                        logger.warning(f"Command conflict: '{cmd_name}' from plugin '{plug.name}' overridden.")
                    self.kernel.commands[cmd_name] = cmd

                self.plugin_loaders.append(FlamingoPluginLoader(plug, path, internal_name))
                logger.info(
                    f"Loaded plugin: {plug.name} v{plug.version} with {warnings} warning(s), and {errors} error(s)")

            return found_plugins

        except Exception as e:
            logger.error(f"Failed to load plugin {path}: {e}")
            self.kernel.out(f"[!] Error loading {os.path.basename(path)}: {e}")
            return []

    def reload_plugin(self, name: str) -> bool:
        """
        Hard Reload: Unloads the plugin, purges the module from memory, and re-reads from disk.
        """
        loader = self.get_plugin_loader(name)
        if not loader:
            raise PluginError(f"Plugin '{name}' not found.")

        path = loader.path
        module_name = loader.module_name

        logger.info(f"Hard Reloading plugin: {name} from {path}")

        # Graceful Unload (Coughing baby)
        self.unload_plugin(name)

        # Purge sys.modules (Hydrogen bomb)
        # Ensures the next load actually reads the file and resets globals
        if module_name in sys.modules:
            del sys.modules[module_name]
            logger.debug(f"Purged {module_name} from sys.modules")

        new_plugins = self.load_plugin_path(path)

        # Did it actually come back?
        for plug in new_plugins:
            if plug.name == name:
                return True

        logger.warning(f"Reload warning: Plugin '{name}' was unloaded but not found in the re-loaded file.")
        return False

    def unload_plugin(self, name: str | FlamingoPluginLoader) -> bool:
        if isinstance(name, FlamingoPluginLoader):
            loader = name
            name = loader.plugin.name
        else:
            loader = self.get_plugin_loader(name)
            if not loader:
                return False

        try:
            warnings, errors = loader.plugin.unload(self.kernel)
        except Exception as e:
            logger.error(f"Error unloading {name}: {e}")
            warnings, errors = 0, 1

        for cmd in loader.plugin.commands:
            if cmd in self.kernel.commands:
                del self.kernel.commands[cmd]

        logger.info(
            f"Unloaded plugin: {loader.plugin.name} v{loader.plugin.version} with {warnings} warning(s), and {errors} error(s)")

        # Don't remove from sys.modules here.
        # If removing on unload, other plugins depending on it might break. Stick to on reload.

        self.plugin_loaders.remove(loader)
        return True

    def get_plugin_loader(self, name: str) -> FlamingoPluginLoader | None:
        for plugin_loader in self.plugin_loaders:
            if plugin_loader.plugin.name == name:
                return plugin_loader
        return None

    def build_command_list(self) -> dict[str, FlamingoCommand]:
        commands = {}
        for plugin in self.plugins:
            commands.update(plugin.commands)
        return commands
