"""Implementation of the download commands.

Implements:
- `from_github`: Download a release from a GitHub repo.
- `from_src`: Copy or symlink a file from the source directory.
- `from_file`: Download a file from a URL.
"""

import logging
from pathlib import Path
from typing import Literal

from custom_repo.modules import ConnectionKeeper, TemporaryDirectory
from custom_repo.modules import download as dl
from custom_repo.modules import file_manup, filter_exts
from custom_repo.parser import (
    Command,
    PackageManager,
    Params,
    TargetDir,
    cmd_groups,
    fix_vars,
)

dl_logger = logging.getLogger(__name__)


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
        dl_logger.warning("%s already points to %s.", target_file, full_src)
        return False

    target_file.symlink_to(full_src)

    dl_logger.info("Symlinked %s to %s.", full_src, target_file)

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
        dl_logger.warning("%s already exists.", target_file)
        return False

    file_manup.copy(full_src, target_file)

    dl_logger.info("Copied %s to %s.", full_src, target_file)

    return True


def from_file(  # pylint: disable=too-complex
    keeper: ConnectionKeeper,
    params: Params,
    cmd: Literal[
        Command.DOWNLOAD, Command.DOWNLOAD_BROWSER, Command.DOWNLOAD_REMOTE_NAME
    ],
    args: list[str],
    wd: Path,
) -> None:
    """Download a file from a URL.
    If DOWNLOAD_BROWSER is used, open the URL in the browser.

    Usage:
    >>> DOWNLOAD URL
    >>> DOWNLOAD_REMOTE_NAME URL
    >>> DOWNLOAD_BROWSER URL
    """
    url = args[0]
    url = fix_vars(params, url)

    if not params["SUFFIXES"]:
        if cmd == Command.DOWNLOAD_REMOTE_NAME:
            raise ValueError("No suffixes given for remote name download.")

        if cmd == Command.DOWNLOAD:
            params["SUFFIXES"] = filter_exts(Path(url))
        elif cmd == Command.DOWNLOAD_BROWSER:
            pass
        else:
            raise ValueError(f"Unknown command: {cmd}")

    if cmd_groups.download_direct(cmd):
        filename = params["STEM"] + "".join(params["SUFFIXES"])
        params["FILE"] = dl.download_direct(url, wd, filename, session=keeper.session)

    # open the URL in the browser and download the file
    elif cmd == Command.DOWNLOAD_BROWSER:
        if params["DIR"] in {
            TargetDir.BREW,
        }:
            stem = None
            prefix = params["STEM"] + "|"
        else:
            stem = params["STEM"]
            prefix = None

        if params["MGR"] == PackageManager.CHOCO:
            stem = None

        try:
            params["FILE"] = dl.download_via_browser(
                keeper.browser, url, wd, stem=stem, prefix=prefix
            )
        except dl.file.DownloadError as e:
            dl_logger.error("Error during download from %s: %s", url, e)
            params["FILE"] = "FAILED_DOWNLOAD"

    else:
        raise ValueError(f"Unknown command: {cmd}")
