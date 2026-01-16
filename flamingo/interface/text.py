import html
from typing import Self

from prompt_toolkit.formatted_text import HTML

from flamingo.core.debug.error import FlamingoException
from flamingo.interface.palette import get_palette


class FmtBuilder:
    def __init__(self, theme_flavor: str = "latte"):
        """
        :param theme_flavor: 'latte', 'frappe', 'macchiato', 'mocha'
        """
        self.palette = get_palette(theme_flavor)
        self.segments = []

    @classmethod
    def from_kernel(cls, kernel):
        """Factory: Grabs the theme from the kernel automatically."""
        flavor = "latte"
        try:
            val = kernel.resolve_var_path("@theme")
            flavor = str(val.value)
        except FlamingoException:
            pass
        return cls(flavor)

    def extend(self, formatted_list: list):
        self.segments.extend(formatted_list)
        return self

    def add(self, text, color_hex, bg=None, bold=False, italic=False, underline=False):
        safe_text = html.escape(str(text))

        style_parts = []
        if color_hex:
            style_parts.append(f'fg="{color_hex}"')
        if bg:
            bg_hex = self.palette.get(bg, bg)
            style_parts.append(f'bg="{bg_hex}"')

        style_str = " ".join(style_parts)

        if style_str:
            style = f'<style {style_str}>{safe_text}</style>'
            if bold:
                style = f'<b>{style}</b>'
            if italic:
                style = f'<i>{style}</i>'
            if underline:
                style = f"<u>{style}</u>"

            self.segments.append(style)
        else:
            self.segments.append(safe_text)
        return self

    def rosewater(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['rosewater'], **kwargs)

    def flamingo(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['flamingo'], **kwargs)

    def pink(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['pink'], **kwargs)

    def mauve(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['mauve'], **kwargs)

    def red(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['red'], **kwargs)

    def maroon(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['maroon'], **kwargs)

    def peach(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['peach'], **kwargs)

    def yellow(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['yellow'], **kwargs)

    def green(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['green'], **kwargs)

    def teal(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['teal'], **kwargs)

    def sky(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['sky'], **kwargs)

    def sapphire(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['sapphire'], **kwargs)

    def blue(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['blue'], **kwargs)

    def lavender(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['lavender'], **kwargs)

    def text(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['text'], **kwargs)

    def subtext1(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['subtext1'], **kwargs)

    def subtext0(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['subtext0'], **kwargs)

    def overlay2(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['overlay2'], **kwargs)

    def overlay1(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['overlay1'], **kwargs)

    def overlay0(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['overlay0'], **kwargs)

    def surface2(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['surface2'], **kwargs)

    def surface1(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['surface1'], **kwargs)

    def surface0(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['surface0'], **kwargs)

    def base(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['base'], **kwargs)

    def mantle(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['mantle'], **kwargs)

    def crust(self, text, **kwargs) -> Self:
        return self.add(text, self.palette['crust'], **kwargs)

    def space(self, count=1):
        self.segments.append(" " * count)
        return self

    def raw(self, text) -> Self:
        """Adds text without escaping (Dangerous, use carefully)"""
        self.segments.append(str(text))
        return self

    def join(self, delimiter=" ") -> Self:
        self.segments = [delimiter.join(self.segments)]
        return self

    def build(self):
        return HTML("".join(self.segments))
