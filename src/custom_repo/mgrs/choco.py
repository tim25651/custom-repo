"""Build Chocolatey packages."""

import json
import logging
import os
import shutil
import subprocess
import urllib.parse
from pathlib import Path

import psutil
import yaml

from custom_repo.modules import TemporaryDirectory, choco, file_manup
from custom_repo.parser import Params, fix_vars

choco_logger = logging.getLogger(__name__)

_APP_YAML = {
    "runtime": "nodejs22",
    "handlers": [{
        "url": "/.*",
        "secure": "always",
        "redirect_http_response_code": 301,
        "script": "auto",
    }],
}
_PACKAGE_JSON = {
    "dependencies": {"express-chocolatey-server": "^1.0.0"},
    "scripts": {"start": "express-chocolatey-server *.nupkg"},
    "engines": {"node": "22.x.x"},
}


def build_choco(repo: Path) -> None:
    """Build the Chocolatey repository.

    Args:
        repo: The repository directory.

    Raises:
        FileExistsError: If the public directory already exists.
        ValueError: If an unexpected file is found in the Chocolatey packages directory.
    """
    pub = repo / "public" / "choco"
    pkgs = repo / "pkgs" / "choco"
    if pub.exists():
        shutil.rmtree(pub)
    pub.mkdir()

    for pkg in pkgs.iterdir():
        if pkg.suffix != ".nupkg":
            raise ValueError(f"Unexpected file in {pkgs}: {pkg}")
        target_pkg = pub / pkg.name
        target_pkg.symlink_to(pkg)

    (pub / "app.yaml").write_text(yaml.dump(_APP_YAML, indent=4), "utf-8")
    (pub / "packages.json").write_text(json.dumps(_PACKAGE_JSON, indent=4), "utf-8")


def _pack_choco_pkg(
    repo: Path, choco_pkgs: Path, name: str, stem: str, wd: Path
) -> None:
    """Pack a Chocolatey package."""
    with TemporaryDirectory(prefix="tmp__pack_choco_pkg_", dir=repo) as tmp:
        choco(
            [
                "pack",
                "--allow-unofficial",
                str(wd / f"{name}.nuspec"),
            ],
            cwd=tmp,
        )
        filename = stem + ".nupkg"
        file = next(tmp.iterdir())
        file.rename(choco_pkgs / filename)


def build_choco_pkg(params: Params, args: list[str], wd: Path) -> bool:
    """Build a Chocolatey package."""
    del args  # build_choco_pkg has no arguments, might have in the future

    pkg = params["PKG"]
    if not pkg:  # pylint: disable=consider-using-assignment-expr
        raise ValueError("Not in a package folder.")

    repo = params["REPO"]
    name = params["NAME"]
    stem = params["STEM"]
    version = params["VERSION"]
    domain = params["DOMAIN"]
    choco_pkgs = repo / "pkgs" / "choco"

    target_path = choco_pkgs / f"{name}.{version}.nupkg"
    if target_path.exists():
        choco_logger.warning("%s already exists.", target_path)
        return False

    files = list(wd.iterdir())
    if not files:  # pylint: disable=consider-using-assignment-expr
        choco_file = False
    elif len(files) > 1:
        raise ValueError("More than one file in the package folder.")
    else:
        file = files.pop()
        rel_path = f"data/choco/{stem}|{file.name}"
        params["VARS"]["CHOCO_FILE"] = f"{domain}/{urllib.parse.quote(str(rel_path))}"
        data_target = repo / "public" / rel_path

        if data_target.exists():
            raise FileExistsError(f"{data_target} already exists.")

        if file.is_symlink():
            data_target.symlink_to(file.resolve())
        else:
            file_manup.copy(file, data_target)

        choco_file = True

    content = (pkg / f"{name}.nuspec").read_text("utf-8")
    content = fix_vars(params, content)
    (wd / f"{name}.nuspec").write_text(content, "utf-8")

    (wd / "tools").mkdir()
    for file in (pkg / "tools").iterdir():
        if file.suffix == ".ps1":
            content = file.read_text("utf-8")
            if "$CHOCO_FILE" in content and not choco_file:
                raise ValueError("No file to be included in the Chocolatey package.")

            content = fix_vars(params, content)
            (wd / "tools" / file.name).write_text(content, "utf-8")
        else:
            file_manup.copy(file, wd / "tools" / file.name)

    _pack_choco_pkg(repo, choco_pkgs, name, params["STEM"], wd)

    return True


def restart_server(repo: Path) -> None:
    """Restart the server."""
    # get proc by name
    pids: dict[int, list[str]] = {}
    for proc in psutil.process_iter():
        if proc.name() == "node":
            cmds = proc.cmdline()
            if "express-chocolatey-server" in cmds[1]:
                pids[proc.pid] = proc.cmdline()

    if not pids:
        choco_logger.warning("No node process found.")
    else:
        if len(pids) > 1:
            raise ValueError("More than one node process found.")
        pid = next(iter(pids))
        old_proc = psutil.Process(pid)
        old_proc.kill()
        old_proc.wait()
        choco_logger.info("Server killed.")

    pub = repo / "public" / "choco"
    files = [x.name for x in pub.glob("*.nupkg")]

    os.environ["PORT"] = "7996"
    subprocess.Popen(  # pylint: disable=consider-using-with
        ["nohup", "npx", "express-chocolatey-server", *files],
        cwd=pub,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    choco_logger.info("Server started.")
