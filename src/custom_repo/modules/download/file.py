"""Download a file from a link."""

import logging
import re
from pathlib import Path

import requests
from playwright._impl import _errors as pw_errors
from playwright._impl._sync_base import EventContextManager, EventInfo
from playwright.sync_api import Browser, Download
from requests import Session

from custom_repo.modules.ext import filter_exts
from custom_repo.modules.nullcontext import TypedNullContext

file_logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Download failed."""


class HeaderError(DownloadError):
    """Header extraction failed."""


class HTTPError(requests.HTTPError, DownloadError):
    """HTTP request failed."""


class BrowserError(DownloadError):
    """Browser download failed."""


class DownloadTimeoutError(TimeoutError, pw_errors.TimeoutError, DownloadError):
    """Download timed out."""


def get_remote_filename(url: str, session: Session | None = None) -> str:
    """Get the remote filename from a URL.

    Starts the download of the first byte of the file to get the filename.

    Args:
        url: The URL to get the filename from.
        session: The requests session to use. Defaults to None.
            Creates a new session if None.

    Returns:
        The filename extracted from the Content-Disposition header.

    Raises:
        HeaderError: If the filename could not be extracted.
    """

    # if session is provided, use it, otherwise create a new one
    session = session or Session()

    # try a get request and close ASAP
    response = session.get(url, stream=True)
    response.close()

    # read the Content-Disposition header and extract the filename
    # attachment; filename="filename"; filename*=UTF-8''filename ...
    if content := response.headers.get("Content-Disposition"):
        if match := re.match(r'attachment; filename="([^"]+)"', content):
            return match.group(1).rsplit("/", 1)[-1]
        raise HeaderError(f"Could not get filename from {content}")
    raise HeaderError(f"Could not get Content-Disposition from {url}")


def download_direct(
    url: str,
    target: Path,
    name: str | None = None,
    session: Session | None = None,
) -> Path:
    """Download a file from a URL to a target directory.

    Args:
        url: The URL to download from.
        target: The directory to download to.
        name: The name of the file to save as. Defaults to None.
        session: The requests session to use. Defaults to None.
            Creates a new session if None.

    Returns:
        The path to the downloaded file.

    Raises:
        HTTPError: If the response status code is not OK.
    """

    # if session is provided, use it, otherwise create a new one
    session = session or Session()

    # filename is the last part of the URL if not provided
    name = name or url.split("/")[-1]

    file_logger.info("Downloading %s directly...", name)

    # get the content and check for errors
    response = session.get(url)
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        raise HTTPError from e

    # save the content to the target directory
    target_path = target / name
    Path(target_path).write_bytes(response.content)

    file_logger.info("Downloaded %s.", name)

    return target_path


def _get_pw_download(browser: Browser, url: str) -> Download:
    """Get playwright download content from a URL and >-separated clicks.

    Raises:
        BrowserError: If the download did not start or a click could not be found.
    """
    url, *clicks = url.split(">")

    # Use the first page in the first context if available
    # Else create a new context and page
    if browser.contexts:
        page = browser.contexts[0].pages[0]
    else:
        context = browser.new_context(storage_state=None)
        page = context.new_page()

    # Mostly for type checking
    # returns an expect_download context manager if ctx=True
    # else returns a nullcontext which just outputs None
    def _build_ctx(
        expect_download: bool = False,
    ) -> EventContextManager[Download] | TypedNullContext[None]:
        """Build the context manager depending if a download is expected."""
        if expect_download:
            return page.expect_download()
        return TypedNullContext(None)

    def _return_download_info(download_info: EventInfo[Download] | None) -> Download:
        """Return the download info."""
        if download_info is None or download_info.value is None:
            raise BrowserError("Download did not start.")

        return download_info.value

    expect_download = len(clicks) == 0
    with _build_ctx(expect_download) as download_info:
        file_logger.debug("Go to %s", url)
        # just open the url
        page.goto(url)

    # if no clicks are provided, it is finished here
    if expect_download:
        return _return_download_info(download_info)

    for ix, click in enumerate(clicks):
        file_logger.debug("Click %s", click)

        # if this is the last click, expect a download
        expect_download = ix == len(clicks) - 1
        with _build_ctx(expect_download) as download_info:

            # click can be selector (#id) or text (text)
            if click.startswith("#"):
                if handle := page.query_selector(click):
                    handle.click()
                else:
                    raise BrowserError(f"Could not find {click} on {page.url}")
            else:
                page.get_by_text(click).first.click()

    # after all clicks, return the download info
    return _return_download_info(download_info)


def download_via_browser(
    browser: Browser,
    url: str,
    target: Path | None,
    stem: str | None = None,
    prefix: str | None = None,
) -> Path:
    """Download a file from a URL via a browser.

    Args:
        browser: The playwright browser to use.
        url: The URL to download from.
        target: The directory to download to. If None, get only the name.
        stem: The stem of the file to save as. Defaults to None.
        prefix: The prefix of the file to save as. Defaults to None.

    Returns:
        Path to the downloaded file (or just the name if target is None).

    Raises:
        DownloadTimeoutError: If the download did not start.
    """
    try:
        download = _get_pw_download(browser, url)
    except pw_errors.TimeoutError as e:
        raise DownloadTimeoutError("Download did not start.") from e

    # Wait for the download process to complete
    # and save the downloaded file somewhere
    sugg_name = download.suggested_filename
    sugg_path = Path(sugg_name)
    sugg_suffix = "".join(filter_exts(sugg_path))
    if not target:
        download.cancel()
        return sugg_path

    name = (stem + sugg_suffix) if stem else sugg_name
    name = prefix + name if prefix else name

    target_path = target / name

    file_logger.info("Downloading %s via browser...", name)

    # wait for the download to finish
    # and save the file to the target path
    download.save_as(target_path)

    file_logger.info("Downloaded %s.", name)

    return target_path
