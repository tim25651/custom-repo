class CommandExecutionError(Exception):
    """An error occurred during the execution of a command."""


class NoElementsError(CommandExecutionError):
    """No elements are found in the directory."""


class MultipleElementsError(CommandExecutionError):
    """Multiple elements are found in the directory."""


class VariableError(Exception):
    """Could not set the variable."""
