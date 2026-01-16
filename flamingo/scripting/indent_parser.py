from flamingo.scripting.error import FlamingoScriptError


def parse_indentation(text):
    root = []

    stack = [(-1, root)]

    lines = text.split('\n')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        indent = len(line) - len(line.lstrip())

        while indent <= stack[-1][0]:
            stack.pop()

        if indent > stack[-1][0]:
            current_scope = stack[-1][1]
            if not current_scope:
                raise FlamingoScriptError("Indentation without a parent line.")

            parent_node = current_scope[-1]

            if "children" not in parent_node:
                parent_node["children"] = []

            stack.append((indent, parent_node["children"]))

        node = {"line": stripped}
        stack[-1][1].append(node)

    return root
