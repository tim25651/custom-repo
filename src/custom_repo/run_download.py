"""Get files to the target directory.

Main entry point is `download_cmd`"""

import logging
from pathlib import Path
from typing import Literal

from custom_repo.modules import ConnectionKeeper, TemporaryDirectory
from custom_repo.modules import download as dl
from custom_repo.modules import file_manup
from custom_repo.parser import (
    DOWNLOAD_CMD,
    Command,
    PackageManager,
    Params,
    TargetDir,
    cmd_groups,
    fix_vars,
    from_file,
)

run_logger = logging.getLogger(__name__)


def download_cmd(
    keeper: ConnectionKeeper,
    params: Params,
    cmd: DOWNLOAD_CMD,
    args: list[str],
    wd: Path,
) -> None:
    """Subset of run_cmd for downloading files"""
    if cmd_groups.download_gh(cmd):
        from_github(keeper, params, args, wd)

    elif cmd_groups.from_file(cmd):
        from_file(keeper, params, cmd, args, wd)

    elif cmd_groups.from_src(cmd):
        from_src(params, cmd, args, wd)

    else:
        raise ValueError(f"Unknown command: {cmd}")


def from_github(
    keeper: ConnectionKeeper,
    params: Params,
    args: list[str],
    wd: Path,
) -> None:
    """Download a release from a GitHub repo.
    If no tag is given, download the latest release.

    Usage: DOWNLOAD_GH GH_REPO PATTERN [TAG]
    """

    gh_repo, pattern, *tags = args
    release_data = dl.get_release_data(
        gh_repo, exclude_prereleases=True, session=keeper.session
    )

    if not tags:
        asset, tag = dl.find_recent_asset(release_data, pattern)
    else:
        tag = tags.pop()

        if asset_by_tag := dl.find_asset_by_tag(release_data, pattern, tag):
            asset = asset_by_tag
        else:
            raise ValueError(
                f"No matching asset found for pattern {pattern} and tag {tag}"
            )

    url = f"https://www.github.com/{gh_repo}/releases/download/{tag}/{asset}"

    if params["MGR"] != PackageManager.APT:
        raise ValueError(f"Unsupported package manager: {params['MGR']}")

    if params["DIR"] == TargetDir.TMP:
        from_file(keeper, params, Command.DOWNLOAD, [url], wd)
        return

    stem = params["STEM"]
    target_path = wd / f"{stem}.deb"

    with TemporaryDirectory(prefix="tmp_from_github_", dir=params["REPO"]) as tmp:
        from_file(keeper, params, Command.DOWNLOAD, [url], tmp)

        try:
            file = next(tmp.iterdir())
            file.rename(target_path)
            params["FILE"] = target_path
        except StopIteration:
            pass


def from_src(
    params: Params,
    cmd: Literal[Command.SYMLINK_SRC, Command.COPY_SRC],
    args: list[str],
    wd: Path,
) -> bool:
    """Copy or symlink a file from the source directory.

    Usage:
    >>> COPY_SRC SRC
    >>> SYMLINK_SRC SRC
    """
    if cmd == Command.COPY_SRC:
        return copy_from_src(params, args, wd)

    if cmd == Command.SYMLINK_SRC:
        return symlink_from_src(params, args, wd)

    raise ValueError(f"Unknown command: {cmd}")


def symlink_from_src(
    params: Params,
    args: list[str],
    wd: Path,
) -> bool:
    """Copy a file from the source directory"""
    src = fix_vars(params, args[0])
    full_src = Path(params["REPO"]) / "private" / src

    src_file = src.split("/")[-1]

    if params["DIR"] != TargetDir.TMP:
        src_file = f"{params['STEM']}|{src_file}"

    target_file = wd / src_file
    params["FILE"] = target_file

    if target_file.exists():
        if not target_file.is_symlink():
            raise ValueError(f"{target_file} already exists and is not a symlink.")
        if (actual_src := target_file.readlink()) != full_src:
            raise ValueError(
                f"{target_file} already exists and points to {actual_src}."
            )
        run_logger.warning("%s already points to %s.", target_file, full_src)
        return False

    target_file.symlink_to(full_src)

    run_logger.info("Symlinked %s to %s.", full_src, target_file)

    return True


def copy_from_src(
    params: Params,
    args: list[str],
    wd: Path,
) -> bool:
    """Copy a file from the source directory"""
    src = fix_vars(params, args[0])
    full_src = Path(params["REPO"]) / "private" / src

    src_file = src.split("/")[-1]
    target_file = wd / src_file
    params["FILE"] = target_file

    if target_file.exists():
        run_logger.warning("%s already exists.", target_file)
        return False

    file_manup.copy(full_src, target_file)

    run_logger.info("Copied %s to %s.", full_src, target_file)

    return True
