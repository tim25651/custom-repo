"""Homebrew tap repository management."""

import logging
import shutil
import urllib.parse
from pathlib import Path

from custom_repo.modules import TemporaryDirectory, file_manup, git
from custom_repo.parser import Params, fix_vars

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
    pkgs = repo / "pkgs" / "tap"

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


def write_caskfile(
    params: Params,
    args: list[str],
) -> bool:
    """Create a Cask file for Homebrew."""
    # content in {{{ ... }}}
    repo = params["REPO"]
    stem = params["STEM"]
    pub = repo / "public"
    pkgs = repo / "pkgs" / "tap"

    content = args[0]

    target_file = pkgs / (stem + ".rb")

    content = fix_vars(params, content)

    if "$TAP_FILE" in content:
        if not isinstance(params["FILE"], Path):
            raise ValueError(f"No FILE set for {params['NAME']}.")

        rel_path = params["FILE"].relative_to(pub)
        escaped_rel_path = urllib.parse.quote(str(rel_path))
        content = content.replace("$TAP_FILE", f"{params['DOMAIN']}/{escaped_rel_path}")

    target_file.write_text(content, "utf-8")
    tap_logger.info("Wrote Cask file: %s", target_file)

    return True
