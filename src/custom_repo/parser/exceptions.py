"""Custom exceptions for the custom_repo package."""


class CustomRepoError(Exception):
    """Base class for exceptions in this module.
    Exists, so that it can be distinguished from other exceptions."""


class UnknownCommandError(CustomRepoError):
    """Unknown command is passed to the parser."""


class ParsingError(CustomRepoError):
    """Parsing of the input file failed."""


class StructureError(CustomRepoError):
    """Structure of the input file or folder is incorrect."""
