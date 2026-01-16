class ContextScope:
    GLOBAL_CONTEXT = []
    """Context Manager for 'with' syntax."""

    def __init__(self, description: str):
        """
        :param description: A quick description of the scope that's about to be entered. I.e. what's about to happen
        """
        self.description = description

    def __enter__(self):
        self.GLOBAL_CONTEXT.append(self.description)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.GLOBAL_CONTEXT.pop()
        return False


class FlamingoExit(SystemExit):
    """Utility exception for the shell"""


class FlamingoException(Exception):
    """Base Exception for all Shell Logic."""

    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception


class PermissionDeniedError(FlamingoException):
    """Raised when a User lacks the specific granular permission."""


class VariableNotFoundError(FlamingoException):
    """Raised when a dot-path cannot be resolved."""


class ReadOnlyError(FlamingoException):
    """Raised when an object, variable or file is read-only."""


class CommandExecutionError(FlamingoException):
    """Raised when a Plugin/Command fails during .execute()."""


class ValidationError(FlamingoException):
    """Raised when a FlamingoVar fails type validation."""


class PluginError(FlamingoException):
    """Raised when an issue with the plugin system occurs."""
