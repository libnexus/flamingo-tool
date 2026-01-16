# Flamingo

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square)
![Status](https://img.shields.io/badge/status-prototype-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)

A self-contained, extensible shell environment tailored for rapid Python utility management.

Flamingo was built to solve a specific frustration: managing scattered Python utility scripts on Windows. Instead of polluting the system `PATH` with batch files or shim scripts, Flamingo provides a single, portable executable environment where utilities exist as native plugins.

**Project Status:** Developed in <36 hours. Currently just a side-project in "alpha".

## Core Philosophy

1.  **Portability:** The entire environment is designed to be compiled via PyInstaller into a single executable.
2.  **State Persistence:** User state, variables, and history are persisted locally via `shelve`.
3.  **Aesthetics:** First-class support for the Catppuccin palette and `prompt_toolkit` styling.
4.  **Strict Typing:** Arguments are parsed and strictly validated against Python types before execution.

## Key Features

### Hierarchical Variable System
Flamingo implements a unique scoped variable system that mimics memory pointers rather than simple text expansion.

* `#system`: System configurations (Prompt format, Plugin paths).
* `$env`: Environmental context (CWD).
* `@user`: User-defined variables and aliases.

Variables support **Reference Linking**. You can link `@alias` to point directly to `@source`. Updating `@source` immediately reflects in `@alias` without copying values.

### The Plugin System

Flamingo is designed to be extended. The core commands (`ls`, `cd`, `set`) are implemented as plugins, ensuring the plugin architecture is first-class, not an afterthought.

Plugins are loaded dynamically from the `plugins/` directory.

## Installation

### From Source

1. Clone the repository.
2. Install dependencies:
```bash
pip install -r requirements.txt

```


3. Run the kernel:
```bash
python -m flamingo.main

```



### Compilation (PyInstaller)

Flamingo is fully compatible with PyInstaller for single-file distribution:

```bash
pyinstaller --onefile flamingo/main.py --name flamingo

```

## Developing Plugins

Adding value to the environment is straightforward. Plugins inherit from `FlamingoCommand` and use declarative argument parsers.

**Example: A custom 'Hello' command**

```python
import flamingo
from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.kernel import FlamingoKernel
from flamingo.interface.text import FmtBuilder
from flamingo.plugins.plugin import FlamingoPlugin


class PingPlugin(FlamingoPlugin):
    def load(self, kernel) -> tuple[int, int]:
        return 0, 0

    def unload(self, kernel) -> [int, int]:
        return 0, 0

    def __init__(self):
        super().__init__("ping", "shaun", "It's a pinging plugin!", "0.1")


ping_plugin = PingPlugin()


@ping_plugin.add_command
class MyCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("ping", "Ping", (), flamingo.core.commands.parser.ArgParser())

    def execute(self, kernel: FlamingoKernel, args: list):
        _ = self.arg_parser.parse(args)
        kernel.out(FmtBuilder.from_kernel(kernel).surface2("pong!").build())
```

## Architecture Notes

* **Kernel:** acts as the central delegator, holding the `VarTable` and `User` states.
* **Shell Interface:** Powered by `prompt_toolkit` for history, auto-completion, and syntax highlighting.
* **Context Scope:** An internal context manager tracks the execution stack for granular error logging.