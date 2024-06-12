"""Utilities for file manipulation.

Implements:
- `extract`: Extract a tarball.
- `copy`: Copy a file or folder.
"""

import fnmatch
import logging
import shutil
import tarfile
from pathlib import Path

from custom_repo.modules.ext import filter_exts

file_logger = logging.getLogger(__name__)


class FileManupilationError(Exception):
    """File manipulation failed."""


class DecompressionError(FileManupilationError):
    """Decompression failed."""


def _get_compression_mode(src: Path) -> str:
    """Return the compression mode for a given tarball.

    If suffix is .tgz or .tar.gz, return 'r:gz'.
    If suffix is .tbz2 or .tar.bz2, return 'r:bz2'.
    Otherwise, return 'r'.
    """
    exts = filter_exts(src)
    if ".tar" not in exts:
        raise DecompressionError(f"Not a tarball: {src}")

    if ".gz" in exts or ".tgz" in exts:
        return "r:gz"
    if ".bz2" in exts or ".tbz2" in exts:
        return "r:bz2"

    raise DecompressionError(f"Unknown compression mode for {src}")


def extract(
    src: Path,
    target: Path | None = None,
    glob: str | None = None,
) -> None:
    """Extract the tar file at `src` to `target`.
    Use the parent directory of `src` if `target` is None."""

    file_logger.debug("Extracting %s to %s with glob %s", src, target, glob)

    mode = _get_compression_mode(src)

    if target is None:
        target = src.parent

    with tarfile.open(src, mode) as tar:
        if glob:
            for member in tar.getmembers():
                if fnmatch.fnmatch(member.name, glob):
                    file_logger.debug("Extracting %s ...", member.name)
                    tar.extract(member, target)
                else:
                    file_logger.debug("Skipping %s ...", member.name)
        else:
            tar.extractall(target)

    file_logger.info("Extracted %s.", src)


def copy(
    src: Path, target: Path, recursive: bool = False, glob: str | None = None
) -> None:
    """Copy the file/folder at `src` to `target`.
    Either copy a single file, a folder recursively or files matching a glob pattern."""
    if recursive and glob:
        raise ValueError("Cannot use recursive and glob together.")

    if recursive:
        shutil.copytree(src, target)
        file_logger.debug("Copied the tree at %s to %s.", src, target)
        return

    if glob:
        for file in src.glob(glob):
            shutil.copy(file, target)
            file_logger.debug("Copied %s to %s.", file, target)
        return

    shutil.copy(src, target)

    file_logger.debug("Copied %s to %s.", src, target)
