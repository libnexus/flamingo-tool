from flamingo.plugins.plugin import FlamingoPlugin


class CorePlugin(FlamingoPlugin):
    def __init__(self):
        super().__init__("core", "flamingo", "Core system functionality", "0.1")

    def load(self, kernel) -> tuple[int, int]:
        return 0, 0

    def unload(self, kernel) -> [int, int]:
        return 0, 0


core = CorePlugin()
