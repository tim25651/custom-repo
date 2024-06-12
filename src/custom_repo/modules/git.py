"""Git utilities for the custom repository.

Implements:
- `init`: Initialize a git repository.
- `clone`: Clone a repository.
- `update_server_info`: Update the server info for the tap repository.
- `commit_everything`: Add all files, commit and push.
"""

from pathlib import Path

from custom_repo.modules.exec_cmd import exec_cmd


def init(repo: Path, bare: bool = False) -> None:
    """Initialize a git repository."""
    if not repo.parent.is_dir():
        raise ValueError("Parent directory does not exist.")

    args = ["git", "init", repo.name]
    if bare:
        args.append("--bare")

    exec_cmd(args, cwd=repo.parent)


def clone(repo: str | Path, dest: Path, allow_same_name: bool = False) -> None:
    """Clone a repository."""
    if not allow_same_name and dest.name == str(repo).rsplit("/", maxsplit=1)[-1]:
        raise ValueError("Repository name and destination folder name are the same.")

    exec_cmd(["git", "clone", str(repo)], cwd=dest)


def update_server_info(bare_repo: Path) -> None:
    """Update the server info for the tap repository."""
    exec_cmd(["git", "update-server-info"], cwd=bare_repo)


def commit_everything(
    repo: Path, bare_repo: Path | None = None, message: str = "Commited."
) -> None:
    """Add all files, commit and push."""
    exec_cmd(["git", "add", "."], cwd=repo)
    exec_cmd(["git", "commit", "-m", message], cwd=repo, raise_on_failure=False)
    exec_cmd(["git", "push"], cwd=repo)
    if bare_repo:
        update_server_info(bare_repo)
