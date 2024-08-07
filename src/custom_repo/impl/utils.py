"""Utility functions for the custom repository implementation."

Implements:
- `DirContext`: Context manager for the repository directory.
- `clean_data`: Clean the data in the repository.
- `final_exists`: Check if the final file already exists in the repository.
- `CommandExecutionError`: An error occurred during the execution of a command.
"""

import logging
from pathlib import Path
from typing import Any

from custom_repo.mgrs import PackageManager
from custom_repo.modules import TemporaryDirectory, filter_exts
from custom_repo.parser.params import Params, TargetDir

utils_logger = logging.getLogger(__name__)


class CommandExecutionError(Exception):
    """An error occurred during the execution of a command."""


class DirContext:
    """Context manager for the repository directory.

    If params["DIR"] is "tmp", a temporary directory is created.
    else either the debs or brew-data directory is returned.
    """

    def __init__(self, params: Params):
        """Initialize the context manager."""
        self.repo = params["REPO"]
        self.dir = params["DIR"]
        self.tmp: TemporaryDirectory | None = None

    def __enter__(self) -> Path:
        """Return the repository directory."""
        if self.dir == TargetDir.TMP:
            self.tmp = TemporaryDirectory(prefix="tmp_DirContext_", dir=self.repo)
            return self.tmp.path

        if self.dir == TargetDir.DEBS:
            return self.repo / "pkgs" / "apt"

        if self.dir == TargetDir.BREW:
            return self.repo / "public" / "data" / "brew"

        raise ValueError(f"Invalid directory: {self.dir}")

    def __exit__(self, *args: Any) -> None:
        """Clean up the temporary directory."""
        if self.tmp:
            self.tmp.cleanup()


def clean_data(repo: Path) -> None:
    """Remove downloaded files that are not installed.

    Args:
        repo (Path): The repository path.

    Raises:
        ValueError: If a file doesn't has the right prefix.
    """

    def _get_data(
        file: Path,
    ) -> tuple[str, str, PackageManager]:
        """Get the data."""
        suffix = "".join(filter_exts(file))
        name, version, maybe_mgr, *_ = file.name.split("|")
        maybe_mgr = maybe_mgr.removesuffix(suffix)

        try:
            mgr = PackageManager(maybe_mgr)
        except ValueError as e:
            raise ValueError(f"Invalid prefix: {maybe_mgr}") from e

        return name, version, mgr

    downloaded_files = list((x, _get_data(x)) for x in repo.glob("public/data/*/*"))
    installed_packages = list(_get_data(x) for x in repo.glob("pkgs/*/*"))
    installed_set = set(installed_packages)

    for file, data in downloaded_files:
        if data not in installed_set:
            utils_logger.warning("Removing %s", file)
            file.unlink()


def final_exists(params: Params) -> bool:
    """Check if the final file already exists in the repository."""

    mgr = params["MGR"]
    exts = {
        PackageManager.CONDA: ".tar.bz2",
        PackageManager.CHOCO: ".nupkg",
        PackageManager.BREW: ".rb",
    }

    if ext := exts.get(mgr):
        final = params["REPO"] / "pkgs" / mgr.value / (params["STEM"] + ext)

    elif mgr == PackageManager.APT:
        files = list((params["REPO"] / "pkgs" / "apt").iterdir())
        return any(f.name.startswith(params["STEM"]) for f in files)

    else:
        raise CommandExecutionError(f"Unknown package manager: {mgr}")

    utils_logger.debug("Checking if %s exists: %s", final, final.exists())

    return final.exists()
