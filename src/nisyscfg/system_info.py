"""System discovery and enumeration functionality for NI System Configuration."""

from typing import Optional

import nisyscfg.errors
from nisyscfg import _library_singleton
from nisyscfg._lib import c_string_decode
from nisyscfg.types import EnumSystemHandle


class SystemInfoIterator(object):
    """Iterates over discovered systems."""

    def __init__(self, handle: Optional[EnumSystemHandle]) -> None:
        """Initialize the system information iterator."""
        self._handle: Optional[EnumSystemHandle] = handle
        self._library = _library_singleton.get()

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
        return c_string_decode(system_name.value)

    def close(self) -> None:
        """Close the system enumeration handle."""
        if self._handle:
            error_code = self._library.CloseHandle(self._handle)
            nisyscfg.errors.handle_error(self, error_code)
            self._handle = None
