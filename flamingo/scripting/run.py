from __future__ import annotations

import os
from typing import TYPE_CHECKING

from flamingo.interface.text import FmtBuilder
from flamingo.scripting.interpreter import Interpreter, FlamingoScriptError
from flamingo.scripting.parse.parser import Parser
from flamingo.scripting.token.token_types import highlight_location
from flamingo.scripting.token.tokenizer import tokenizer

if TYPE_CHECKING:
    from flamingo.core.kernel import FlamingoKernel


class FlamingoScriptRunner:
    def __init__(self, kernel: FlamingoKernel, name: str, source: str, local_vars: dict):
        self.kernel = kernel
        self.name = name
        self.source = source

        self.local_vars = local_vars

        self.tokens = tokenizer(source)
        self.parser = Parser(self.tokens)
        self.script = None

        try:
            self.script = self.parser.parse()
        except FlamingoScriptError as e:
            if self.source:
                location = highlight_location(self.source, e.token)

                b = FmtBuilder.from_kernel(self.kernel)
                b.red(f"Error at ").yellow(str(e.token.line)).red(", ").yellow(str(e.token.col)) \
                    .red(f":\n{location}\n{e.message}")
                self.kernel.out(b.build())

    def run(self):
        Interpreter(self.kernel, self.name, self.source, self.local_vars).interpret(self.script)

    @classmethod
    def from_file(cls, kernel: FlamingoKernel, path: str, local_vars: dict) -> FlamingoScriptRunner:
        with open(path, "r") as file:
            return cls(kernel, os.path.basename(path), file.read(), local_vars)
