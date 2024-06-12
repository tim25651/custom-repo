"""Expands the `tempfile` module

Implements:
- `TemporaryDirectory`: A temporary directory context manager,
    with `TMPDIR_DEBUG` set, the directory won't be removed.
"""

import logging
import os
import tempfile
from pathlib import Path

from typing_extensions import override

temp_logger = logging.getLogger(__name__)


class TemporaryDirectory(tempfile.TemporaryDirectory):
    """A temporary directory context manager,
    with `TMPDIR_DEBUG` set, the directory won't be removed.

    Attributes:
        path (Path): The path of the temporary directory.
    """

    def __init__(
        self,
        prefix: str | None = None,
        dir: Path | None = None,  # pylint: disable=redefined-builtin
    ) -> None:
        """Initialize the class.

        Args:
            prefix: The prefix of the temporary directory.
            dir: The directory to create the temporary directory in.
        """
        self.debug = bool(os.getenv("TMPDIR_DEBUG"))
        super().__init__(prefix=prefix, dir=dir)
        self.path = Path(self.name)

        if self.debug:
            temp_logger.warning(
                "Temporary directory created and won't be removed: %s", self.name
            )

    @override
    def __enter__(self) -> Path:
        """Changed from `str` to `Path`.

        Returns:
            The path of the temporary directory."""
        return self.path

    @classmethod
    def _cleanup(
        cls, name: str, warn_message: str, ignore_errors: bool = False
    ) -> None:
        if bool(os.getenv("TMPDIR_DEBUG")):
            temp_logger.warning("Temporary directory %s not removed.", name)
        else:
            super()._cleanup(name, warn_message, ignore_errors)  # type: ignore[misc]

    @override
    def cleanup(self) -> None:
        """Remove the temporary directory or warn if `TMPDIR_DEBUG` is set."""
        if self.debug:
            temp_logger.warning("Temporary directory %s not removed.", self.name)
        else:
            super().cleanup()
