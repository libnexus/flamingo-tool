import random
import re
from typing import Dict, List, Union, Optional
from dataclasses import dataclass

from flamingo.core.debug.error import CommandExecutionError
from flamingo.core.vars.var_validators_builtin import LiteralValidator
from flamingo.plugins.plugin import FlamingoPlugin
from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.parser import ArgParser
from flamingo.core.commands.completer import FlamingoArg, StaticCompleter
from flamingo.interface.text import FmtBuilder
from flamingo.core.vars.flamingo_var import FlamingoVar

@dataclass
class RollResult:
    value: Union[int, bool]
    pool: List[int]
    expression: str
    description: Optional[str] = None

class DiceCore:
    users = {}
    
    @staticmethod
    def parse(text: str):
        text = text.replace(" ", "")
        
        for op in [">=", "<=", ">", "<"]:
            if op in text:
                left, right = text.rsplit(op, 1)
                return {"op": op, "left": DiceCore.parse(left), "right": DiceCore.parse(right)}
        
        for op in ["+", "-"]:
            if op in text:
                left, right = text.rsplit(op, 1)
                return {"op": op, "left": DiceCore.parse(left), "right": DiceCore.parse(right)}
        
        if "d" in text:
            match = re.match(r"^(\d*)d(\d+)(d|a)?$", text)
            if match:
                cnt, sides, adv = match.groups()
                return {"op": "dice", "count": int(cnt or 1), "sides": int(sides), "adv": adv}
        
        if text.isdigit():
            return {"op": "lit", "value": int(text)}
        
        elif text.startswith("%") and len(text) > 2:
            return {"op": "macro", "value": text[1:]}
            
        return {"op": "ref", "value": text}

    @staticmethod
    def evaluate(b: FmtBuilder, node: dict, saved: dict, macros: dict) -> RollResult:
        op = node["op"]
        
        if op == "lit":
            b.surface2(str(node["value"]))
            return RollResult(node["value"], [node["value"]], str(node["value"]))

        if op == "ref":
            name = node["value"]
            if name in saved:
                stored = saved[name]
                val = stored.value if isinstance(stored.value, int) else sum(stored.pool)
                b.lavender(name).surface2(f"({val})")
                return RollResult(val, stored.pool, name)
            raise CommandExecutionError(f"Reference '{name}' not found")
        
        elif op == "macro":
            name = node["value"]
            if name in macros:
                macro = macros[name]
                return DiceCore.evaluate(b, macro, saved, macros)
            raise CommandExecutionError(f"Macro '{name}' not found")


        if op in [">", "<", ">=", "<="]:
            l_res = DiceCore.evaluate(b, node["left"], saved, macros)
            b.surface2(f" {op} ")
            r_res = DiceCore.evaluate(b, node["right"], saved, macros)
            ops = {">": lambda a,b: a>b, "<": lambda a,b: a<b, ">=": lambda a,b: a>=b, "<=": lambda a,b: a<=b}
            bool_val = ops[op](l_res.value, r_res.value)
            return RollResult((bool_val, l_res.value), l_res.pool, f"{l_res.expression}{op}{r_res.expression}")

        if op in ["+", "-"]:
            l_res = DiceCore.evaluate(b, node["left"], saved, macros)
            b.surface2(f" {op} ")
            r_res = DiceCore.evaluate(b, node["right"], saved, macros)
            val = (l_res.value + r_res.value) if op == "+" else (l_res.value - r_res.value)
            return RollResult(val, l_res.pool + r_res.pool, f"{l_res.expression}{op}{r_res.expression}")

        if op == "dice":
            rolls = []
            for _ in range(node["count"]):
                r1 = random.randint(1, node["sides"])
                if node["adv"]:
                    r2 = random.randint(1, node["sides"])
                    # a for advantage, d for disadvantage 
                    kept, dropped = (max(r1, r2), min(r1, r2)) if node["adv"] == "a" else (min(r1, r2), max(r1, r2))
                    rolls.append({"kept": kept, "dropped": dropped})
                else:
                    rolls.append({"kept": r1})

            # TODO make it optional
            if node["count"] > 1:
                rolls.sort(key=lambda x: x["kept"], reverse=True)
            
            total = sum(r["kept"] for r in rolls)
            
            # Formatting logic for the trace
            if node["count"] > 1: b.surface2("(")
            for i, r in enumerate(rolls):
                if node["adv"]:
                    b.surface2("(")
                    if r["kept"] not in (node["sides"], 1):
                        b.mauve(r["kept"], italic=True, underline=True)
                    else:
                        DiceCore.highlight(b, r["kept"], node["sides"], True, True)
                    b.surface2(", ")
                    DiceCore.highlight(b, r["dropped"], node["sides"])
                    b.surface2(")")
                else:
                    DiceCore.highlight(b, r["kept"], node["sides"])
                if i < len(rolls)-1: b.surface2(", ")
            if node["count"] > 1: b.surface2(")")
            
            return RollResult(total, [r["kept"] for r in rolls], f"{node["count"]}d{node["sides"]}{node["adv"] or ""}")

    @staticmethod
    def highlight(b, roll, ceil, u=False, it=False):
        """Highlights natural 1s (Red) and Crits (Green)."""
        if roll == 1: 
            b.red("1", underline=u, italic=it)
        elif roll == ceil: 
            b.green(str(ceil), underline=u, italic=it)
        else: b.surface2(str(roll), underline=u, italic=it)

    @staticmethod 
    def user_pools(name: str):
        if name not in DiceCore.users:
            saved = {}
            history = []
            macros = {}
            DiceCore.users = {name: {"history": history, "saved": saved, "macros": macros}}
            return saved, history, macros
        return DiceCore.users[name]["saved"], DiceCore.users[name]["history"], DiceCore.users[name]["macros"]


class D20Plugin(FlamingoPlugin):
    def __init__(self):
        super().__init__("d20", "shaun", "Advanced D20 Dice Suite", "1.0")

    def load(self, kernel) -> tuple[int, int]:
        return 0, 0
    
    def unload(self, kernel) -> tuple[int, int]:
        return 0, 0

d20_plugin = D20Plugin()

@d20_plugin.add_command
class RollCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("roll", "Roll dice with saving and history features", ("right",), ArgParser())
        self.arg_parser.add_arg(FlamingoArg("expression", greedy=True, completer=StaticCompleter(["--desc", "--save"])))
        self.arg_parser.add_flag("desc", FlamingoArg("desc", required=False))
        self.arg_parser.add_flag("save", FlamingoArg("save", required=False))

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        
        saved, history, macros = DiceCore.user_pools(kernel.current_user.name)

        expr_raw = " ".join(parsed["expression"])
        if not expr_raw: 
            return
        
        exprs = [e.strip() for e in expr_raw.split(",")]
 
        b = FmtBuilder.from_kernel(kernel)
        b.surface2("Rolls")

        if parsed["desc"]: 
            b.surface2(" (").subtext0(parsed["desc"]).surface2(")")

        b.surface2(":\n")

        total = 0

        for e in exprs:
            try:
                ast = DiceCore.parse(e)
                breakdown = FmtBuilder.from_kernel(kernel)
                res = DiceCore.evaluate(breakdown, ast, saved, macros)
                res.description = parsed["desc"]

                b.raw("   ")

                if isinstance(res.value, tuple):
                    passed, v = res.value
                    b.green(f"{v:<6}") if passed else b.red(f"{v:<6}")
                    total += v
                else:
                    b.lavender(f"{res.value:<6}")
                    total += res.value
                
                b.extend(breakdown.segments).raw("\n")
                
                history.append(res)
                if len(history) > 20: 
                    history.pop(0)
                if parsed["save"]: 
                    saved[parsed["save"]] = res

            except Exception as ex:
                kernel.out(FmtBuilder.from_kernel(kernel).red(f"Error evaluating '{e}': {ex}").raw("\n").build())
                return 

        b.surface2("Total: ").lavender(str(total)).raw("\n")
        kernel.out(b.build())


@d20_plugin.add_command
class RollHistoryCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("rollhistory", "Displays the current user's roll history or clears it", (), ArgParser())
        self.arg_parser.add_flag("clear", FlamingoArg("clear", completer=StaticCompleter(["clear"]), required=False, default=False))

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)

        if parsed["clear"]:
            kernel.current_user.var_table.values["dice_history"] = FlamingoVar([])
            kernel.out(FmtBuilder.from_kernel(kernel).green("Roll history cleared.").build())
            return

        self._show_history(kernel)

    def _show_history(self, kernel):
        _, history, _ = DiceCore.user_pools(kernel.current_user.name)
        if not history:
            kernel.out(FmtBuilder.from_kernel(kernel).surface2("No roll history found.").build())
            return

        b = FmtBuilder.from_kernel(kernel)
        b.flamingo("Roll History:").raw("\n")
        for i, res in enumerate(reversed(history)):
            idx = len(history) - i
            b.surface2(f"{idx:>2}. ")
            if isinstance(res.value, tuple):
                passed, v = res.value
                b.green(f"{v:<6}") if passed else b.red(f"{v:<6}")
            else:
                b.lavender(f"{res.value:<6} ")
            
            b.text(res.expression)
            if res.description: 
                b.subtext0(f" [{res.description}]")
            b.raw("\n")
        kernel.out(b.build())

@d20_plugin.add_command
class RollMacroCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("rollmacro", "Displays the current user's roll history or clears it", (), ArgParser())
        self.arg_parser.add_arg(FlamingoArg("name", required=True, help_text="Name to save the macro as"))
        self.arg_parser.add_arg(FlamingoArg("dice roll", required=True, greedy=True))

    def execute(self, kernel, args):
        parsed = self.arg_parser.parse(args)
        
        _, _, macros = DiceCore.user_pools(kernel.current_user.name)
        
        dice_roll = " ".join(parsed["dice roll"])

        macro = DiceCore.parse(dice_roll)

        macros[parsed["name"]] = macro 

        kernel.out(FmtBuilder.from_kernel(kernel).raw("Saved: [").mauve(dice_roll).raw("] to ").flamingo(f"%{parsed["name"]}").build())
        
