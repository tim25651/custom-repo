from collections.abc import Callable
from pathlib import Path

from custom_repo.impl.cmds import (
    copy_cmd,
    download_cmd,
    extract,
    mkdir,
    rename,
    set_cmd,
    write_caskfile,
)
from custom_repo.mgrs import (
    build_choco_pkg,
    build_conda_pkg,
    build_deb,
    create_deb,
    dh_disable,
)
from custom_repo.modules import ConnectionKeeper
from custom_repo.parser import Command, Params

IMPLEMENTATIONS: dict[
    Command, Callable[[ConnectionKeeper, Params, list[str], Path], None]
] = {
    Command.EXTRACT: lambda *args: extract(*args[1:]),
    Command.MKDIR: lambda *args: mkdir(*args[1:]),
    Command.RENAME: lambda *args: rename(*args[1:]),
    Command.CASK: lambda *args: write_caskfile(args[1], args[2]),
    Command.SET: lambda *args: set_cmd(args[1], args[2]),
    Command.COPY: lambda *args: copy_cmd(Command.COPY, *args[1:]),
    Command.COPY_FIX: lambda *args: copy_cmd(Command.COPY_FIX, *args[1:]),
    Command.COPY_DIR: lambda *args: copy_cmd(Command.COPY_DIR, *args[1:]),
    Command.COPY_GLOB: lambda *args: copy_cmd(Command.COPY_GLOB, *args[1:]),
    Command.DOWNLOAD: lambda *args: download_cmd(Command.DOWNLOAD, *args),
    Command.DOWNLOAD_GH: lambda *args: download_cmd(Command.DOWNLOAD_GH, *args),
    Command.DOWNLOAD_REMOTE_NAME: lambda *args: download_cmd(
        Command.DOWNLOAD_REMOTE_NAME, *args
    ),
    Command.DOWNLOAD_BROWSER: lambda *args: download_cmd(
        Command.DOWNLOAD_BROWSER, *args
    ),
    Command.CREATE_DEB: lambda *args: create_deb(*args[1:]),
    Command.BUILD_DEB: lambda *args: build_deb(args[1], args[3]),
    Command.DH_DISABLE: lambda *args: dh_disable(*args[1:]),
    Command.CONDA_BUILD: lambda *args: build_conda_pkg(args[1], args[3]),
    Command.CHOCO: lambda *args: build_choco_pkg(args[1], args[3]),
}
