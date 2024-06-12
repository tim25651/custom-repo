"""Actual parsing of the command line arguments.

Implements:
- `BuildArgs`: The parsed build arguments.
- `parse_build_args`: Parse the build arguments.
- `parse_restart_args`: Parse the restart arguments.
"""

import argparse
from pathlib import Path


class RestartArgs(argparse.Namespace):
    """The parsed restart arguments.

    Attributes:
        verbose (int): The verbosity level.
        repo (Path): The repository folder.
    """

    verbose: int
    repo: Path


def parse_restart_args() -> RestartArgs:
    """Return the restart arguments."""
    parser = argparse.ArgumentParser(description="Restart the repository server.")
    parser.add_argument(
        "repo",
        type=Path,
        help="The repository folder.",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )
    args: RestartArgs = parser.parse_args()  # type: ignore[assignment]

    return args


class BuildArgs(argparse.Namespace):
    """The parsed build arguments.

    Attributes:
        verbose (int): The verbosity level.
        repo (Path): The repository folder.
        key (Path): The private key file to sign the repository.
        github (Path): The github token file for access to the API.
        domain (str): The domain name of the repository.
        headless (bool): Run the browser in headless mode.
        user (str): The user for the repository.
        passwd (Path): The password file for the repository.
        restart (bool): Restart the repository server.
    """

    verbose: int
    repo: Path
    key: Path
    github: Path | None
    domain: str
    headless: bool
    user: str
    passwd: Path | None
    restart: bool


def parse_build_args() -> BuildArgs:
    """Return the build arguments."""

    build = argparse.ArgumentParser(
        description="Build a Debian repository.",
    )

    build.add_argument("repo", type=Path, help="The repository folder.")

    build.add_argument(
        "--key",
        "-k",
        type=Path,
        help="The private key file to sign the repository.",
        required=True,
    )
    build.add_argument(
        "--github",
        "-g",
        type=Path,
        help=(
            "The github token file for access to the API. If not provided, GH_TOKEN env"
            " var is used."
        ),
    )
    build.add_argument(
        "--headful",
        "-H",
        action="store_false",
        dest="headless",
        help="Run the browser in headful mode.",
    )
    build.add_argument(
        "--domain",
        "-d",
        type=str,
        help="The domain name of the repository.",
        required=True,
    )
    build.add_argument(
        "--user",
        "-u",
        type=str,
        help="The user for the repository.",
        default="repo",
    )
    build.add_argument(
        "--passwd",
        "-p",
        type=Path,
        help=(
            "The password file for the repository."
            " If not provided, REPO_PASSWD env var is used."
        ),
    )

    build.add_argument(
        "-v", "--verbose", action="count", help="Verbosity level", default=0
    )

    build.add_argument(
        "-r",
        "--restart",
        action="store_true",
        help="Restart the repository server.",
    )
    args: BuildArgs = build.parse_args()  # type: ignore[assignment]
    return args
