"""Module to handle file extensions.

Implements:
- `COMPRESSION_EXTENSIONS`: A set with the supported compression file extensions.
- `ALLOWED_EXTENSIONS`: A set with the supported file extensions.
- `filter_exts`: Filter the file extensions.
"""

from collections.abc import Sequence
from pathlib import Path


class ExtensionError(Exception):
    """File extension not supported."""


COMPRESSION_EXTENSIONS = {
    ".tgz",
    ".tar.gz",
    ".tbz2",
    ".bz2",
    ".tar",
    ".gz",
    ".xz",
    ".zip",
    ".7z",
}

ALLOWED_EXTENSIONS = COMPRESSION_EXTENSIONS | {
    ".deb",
    ".rpm",
    ".exe",
    ".msi",
    ".rb",
    ".nupkg",
    ".nuspec",
    ".ps1",
    ".xml",
}


def filter_exts(path_or_suffixes: Path | list[str]) -> list[str]:
    """Filter the file extensions.

    Args:
        path_or_suffixes: The path or the suffixes to filter.

    Returns:
        The filtered file extensions.

    Raises:
        ExtensionError: If an allowed extension preceeds a disallowed one.
    """
    if isinstance(path_or_suffixes, Path):
        suffixes = path_or_suffixes.suffixes
    else:
        suffixes = path_or_suffixes

    filtered: list[str] = []
    for suffix in reversed(suffixes):
        if suffix in ALLOWED_EXTENSIONS:
            filtered.append(suffix)
        else:
            break
    filtered.reverse()

    remaining = suffixes[: len(suffixes) - len(filtered)]
    if set(remaining) & ALLOWED_EXTENSIONS:
        raise ExtensionError(
            f"An allowed extensions preceeds a disallowed one: {path_or_suffixes}"
        )

    return filtered
