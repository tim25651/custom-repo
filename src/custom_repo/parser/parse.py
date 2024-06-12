"""Utility functions for the parser module."""

import logging
import re
import shlex
from collections import Counter
from pathlib import Path
from typing import Literal

from custom_repo.modules import ConnectionKeeper
from custom_repo.modules import download as dl
from custom_repo.modules import filter_exts, has_correct_struct
from custom_repo.modules.struct import FolderStructureError
from custom_repo.parser import cmd_groups
from custom_repo.parser.cmd_groups import DOWNLOAD_CMDS, UNIQUE_CMDS
from custom_repo.parser.cmds import Command, check_number_of_args
from custom_repo.parser.exceptions import (
    CustomRepoError,
    ParsingError,
    StructureError,
    UnknownCommandError,
)
from custom_repo.parser.params import PackageManager, Params, TargetDir
from custom_repo.parser.utils import adjust_regex_version

parse_logger = logging.getLogger(__name__)


def get_name(
    cmd: Literal[Command.DOWNLOAD_REMOTE_NAME, Command.DOWNLOAD_BROWSER],
    url: str,
    keeper: ConnectionKeeper,
) -> str | Literal["FAILED_DOWNLOAD"]:
    """Get the name of a remote file or download it via the browser."""
    if cmd == Command.DOWNLOAD_REMOTE_NAME:
        return dl.get_remote_filename(url)

    if cmd == Command.DOWNLOAD_BROWSER:
        try:
            return str(dl.download_via_browser(keeper.browser, url, None))
        except dl.file.DownloadError as e:
            parse_logger.error("Error during download from %s: %s", url, e)
            return "FAILED_DOWNLOAD"

    raise ValueError(f"Unknown command: {cmd}")


def read_lines(inputs: list[str]) -> list[tuple[str, list[str]]]:
    """Read a file and return its content.
    First word of each line is the command, if it's not a comment
    If the line is indented, it's a single argument to the
    previous command.

    ```
    inputs = \"\"\"TEST arg1 arg2
    MULTILINE
        arg1
            arg1 continuation
            arg1 continuation
    EXIT
    \"\"\"
    read_lines(inputs.splitlines())
    >>> [
            ("TEST", ["arg1", "arg2"]),
            ("MULTILINE", ["arg1\\n    arg1 continuation\\n    arg1 continuation\\n"
            ("EXIT", [])
        ]
    ```
    """
    lines: list[tuple[str, list[str]]] = []
    indent: str = ""
    for line in inputs:
        # skip empty lines and comments
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("\t"):
            if not lines:
                raise ParsingError("First line must not be indented.")

            if not indent:
                # add a new argument to the last command
                lines[-1][1].append("")
                # set the minimum indentation
                n_indent = len(line) - len(line.lstrip())
                indent = line[:n_indent]

            # remove the indentation defined by the first line
            # and re-add the newline character
            try:
                line = line.removeprefix(indent) + "\n"
            except AttributeError as e:
                raise ParsingError(
                    "Found a line with less indentation than the first."
                ) from e
                # TODO: more message: which was the first indent, what is it now

            # append to the new argument
            # do not strip, keep the spaces # TODO: might remove the forced indentation
            lines[-1][1][-1] += line
        else:
            indent = ""
            cmd, *args = shlex.split(line)
            lines.append((cmd, args))
    return lines


def parse_single_cmd(cmd: str) -> Command:
    """Parse a single command.

    Args:
        cmd (str): The command to parse.

    Returns:
        Command: The parsed command.

    Raises:
        UnknownCommandError: If the command is not recognized.
        ParsingError: If the command is unallowed.
    """
    try:
        parsed_cmd = Command(cmd)
        if (  # pylint: disable=consider-using-assignment-expr
            parsed_cmd == Command.CONDA_BUILD
        ):
            raise ParsingError("CONDA_BUILD command not allowed! Use CONDA instead.")
        return parsed_cmd
    except ValueError as e:
        raise UnknownCommandError(f"Unknown command: {cmd}") from e


def parse_cmds(fn: Path) -> list[tuple[Command, list[str]]]:
    """Read the lines from the file at `fn` and parse them.

    intendent lines are considered arguments to the previous command.
    The first word of each line is the command.
    The number of arguments is checked.
    """

    inputs = fn.read_text("utf-8").splitlines()

    lines = read_lines(inputs)

    cmds: list[tuple[Command, list[str]]] = [
        (parse_single_cmd(cmd), args) for cmd, args in lines
    ]

    for cmd, args in cmds:
        check_number_of_args(cmd, args)

    return cmds


def get_version_from_download(
    keeper: ConnectionKeeper,
    orig_version: str,
    download_cmd: tuple[Command, list[str]] | None,
) -> tuple[str, list[str]]:
    """Get the version from the downloaded file."""
    if not download_cmd:
        raise ParsingError("Regex VERSION must be used with a download command.")

    dl_cmd, dl_args = download_cmd

    assert cmd_groups.download_cmd(dl_cmd)

    if not cmd_groups.from_file(dl_cmd):
        raise ParsingError("Regex VERSION not allowed with COPY_SRC or SYMLINK_SRC.")
    if dl_cmd == Command.DOWNLOAD:
        raise ParsingError("Regex VERSION not allowed with DOWNLOAD_FILE.")

    url = dl_args[0]
    filename = get_name(dl_cmd, url, keeper)
    if filename == "FAILED_DOWNLOAD":  # pylint: disable=consider-using-assignment-expr
        raise ParsingError("Failed to download the file.")

    version = adjust_regex_version(orig_version, filename)
    suffixes = Path(filename).suffixes

    parse_logger.info("Found version %s from %s", version, filename)

    return version, suffixes


def get_version_from_github(
    keeper: ConnectionKeeper,
    repo: str,
    pattern: str | None,
    tag: str | None = None,
) -> tuple[str, list[str]]:
    """Get the latest release version from GitHub."""
    if release_data := dl.get_release_data(
        repo, exclude_prereleases=True, session=keeper.session
    ):
        asset: str | None = None
        if not pattern:
            version_str = next(iter(release_data))

        elif tag:
            if asset := dl.find_asset_by_tag(release_data, pattern, tag):
                version_str = tag
            else:
                raise ParsingError(f"No asset found for tag {tag} in the GitHub repo.")

        else:
            asset, version_str = dl.find_recent_asset(release_data, pattern)

        suffixes = Path(asset).suffixes if asset else []
        version = re.sub(r"[^\d.-_]", "", version_str)

        parse_logger.info("Found release %s from %s", version, repo)

        return version, suffixes

    raise ParsingError("No release found on GitHub.")


def filter_cmds(  # pylint: disable=too-complex
    cmds: list[tuple[Command, list[str]]], keeper: ConnectionKeeper
) -> tuple[str, list[str], TargetDir, list[tuple[Command, list[str]]]]:
    """Check if unique commands are not multiple times in the list.
    Check if the VERSION command is first if present.
    Check if the SANDBOX command is after VERSION or first if no VERSION.
    Check if the CASK command is last if present.
    """
    suffixes: list[str] = []

    actual_cmds = [x[0] for x in cmds]

    counts = Counter(actual_cmds)

    for cmd in UNIQUE_CMDS:
        if counts[cmd] > 1:
            raise ParsingError(f"Multiple {cmd} commands.")

    # check if multiple download commands are present
    download_cmds = [(cmd, args) for cmd, args in cmds if cmd in DOWNLOAD_CMDS]

    if len(download_cmds) > 1:
        raise ParsingError("Multiple download commands.")

    download_cmd = download_cmds[0] if download_cmds else None

    first_ix = 0

    if Command.VERSION in counts:
        if actual_cmds[0] != Command.VERSION:
            raise ParsingError("VERSION command must be first if present.")

        if download_cmd and download_cmd[0] == Command.DOWNLOAD_GH:
            raise ParsingError(
                "VERSION command must not be present if github download command."
            )

        first_ix = 1
        version = cmds[0][1][0]

        if version.startswith("gh:"):
            gh_repo, *gh_pattern = version.removeprefix("gh:").split(":", maxsplit=1)
            pattern = gh_pattern[0] if gh_pattern else None
            version, suffixes = get_version_from_github(keeper, gh_repo, pattern)

        elif version.startswith("re:"):
            version, suffixes = get_version_from_download(keeper, version, download_cmd)

    else:
        if not download_cmd or download_cmd[0] != Command.DOWNLOAD_GH:
            raise ParsingError(
                "VERSION command must be present if no or other than github download"
                " command."
            )

        gh_repo, pattern, *maybe_gh_tag = download_cmd[1]
        gh_tag = maybe_gh_tag[0] if maybe_gh_tag else None
        version, _ = get_version_from_github(keeper, gh_repo, pattern, gh_tag)

    if Command.SANDBOX in counts:
        if actual_cmds[first_ix] != Command.SANDBOX:
            raise ParsingError(
                "SANDBOX command must be after VERSION or at first (if no VERSION) if"
                " present."
            )
        first_ix += 1
        sandbox = True
    else:
        sandbox = False

    cask = Command.CASK in counts

    # remove the first commands (VERSION, SANDBOX) if present
    cmds = cmds[first_ix:]

    # Check for multiple SET commands with the same key
    # Check for setting parameter keys directly
    enumerated_set_keys = [
        (ix, args[0]) for ix, (cmd, args) in enumerate(cmds) if cmd == Command.SET
    ]
    set_keys = [key for _, key in enumerated_set_keys]
    set_ix = [ix for ix, _ in enumerated_set_keys]

    if not set_ix == list(range(len(set_ix))):
        raise ParsingError(
            "SET commands must be in order after VERSION and SANDBOX (if they are"
            " present)."
        )

    if len(set_keys) != len(set(set_keys)):
        raise ParsingError("Multiple SET commands with the same key.")

    for key in set_keys:
        if key in {"NAME", "DIR", "REPO", "DOMAIN", "VERSION", "PKG", "FILE"}:
            raise ParsingError(
                "Cannot set parameter keys directly, for version use `VERSION ...`"
            )
        if key in {"VARS", "DEST", "TAP_FILE", "CHOCO_FILE", "AUTHORIZATION"}:
            raise ParsingError(f"Cannot set {key} directly.")

    target_dir = TargetDir.TMP if sandbox else TargetDir.TAP if cask else TargetDir.DEBS

    # Check if MKDIR command is used together with SANDBOX
    if target_dir != TargetDir.TMP:
        if Command.MKDIR in actual_cmds:
            raise ParsingError("MKDIR command only allowed in sandbox mode.")

    return version, suffixes, target_dir, cmds


def parse_choco_pkg(name: str, pkg: Path) -> None:
    """Check if the folder structure is correct."""

    must_have_dirs: set[str] = {"tools"}
    must_have_files: set[str] = {
        f"{name}.choco",
        "tools/chocolateyInstall.ps1",
        f"{name}.nuspec",
    }
    allowed_files: set[str] = must_have_files | {
        "tools/chocolateyUninstall.ps1",
        "tools/*",
    }

    try:
        has_correct_struct(pkg, must_have_dirs, allowed_files, tuple(), must_have_files)
    except FolderStructureError as e:
        raise FolderStructureError(
            f"Invalid folder structure in a .choco folder: {e}"
        ) from e


def parse_apt_pkg(name: str, pkg: Path) -> None:
    """Check if the folder structure is correct."""
    allowed_dirs: set[str] = set()
    must_have_files = {f"{name}.rep"}
    allowed_files = {"*"}

    try:
        has_correct_struct(pkg, allowed_dirs, allowed_files, tuple(), must_have_files)
    except FolderStructureError as e:
        raise FolderStructureError(
            f"Invalid folder structure in a .rep folder: {e}"
        ) from e

    if any(x.suffix == ".rep" for x in pkg.iterdir() if x.stem != name):
        raise StructureError("Only one .rep file allowed.")

    # must have commands:
    # SANDBOX ANY_DOWNLOAD_CMD CREATE_DEB BUILD_DEB EXIT


def parse_apt_file(  # pylint: disable=too-complex
    params: Params, cmds: list[tuple[Command, list[str]]]
) -> list[tuple[Command, list[str]]]:
    """Parse a .rep file and return a list of commands."""
    pkg = params["PKG"]

    actual_cmds = [x[0] for x in cmds]
    not_allowed = {Command.CASK, Command.CONDA}

    if not any(x in DOWNLOAD_CMDS for x in actual_cmds):
        raise ParsingError("No download command found.")

    if not pkg:
        not_allowed |= {Command.CREATE_DEB, Command.BUILD_DEB, Command.DH_DISABLE}

    if used := set(actual_cmds) & not_allowed:
        raise ParsingError(f"Not allowed commands in a package folder: {used}")

    if pkg:
        if params["DIR"] != TargetDir.TMP:
            raise ParsingError("Only TMP allowed for apt pkg folders.")

        must_have = {
            Command.CREATE_DEB,
            Command.BUILD_DEB,
        }
        if missing := must_have - set(actual_cmds):
            raise ParsingError(f"Missing commands in a package folder: {missing}")

        if actual_cmds[-1] != Command.BUILD_DEB:
            raise ParsingError(
                "BUILD_DEB must be the last command in a package folder."
            )

        disable_cmds = [
            (ix, args[0])
            for ix, (cmd, args) in enumerate(cmds)
            if cmd == Command.DH_DISABLE
        ]
        if disable_cmds:
            disable_ix = [ix for ix, _ in disable_cmds]
            disable_args = [arg for _, arg in disable_cmds]

            should_range = list(
                range(len(actual_cmds) - len(disable_cmds) - 1, len(actual_cmds) - 1)
            )
            if disable_ix != should_range:
                raise ParsingError(
                    "All DH_DISABLE commands must be directly before BUILD_DEB."
                )

            if len(set(disable_args)) != len(disable_args):
                raise ParsingError("All DH_DISABLE commands must be unique.")

            for arg in disable_args:
                if arg not in {"dh_usrlocal"}:
                    raise ValueError(f"Unknown or not implemented debian helper: {arg}")
    return cmds


def parse_conda_pkg(name: str, pkg: Path) -> None:
    """Check if the folder structure is correct."""
    must_have_dirs = {
        "recipe",
    }
    must_have_files = {
        "recipe/meta.yaml",
        f"{name}.conda",
    }
    allowed_dirs = must_have_dirs
    allowed_files = must_have_files | {"recipe/build.sh", "recipe/run_test.sh"}

    try:
        has_correct_struct(
            pkg, must_have_dirs, allowed_files, allowed_dirs, must_have_files
        )
    except FolderStructureError as e:
        raise FolderStructureError(
            f"Invalid folder structure in a .conda folder: {e}"
        ) from e

    # must have commands:
    # VERSION ANY_DOWNLOAD_CMD CONDA_BUILD EXIT

    # must have structure:
    # recipe/meta.yaml
    # [recipe/build.sh]
    # [recipe/run_test.sh]


def parse_conda_file(
    params: Params, cmds: list[tuple[Command, list[str]]]
) -> list[tuple[Command, list[str]]]:
    """Parse a .conda file and return a list of commands."""

    if not params["VERSION"]:
        raise ParsingError("No VERSION command found.")

    actual_cmds = [x[0] for x in cmds]

    if len(actual_cmds) not in {1, 2}:
        raise ParsingError(
            "Invalid number of commands in a .conda file (DOWNLOAD_CMD)."
        )

    if not params["PKG"]:
        raise StructureError("Not in a package folder.")

    if len(actual_cmds) == 2 and actual_cmds[0] not in DOWNLOAD_CMDS:
        raise ParsingError("Second command must be a download command.")

    if actual_cmds[-1] != Command.CONDA:
        raise ParsingError("Last command must be CONDA.")

    new_cmds = cmds[:-1] + [
        (Command.COPY_DIR, ["$PKG/recipe", "recipe"]),
        (Command.CONDA_BUILD, []),
    ]
    params["DIR"] = TargetDir.TMP

    return new_cmds


def parse_tap_file(
    params: Params, cmds: list[tuple[Command, list[str]]]
) -> list[tuple[Command, list[str]]]:
    """Parse a .tap file and return a list of commands."""
    if params["PKG"]:
        raise StructureError("Not allowed in a package folder.")

    actual_cmds = [x[0] for x in cmds]

    allowed = set(DOWNLOAD_CMDS) | {Command.CASK}

    if used := set(actual_cmds) - allowed:
        raise ParsingError(f"Not allowed commands in a tap folder: {used}")

    if Command.CASK not in actual_cmds:
        raise ParsingError("CASK command must be present in a tap folder.")

    if actual_cmds[-1] != Command.CASK:
        raise ParsingError("CASK command must be last if present.")

    content = cmds[-1][1][0]
    if "$TAP_FILE" in content:
        if not any(x in DOWNLOAD_CMDS for x in actual_cmds):
            raise ParsingError("No download command found, but $TAP_FILE is used.")

    return cmds


def parse_pkg(tool: Path) -> tuple[str, Path, Path]:
    """Parse a .tap file and return a list of commands."""
    name = tool.stem
    pkg = tool
    fn = tool / tool.name

    if tool.suffix == ".conda":
        parse_conda_pkg(tool.stem, tool)

    elif tool.suffix == ".rep":
        parse_apt_pkg(tool.stem, tool)

    elif tool.suffix == ".choco":
        parse_choco_pkg(tool.stem, tool)

    else:
        raise StructureError("Unknown suffix.")

    return name, pkg, fn


def parse_tool_structure(tool: Path) -> tuple[str, Path | None, Path, PackageManager]:
    """Check the folder structure and the filenames of the tool."""

    if tool.is_dir():
        name, pkg, fn = parse_pkg(tool)
    else:
        name = tool.stem
        pkg = None
        fn = tool

    if fn.suffix == ".choco":
        pkg_mgr = PackageManager.CHOCO
    elif fn.suffix == ".rep":
        pkg_mgr = PackageManager.APT
    elif fn.suffix == ".conda":
        pkg_mgr = PackageManager.CONDA
    elif fn.suffix == ".tap":
        pkg_mgr = PackageManager.BREW
    else:
        raise CustomRepoError(f"Unknown file type: {fn.suffix}")

    return name, pkg, fn, pkg_mgr


def parse_tool(
    tool: Path, domain: str, authorization: str, keeper: ConnectionKeeper
) -> tuple[Params, list[tuple[Command, list[str]]]]:
    """Parse a .rep file and return a list of commands."""
    repo = tool.parent.parent

    name, pkg, fn, pkg_mgr = parse_tool_structure(tool)

    cmds = parse_cmds(fn)
    version, suffixes, target_dir, cmds = filter_cmds(cmds, keeper)

    stem = f"{name}|{version}|{pkg_mgr.value}"

    suffixes = filter_exts(suffixes)

    params: Params = {
        "NAME": name,
        "DIR": target_dir,
        "REPO": repo,
        "DOMAIN": domain,
        "MGR": pkg_mgr,
        "VERSION": version,
        "PKG": pkg,
        "FILE": None,
        "VARS": {},
        "AUTHORIZATION": authorization,
        "STEM": stem,
        "SUFFIXES": suffixes,
    }

    if pkg_mgr == PackageManager.CHOCO:
        cmds = parse_choco_file(params, cmds)

    elif pkg_mgr == PackageManager.CONDA:
        cmds = parse_conda_file(params, cmds)

    elif pkg_mgr == PackageManager.APT:
        cmds = parse_apt_file(params, cmds)

    elif pkg_mgr == PackageManager.BREW:
        cmds = parse_tap_file(params, cmds)

    else:
        raise CustomRepoError(f"Unknown package manager: {pkg_mgr}")

    return params, cmds


def parse_choco_file(
    params: Params, cmds: list[tuple[Command, list[str]]]
) -> list[tuple[Command, list[str]]]:
    """Parse a .choco file and return a list of commands."""
    actual_cmds = [x[0] for x in cmds]

    if not params["VERSION"]:
        raise ParsingError("No VERSION command found.")

    if len(actual_cmds) not in {1, 2}:
        raise ParsingError(
            "Invalid number of commands in a .choco file (DOWNLOAD_CMD)."
        )

    if not params["PKG"]:
        raise StructureError("Not in a package folder.")

    if actual_cmds[-1] != Command.CHOCO:
        raise ParsingError("Last command must be CHOCO.")

    params["DIR"] = TargetDir.TMP

    return cmds


def load_configs(
    repo: Path, domain: str, authorization: str, keeper: ConnectionKeeper
) -> list[tuple[Params, list[tuple[Command, list[str]]]]]:
    """Load the configurations."""
    config_files = list((repo / "configs").iterdir())
    if not config_files:  # pylint: disable=consider-using-assignment-expr
        raise ValueError("No configuration files found in the configs folder.")
    # Try to load all the configuration files, to check for errors early
    loaded_configs: list[tuple[Params, list[tuple[Command, list[str]]]]] = []

    for tool in config_files:
        # Skip hidden files
        if tool.name.startswith("."):
            continue

        try:
            params, cmds = parse_tool(tool, domain, authorization, keeper)
        except ParsingError as e:
            raise ParsingError(f"Error in {tool}: {e}") from e

        loaded_configs.append((params, cmds))

    return loaded_configs


def check_for_duplicates(
    loaded_configs: list[tuple[Params, list[tuple[Command, list[str]]]]],
) -> None:
    """Check for duplicate configurations."""
    names = [(params["NAME"], params["MGR"]) for params, _ in loaded_configs]

    counts = Counter(names)
    if multiple := [name for name, count in counts.items() if count > 1]:
        raise ValueError(f"Multiple configurations found for {multiple}.")
