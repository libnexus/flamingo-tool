import random
import re
from flamingo.plugins.plugin import FlamingoPlugin
from flamingo.core.commands.command import FlamingoCommand
from flamingo.core.commands.parser import ArgParser
from flamingo.core.commands.completer import FlamingoArg
from flamingo.interface.text import FmtBuilder

class D20Plugin(FlamingoPlugin):
    def __init__(self):
        super().__init__("d20", "shaun", "D20 Dice Roller", "0.1")

    def load(self, kernel) -> tuple[int, int]:
        return 0, 0
    
    def unload(self, kernel) -> tuple[int, int]:
        return 0, 0

d20_plugin = D20Plugin()

@d20_plugin.add_command
class RollCommand(FlamingoCommand):
    def __init__(self):
        super().__init__("roll", "Evaluate dice notation (e.g., 2d20+5)", ("r",), ArgParser())
        self.arg_parser.add_arg(FlamingoArg("expression", greedy=True, help_text="Dice expression(s)"))

    def execute(self, kernel, args):
        parsed_args = self.arg_parser.parse(args)
        full_text = " ".join(parsed_args["expression"])
        expressions = [e.strip() for e in full_text.split(",")]

        b = FmtBuilder.from_kernel(kernel)

        for expr in expressions:
            if not expr: continue
            
            try:
                ast = self._parse(expr)
                
                breakdown = FmtBuilder.from_kernel(kernel)
                total = self._evaluate(breakdown, ast)                
                b.flamingo(f"{total:<6}")
                b.extend(breakdown.segments)
                b.raw("\n")
                
            except ValueError as e:
                b.red(f"Error '{expr}': {e}").raw("\n")

        kernel.out(b.build())

    def _parse(self, text):
        text = text.replace(" ", "")
        
        if '+' in text:
            left, right = text.rsplit('+', 1)
            return {'op': '+', 'left': self._parse(left), 'right': self._parse(right)}
        if '-' in text:
            left, right = text.rsplit('-', 1)
            return {'op': '-', 'left': self._parse(left), 'right': self._parse(right)}
            
        if 'd' in text:
            match = re.match(r'^(\d*)d(\d+)(d|a)?$', text)
            if match:
                count_str, sides_str, advantage = match.groups()
                count = int(count_str) if count_str else 1
                return {'op': 'dice', 'n': count, 'sides': int(sides_str), 'advantage': advantage}
            raise ValueError("Invalid dice format")

        if text.isdigit():
            return {'op': 'lit', 'val': int(text)}
            
        raise ValueError(f"Unknown token: {text}")

    def _evaluate(self, b: FmtBuilder, node) -> tuple[int, str]:
        op = node['op']
        
        if op == 'lit':
            b.surface2(str(node['val']))
            return node['val']
            
        if op == 'dice':
            rolls = [random.randint(1, node['sides']) for _ in range(node['n'])]

            total = 0

            if node["n"] > 1:
                b.surface2("(")
            
            for i, _ in enumerate(range(node["n"])):
                if node["advantage"]:
                    r1, r2 = random.randint(1, node["sides"]), random.randint(1, node["sides"])
                    high, low = max(r1, r2), min(r1, r2)
                    b.surface2("(")

                    if node["advantage"] == "a":
                        self.highlight(b, high, node["sides"], underline=True, italic=True)
                        b.surface2(", ")
                        self.highlight(b, low, node["sides"])
                        roll = high
                    else:
                        self.highlight(b, low, node["sides"], underline=True, italic=True)
                        b.surface2(", ")
                        self.highlight(b, high, node["sides"])
                        roll = low 
                    b.surface2(")")
                else:
                    roll = random.randint(1, node["sides"])
                    self.highlight(b, roll, node["sides"])

                total += roll 
                    
                if i < len(rolls) - 1:
                    b.surface2(", ")

            if node["n"] > 1:
                b.surface2(")")
            return total
            
        if op == '+':
            l_val = self._evaluate(b, node['left'])
            b.surface2(" + ")
            r_val = self._evaluate(b, node['right']) 
            return l_val + r_val
            
        if op == '-':
            l_val = self._evaluate(b, node['left'])
            b.surface2(" - ")
            r_val = self._evaluate(b, node['right'])
            return l_val - r_val
        
    @staticmethod 
    def highlight(b: FmtBuilder, roll, ceil, underline=False, italic=False):
        if roll == 1:
            b.red("1", underline=underline, italic=italic)
        elif roll == ceil:
            b.green(str(ceil), underline=underline, italic=italic)
        else:
            b.surface2(str(roll), underline=underline, italic=italic)