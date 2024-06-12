"""Utility functions for logging.

Implements:
- `set_log_level`: Set the level of all loggers to the given level.
"""

import logging


def set_log_level(level: int, only_pkg: bool = False) -> None:
    """Set the level of all loggers to the given level.

    Args:
        level (int): The level to set.
        only_pkg (bool): If True, only set the level for the package.
    """
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=level,
    )

    pkg_name = __name__.split(".", 1)[0]

    def _filter(name: str) -> bool:
        if not only_pkg:
            return True
        return name.startswith(f"{pkg_name}.")

    loggers = [
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict  # pylint: disable=no-member
        if _filter(name)
    ]

    for logger in loggers:
        logger.setLevel(level)
