"""Parse and check the command line arguments.

Implements:
- `check_build_args`: Check the build arguments.
- `check_restart_args`: Check the restart arguments.
"""

import base64
import logging
import os
from pathlib import Path

from custom_repo.cli.args import BuildArgs, parse_build_args, parse_restart_args
from custom_repo.cli.elems import ALLOWED_DIRS, ALLOWED_FILES, MUST_HAVE_DIRS
from custom_repo.modules import gpg, has_correct_struct, set_log_level

cli_logger = logging.getLogger(__name__)


def _parse_verbosity(verbose: int) -> None:
    """Set the log level for the custom-repo package.

    Args:
        verbose (int): The verbosity level.
            (0: WARNING, 1: INFO, >1: DEBUG)

    Raises:
        ValueError: If the verbosity level is invalid.
    """
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    elif verbose > 1:
        level = logging.DEBUG
    else:
        raise ValueError("Invalid verbosity level.")

    set_log_level(level, only_pkg=True)


def _check_domain(domain: str) -> str:
    """Check the domain argument.

    Args:
        domain (str): The domain name.

    Returns:
        The domain name.

    Raises:
        ValueError: If the domain is invalid.
    """

    if not domain:
        raise ValueError("The domain must be a non-empty string.")

    if not (domain.startswith("http://") or domain.startswith("https://")):
        raise ValueError("The domain must start with http:// or https://")

    return domain


def _check_token(token_file: Path | None) -> None:
    """Check the token file argument.

    Sets the GH_TOKEN environment variable if a token file is provided.

    Args:
        token_file (Path | None): The token file path.

    Raises:
        FileNotFoundError: If the file is not found.
        ValueError: If the token is not set.
    """
    if token_file:
        token_file = token_file.expanduser().absolute()
        if not token_file.is_file():
            raise FileNotFoundError(f"{token_file} not found.")

        os.environ["GH_TOKEN"] = token_file.read_text("utf-8").strip()
        cli_logger.warning("GH_TOKEN set from file.")

    elif not os.getenv("GH_TOKEN"):
        raise ValueError(
            "No GH_TOKEN environment variable set and no token file provided."
        )
    else:
        cli_logger.warning("GH_TOKEN used from environment.")


def _check_auth(args: BuildArgs) -> str:
    """Check the user and password arguments.

    Args:
        args (CLIArgs): The parsed arguments.

    Returns:
        The authentification string.

    Raises:
        ValueError: If the user is not set or the password is not set
        FileNotFoundError: If the password file is not found.
    """
    if not args.user:
        raise ValueError("The user must be a non-empty string.")

    passwd_file = Path(args.passwd).expanduser().absolute() if args.passwd else None
    if passwd_file:
        if not passwd_file.is_file():
            raise FileNotFoundError(f"{passwd_file} not found.")

        passwd = passwd_file.read_text("utf-8").strip()
        cli_logger.warning("Password set from file.")
    else:
        try:
            passwd = os.environ["REPO_PASSWD"]
        except KeyError as e:
            raise ValueError(
                "No REPO_PASSWD environment variable set and no password file provided."
            ) from e
        cli_logger.warning("Password used from environment.")

    auth = base64.b64encode(f"{args.user}:{passwd}".encode("utf-8")).decode("utf-8")
    return auth


def _check_repo_struct(repo: Path) -> None:
    """Check if the repository has the correct structure."""
    has_correct_struct(repo, ALLOWED_DIRS, ALLOWED_FILES, MUST_HAVE_DIRS, tuple())


def _init_repo(repo: Path) -> None:
    """Initialize a new repository."""
    assert not any(repo.iterdir()), "Folder must be empty."

    for d in MUST_HAVE_DIRS:
        (repo / d).mkdir(parents=True, exist_ok=True)

    cli_logger.warning("Folder structure created.")
    cli_logger.warning("Please add config files to %s", repo / "configs")
    cli_logger.warning(
        "Then continue with `custom-repo key %s [-p <priv_key>] [-v]`.", repo
    )


def check_restart_args() -> Path:
    """Check the repository folder.

    Returns:
        The repository folder.

    Raises:
        FileNotFoundError: If the folder does not exist.
        ValueError: If an invalid file/folder is present.
    """
    args = parse_restart_args()
    repo = args.repo.expanduser().absolute()

    verbose = args.verbose
    set_log_level(verbose)

    if not repo.exists():
        raise FileNotFoundError(f"Folder {repo} does not exist.")
    _check_repo_struct(repo)
    return repo


def check_build_args() -> tuple[Path, str, Path, str, bool, bool]:
    """Check the build arguments.

    Sets the GH_TOKEN environment variable if a token file is provided.

    Returns:
        A tuple with the repo path, domain, the private key file,
        the authentification string and the headless and restart flags.

    Raises:
        ValueError: If the arguments are invalid.
        FileNotFoundError: If a file is not found.
    """
    args = parse_build_args()

    _parse_verbosity(args.verbose)

    repo = args.repo.expanduser().absolute()
    if not repo.exists():
        raise FileNotFoundError(f"Folder {repo} does not exist. Please create it.")

    if any(repo.iterdir()):
        _check_repo_struct(repo)
    else:
        _init_repo(repo)

    domain = _check_domain(args.domain)

    priv_file = Path(args.key).expanduser().absolute()
    if not priv_file.exists():
        gpg.create_priv_key(priv_file, tmp=args.repo)

    _check_token(args.github)

    auth = _check_auth(args)

    return repo, domain, priv_file, auth, args.headless, args.restart
