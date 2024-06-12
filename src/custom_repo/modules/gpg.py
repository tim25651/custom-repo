"""Key generation and signing functions.

Implements:
- `create_priv_key`: Create a PGP key.
- `sign_repo`: Sign the Release file and create the InRelease file.
"""

import logging
from pathlib import Path
from typing import Any

import gnupg

from custom_repo.modules.temp import TemporaryDirectory

gpg_logger = logging.getLogger(__name__)


class KeyCreationError(Exception):
    """Key creation failed."""


class TempGPG:
    """Create a temporary GPG home directory.

    Attributes:
        dir (Path, optional): The directory to create the temporary directory.
    """

    def __init__(
        self, dir: Path | None = None  # pylint: disable=redefined-builtin
    ) -> None:
        """Initialize the TempGPG class.

        Args:
            dir (Path, optional): The directory to create the temporary directory.
                Defaults to None.
        """
        self._tmp: TemporaryDirectory | None = None
        self.dir = dir

    def __enter__(self) -> gnupg.GPG:
        """Create the temporary GPG home directory.

        Returns:
            gnupg.GPG: The GPG object.
        """
        self._tmp = TemporaryDirectory(prefix="tmp_TempGPG_", dir=self.dir)
        tmp = self._tmp.path
        pgp_tmp = tmp / "pgpkeys-AAAAAA"
        pgp_tmp.mkdir()

        gpg = gnupg.GPG(gnupghome=pgp_tmp)
        gpg.encoding = "utf-8"
        return gpg

    def __exit__(self, *args: Any) -> None:
        """Cleanup the temporary directory."""
        if not self._tmp:
            return

        self._tmp.cleanup()


def create_priv_key(priv_file: Path, tmp: Path | None = None) -> None:
    """Create a PGP key

    Args:
        priv_file (Path): The path to the private key file.
        tmp (Path, optional): The temporary directory path. Defaults to None.

    Raises:
        FileExistsError: If the private key file already exists.
        KeyCreationError: If the key creation failed.
    """
    if priv_file.exists():
        raise FileExistsError(f"{priv_file} already exists.")

    with TempGPG(tmp) as gpg:

        name_real = "example"
        name_email = "example@example.com"

        input_data = gpg.gen_key_input(
            Key_Type="RSA",
            Key_Length=4096,
            Name_Real=name_real,
            Name_Email=name_email,
            Expire_Date=0,
            no_protection=True,
        )
        key = gpg.gen_key(input_data)

        if key is None:  # pylint: disable=consider-using-assignment-expr
            raise KeyCreationError("GPG returned None.")

        gpg.export_keys(
            key.fingerprint,
            secret=True,
            armor=False,
            expect_passphrase=False,
            output=str(priv_file),
        )

        if not priv_file.exists():
            raise KeyCreationError(f"No file at {priv_file}")
        if not priv_file.stat().st_size:
            priv_file.unlink()
            raise KeyCreationError(f"File at {priv_file} is empty.")

    gpg_logger.warning("Created key file at %s", priv_file)


def sign_repo(
    root: Path, pub_file: Path, priv_file: Path, tmp: Path | None = None
) -> None:
    """Sign the Release file and create the InRelease file and exports the public key.

    Args:
        root: The root directory (subdirs: pool and dists).
        pub_file: Target public key file.
        priv_file: The private key file.
        tmp: The temporary directory path. Defaults to None.
    """

    release = root / "dists" / "stable" / "Release"

    with TempGPG(tmp) as gpg:

        # Import the private key to the temporary keyring
        exp = gpg.import_keys(priv_file.read_bytes())

        # Sign the Release file
        # -abs: --armor --detach-sign --sign
        gpg.sign_file(
            str(release),
            detach=True,
            clearsign=False,
            binary=False,
            output=str(release.with_suffix(".gpg")),
        )

        # Sign the InRelease file
        # --clearsign: make a clear text signature
        gpg.sign_file(
            str(release),
            detach=False,
            clearsign=True,
            output=str(release.with_name("InRelease")),
        )

        gpg.export_keys(exp.fingerprints[0], armor=False, output=str(pub_file))
