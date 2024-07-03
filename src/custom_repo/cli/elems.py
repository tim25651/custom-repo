"""Defines allowed elements for the custom repo structure."""

MUST_HAVE_DIRS = {
    "configs",
    "private",
    "pkgs",
    "pkgs/apt",
    "pkgs/choco",
    "pkgs/conda",
    "pkgs/brew",
    "public",
    "public/data",
    "public/data/choco",
    "public/data/brew",
}
ALLOWED_DIRS = {
    "private",
    "private/*",
    "configs",
    "configs/*.apt",
    "configs/*.conda",
    "configs/*.choco",
    "configs/*.choco/tools",
    "configs/*.conda/recipe",
    "public",
    "public/choco",
    "public/debs",
    "public/debs/dists",
    "public/debs/dists/stable",
    "public/debs/dists/stable/main",
    "public/debs/dists/stable/main/binary-amd64",
    "public/debs/pool",
    "public/debs/pool/main",
    "public/data",
    "public/data/brew",
    "public/data/choco",
    "public/tap.git",
    "public/tap.git/*",
    "public/conda",
    "public/conda/linux-64",
    "public/conda/noarch",
    "public/conda/linux-64/.cache",
    "public/conda/noarch/.cache",
    "pkgs",
    "pkgs/apt",
    "pkgs/choco",
    "pkgs/conda",
    "pkgs/brew",
}
ALLOWED_FILES = {
    "private/README.md",
    "public/choco/packages.json",
    "public/choco/app.yaml",
    "public/choco/*.nupkg",
    "pkgs/choco/*.nupkg",
    "public/data/brew/*",
    "public/data/choco/*",
    "public/debs/.debs.list",
    "public/debs/.debs.list.old",
    "public/debs/dists/stable/InRelease",
    "public/debs/dists/stable/Release",
    "public/debs/dists/stable/Release.gpg",
    "public/debs/dists/stable/main/binary-amd64/Packages",
    "public/debs/dists/stable/main/binary-amd64/Packages.gz",
    "public/debs/pool/main/*.deb",
    "public/debs/pool/main/*.tar",
    "public/debs/pool/main/*.tar.gz",
    "pkgs/apt/*.deb",
    "pkgs/apt/*.tar",
    "pkgs/apt/*.tar.gz",
    "private/*/*",
    "public/debs/pub.gpg",
    "configs/*.apt",
    "configs/*.brew",
    "configs/*.apt/*",
    "configs/*.choco/*",
    "configs/*.choco/tools/*",
    "configs/*.conda/recipe/*",
    "configs/*.conda/*.conda",
    "public/tap.git/*",
    "pkgs/brew/*.rb",
    "public/conda/index.html",
    "public/conda/channeldata.json",
    "public/conda/*/index.html",
    "public/conda/*/*repodata*.json*",
    "public/conda/*/*.tar.bz2",
    "public/conda/*/.cache/cache.db*",
    "pkgs/conda/*.tar.bz2",
}
