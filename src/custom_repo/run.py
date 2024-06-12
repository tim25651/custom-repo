"""A .rep file contains of lines of the form:
CMD ARG1 ARG2 ...
The first word is the command to be executed and the rest are the arguments.
"""

# pylint: disable=too-complex,too-many-return-statements

import logging
from pathlib import Path
from typing import Literal, TypeAlias, TypeGuard

from custom_repo.exceptions import CustomRepoError
from custom_repo.mgrs import (
    build_choco_pkg,
    build_conda_pkg,
    build_deb,
    create_deb,
    dh_disable,
    write_caskfile,
)
from custom_repo.modules import (
    ConnectionKeeper,
    TemporaryDirectory,
    file_manup,
    filter_exts,
)
from custom_repo.parser import (
    COPY_CMD,
    Command,
    PackageManager,
    Params,
    TargetDir,
    cmd_groups,
    fix_vars,
)
from custom_repo.run_download import download_cmd

run_logger = logging.getLogger(__name__)


def _copy(params: Params, cmd: COPY_CMD, args: list[str], wd: Path) -> bool:
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

    return True


def _extract(params: Params, args: list[str], wd: Path) -> bool:
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

    return True


def _rename(params: Params, args: list[str], wd: Path) -> bool:
    """Rename the first directory in `wd`.

    Usage: RENAME NEW_NAME
    """
    dest = fix_vars(params, args[0])

    first_dir = next(wd.iterdir())

    parent_dir = (wd / dest).parent
    if not parent_dir.exists():
        parent_dir.mkdir(parents=True)

    first_dir.rename(wd / dest)

    return True


def _set(params: Params, args: list[str]) -> bool:
    """Set an environment variable.

    Usage: SET KEY VALUE
    """
    key, value = args

    value = value.replace("$NAME", params["NAME"])

    if "$VERSION" in value:
        version = params["VERSION"]
        if not version:  # pylint: disable=consider-using-assignment-expr
            raise ValueError("No version set.")
        value = value.replace("$VERSION", version)

    value = fix_vars(params, value, params.keys())

    for sub_key in params.keys():
        if f"${sub_key}" in value:
            raise ValueError(
                f"Params var other than NAME or VERSION in value: {value}. Only custom"
                " vars allowed."
            )

    if "$" in value:
        raise ValueError(f"Unknown variable in value: {value}")

    params["VARS"][key] = value

    return True


def _mkdir(params: Params, args: list[str], wd: Path) -> bool:
    """Create a directory in `wd`.

    Usage: MKDIR DIR
    """
    directory = fix_vars(params, args[0])
    (wd / directory).mkdir(parents=True)

    return True


def run_cmd(
    keeper: ConnectionKeeper,
    params: Params,
    cmd: Command,
    args: list[str],
    wd: Path,
    running: bool = True,
) -> bool:
    """Parse and run a command in `wd`.
    Returns if the program should keep running."""

    def _log(max_size: bool = False) -> None:
        """Log the command."""
        small_args = [x[:10] for x in args]
        used_args = small_args if max_size else args

        run_logger.debug("CMD: %s ARGS: %s (RUN: %s)", cmd, used_args, running)

    # Commands which will be always executed,
    # also if not download is needed (no new version)
    # ----------------------------------------------

    if not running:
        return False

    if cmd == Command.CASK:
        _log(max_size=True)
        return write_caskfile(params, args)

    _log()

    if cmd == Command.SET:
        return _set(params, args)

    if cmd_groups.download_cmd(cmd):
        download_cmd(keeper, params, cmd, args, wd)
        if params["FILE"] == "FAILED_DOWNLOAD":
            raise ValueError("Download failed.")
        return True

    if cmd_groups.copy_cmd(cmd):
        return _copy(params, cmd, args, wd)

    if cmd == Command.MKDIR:
        return _mkdir(params, args, wd)

    if cmd == Command.EXTRACT:
        return _extract(params, args, wd)

    if cmd == Command.CREATE_DEB:
        return create_deb(params, args, wd)

    if cmd == Command.RENAME:
        return _rename(params, args, wd)

    if cmd == Command.BUILD_DEB:
        return build_deb(params, args, wd)

    if cmd == Command.DH_DISABLE:
        return dh_disable(params, args, wd)

    if cmd == Command.CONDA_BUILD:
        return build_conda_pkg(params, args, wd)

    if cmd == Command.CHOCO:
        return build_choco_pkg(params, args, wd)

    raise ValueError(f"Unknown command: {cmd}")


def clean_data(repo: Path) -> None:
    """Remove downloaded files that are not installed.

    Args:
        repo (Path): The repository path.

    Raises:
        ValueError: If a file doesn't has the right prefix.
    """

    _MGR_SUFFIX: TypeAlias = Literal[  # pylint: disable=invalid-name
        "conda", "choco", "apt", "brew"
    ]

    def typeguard_mgr(mgr_: str) -> TypeGuard[_MGR_SUFFIX]:
        """Typeguard for the package managers."""
        return mgr_ in {"conda", "choco", "apt", "brew"}

    def _get_data(
        file: Path,
    ) -> tuple[str, str, _MGR_SUFFIX]:
        """Get the data."""
        suffix = "".join(filter_exts(file))
        name, version, mgr, *_ = file.name.split("|")
        mgr = mgr.removesuffix(suffix)
        if not typeguard_mgr(mgr):
            raise ValueError(f"Unknown manager: {mgr}")
        return name, version, mgr

    downloaded_files = list((x, _get_data(x)) for x in repo.glob("public/data/*/*"))
    installed_packages = list(_get_data(x) for x in repo.glob("pkgs/*/*"))
    installed_set = set(installed_packages)

    for file, data in downloaded_files:
        if data not in installed_set:
            run_logger.warning("Removing %s", file)
            file.unlink()


def final_exists(params: Params) -> bool:
    """Check if the final file already exists in the repository."""

    mgr = params["MGR"]
    repo = params["REPO"]
    stem = params["STEM"]

    if mgr == PackageManager.CONDA:
        final = repo / "pkgs" / "conda" / f"{stem}.tar.bz2"
    elif mgr == PackageManager.CHOCO:
        final = repo / "pkgs" / "choco" / f"{stem}.nupkg"
    elif mgr == PackageManager.BREW:
        final = repo / "pkgs" / "tap" / f"{stem}.rb"
    elif mgr == PackageManager.APT:
        files = list((repo / "pkgs" / "apt").iterdir())
        return any(f.name.startswith(stem) for f in files)
    else:
        raise CustomRepoError(f"Unknown package manager: {mgr}")

    run_logger.debug("Checking if %s exists: %s", final, final.exists())

    return final.exists()
