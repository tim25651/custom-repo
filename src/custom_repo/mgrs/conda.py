"""Conda package manager."""

import json
import logging
import os
import shutil
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from subprocess import CalledProcessError

from conda_index import api as index_api

from custom_repo.modules import ConnectionKeeper, exec_cmd, file_manup, set_log_level
from custom_repo.parser import Params, fix_vars

conda_logger = logging.getLogger(__name__)


def build_channel(repo: Path) -> None:
    """Build the channel for conda packages.

    Args:
       repo: The repository directory.

    Raises:
        FileExistsError: If the public directory already exists.
        ValueError: If an unexpected file is found in the conda packages directory.
    """
    pub = repo / "public" / "conda"
    pkgs = repo / "pkgs" / "conda"
    if pub.exists():
        shutil.rmtree(pub)
    pub.mkdir()

    amd64 = pub / "linux-64"
    amd64.mkdir()
    for pkg in pkgs.iterdir():
        if pkg.suffixes[-2:] != [".tar", ".bz2"]:
            raise ValueError(f"Unexpected file in {pkgs}: {pkg}")
        target_pkg = amd64 / pkg.name
        target_pkg.symlink_to(pkg)

    index_api.update_index(pub)

    for file in pub.glob("**/*.json"):
        content = json.loads(file.read_text("utf-8"))
        file.write_text(json.dumps(content, indent=4), "utf-8")


def _move_pkg(name: str, stem: str, version: str, target_dir: Path) -> None:
    """Move the built package to the target directory."""
    conda_prefix = os.getenv("CONDA_PREFIX")
    if not conda_prefix:  # pylint: disable=consider-using-assignment-expr
        raise ValueError("CONDA_PREFIX is not set.")

    build_dir = Path(conda_prefix) / "conda-bld" / "linux-64"

    pkg = file_manup.get_first_elem(build_dir, f"{name}-{version}-*.tar.bz2")

    pkg.rename(target_dir / (stem + ".tar.bz2"))


def _log_debug(out: str, err: str, wd: Path) -> None:
    """Log debug information."""
    debug_dir = Path("/tmp/conda-build-debug")
    if debug_dir.exists():
        shutil.rmtree(debug_dir)

    shutil.copytree(wd, debug_dir)

    (debug_dir / "build.log").write_text(out, "utf-8")
    (debug_dir / "error.log").write_text(err, "utf-8")

    conda_logger.error("Error building package. Debug files are in %s", debug_dir)
    conda_logger.error("Build log: %s", out)
    conda_logger.error("Error log: %s", err)


def _build(recipe: Path, domain: str | None) -> tuple[str, str, int]:
    """Build a conda package."""
    out_io = StringIO()
    err_io = StringIO()
    code = 0

    prev_level = conda_logger.getEffectiveLevel()

    args = ["conda-build", "./recipe", "-c", "conda-forge"]
    if domain:
        args.extend(["-c", f"{domain}/conda"])

    with redirect_stdout(out_io), redirect_stderr(err_io):
        try:
            exec_cmd(
                args,
                cwd=recipe.parent,
            )

        except CalledProcessError as e:
            code = 1
            # KEEP PRINT, do not use logging - as it will be redirected to err_io
            print("Error building package:", e, file=sys.stderr)

    set_log_level(logging.WARNING)
    set_log_level(prev_level, only_pkg=True)

    out = out_io.getvalue()
    err = err_io.getvalue()
    out_io.close()
    err_io.close()

    return out, err, code


def build_conda_pkg(keeper: ConnectionKeeper, params: Params, wd: Path) -> None:
    """Build a conda package."""
    repo = params["REPO"]
    domain = params["DOMAIN"]
    name = params["NAME"]
    stem = params["STEM"]
    version = params["VERSION"]

    pkgs_conda = repo / "pkgs" / "conda"

    meta_yaml_path = wd / "recipe" / "meta.yaml"
    meta_yaml_text = fix_vars(params, meta_yaml_path.read_text("utf-8"))
    meta_yaml_path.write_text(meta_yaml_text, "utf-8")

    recipe = wd / "recipe"

    # test if %domain%/conda is reachable
    reponse = keeper.session.get(f"{domain}/conda")
    if reponse.status_code == 200:
        checked_domain = domain
    else:
        conda_logger.error(
            "Error: %s/conda is not reachable (%s). Only conda-forge will be used.",
            domain,
            reponse.status_code,
        )
        checked_domain = None

    out, err, code = _build(recipe, checked_domain)

    if code != 0:
        _log_debug(out, err, wd)
        raise ValueError(f"Error building {name} {version} (error code {code}).")

    exec_cmd(["conda-build", "purge"])

    _move_pkg(name, stem, version, pkgs_conda)
