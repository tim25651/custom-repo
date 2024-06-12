"""Implementation of the commands in the custom repository.

Implements:
- `set_cmd`: Set an environment variable.
- `rename`: Rename the first directory in `wd`.
- `extract`: Extract a tarball.
- `mkdir`: Create a directory in `wd`.
- `write_caskfile`: Create a Cask file for Homebrew.
- `copy_cmd`: Copy a file, a folder recursively or files matching a glob pattern.
- `download_cmd`: Subset of run_cmd for downloading files.
"""

import logging
import urllib.parse
from pathlib import Path

from custom_repo.impl.download import from_file, from_github, from_src
from custom_repo.impl.utils import CommandExecutionError
from custom_repo.modules import ConnectionKeeper, TemporaryDirectory, file_manup
from custom_repo.parser import COPY_CMD, DOWNLOAD_CMD, Command, cmd_groups
from custom_repo.parser.params import Params, TargetDir
from custom_repo.parser.utils import fix_vars

impl_logger = logging.getLogger(__name__)


class VariableError(CommandExecutionError):
    """Could not set the variable."""


def set_cmd(params: Params, args: list[str]) -> None:
    """Set an environment variable.

    Usage: SET KEY VALUE
    """
    key, value = args

    value = value.replace("$NAME", params["NAME"]).replace(
        "$VERSION", params["VERSION"]
    )

    value = fix_vars(params, value, params.keys())

    for sub_key in params.keys():
        if f"${sub_key}" in value:
            raise VariableError(
                f"Params var other than NAME or VERSION in value: {value}. Only custom"
                " vars allowed."
            )

    if "$" in value:
        raise VariableError(f"Unknown variable in value: {value}")

    params["VARS"][key] = value


def rename(params: Params, args: list[str], wd: Path) -> None:
    """Rename the first directory in `wd`.

    Usage: RENAME NEW_NAME

    Raises:
        CommandExecutionError: If an error occurs during the execution of the command.
    """
    new_name = args[0]

    dest = fix_vars(params, new_name)

    first_elem = file_manup.get_first_elem(wd)

    parent_dir = (wd / dest).parent

    if not parent_dir.exists():
        parent_dir.mkdir(parents=True)

    first_elem.rename(wd / dest)


def extract(params: Params, args: list[str], wd: Path) -> None:
    """Extract a tarball.

    Usage: EXTRACT [GLOB]
    """
    repo = params["REPO"]

    glob: str | None = None
    if len(args) == 1:
        glob = args[0]

    file = params["FILE"]

    if not isinstance(file, Path):
        raise ValueError("No FILE set.")

    if params["DIR"] != TargetDir.TMP:
        with TemporaryDirectory(prefix="tmp__extract_", dir=repo) as tmp:
            file_manup.extract(file, tmp, glob=glob)
            for extracted in Path(tmp).iterdir():
                new_name = f"{params['STEM']}|{extracted.name}"
                extracted.rename(wd / new_name)
    else:
        file_manup.extract(file, wd, glob=glob)

    # remove the tarball in the sandbox
    # else keep it so it won't be downloaded again

    if params["DIR"] == TargetDir.TMP:
        file.unlink()


def mkdir(params: Params, args: list[str], wd: Path) -> None:
    """Create a directory in `wd`.

    Usage: MKDIR DIR
    """
    directory = fix_vars(params, args[0])
    (wd / directory).mkdir(parents=True)


def write_caskfile(
    params: Params,
    args: list[str],
) -> None:
    """Create a Cask file for Homebrew."""
    # content in {{{ ... }}}
    repo = params["REPO"]
    stem = params["STEM"]
    pub = repo / "public"
    pkgs = repo / "pkgs" / "brew"

    content = args[0]

    target_file = pkgs / (stem + ".rb")

    content = fix_vars(params, content)

    if "$TAP_FILE" in content:
        if not isinstance(params["FILE"], Path):
            raise ValueError(f"No FILE set for {params['NAME']}.")

        rel_path = params["FILE"].relative_to(pub)
        escaped_rel_path = urllib.parse.quote(str(rel_path))
        content = content.replace("$TAP_FILE", f"{params['DOMAIN']}/{escaped_rel_path}")

    target_file.write_text(content, "utf-8")
    impl_logger.info("Wrote Cask file: %s", target_file)


def copy_cmd(cmd: COPY_CMD, params: Params, args: list[str], wd: Path) -> None:
    """Copy a file, a folder recursively or files matching a glob pattern.

    Usage:
    >>> COPY SRC TARGET
    >>> COPY_FIX SRC TARGET
    >>> COPY_DIR SRC TARGET
    >>> COPY_GLOB SRC TARGET GLOB
    """
    glob: str | None = None

    if len(args) == 2:
        src, target = args
    else:
        src, target, glob = args

    target = fix_vars(params, target)

    if not (wd / target).parent.exists():
        (wd / target).parent.mkdir(parents=True)

    if "$PKG" in src:
        pkg = params["PKG"]
        if not pkg:  # pylint: disable=consider-using-assignment-expr
            raise ValueError("Not in a package folder.")

        src = fix_vars(params, src, skip=["PKG"])
        full_src = Path(src.replace("$PKG", str(pkg)))

    else:
        src = fix_vars(params, src)
        full_src = wd / src

    if cmd == Command.COPY:
        file_manup.copy(full_src, wd / target)

    elif cmd == Command.COPY_FIX:
        data = Path(full_src).read_text("utf-8")
        data = fix_vars(params, data)
        (wd / target).write_text(data, "utf-8")

    elif cmd == Command.COPY_DIR:
        file_manup.copy(full_src, wd / target, recursive=True)

    else:
        if not glob:
            raise ValueError("No glob pattern given for COPY_GLOB")

        file_manup.copy(full_src, wd / target, glob=glob)


def download_cmd(
    cmd: DOWNLOAD_CMD,
    keeper: ConnectionKeeper,
    params: Params,
    args: list[str],
    wd: Path,
) -> None:
    """Subset of run_cmd for downloading files"""
    if cmd_groups.download_gh(cmd):
        from_github(keeper, params, args, wd)

    elif cmd_groups.from_file(cmd):
        from_file(keeper, params, cmd, args, wd)

    elif cmd_groups.from_src(cmd):
        from_src(params, cmd, args, wd)

    else:
        raise ValueError(f"Unknown command: {cmd}")

    if params["FILE"] == "FAILED_DOWNLOAD":
        raise CommandExecutionError("Download failed.")
