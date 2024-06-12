"""Commands for the apt package manager."""

import gzip
import hashlib
import logging
import shutil
from collections.abc import Callable
from datetime import datetime
from difflib import unified_diff
from io import BytesIO
from pathlib import Path
from typing import Literal

import pytz

from custom_repo.modules import exec_cmd, file_manup, gpg
from custom_repo.parser import Params

apt_logger = logging.getLogger(__name__)


def has_updated(repo: Path, verbose: bool = False) -> tuple[bool, list[str], list[str]]:
    """Check if the repository has been updated."""
    pub = repo / "public" / "debs"

    file_list = pub / ".debs.list"
    debs_dir = repo / "pkgs" / "apt"

    curr_files = sorted(x.name for x in debs_dir.iterdir() if x.suffix == ".deb")

    if file_list.exists():
        old_files = file_list.read_text().splitlines()
        old_file_list = pub / ".debs.list.old"
        old_file_list.write_text("\n".join(old_files))
    else:
        old_files = []

    if pub.exists():
        file_list.write_text("\n".join(curr_files))

    changed = curr_files != old_files

    if verbose:
        if changed:
            apt_logger.info("Changed debs:")
            for line in unified_diff(old_files, curr_files):
                apt_logger.info(line)
        else:
            apt_logger.info("No changes in debs.")

    return changed, curr_files, old_files


def update_repo(repo: Path, priv_file: Path) -> None:
    """Update the repository."""

    changed, curr, old = has_updated(repo)

    if not changed:
        return

    build_repo(repo, priv_file)

    pub = repo / "public" / "debs"
    (pub / ".debs.list.old").write_text("\n".join(old))
    (pub / ".debs.list").write_text("\n".join(curr))


def build_repo(repo: Path, priv_file: Path) -> None:
    """Build the repository for apt packages.

    Args:
        repo: The repository directory.
        priv_file: The private key file for signing the repository.

    Raises:
        FileExistsError: If the public directory already exists.
        ValueError: If an unexpected file is found in the apt packages directory.
    """
    pub = repo / "public" / "debs"
    pkgs = repo / "pkgs" / "apt"
    if pub.exists():
        shutil.rmtree(pub)
    pub.mkdir()

    main = pub / "pool" / "main"
    main.mkdir(parents=True)
    for pkg in pkgs.iterdir():
        if pkg.suffix != ".deb":
            if pkg.suffix == ".tar" or pkg.suffixes[-2:] == [".tar", ".gz"]:
                continue
            raise ValueError(f"Unexpected file in {pkgs}: {pkg}")
        target_pkg = main / pkg.name
        target_pkg.symlink_to(pkg)

    stable = pub / "dists" / "stable"
    amd64 = stable / "main" / "binary-amd64"
    amd64.mkdir(parents=True)

    create_repo(pub)

    gpg.sign_repo(pub, pub / "pub.gpg", priv_file, repo)


def create_deb(params: Params, args: list[str], wd: Path) -> None:
    """Create a .deb folder structure with `args` as dependencies.

    Usage: CREATE_DEB "DEPENDENCY1 DEPENDENCY2" ...
    """
    name = params["NAME"]
    version = params["VERSION"]

    dest_dir = wd / f"{name}-{version}"
    exec_cmd(["dh_make", "--createorig", "-i", "-y"], cwd=dest_dir)

    if args:
        control = (dest_dir / "debian" / "control").read_text("utf-8")
        control = control.replace("Depends: ", f"Depends: {args[0]}, ")
        (dest_dir / "debian" / "control").write_text(control, "utf-8")
    # else: no dependencies


def build_deb(params: Params, wd: Path) -> None:
    """Build a .deb file from the .deb folder structure.

    Usage: BUILD_DEB
    """
    dest_dir = wd / f"{params['NAME']}-{params['VERSION']}"
    exec_cmd(["dpkg-buildpackage", "-rfakeroot", "-us", "-uc"], cwd=dest_dir)

    target_dir = params["REPO"] / "pkgs" / "apt"

    file = file_manup.get_first_elem(dest_dir.parent, "*.deb")

    filename = f"{params['STEM']}.deb"
    file_manup.copy(file, target_dir / filename)


def get_packages_hashes(
    packages: tuple[Path, str],
    packages_gz: tuple[Path, bytes],
) -> list[str]:
    """Get the hashes for the Packages and Packages.gz files."""

    lines: list[str] = []

    def _hash_func(s: str | bytes, hash_type: Literal["md5", "sha1", "sha256"]) -> str:
        if isinstance(s, str):
            s = s.encode("utf-8")
        if hash_type == "md5":
            return hashlib.md5(s).hexdigest()
        if hash_type == "sha1":
            return hashlib.sha1(s).hexdigest()
        if hash_type == "sha256":
            return hashlib.sha256(s).hexdigest()
        raise ValueError(f"Unknown hash type: {hash_type}")

    header_hashes: list[tuple[str, Callable[[str | bytes], str]]] = [
        ("MD5Sum", lambda x: _hash_func(x, "md5")),
        ("SHA1", lambda x: _hash_func(x, "sha1")),
        ("SHA256", lambda x: _hash_func(x, "sha256")),
    ]
    all_packages: list[tuple[Path, str | bytes]] = [packages, packages_gz]
    for header, hash_func in header_hashes:
        lines.append(f"{header}:")
        for path, content in all_packages:
            rel_path = path.relative_to(path.parent.parent.parent)
            char_count = len(content)
            hash_str = hash_func(content)
            lines.append(f" {hash_str} {char_count} {rel_path}")

    return lines


def create_release_file(
    package: tuple[Path, str], packages_gz: tuple[Path, bytes]
) -> str:
    """Create the Release file for the apt repository."""
    origin = "Custom Repository"
    label = "Custom"
    suite = codename = "stable"
    version = "1.0"
    arch = "amd64"
    components = "main"
    desc = "A set of packages not available in the official repositories."
    date = datetime.now(pytz.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    lines = [
        f"Origin: {origin}",
        f"Label: {label}",
        f"Suite: {suite}",
        f"Codename: {codename}",
        f"Version: {version}",
        f"Architectures: {arch}",
        f"Components: {components}",
        f"Description: {desc}",
        f"Date: {date}",
    ]
    lines += get_packages_hashes(package, packages_gz)
    return "\n".join(lines) + "\n"


def create_packages(pub: Path) -> tuple[Path, str]:
    """Create the Packages file for the apt repository."""
    packages_file = pub / "dists" / "stable" / "main" / "binary-amd64" / "Packages"

    packages = exec_cmd(["dpkg-scanpackages", "-m", "pool/"], cwd=pub)
    packages_file.write_text(packages, "utf-8")

    return packages_file, packages


def create_packages_gz(
    packages_file: Path, packages: str, skip_update: bool = False
) -> tuple[Path, bytes]:
    """Create the Packages.gz file for the apt repository."""
    packages_gz_file = packages_file.with_suffix(".gz")

    if skip_update:
        return packages_gz_file, packages_gz_file.read_bytes()

    packages_gz_io = BytesIO()
    with gzip.GzipFile(fileobj=packages_gz_io, mode="wb") as f:
        f.write(packages.encode("utf-8"))
    packages_gz = packages_gz_io.getvalue()
    packages_gz_io.close()
    packages_file.with_suffix(".gz").write_bytes(packages_gz)

    return packages_gz_file, packages_gz


def create_repo(pub: Path) -> None:
    """Create the apt repository at `repo`/debs."""
    release_file = pub / "dists" / "stable" / "Release"
    inrelease_file = release_file.with_name("InRelease")
    release_gpg = release_file.with_suffix(".gpg")

    release_file.unlink(missing_ok=True)
    inrelease_file.unlink(missing_ok=True)
    release_gpg.unlink(missing_ok=True)

    packages_file, packages = create_packages(pub)
    packages_gz_file, packages_gz = create_packages_gz(packages_file, packages)

    # no shell injection here, as the script is hardcoded
    release = create_release_file(
        (packages_file, packages), (packages_gz_file, packages_gz)
    )
    release_file.write_text(release, "utf-8")


def dh_disable(params: Params, args: list[str], wd: Path) -> None:
    """Disable the dh_auto_* commands in the rules file.

    Usage: DH_DISABLE
    """
    arg = args[0]

    dest = f"{params['NAME']}-{params['VERSION']}"
    rules_file = wd / dest / "debian" / "rules"
    rules = rules_file.read_text("utf-8")
    rules += f"\noverride_{arg}:\n\t# do nothing\n"
    rules_file.write_text(rules, "utf-8")
