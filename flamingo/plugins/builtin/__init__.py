import importlib
import pkgutil
import inspect

from flamingo.core.debug.logging import logger
from flamingo.plugins.builtin._core_plugin import core
from flamingo.core.commands.command import FlamingoCommand
import flamingo.plugins.builtin as builtin_pkg


def register_builtin_commands():
    """
    Scans the builtin package and registers all classes that inherit
    from FlamingoCommand.
    """

    for _, name, _ in pkgutil.iter_modules(builtin_pkg.__path__, builtin_pkg.__name__ + "."):
        if "_core_plugin" in name:
            continue

        try:
            module = importlib.import_module(name)
            for member_name, member_class in inspect.getmembers(module, inspect.isclass):

                if (issubclass(member_class, FlamingoCommand) and
                        member_class is not FlamingoCommand):

                    if member_class.__module__ == module.__name__:
                        instance = core.add_command(member_class)
                        logger.info(f"Registered command {instance.name}")

        except ImportError as e:
            print(f"Could not import module {name}: {e}")


register_builtin_commands()
