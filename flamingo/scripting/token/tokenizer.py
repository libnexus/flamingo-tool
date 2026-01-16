import re
from typing import Union
from flamingo.scripting.token.token_types import *

TRIGGER_KEYWORDS = frozenset({
    "!if", "!else", "!macro", "!while", "!for", "!do", "!set"
})

NORMAL_PATTERN = re.compile(
    r'(?P<VAR_START>\{)|'
    r'(?P<OP2>&&|\*\*|==|\+=|-=|!=|<=|>=|<<|>>)|'
    r'(?P<ID>!?[a-zA-Z_$][a-zA-Z0-9_$]*)|'
    r'(?P<OP1>[!%^&*()\-=+\[\]:;@<>,./?])|'
    r'(?P<FLOAT>[\d_]*\.[\d_]+)|'
    r'(?P<INT>[\d_]+)|'
    r'(?P<STR>"[^"\n]*"|\'[^\'\n]*\')|'
    r'(?P<WS> +)|'
    r'(?P<COMMENT>#[^\n]*)'
)

BRACE_SEARCH = re.compile(r'[{}]')

OP_MAP = {
    "&&": T_DOUBLE_AMPERSAND, "**": T_DOUBLE_STAR, "==": T_DOUBLE_EQUALS,
    "+=": T_PLUS_EQUALS, "-=": T_MINUS_EQUALS, "!=": T_BANG_EQUALS,
    "<=": T_LESS_THAN_EQUALS, ">=": T_MORE_THAN_EQUALS, "<<": T_LEFT_SHIFT,
    ">>": T_RIGHT_SHIFT, "!": T_BANG, "%": T_PERCENT, "^": T_CARET,
    "&": T_AMPERSAND, "*": T_STAR, "(": T_OPEN_PARENS, ")": T_CLOSE_PARENS,
    "-": T_MINUS, "+": T_PLUS, "=": T_EQUALS, "[": T_OPEN_BRACKETS,
    "]": T_CLOSE_BRACKETS, ":": T_COLON, ";": T_SEMI_COLON, "@": T_AT,
    "<": T_LESS_THAN, ">": T_MORE_THAN, ",": T_COMMA, ".": T_DOT,
    "/": T_SLASH, "?": T_QUESTION_MARK
}

ERR_BIG_INDENT = 0
ERR_INCONSISTENT_INDENT = 1


def tokenizer(source: str) -> Union[list[Token], int]:
    tokens = []
    append_token = tokens.append

    indent_size = None
    indent_stack = 0
    line_no = 0

    lines = source.splitlines(keepends=True)

    for line in lines:
        line_no += 1
        line_len = len(line)
        pos = 0

        ws_len = 0
        while pos + ws_len < line_len and line[pos + ws_len] == ' ':
            ws_len += 1

        remaining_char = line[pos + ws_len] if pos + ws_len < line_len else ''
        if remaining_char == '\n' or remaining_char == '' or remaining_char == '#':
            continue

        curr_indent = ws_len
        if indent_size is None and curr_indent > 0:
            indent_size = curr_indent
            indent_stack = curr_indent
            append_token(Token(T_INDENT, line_no, 1))
        elif indent_size is not None:
            if curr_indent % indent_size != 0:
                return ERR_INCONSISTENT_INDENT

            if curr_indent > indent_stack:
                if curr_indent == indent_stack + indent_size:
                    indent_stack += indent_size
                    append_token(Token(T_INDENT, line_no, 1))
                else:
                    return ERR_BIG_INDENT
            elif curr_indent < indent_stack:
                while indent_stack > curr_indent:
                    indent_stack -= indent_size
                    append_token(Token(T_DEDENT, line_no, 1))

        pos += ws_len

        match_peek = NORMAL_PATTERN.match(line, pos)

        if match_peek and match_peek.lastgroup == 'ID' and match_peek.group('ID') in TRIGGER_KEYWORDS:
            while pos < line_len:
                if line[pos] == '\n':
                    break

                match = NORMAL_PATTERN.match(line, pos)
                if not match:
                    pos += 1
                    continue

                kind = match.lastgroup

                if kind == 'VAR_START':
                    start_var = pos
                    balance = 1
                    scan_pos = pos + 1

                    while True:
                        brace_match = BRACE_SEARCH.search(line, scan_pos)
                        if not brace_match:
                            scan_pos = line_len
                            if line[scan_pos - 1] == '\n':
                                scan_pos -= 1
                            break

                        scan_pos = brace_match.end()
                        if brace_match.group() == '{':
                            balance += 1
                        else:
                            balance -= 1

                        if balance == 0:
                            break

                    append_token(Token(T_VARIABLE, line_no, start_var + 1, line[start_var + 1: scan_pos - 1]))
                    pos = scan_pos
                    continue

                col = pos + 1
                pos = match.end()
                text = match.group(kind)

                if kind == 'WS':
                    continue
                elif kind == 'COMMENT':
                    break
                elif kind == 'ID':
                    if text in TRIGGER_KEYWORDS:
                        append_token(Token(T_KEYWORD, line_no, col, text))
                    else:
                        append_token(Token(T_IDENTIFIER, line_no, col, text))
                elif kind == 'OP1' or kind == 'OP2':
                    append_token(Token(OP_MAP[text], line_no, col))
                elif kind == 'INT':
                    append_token(Token(T_INTEGER, line_no, col, text))
                elif kind == 'FLOAT':
                    append_token(Token(T_FLOAT, line_no, col, text))
                elif kind == 'STR':
                    append_token(Token(T_STRING, line_no, col, text[1:-1]))

        else:
            content_end = line_len
            if line.endswith('\n'):
                content_end -= 1

            command_text = line[pos:content_end]
            if command_text:
                append_token(Token(T_COMMAND, line_no, pos + 1, command_text))

        append_token(Token(T_NEWLINE, line_no, line_len))

    if indent_size:
        while indent_stack > 0:
            indent_stack -= indent_size
            append_token(Token(T_DEDENT, line_no + 1, 1))

    return tokens