"""A .rep file contains of lines of the form:
CMD ARG1 ARG2 ...
The first word is the command to be executed and the rest are the arguments.
"""

import logging
from pathlib import Path

from custom_repo.exceptions import CustomRepoError
from custom_repo.impl import IMPLEMENTATIONS
from custom_repo.modules import ConnectionKeeper, filter_exts
from custom_repo.parser import Command, PackageManager, Params

run_logger = logging.getLogger(__name__)


def run_cmd(
    keeper: ConnectionKeeper,
    params: Params,
    cmd: Command,
    args: list[str],
    wd: Path,
) -> None:
    """Parse and run a command in `wd`.
    Returns if the program should keep running."""
    if cmd == Command.CASK:
        log_args = [x[:10] for x in args]
    else:
        log_args = args

    run_logger.debug("CMD: %s ARGS: %s", cmd, log_args)

    func = IMPLEMENTATIONS[cmd]
    func(keeper, params, args, wd)


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
            run_logger.warning("Removing %s", file)
            file.unlink()


def final_exists(params: Params) -> bool:
    """Check if the final file already exists in the repository."""

    mgr = params["MGR"]
    repo = params["REPO"]
    stem = params["STEM"]

    def _prefix(mgr: PackageManager) -> Path:
        """Get the prefix for the pkgs folder."""
        return repo / "pkgs" / mgr.value

    if mgr == PackageManager.CONDA:
        final = _prefix(mgr) / f"{stem}.tar.bz2"
    elif mgr == PackageManager.CHOCO:
        final = _prefix(mgr) / f"{stem}.nupkg"
    elif mgr == PackageManager.BREW:
        final = _prefix(mgr) / f"{stem}.rb"
    elif mgr == PackageManager.APT:
        files = list(_prefix(mgr).iterdir())
        return any(f.name.startswith(stem) for f in files)
    else:
        raise CustomRepoError(f"Unknown package manager: {mgr}")

    run_logger.debug("Checking if %s exists: %s", final, final.exists())

    return final.exists()
