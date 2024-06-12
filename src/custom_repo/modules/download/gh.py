"""GitHub API helpers.

Needs gh installed and a .gh_token file with a GitHub token in the working directory.
"""

import fnmatch
import os
from typing import Any

from requests import Session


class GitHubError(Exception):
    """GitHub API error."""


class GitHubTokenError(GitHubError):
    """GitHub token error."""


class GitHubSession:
    """Updates the session headers for GitHub API requests.

    Attributes:
        session: The requests session to use.
    """

    def __init__(self, session: Session | None = None) -> None:
        """Initialize the class.

        Args:
            session: The requests session to use. Defaults to None.
                Creates a new session if None.
        """
        self.session = session or Session()

    def __enter__(self) -> Session:
        """Enter the context manager.

        Returns:
            The session with updated headers.

        Raises:
            GitHubTokenError: If no GitHub token is set.
        """
        token = os.getenv("GH_TOKEN")
        if not token:  # pylint: disable=consider-using-assignment-expr
            raise GitHubTokenError("No GH_TOKEN environment variable set.")

        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        return self.session

    def __exit__(self, *args: Any) -> None:
        """Exit the context manager. Clear the headers."""
        self.session.headers.clear()


def get_release_data(
    repo: str, exclude_prereleases: bool = True, session: Session | None = None
) -> dict[str, list[str]]:
    """Get all tag names and assets for a GitHub repository.

    Args:
        repo: The GitHub repository in the format "owner/repo".
        exclude_prereleases: Whether to exclude prereleases. Defaults to True.
        session: The requests session to use. Defaults to None.
            Creates a new session if None.

    Returns:
        A dictionary with tag names as keys and asset names as values.
    """

    with GitHubSession(session) as gh_session:
        url = f"https://api.github.com/repos/{repo}/releases"
        response = gh_session.get(url)

    def _exclude_release(release: dict[str, Any]) -> bool:
        return exclude_prereleases and release["prerelease"]

    def _get_assets(release: dict[str, Any]) -> list[str]:
        return [asset["name"] for asset in release["assets"]]

    return {
        release["tag_name"]: _get_assets(release)
        for release in response.json()
        if not _exclude_release(release)
    }


def find_asset_by_tag(
    release_data: dict[str, list[str]],
    pattern: str,
    tag: str,
) -> str | None:
    """Find an asset by tag in the GitHub repo.

    Args:
        release_data: The release data dictionary (tag name: asset names).
        pattern: The pattern to match.
        tag: The tag to search for.

    Returns:
        The asset name if found, otherwise None.

    Raises:
        GitHubError: If no assets are found for the tag.
    """
    assets = release_data.get(tag)
    if not assets:  # pylint: disable=consider-using-assignment-expr
        raise GitHubError(f"No assets found for tag {tag}.")

    matches = fnmatch.filter(assets, pattern)
    if not matches:  # pylint: disable=consider-using-assignment-expr
        return None
    if len(matches) > 1:
        raise GitHubError(f"Multiple matching tags for pattern {pattern}: {matches}.")
    return matches.pop()


def find_recent_asset(
    release_data: dict[str, list[str]], pattern: str
) -> tuple[str, str]:
    """Find the most recent tag and asset that matches the pattern.

    Args:
        release_data: The release data dictionary (tag name: asset names).
        pattern: The pattern to match.

    Returns:
        A tuple with the asset name and tag name.

    Raises:
        GitHubError: If no matching tag is found.
    """
    for tag in release_data:
        if asset := find_asset_by_tag(release_data, pattern, tag):
            return asset, tag

    raise GitHubError(f"No matching tag found for pattern {pattern}.")
