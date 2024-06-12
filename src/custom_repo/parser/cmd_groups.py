"""Defines groups of commands for the parser and typeguard functions.

Implements:
- `DOWNLOAD_CMD`: A type alias with the download commands.
- `DOWNLOAD_CMDS`: A tuple with the download commands.
- `COPY_CMD`: A type alias with the copy commands.
- `COPY_CMDS`: A tuple with the copy commands.
- `UNIQUE_CMD`: A type alias with the unique commands.
- `UNIQUE_CMDS`: A tuple with the unique commands.
- `unique_cmd`: Typeguard for the UNIQUE commands.
- `download_cmd`: Typeguard for the DOWNLOAD commands.
- `download_gh`: Typeguard for the DOWNLOAD_GH command.
- `from_file`: Typeguard for the DOWNLOAD and DOWNLOAD_BROWSER commands.
- `download_direct`: Typeguard for the DOWNLOAD command.
- `from_src`: Typeguard for the SYMLINK_SRC and COPY_SRC commands.
- `copy_cmd`: Typeguard for the COPY commands.
"""

from typing import Literal, TypeAlias, TypeGuard

from custom_repo.parser.cmds import Command

DOWNLOAD_CMD: TypeAlias = Literal[  # pylint: disable=invalid-name
    Command.DOWNLOAD,
    Command.DOWNLOAD_REMOTE_NAME,
    Command.DOWNLOAD_BROWSER,
    Command.DOWNLOAD_GH,
    Command.SYMLINK_SRC,
    Command.COPY_SRC,
]
DOWNLOAD_CMDS = (
    Command.DOWNLOAD,
    Command.DOWNLOAD_REMOTE_NAME,
    Command.DOWNLOAD_BROWSER,
    Command.DOWNLOAD_GH,
    Command.SYMLINK_SRC,
    Command.COPY_SRC,
)

COPY_CMD: TypeAlias = Literal[  # pylint: disable=invalid-name
    Command.COPY,
    Command.COPY_FIX,
    Command.COPY_DIR,
    Command.COPY_GLOB,
]
COPY_CMDS = (Command.COPY, Command.COPY_FIX, Command.COPY_DIR, Command.COPY_GLOB)

UNIQUE_CMD: TypeAlias = Literal[  # pylint: disable=invalid-name
    Command.VERSION,
    Command.SANDBOX,
    Command.CREATE_DEB,
    Command.BUILD_DEB,
    Command.CASK,
    Command.CONDA,
]

UNIQUE_CMDS = (
    Command.VERSION,
    Command.SANDBOX,
    Command.CREATE_DEB,
    Command.BUILD_DEB,
    Command.CASK,
    Command.CONDA,
)


def unique_cmd(
    cmd: Command,
) -> TypeGuard[UNIQUE_CMD]:
    """Typeguard for the UNIQUE commands."""
    return cmd in UNIQUE_CMDS


def download_cmd(
    cmd: Command,
) -> TypeGuard[DOWNLOAD_CMD]:
    """Typeguard for the DOWNLOAD commands."""
    return cmd in DOWNLOAD_CMDS


def download_gh(
    cmd: DOWNLOAD_CMD,
) -> TypeGuard[Literal[Command.DOWNLOAD_GH]]:
    """Typeguard for the DOWNLOAD_GH command."""
    return cmd in {Command.DOWNLOAD_GH}


def from_file(
    cmd: DOWNLOAD_CMD,
) -> TypeGuard[
    Literal[Command.DOWNLOAD, Command.DOWNLOAD_BROWSER, Command.DOWNLOAD_REMOTE_NAME]
]:
    """Typeguard for the DOWNLOAD and DOWNLOAD_BROWSER commands."""
    return cmd in {
        Command.DOWNLOAD,
        Command.DOWNLOAD_BROWSER,
        Command.DOWNLOAD_REMOTE_NAME,
    }


def download_direct(
    cmd: DOWNLOAD_CMD,
) -> TypeGuard[Literal[Command.DOWNLOAD, Command.DOWNLOAD_REMOTE_NAME]]:
    """Typeguard for the DOWNLOAD command."""
    return cmd in {Command.DOWNLOAD, Command.DOWNLOAD_REMOTE_NAME}


def from_src(
    cmd: DOWNLOAD_CMD,
) -> TypeGuard[Literal[Command.SYMLINK_SRC, Command.COPY_SRC]]:
    """Typeguard for the SYMLINK_SRC and COPY_SRC commands."""
    return cmd in {Command.SYMLINK_SRC, Command.COPY_SRC}


def copy_cmd(
    cmd: Command,
) -> TypeGuard[COPY_CMD]:
    """Typeguard for the COPY commands."""
    return cmd in COPY_CMDS
