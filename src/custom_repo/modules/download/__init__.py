"""Module for downloading files from the internet or GitHub.

Implements:

- `download_direct`: Download a file directly.
- `download_via_browser`: Download a file via a browser.
- `get_remote_filename`: Get the filename from a URL.
- `get_release_data`: Get the release data from a GitHub repository.
- `find_asset_by_tag`: Find an asset by tag name.
- `find_recent_asset`: Find the most recent asset that matches a pattern.
- `CacheSession`: A session that caches responses.
- `ConnectionKeeper`: A context manager for keeping connections open.
"""

from custom_repo.modules.download import file, gh, session
from custom_repo.modules.download.file import (
    download_direct,
    download_via_browser,
    get_remote_filename,
)
from custom_repo.modules.download.gh import (
    find_asset_by_tag,
    find_recent_asset,
    get_release_data,
)
from custom_repo.modules.download.session import CacheSession, ConnectionKeeper
