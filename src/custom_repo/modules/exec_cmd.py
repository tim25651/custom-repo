"""Module to run shell commands.

Implements:
- `exec_cmd`: Execute a command and return the output.
- `exec_cmd_with_status`: Execute a command and return the output and status.
"""

import logging
import subprocess
from pathlib import Path

exec_logger = logging.getLogger(__name__)


class ExecError(Exception):
    """Command execution failed."""


def exec_cmd_with_status(
    args: list[str],
    cwd: str | Path | None = None,
) -> tuple[str, str, int]:
    """Run a command and return the output and status.

    Args:
        args: The command to run splitted like in a shell.
        cwd: The working directory. Defaults to the current directory.

    Returns:
        A tuple with the stdout, stderr and return code.
    """
    exec_logger.debug("Running %s in %s", args, cwd)

    with subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd
    ) as p:
        stdout, stderr = p.communicate()

        decoded_out = stdout.decode("utf-8")
        decoded_err = stderr.decode("utf-8")

        return decoded_out, decoded_err, p.returncode


def exec_cmd(
    args: list[str],
    cwd: str | Path | None = None,
    raise_on_failure: bool = True,
) -> str:
    """Run a command and return the output.

    Args:
        args: The command to run splitted like in a shell.
        cwd: The working directory. Defaults to the current directory.
        raise_on_failure: Raise an error if the command fails. Defaults to True.

    Returns:
        The output of the command.

    Raises:
        ExecError: If the command fails and raise_on_failure is True.
    """
    stdout, stderr, errorcode = exec_cmd_with_status(args, cwd)

    if raise_on_failure and errorcode != 0:
        raise ExecError(f"Error running {args}: {stderr}")

    return stdout
