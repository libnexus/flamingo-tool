from timeit import default_timer

from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.completer import FlamingoArg, PathCompleter
from flamingo.core.commands.parser import ArgParser
from flamingo.core.vars.flamingo_var import FlamingoVar
from flamingo.core.vars.var_validators_builtin import PathValidator, TypeValidator, ListValidator
from flamingo.interface.text import FmtBuilder
from flamingo.scripting.interpreter import FlamingoScriptError
from flamingo.scripting.run import FlamingoScriptRunner
from re import compile 


class RunCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("run", "Run a flamingo script", ("exe", "fgo"), ArgParser())
        self.arg_parser.add_arg(
            FlamingoArg("script",
                        required=True,
                        validator=PathValidator(must_exist=True, must_be_file=True),
                        completer=PathCompleter(must_be_file=True, re_filter=compile(r".*?\.fgo")),
                        help_text="Path to script to run"
                        ))
        self.arg_parser.add_arg(
            FlamingoArg("args", required=False, greedy=True, help_text="Arguments to pass to script"))

        self.arg_parser.add_flag("time", FlamingoArg(name="time", is_flag=True, help_text="Show execution time"))

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        greedy_args = parsed['args']
        local_vars = {f"arg{i}": FlamingoVar(arg, validator=TypeValidator(str), readonly=True) for i, arg in
                      enumerate(greedy_args)} if greedy_args else {}
        local_vars["args"] = FlamingoVar(greedy_args or [], validator=ListValidator(TypeValidator(str)), readonly=True)

        script_runner = FlamingoScriptRunner.from_file(kernel, parsed['script'], local_vars)

        if script_runner.script is None:
            # Exit silently because the error has been printed already
            return

        if parsed["time"]:
            start = default_timer()
            script_runner.run()
            time = (default_timer() - start) * 1000  # convert to milliseconds
            kernel.out(FmtBuilder.from_kernel(kernel).surface2(f"Script finished in {time}ms").build())
        else:
            script_runner.run()
