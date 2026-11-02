"""System discovery and enumeration functionality for NI System Configuration."""

from typing import Any, Callable, Optional, cast

import nisyscfg.errors
from nisyscfg import _library_singleton
from nisyscfg._lib import c_string_decode


class SystemInfoIterator(object):
    """Iterates over discovered systems."""

    def __init__(self, handle: Optional[int]) -> None:
        """Initialize the system information iterator."""
        # The handle is typically an integer/opaque C handle; allow None for closed state.
        self._handle: Optional[int] = handle
        # Cast the getter to Any before calling so mypy allows the call to an untyped function.
        self._library: Any = cast(Any, _library_singleton.get())

    def __del__(self) -> None:
        """Release resources associated with the iterator."""
        self.close()

    def __iter__(self) -> "SystemInfoIterator":
        """Return the iterator instance."""
        return self

    def __next__(self) -> str:
        """Return the next discovered system."""
        if not self._handle:
            raise StopIteration()
        system_name = nisyscfg.types.simple_string()
        error_code = self._library.NextSystemInfo(self._handle, system_name)
        if error_code == nisyscfg.errors.Status.END_OF_ENUM:
            raise StopIteration()
        nisyscfg.errors.handle_error(self, error_code)
        # c_string_decode is untyped in stubs; cast it to a Callable that returns str
        # so mypy treats this call as returning a str without changing runtime behavior.
        c_string_decode_t = cast(Callable[[Any], str], c_string_decode)
        return c_string_decode_t(system_name.value)

    def close(self) -> None:
        """Close the system enumeration handle."""
        if self._handle:
            error_code = self._library.CloseHandle(self._handle)
            nisyscfg.errors.handle_error(self, error_code)
            self._handle = None
