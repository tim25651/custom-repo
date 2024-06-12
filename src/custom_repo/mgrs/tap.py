"""Homebrew tap repository management."""

import logging
import shutil
from pathlib import Path

from custom_repo.modules import TemporaryDirectory, file_manup, git

tap_logger = logging.getLogger(__name__)


def build_tap(repo: Path) -> None:
    """Build the tap repository.

    Args:
        repo: The repository directory.

    Raises:
        FileExistsError: If the public directory already exists.
        ValueError: If an unexpected file is found in the temporary directory.
    """
    pub = repo / "public" / "tap.git"
    pkgs = repo / "pkgs" / "brew"

    if not pub.exists():
        git.init(pub, bare=True)
        git.update_server_info(pub)

    with TemporaryDirectory(prefix="tmp_build_tap_", dir=repo) as tmp_parent:
        git.clone(pub, tmp_parent)
        curr_tmp = tmp_parent / "tap"

        casks = curr_tmp / "Casks"
        if casks.exists():
            shutil.rmtree(casks)

        casks.mkdir()

        files = list(pkgs.iterdir()) if pkgs.exists() else []

        if not files:  # pylint: disable=consider-using-assignment-expr
            tap_logger.warning("No Cask files found in %s.", pkgs)
            (casks / ".empty").write_text("No Cask files found.", "utf-8")

        for file in files:
            if file.suffix != ".rb":
                raise ValueError(f"Unexpected file in {pkgs}: {file}")
            filename = file.stem.split("|")[0] + ".rb"
            file_manup.copy(file, casks / filename)

        git.commit_everything(curr_tmp, pub, message="Pushed.")
