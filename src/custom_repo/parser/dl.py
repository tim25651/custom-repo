"""TODO: weird module, need to be refactored.
Is here, so no cyclic imports occur."""

import logging
from pathlib import Path
from typing import Literal

from custom_repo.modules import ConnectionKeeper
from custom_repo.modules import download as dl
from custom_repo.modules import filter_exts
from custom_repo.parser import cmd_groups
from custom_repo.parser.cmds import Command
from custom_repo.parser.params import PackageManager, Params, TargetDir
from custom_repo.parser.utils import fix_vars

dl_logger = logging.getLogger(__name__)


def get_name(
    cmd: Literal[Command.DOWNLOAD_REMOTE_NAME, Command.DOWNLOAD_BROWSER],
    url: str,
    keeper: ConnectionKeeper,
) -> str | Literal["FAILED_DOWNLOAD"]:
    """Get the name of a remote file or download it via the browser."""
    if cmd == Command.DOWNLOAD_REMOTE_NAME:
        return dl.get_remote_filename(url)

    if cmd == Command.DOWNLOAD_BROWSER:
        try:
            return str(dl.download_via_browser(keeper.browser, url, None))
        except dl.file.DownloadError as e:
            dl_logger.error("Error during download from %s: %s", url, e)
            return "FAILED_DOWNLOAD"

    raise ValueError(f"Unknown command: {cmd}")

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
            TargetDir.TAP,
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
