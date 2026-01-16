from prompt_toolkit.styles import Style

PALETTE = {
    'Flamingo': '#f2cdcd',
    'Mauve': '#cba6f7',
    'Base': '#1e1e2e',
    'Text': '#cdd6f4',
    'Green': '#a6e3a1',
    'Red': '#f38ba8',
    'Overlay': '#7f849c',
    'Surface': '#313244'
}

FlamingoStyle = Style.from_dict({
    # Valid characters: a-z, 0-9, _, -, .
    'prompt.symbol': f"{PALETTE['Flamingo']} bold",

    # Default text
    '': f"{PALETTE['Text']}",

    'completion-menu.completion': f"bg:{PALETTE['Base']} {PALETTE['Text']}",
    'completion-menu.completion.current': f"bg:{PALETTE['Mauve']} {PALETTE['Base']} bold",
    'completion-menu.meta.completion': f"bg:{PALETTE['Surface']} {PALETTE['Overlay']}",
    'error': f"{PALETTE['Red']} bold",
    'meta': f"{PALETTE['Overlay']} italic",
})
