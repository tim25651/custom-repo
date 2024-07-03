"""Defines the parameters used by the for the single commands"""

from enum import Enum
from pathlib import Path
from typing import Literal, TypedDict


class TargetDir(Enum):
    """Where to put the downloaded files.

    Attributes:
        TMP: The temporary directory.
        DEBS: The $REPO/debs/pool/main directory.
        TAP: The $REPO/debs/brew-data directory.
    """

    TMP = "tmp"
    DEBS = "debs"
    BREW = "brew"


class PackageManager(Enum):
    """The package manager to use.

    Attributes:
        CHOCO: Chocolatey.
        APT: Apt.
        BREW: Homebrew.
    """

    CHOCO = "choco"
    APT = "apt"
    BREW = "brew"
    CONDA = "conda"


class Params(TypedDict):
    """A TypedDict with the parameters used by the custom_repo module.

    Attributes:
        NAME (str): The name of the package.
        DIR (TargetDir): Where to put the downloaded files.
        REPO (Path): The path to the repository.
        DOMAIN (str): The domain of the repository.
        MGR (PackageManager): The package manager to use.
        VERSION (str): The version of the package.
        PKG (Path | None): The path to the package file.
        FILE (Path | None | Literal["FAILED_DOWNLOAD"]):
            The path to the file to download.
        VARS (dict[str, str]):
            Additional variables to replace in the configuration file.
        AUTHORIZATION (str): The authorization base64 string.
        STEM (str): The stem of the final package file.
        SUFFIXES (list[str]): The suffixes of a file to download.
    """

    NAME: str
    DIR: TargetDir
    REPO: Path
    DOMAIN: str
    MGR: PackageManager
    VERSION: str
    PKG: Path | None
    FILE: Path | None | Literal["FAILED_DOWNLOAD"]
    VARS: dict[str, str]
    AUTHORIZATION: str
    STEM: str
    SUFFIXES: list[str]
