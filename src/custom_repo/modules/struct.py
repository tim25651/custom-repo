"""Compare a folder structure with set values

Implements:
- `has_missing_elems`: Raises an error if a folder structure is missing elements
- `has_invalid_elems`: Raises an error if a folder structure has invalid elements
- `has_correct_struct`: Raises an error if a folder structure is incorrect
"""

import fnmatch
from collections.abc import Iterable
from pathlib import Path


class FolderStructureError(Exception):
    """Folder structure is incorrect."""


class ElementNotFoundError(FileNotFoundError, FolderStructureError):
    """Element is missing."""


class ElementInvalidError(FileExistsError, FolderStructureError):
    """Element is invalid."""


def has_missing_elems(must_have: Iterable[str], base: Path, elem_name: str) -> None:
    """Check if the folder structure is correct.

    Args:
        must_have: The list of elements that must exist.
        base: The base path.
        elem_name: The name of the element.

    Raises:
        ElementNotFoundError: If an element is missing.
    """
    error: list[str] = []
    for d in must_have:
        if not (base / d).exists():
            error.append(f"Missing {elem_name}: {base/d}")
    if error:
        error.insert(0, f"Missing {elem_name}s in folder structure:")
        raise ElementNotFoundError("\n".join(error))


def has_invalid_elems(
    base: Path, allowed_dirs: set[str], allowed_files: set[str]
) -> None:
    """Check if no invalid files/folders are present in the repository.

    Args:
        base: The base path.
        allowed_dirs: The allowed directories.
        allowed_files: The allowed files.

    Raises:
        ElementInvalidError: If an invalid file/folder is present.
    """

    all_files = [(x.relative_to(base), x.is_dir()) for x in base.rglob("*")]

    error: list[str] = []
    for f, is_dir in all_files:
        sub_error = True
        if is_dir:
            for x in allowed_dirs:
                if fnmatch.fnmatch(str(f), x):
                    sub_error = False
                    break
        else:
            for x in allowed_files:
                if fnmatch.fnmatch(str(f), x):
                    sub_error = False
                    break

        if sub_error:
            error.append(f"- {f}")

    if error:
        error.insert(0, "Invalid files/folders in the repository:")
        raise ElementInvalidError("\n".join(error))


def has_correct_struct(
    base: Path,
    allowed_dirs: set[str],
    allowed_files: set[str],
    must_have_dirs: Iterable[str],
    must_have_files: Iterable[str],
) -> None:
    """Check if the folder structure is correct.

    Args:
        base: The base path.
        allowed_dirs: The allowed directories.
        allowed_files: The allowed files.
        must_have_dirs: The directories that must exist.
        must_have_files: The files that must exist.

    Raises:
        ElementNotFoundError: If an element is missing.
        ElementInvalidError: If an invalid file/folder is present.
    """
    has_missing_elems(must_have_dirs, base, "folder")
    has_missing_elems(must_have_files, base, "file")
    has_invalid_elems(base, allowed_dirs, allowed_files)
