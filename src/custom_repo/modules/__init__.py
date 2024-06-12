"""Submodules for single functions

This submodule is independent of the main module
(no `Params` or `Command` or ... are used here).

- `download`: Download a file from the internet.
- `gpg`: Create a GPG key or sign a APT repository.
- `git`: Small git functions.
- `file_manup`: File manipulation functions.
- `choco`: Run choco commands via mono.
- `check_installs`: Check if the required programs are installed.
- `TypedNullContext`: A typed version of `nullcontext`.
- `TemporaryDirectory`: A typed version of `tempfile.TemporaryDirectory`.
- `CacheSession`: A session with a cache.
- `ConnectionKeeper`: A context manager to keep the connection open.
- `exec_cmd`: Execute a command and return the output.
- `exec_cmd_with_status`: Execute a command and return the output and status.
- `filter_exts`: Filter the file extensions.
- `has_correct_struct`: Check if the folder structure is correct.
- `has_invalid_elems`: Check if no invalid files/folders are present in the repository.
- `has_missing_elems`: Check if an element is missing.
- `set_log_level`: Set the log level.
"""

from custom_repo.modules import download, file_manup, git, gpg
from custom_repo.modules.choco import choco
from custom_repo.modules.download import CacheSession, ConnectionKeeper
from custom_repo.modules.exec_cmd import exec_cmd, exec_cmd_with_status
from custom_repo.modules.ext import filter_exts
from custom_repo.modules.installs import check_installs
from custom_repo.modules.log import set_log_level
from custom_repo.modules.nullcontext import TypedNullContext
from custom_repo.modules.struct import (
    has_correct_struct,
    has_invalid_elems,
    has_missing_elems,
)
from custom_repo.modules.temp import TemporaryDirectory
