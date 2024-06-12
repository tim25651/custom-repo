"""Like a custom package manager"""

import logging
from pathlib import Path

from custom_repo import cli, impl, mgrs
from custom_repo.modules import check_installs, download, set_log_level
from custom_repo.parser import parse

set_log_level(logging.WARNING)

main_logger = logging.getLogger(__name__)

# TODO: check commands run before and after a command
# TODO: check if some configs have to be run before others
# TODO: main already exists, wrong output (can't find real main)
# TODO: checksum check of config files and downloaded files
# TODO: allow to only update single values


def restart(repo: Path | None = None) -> None:
    """Restart the repository server.

    Args:
        repo (Path, optional): The repository folder. Defaults to None.
    """
    if repo is None:
        repo = cli.check_restart_args()
    check_installs({"nohup", "npx"})
    mgrs.restart_server(repo)


def main() -> None:
    """Main function."""

    repo, domain, priv_file, auth, headless, restart_flag = cli.check_build_args()

    check_installs({
        "git",
        "dh_make",
        "dpkg-buildpackage",
        "dpkg-scanpackages",
        "gpg",
        "mono",
    })

    impl.clean_data(repo)

    with download.ConnectionKeeper(headless=headless) as keeper:
        configs = parse.load_configs(repo, domain, auth, keeper)

        parse.check_for_duplicates(configs)

        for params, cmds in configs:
            if impl.final_exists(params):
                continue

            main_logger.debug("Loading %s (%s)", params["NAME"], params["MGR"].name)
            main_logger.debug(
                "Commands: %s",
                [actual_cmd.name for actual_cmd, _ in cmds],
            )

            with impl.DirContext(params) as wd:
                for actual_cmd, cmd_args in cmds:
                    impl.run_cmd(
                        keeper,
                        params,
                        actual_cmd,
                        cmd_args,
                        wd,
                    )

            main_logger.info(
                "Finished %s (%s): %s",
                params["NAME"],
                params["MGR"].name,
                params["VERSION"],
            )

    mgrs.update_repo(repo, priv_file)
    mgrs.build_channel(repo)
    mgrs.build_choco(repo)
    mgrs.build_tap(repo)

    if restart_flag:
        restart(repo)


if __name__ == "__main__":
    main()
