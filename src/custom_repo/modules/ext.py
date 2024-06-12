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


def has_ext(
    path: Path,
    comp_exts: str | Sequence[Sequence[str] | str],
    filter: bool = False,  # pylint: disable=redefined-builtin
) -> bool:
    """Check if a file has any of the given extensions.

    Args:
        path: The path to check.
        comp_exts: The extensions to check.
        filter: If True, the extensions or `path` are filtered.

    Returns:
        True if the file has any of the given extensions, False otherwise.
    """
    exts = path.suffixes
    if filter:
        exts = filter_exts(exts)
    ext = exts[-1]

    # if only one suffix is provided
    if isinstance(comp_exts, str):
        return ext == comp_exts

    def _has_exts(exts: Sequence[str], sub_comp_exts: Sequence[str]) -> bool:
        """Check if the file has the given suffixes."""
        available = len(exts)
        goal = len(sub_comp_exts)
        return available >= goal and exts[-goal:] == sub_comp_exts

    for sub_ext in comp_exts:
        if isinstance(sub_ext, str):
            if ext == sub_ext:
                return True
        elif _has_exts(exts, sub_ext):
            return True

    return False
