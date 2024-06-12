"""Parser module for custom_repo."""

from custom_repo.parser import parse
from custom_repo.parser.cmd_groups import (
    COPY_CMD,
    COPY_CMDS,
    DOWNLOAD_CMD,
    DOWNLOAD_CMDS,
    UNIQUE_CMD,
    UNIQUE_CMDS,
)
from custom_repo.parser.cmds import Command, check_number_of_args
from custom_repo.parser.params import PackageManager, Params, TargetDir
from custom_repo.parser.utils import adjust_regex_version, fix_vars
