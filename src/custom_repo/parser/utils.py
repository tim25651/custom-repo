"""Utility functions for the parser module.

Implements:
- `DirContext`: Context manager for the repository directory.
- `fix_vars`: Replace all variables in a string with their values.
- `adjust_regex_version`: Get the version from the filename.
"""

import re
from collections.abc import Iterable
from enum import Enum
from pathlib import Path
from typing import Any

from custom_repo.modules import TemporaryDirectory
from custom_repo.parser.params import Params, TargetDir


class DirContext:
    """Context manager for the repository directory.

    If params["DIR"] is "tmp", a temporary directory is created.
    else either the debs or tap-data directory is returned.
    """

    def __init__(self, params: Params):
        """Initialize the context manager."""
        self.repo = params["REPO"]
        self.dir = params["DIR"]
        self.tmp: TemporaryDirectory | None = None

    def __enter__(self) -> Path:
        """Return the repository directory."""
        if self.dir == TargetDir.TMP:
            self.tmp = TemporaryDirectory(prefix="tmp_DirContext_", dir=self.repo)
            return self.tmp.path

        if self.dir == TargetDir.DEBS:
            return self.repo / "pkgs" / "apt"

        if self.dir == TargetDir.TAP:
            return self.repo / "public" / "data" / "tap"

        raise ValueError(f"Invalid directory: {self.dir}")

    def __exit__(self, *args: Any) -> None:
        """Clean up the temporary directory."""
        if self.tmp:
            self.tmp.cleanup()


def fix_vars(params: Params, string: str, skip: Iterable[str] | None = None) -> str:
    """Replace all variables in a string with their values.

    Does not replace variables in the skip list or None values.
    """
    if skip is None:
        skip = []
    skip_set = set(skip) | {"VARS", "SUFFIXES"}

    all_vars = {**params, **params["VARS"]}

    for k, v in all_vars.items():
        if k in skip_set:
            continue
        if v is None:
            continue
        if isinstance(v, Path):
            v = str(v)
        if isinstance(v, Enum):
            v = v.value
        assert isinstance(v, str), f"Value for {k} is not a string: {v}"
        string = string.replace(f"${k}", v)

    if "$DEST" in string:
        string = string.replace("$DEST", f"{params['NAME']}-{params['VERSION']}")
    return string


def adjust_regex_version(version: str, filename: str) -> str:
    """Get the version from the filename."""
    if not version.startswith("re:"):
        raise ValueError(f"Not a regex VERSION: {version}")

    version = version.removeprefix("re:")

    for suffix in (".tar", ".gz", ".tgz", ".bz2", ".tbz2"):
        filename = filename.replace(suffix, "")

    version_pattern = re.compile(version)
    version_match = version_pattern.match(filename)
    if not version_match:  # pylint: disable=consider-using-assignment-expr
        raise ValueError(f"Could not match {filename} with {version_pattern}")

    version = version_match.group(1)

    return version
