"""Software feed enumeration functionality for NI System Configuration."""

import ctypes
import typing
from typing import Any, Optional

import nisyscfg._library_singleton
import nisyscfg.errors
from nisyscfg._lib import c_string_decode

SoftwareFeed = typing.NamedTuple(
    "SoftwareFeed",
    [
        ("name", str),
        ("uri", str),
        ("enabled", bool),
        ("trusted", bool),
    ],
)


class SoftwareFeedIterator(object):
    """Iterates over configured software feeds."""

    def __init__(self, handle: Optional[Any]) -> None:
        """Initialize the software feed iterator."""
        self._handle: Optional[Any] = handle
        # _library is untyped at runtime; keep the type as Any to avoid
        # leaking implementation details while satisfying type checking.
        self._library: Any = nisyscfg._library_singleton.get()

    def __del__(self) -> None:
        """Release resources associated with the iterator."""
        self.close()

    def __iter__(self) -> "SoftwareFeedIterator":
        """Return the iterator instance."""
        return self

    def __next__(self) -> SoftwareFeed:
        """Return the next software feed."""
        if not self._handle:
            raise StopIteration()
        name = nisyscfg.types.simple_string()
        uri = nisyscfg.types.simple_string()
        enabled = ctypes.c_int()
        trusted = ctypes.c_int()
        error_code = self._library.NextSoftwareFeed(
            self._handle, name, uri, ctypes.pointer(enabled), ctypes.pointer(trusted)
        )
        if error_code == nisyscfg.errors.Status.END_OF_ENUM:
            raise StopIteration()
        nisyscfg.errors.handle_error(self, error_code)
        return SoftwareFeed(
            name=c_string_decode(name.value),
            uri=c_string_decode(uri.value),
            enabled=enabled.value != 0,
            trusted=trusted.value != 0,
        )

    def close(self) -> None:
        """Close the software feed enumeration handle."""
        if self._handle:
            error_code = self._library.CloseHandle(self._handle)
            nisyscfg.errors.handle_error(self, error_code)
            self._handle = None
