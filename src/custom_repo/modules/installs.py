"""Check if the programs are installed.

Implements:
- `check_installs`: Check if the programs are installed.
"""

from collections.abc import Iterable

from custom_repo.modules.choco import choco
from custom_repo.modules.exec_cmd import exec_cmd


def _check_choco() -> None:
    """Check if choco is installed

    Raises:
        ValueError: If choco is not installed.
    """
    try:
        choco(["--help"])
    except ValueError as e:
        raise ValueError("Chocolatey is not installed.") from e


def _check_conda_build() -> None:
    """Check if conda-build is installed

    Raises:
        ValueError: If conda-build is not installed.
    """
    try:
        exec_cmd(["conda-build", "--version"])
    except ValueError as e:
        raise ValueError("Conda is not installed.") from e


def check_installs(progs: Iterable[str]) -> None:
    """Check if the programs are installed.

    Args:
        progs (Iterable[str]): The programs to check.
            Special programs are "choco" and "conda-build".

    Raises:
        ValueError: If a program is not installed.
    """

    parsed: list[str] = []
    for prog in set(progs):
        if prog == "choco":
            _check_choco()
        elif prog == "conda-build":
            _check_conda_build()
        else:
            parsed.append(prog)

    sub_cmds = [f"which {prog} 2>&1 >/dev/null; echo $?;" for prog in parsed]
    cmd = " ".join(sub_cmds)

    # no shell injection here, as the progs are hardcoded
    ret_vals = exec_cmd(["sh", "-c", cmd]).splitlines()

    for prog, retval in zip(parsed, ret_vals):
        if int(retval) != 0:
            raise ValueError(f"{prog} is not installed.")
