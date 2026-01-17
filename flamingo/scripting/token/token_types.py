from dataclasses import dataclass


@dataclass(slots=True)
class Token:
    t_type: int
    line: int
    col: int
    value: str | None = None


def highlight_location(source: str, token: Token, context: int = 0) -> str:
    """
    Generates a visual snippet pointing to the token's location in the source.
    Handles tab alignment automatically.
    """
    lines = source.splitlines()
    if not lines:
        return "[Error: Source is empty]"

    line_idx = token.line - 1

    if line_idx < 0 or line_idx >= len(lines):
        return f"[Error: Token line {token.line} is out of bounds]"

    start_line = max(0, line_idx - context)
    end_line = min(len(lines), line_idx + 1 + context)

    output = []

    for i in range(start_line, end_line):
        line_num = i + 1
        line_text = lines[i]

        gutter = f"{line_num:4} | "
        output.append(f"{gutter}{line_text}")

        if i == line_idx:
            raw_prefix = line_text[:token.col - 1]
            padding = "".join('\t' if c == '\t' else ' ' for c in raw_prefix)
            gutter_space = " " * len(gutter)

            output.append(f"{gutter_space}{padding}^")

    return "\n".join(output)


T_NEWLINE = 0
T_INDENT = 2001
T_DEDENT = 2002
T_END_OF_FILE = 2003

T_COMMAND = 4000
T_VARIABLE = 4001

T_IDENTIFIER = 1001
T_KEYWORD = 1002
T_FLOAT = 1003
T_INTEGER = 1004
T_STRING = 1005

T_BANG = 1
T_PERCENT = 2
T_CARET = 3
T_AMPERSAND = 4
T_DOUBLE_AMPERSAND = 5
T_STAR = 6
T_DOUBLE_STAR = 7
T_OPEN_PARENS = 8
T_CLOSE_PARENS = 9
T_MINUS = 10
T_PLUS = 11
T_EQUALS = 12
T_DOUBLE_EQUALS = 13
T_PLUS_EQUALS = 14
T_MINUS_EQUALS = 15
T_BANG_EQUALS = 16
T_LESS_THAN_EQUALS = 17
T_MORE_THAN_EQUALS = 18
T_OPEN_BRACKETS = 19
T_CLOSE_BRACKETS = 20
T_COLON = 23
T_SEMI_COLON = 24
T_AT = 25
T_LESS_THAN = 26
T_LEFT_SHIFT = 27
T_MORE_THAN = 28
T_RIGHT_SHIFT = 29
T_COMMA = 30
T_DOT = 31
T_SLASH = 32
T_QUESTION_MARK = 33
T_DOUBLE_PIPES = 34
