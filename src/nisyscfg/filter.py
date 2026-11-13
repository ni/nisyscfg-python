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
    import nisyscfg.enums
    import nisyscfg.xnet.enums

    class _XnetFilterProperties(Protocol):
        number_of_ports: int
        port_number: int
        protocol: nisyscfg.xnet.enums.Protocol
        can_termination_capability: nisyscfg.enums.Bool
        can_transceiver_capability: nisyscfg.xnet.enums.CanTransceiverCapability
        dongle_id: nisyscfg.xnet.enums.DongleId
        enet_phy_state: nisyscfg.xnet.enums.EnetPhyState
        enet_port_mode: nisyscfg.xnet.enums.EnetPortMode
        enet_link_speed_configured: nisyscfg.xnet.enums.EnetLinkSpeed


@nisyscfg.properties.PropertyBag(nisyscfg.properties.Filter)
@nisyscfg.properties.PropertyBag(nisyscfg.xnet.properties.Filter, expert="xnet")
class Filter(object):
    """Represents a NI System Configuration filter."""

    if TYPE_CHECKING:
        is_device: bool
        is_present: bool | nisyscfg.enums.IsPresentType
        is_ni_product: bool
        is_chassis: bool
        service_type: nisyscfg.enums.ServiceType
        connects_to_bus_type: nisyscfg.enums.BusType
        connects_to_link_name: str
        provides_bus_type: nisyscfg.enums.BusType
        vendor_id: int
        product_id: int
        serial_number: str
        is_simulated: bool
        slot_number: int
        has_driver: nisyscfg.enums.HasDriverType
        supports_calibration: bool
        supports_firmware_update: bool
        provides_link_name: str
        resource_name: str
        user_alias: str
        expert_name: str
        xnet: _XnetFilterProperties

    _handle: Optional["nisyscfg.types.FilterHandle"]

    def __init__(self, session: "nisyscfg.types.SessionHandle") -> None:
        """Initialize a hardware filter."""
        self._handle = nisyscfg.types.FilterHandle()
        self._library = _library_singleton.get()

        # PropertyAccessor is a typed class in nisyscfg.properties; construct it directly.
        self._property_accessor: PropertyAccessor = PropertyAccessor(
            setter=self._set_property_with_type
        )

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

        error_code = self._library.SetFilterPropertyWithType(self._handle, id, nisyscfg_type, value)
        nisyscfg.errors.handle_error(self, error_code)
