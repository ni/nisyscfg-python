"""Hardware filter functionality for NI System Configuration."""

import ctypes
from typing import TYPE_CHECKING, Any, Optional, Protocol, Type

import nisyscfg.errors
import nisyscfg.properties
import nisyscfg.xnet.properties
from nisyscfg import _library_singleton
from nisyscfg._lib import c_string_encode
from nisyscfg.properties import PropertyAccessor

if TYPE_CHECKING:

    class _XnetFilterProperties(Protocol):
        port_number: int


@nisyscfg.properties.PropertyBag(nisyscfg.properties.Filter)
@nisyscfg.properties.PropertyBag(nisyscfg.xnet.properties.Filter, expert="xnet")
class Filter(object):
    """Represents a NI System Configuration filter."""

    if TYPE_CHECKING:
        is_device: bool
        is_present: bool
        is_ni_product: bool
        is_chassis: bool
        serial_number: str
        user_alias: str
        connects_to_link_name: str
        expert_name: str
        xnet: _XnetFilterProperties

    _handle: Optional["nisyscfg.types.FilterHandle"]

    """Represents a hardware resource filter."""

    def __init__(self, session: "nisyscfg.types.SessionHandle") -> None:
        """Initialize a hardware filter."""
        self._handle = nisyscfg.types.FilterHandle()
        self._library = _library_singleton.get()

        # PropertyAccessor is a typed class in nisyscfg.properties; construct it directly.
        self._property_accessor: PropertyAccessor = PropertyAccessor(
            setter=self._set_property_with_type
        )

        # ctypes.pointer expects a C compatible handle.
        # mypy can't verify the dynamic ctypes types here.
        error_code = self._library.CreateFilter(session, ctypes.pointer(self._handle))
        nisyscfg.errors.handle_error(self, error_code)

    def __del__(self) -> None:
        """Release the filter handle."""
        self.close()

    def close(self) -> None:
        """Close the filter handle."""
        if self._handle:
            error_code = self._library.CloseHandle(self._handle)
            nisyscfg.errors.handle_error(self, error_code)
            self._handle = None

    def _set_property_with_type(
        self, id: int, value: Any, c_type: Type[Any], nisyscfg_type: int
    ) -> None:
        if c_type == ctypes.c_char_p:
            value = c_string_encode(value)
        elif issubclass(c_type, nisyscfg.enums.BaseEnum) or issubclass(
            c_type, nisyscfg.enums.BaseFlag
        ):
            value = ctypes.c_int(value)
        else:
            value = c_type(value)

        # The SetFilterPropertyWithType call is to a C library; mypy cannot type-check it.
        error_code = self._library.SetFilterPropertyWithType(self._handle, id, nisyscfg_type, value)
        nisyscfg.errors.handle_error(self, error_code)
