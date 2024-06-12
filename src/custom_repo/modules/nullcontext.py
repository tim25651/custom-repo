"""Implements contextlib.nullcontext in a typed manner.

Implements:
- `TypedNullContext`: A typed version of `nullcontext`.
"""

from contextlib import AbstractContextManager
from typing import Any, Generic, TypeVar

from typing_extensions import override

_T = TypeVar("_T")


class TypedNullContext(AbstractContextManager, Generic[_T]):
    """Context manager that does no additional processing.

    Attributes:
        enter_result: The value to return from __enter__.
    """

    def __init__(self, enter_result: _T) -> None:
        """Initialize the class.

        Args:
            enter_result: The value to return from __enter__.
        """
        self.enter_result = enter_result

    @override
    def __enter__(self) -> _T:
        """Return the value passed to the constructor."""
        return self.enter_result

    @override
    def __exit__(self, *excinfo: Any) -> None:
        """Do nothing."""
