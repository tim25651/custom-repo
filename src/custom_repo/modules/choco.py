"""Chocolatey commands."""

import os
from pathlib import Path

from custom_repo.modules.exec_cmd import exec_cmd


def choco(args: list[str], cwd: Path | None = None) -> str:
    """Run a Chocolatey command."""
    conda_prefix = os.getenv("CONDA_PREFIX")
    if not conda_prefix:  # pylint: disable=consider-using-assignment-expr
        raise ValueError("CONDA_PREFIX is not set.")

    return exec_cmd(
        ["mono", f"{conda_prefix}/opt/chocolatey/choco.exe", *args], cwd=cwd
    )
