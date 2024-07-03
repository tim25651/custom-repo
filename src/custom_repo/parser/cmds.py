"""This module contains the Command enum.

Implements:
- `Command`: An enum with the available commands.
- `NUMBER_OF_ARGS`: A dictionary with
    the number of arguments allowed for each command.
- `check_number_of_args`: Check if the number of arguments is correct.
"""

from enum import Enum


class Command(Enum):
    """Available commands for the custom_repo script."""

    CHOCO = "CHOCO"
    VERSION = "VERSION"
    DOWNLOAD = "DOWNLOAD"
    DOWNLOAD_GH = "DOWNLOAD_GH"
    DOWNLOAD_BROWSER = "DOWNLOAD_BROWSER"
    SYMLINK_SRC = "SYMLINK_SRC"
    COPY_SRC = "COPY_SRC"
    COPY = "COPY"
    COPY_FIX = "COPY_FIX"
    COPY_DIR = "COPY_DIR"
    COPY_GLOB = "COPY_GLOB"
    SANDBOX = "SANDBOX"
    RENAME = "RENAME"
    SET = "SET"
    EXTRACT = "EXTRACT"
    CREATE_DEB = "CREATE_DEB"
    BUILD_DEB = "BUILD_DEB"
    CASK = "CASK"
    CONDA = "CONDA"
    CONDA_BUILD = "CONDA_BUILD"
    MKDIR = "MKDIR"
    DH_DISABLE = "DH_DISABLE"
    INCLUDE_BINARIES = "INCLUDE_BINARIES"
    DOWNLOAD_REMOTE_NAME = "DOWNLOAD_REMOTE_NAME"
    SET_NATIVE = "SET_NATIVE"
    REMOVE = "REMOVE"


NUMBER_OF_ARGS: dict[Command, int | tuple[int, ...]] = {
    Command.CHOCO: 0,
    Command.VERSION: 1,
    Command.DOWNLOAD: 1,
    Command.DOWNLOAD_REMOTE_NAME: 1,
    Command.DOWNLOAD_GH: (2, 3),
    Command.DOWNLOAD_BROWSER: 1,
    Command.SYMLINK_SRC: 1,
    Command.COPY_SRC: 1,
    Command.COPY: 2,
    Command.COPY_FIX: 2,
    Command.COPY_DIR: 2,
    Command.COPY_GLOB: 3,
    Command.SANDBOX: 0,
    Command.MKDIR: 1,
    Command.RENAME: 1,
    Command.SET: 2,
    Command.EXTRACT: (0, 1),
    Command.CREATE_DEB: (0, 1),
    Command.BUILD_DEB: 0,
    Command.CASK: 1,
    Command.CONDA: 0,
    Command.CONDA_BUILD: 0,
    Command.DH_DISABLE: 1,
    Command.INCLUDE_BINARIES: 0,
    Command.SET_NATIVE: 0,
    Command.REMOVE: 1,
}


def check_number_of_args(cmd: Command, args: list[str]) -> None:
    """Check if the number of arguments is correct.

    Args:
        cmd (Command): The command to check.
        args (list[str]): The arguments to check.
    """
    num_args = NUMBER_OF_ARGS[cmd]

    msg = (
        f"Expected {num_args} arguments, got {len(args)}"
        f" in line: {cmd.value} {' '.join(args)}"
    )

    if isinstance(num_args, int):
        if len(args) != num_args:
            raise ValueError(msg)
    elif len(args) not in num_args:
        raise ValueError(msg)
