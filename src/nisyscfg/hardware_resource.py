"""Hardware resource access and management functionality."""

import ctypes
import typing
from functools import reduce
from typing import Protocol, TYPE_CHECKING

import nisyscfg.errors
import nisyscfg.properties
import nisyscfg.pxi.properties
import nisyscfg.timestamp
import nisyscfg.types
import nisyscfg.xnet.properties
from nisyscfg import _library_singleton
from nisyscfg._lib import c_string_decode, c_string_encode

if TYPE_CHECKING:

    import hightime

    import nisyscfg.enums
    import nisyscfg.pxi.enums
    import nisyscfg.xnet.enums

    class _XnetResourceProperties(Protocol):
        number_of_ports: int
        ip_stack_info_json: str
        ip_stack_info_text: str
        port_number: int
        protocol: nisyscfg.xnet.enums.Protocol
        can_termination_capability: nisyscfg.enums.Bool
        can_transceiver_capability: nisyscfg.xnet.enums.CanTransceiverCapability
        dongle_id: nisyscfg.xnet.enums.DongleId
        dongle_state: nisyscfg.xnet.enums.DongleState
        blink: nisyscfg.xnet.enums.Blink
        enet_mac_addr: str
        enet_ip_v4_addr: str
        enet_os_adapter_name: str
        enet_os_adapter_desc: str
        enet_link_speed: nisyscfg.xnet.enums.EnetLinkSpeed
        enet_sleep_capability: nisyscfg.xnet.enums.EnetSleepCapability
        enet_phy_power_mode: nisyscfg.xnet.enums.EnetPhyPowerMode
        enet_phy_state: nisyscfg.xnet.enums.EnetPhyState
        enet_port_mode: nisyscfg.xnet.enums.EnetPortMode
        enet_link_speed_configured: nisyscfg.xnet.enums.EnetLinkSpeed
        enet_jumbo_frames: nisyscfg.xnet.enums.EnetJumboFrames
        enet_interrupt_moderation: nisyscfg.xnet.enums.EnetInterruptModeration
        enet_sleep_capability_configured: nisyscfg.xnet.enums.EnetSleepCapability

    class _PxiResourceProperties(Protocol):
        pxi_chassis_number: int
        chassis_led_blink_pattern: int
        clk10_source: nisyscfg.pxi.enums.Clock10Sources
        external_clock_output_source: nisyscfg.pxi.enums.ExternalClockOutputSources
        internal_oscillator: nisyscfg.pxi.enums.InternalOscillators
        high_density_trig_port_count: int
        fan_mode: nisyscfg.pxi.enums.FanModes
        fan_user_rpm: int
        supported_fan_modes: nisyscfg.pxi.enums.FanModes
        fan_manual_rpm_lower_bound: int
        fan_manual_rpm_upper_bound: int
        cooling_profile: nisyscfg.pxi.enums.CoolingProfiles
        cooling_profile_source: nisyscfg.pxi.enums.CoolingProfileSource
        supported_cooling_profiles: nisyscfg.pxi.enums.CoolingProfiles
        enable_user_override_of_cooling_profile: bool
        power_supply_bay_count: int
        power_supplies_redundant: int
        inhibit_mode: nisyscfg.pxi.enums.InhibitModes
        supported_inhibit_modes: nisyscfg.pxi.enums.InhibitModes
        cal_ext_action: nisyscfg.pxi.enums.CalExtActions
        cal_ext_dac_value: int
        power_supply_name: nisyscfg.properties.IndexedPropertyItems
        power_supply_state: nisyscfg.properties.IndexedPropertyItems
        power_supply_power: nisyscfg.properties.IndexedPropertyItems
        power_supply_power_reading: nisyscfg.properties.IndexedPropertyItems
        power_supply_intake_temp: nisyscfg.properties.IndexedPropertyItems
        power_supply_power_line_frequency: nisyscfg.properties.IndexedPropertyItems
        trig_port_name: nisyscfg.properties.IndexedPropertyItems
        trig_port_state: nisyscfg.properties.IndexedPropertyItems
        trig_port_remove_device_alias: nisyscfg.properties.IndexedPropertyItems


class _NoDefault(object):
    pass


SaveChangesResult = typing.NamedTuple(
    "SaveChangesResult",
    [
        ("restart_required", bool),
        ("details", typing.Optional[str]),
    ],
)

UpgradeFirmwareResult = typing.NamedTuple(
    "UpgradeFirmwareResult",
    [
        ("status", nisyscfg.enums.FirmwareStatus),
        ("details", typing.Optional[str]),
    ],
)

FirmwareStatusResult = typing.NamedTuple(
    "FirmwareStatusResult",
    [
        ("percent_complete", int),
        ("status", nisyscfg.enums.FirmwareStatus),
        ("details", typing.Optional[str]),
    ],
)

DeleteResult = typing.NamedTuple(
    "DeleteResult",
    [
        ("dependent_items_deleted", bool),
        ("details", typing.Optional[str]),
    ],
)


class HardwareResourceIterator(object):
    """Iterates over hardware resources returned by a query."""

    def __init__(
        self,
        session: "nisyscfg.types.SessionHandle",
        handle: typing.Optional["nisyscfg.types.EnumResourceHandle"],
    ) -> None:
        """Initialize the hardware resource iterator."""
        self._children: list["HardwareResource"] = []
        self._session: "nisyscfg.types.SessionHandle" = session
        # Handle may be cleared by close(); make it Optional for typing.
        self._handle: typing.Optional["nisyscfg.types.EnumResourceHandle"] = handle
        self._library = _library_singleton.get()

    def __del__(self) -> None:
        """Release resources associated with the iterator."""
        self.close()

    def __iter__(self) -> "HardwareResourceIterator":
        """Return the iterator instance."""
        return self

    def __next__(self) -> "HardwareResource":
        """Return the next hardware resource."""
        if not self._handle:
            # TODO(tkrebes): raise RuntimeError
            raise StopIteration()
        resource_handle = nisyscfg.types.ResourceHandle()
        error_code = self._library.NextResource(
            self._session, self._handle, ctypes.pointer(resource_handle)
        )
        if error_code == nisyscfg.errors.Status.END_OF_ENUM:
            raise StopIteration()
        nisyscfg.errors.handle_error(self, error_code)
        resource = HardwareResource(resource_handle)
        self._children.append(resource)
        return resource

    def close(self) -> None:
        """Close the resource enumeration handle."""
        self._children.reverse()
        for child in self._children:
            child.close()
        if self._handle:
            error_code = self._library.CloseHandle(self._handle)
            nisyscfg.errors.handle_error(self, error_code)
            self._handle = None


@nisyscfg.properties.PropertyBag(nisyscfg.properties.Resource, nisyscfg.properties.IndexedResource)
@nisyscfg.properties.PropertyBag(
    nisyscfg.pxi.properties.Resource,
    nisyscfg.pxi.properties.IndexedResource,
    expert="pxi",
)
@nisyscfg.properties.PropertyBag(nisyscfg.xnet.properties.Resource, expert="xnet")
class HardwareResource(object):
    """Represents a hardware resource managed by NI System Configuration."""

    if TYPE_CHECKING:
        is_device: bool
        is_chassis: bool
        connects_to_bus_type: nisyscfg.enums.BusType
        vendor_id: int
        vendor_name: str
        product_id: int
        product_name: str
        serial_number: str
        firmware_revision: str
        is_ni_product: bool
        is_simulated: bool
        connects_to_link_name: str
        has_driver: nisyscfg.enums.HasDriverType
        is_present: nisyscfg.enums.IsPresentType
        slot_number: int
        supports_internal_calibration: bool
        internal_calibration_last_time: hightime.datetime
        internal_calibration_last_temp: float
        supports_external_calibration: bool
        external_calibration_last_temp: float
        calibration_comments: str
        internal_calibration_last_limited: bool
        external_calibration_checksum: str
        current_temp: float
        pxi_pci_bus_number: int
        pxi_pci_device_number: int
        pxi_pci_function_number: int
        pxi_pci_link_width: int
        pxi_pci_max_link_width: int
        usb_interface: int
        tcp_host_name: str
        tcp_mac_address: str
        tcp_ip_address: str
        tcp_device_class: str
        gpib_primary_address: int
        gpib_secondary_address: int
        serial_port_binding: str
        provides_bus_type: nisyscfg.enums.BusType
        provides_link_name: str
        number_of_slots: int
        supports_firmware_update: bool
        firmware_file_pattern: str
        recommended_calibration_interval: int
        supports_calibration_write: bool
        hardware_revision: str
        cpu_model_name: str
        cpu_stepping_revision: int
        model_name_number: int
        module_program_mode: nisyscfg.enums.ModuleProgramMode
        connects_to_num_slots: int
        slot_offset_left: int
        internal_calibration_values_in_range: bool
        firmware_update_mode: nisyscfg.enums.FirmwareUpdateMode
        external_calibration_last_time: hightime.datetime
        recommended_next_calibration_time: hightime.datetime
        external_calibration_last_limited: bool
        calibration_current_password: str
        calibration_new_password: str
        system_configuration_web_access: nisyscfg.enums.AccessType
        adapter_type: nisyscfg.enums.AdapterType
        mac_address: str
        adapter_mode: nisyscfg.enums.AdapterMode
        tcp_ip_request_mode: nisyscfg.enums.IpAddressMode
        tcp_ip_v4_address: str
        tcp_ip_v4_subnet: str
        tcp_ip_v4_gateway: str
        tcp_ip_v4_dns_server: str
        tcp_preferred_link_speed: nisyscfg.enums.LinkSpeed
        tcp_current_link_speed: nisyscfg.enums.LinkSpeed
        tcp_packet_detection: nisyscfg.enums.PacketDetection
        tcp_polling_interval: int
        is_primary_adapter: bool
        ether_cat_master_id: int
        ether_cat_master_redundancy: bool
        wlan_bssid: str
        wlan_current_link_quality: int
        wlan_current_ssid: str
        wlan_current_connection_type: nisyscfg.enums.ConnectionType
        wlan_current_security_type: nisyscfg.enums.SecurityType
        wlan_current_eap_type: nisyscfg.enums.EapType
        wlan_country_code: int
        wlan_channel_number: int
        wlan_client_certificate: str
        wlan_security_identity: str
        wlan_security_key: str
        system_start_time: hightime.datetime
        current_time: hightime.datetime
        time_zone: str
        user_directed_safe_mode_switch: bool
        console_out_switch: bool
        ip_reset_switch: bool
        number_of_discovered_access_points: int
        number_of_experts: int
        number_of_services: int
        number_of_available_firmware_versions: int
        number_of_cpus: int
        number_of_fans: int
        number_of_power_sensors: int
        number_of_temperature_sensors: int
        number_of_voltage_sensors: int
        number_of_user_led_indicators: int
        number_of_user_switches: int
        service_type: nisyscfg.properties.IndexedPropertyItems
        available_firmware_version: nisyscfg.properties.IndexedPropertyItems
        wlan_available_ssid: nisyscfg.properties.IndexedPropertyItems
        wlan_available_bssid: nisyscfg.properties.IndexedPropertyItems
        wlan_available_connection_type: nisyscfg.properties.IndexedPropertyItems
        wlan_available_security_type: nisyscfg.properties.IndexedPropertyItems
        wlan_available_link_quality: nisyscfg.properties.IndexedPropertyItems
        wlan_available_channel_number: nisyscfg.properties.IndexedPropertyItems
        wlan_available_link_speed: nisyscfg.properties.IndexedPropertyItems
        cpu_total_load: nisyscfg.properties.IndexedPropertyItems
        cpu_interrupt_load: nisyscfg.properties.IndexedPropertyItems
        cpu_speed: nisyscfg.properties.IndexedPropertyItems
        fan_name: nisyscfg.properties.IndexedPropertyItems
        fan_reading: nisyscfg.properties.IndexedPropertyItems
        power_name: nisyscfg.properties.IndexedPropertyItems
        power_reading: nisyscfg.properties.IndexedPropertyItems
        power_upper_critical: nisyscfg.properties.IndexedPropertyItems
        temperature_name: nisyscfg.properties.IndexedPropertyItems
        temperature_reading: nisyscfg.properties.IndexedPropertyItems
        temperature_lower_critical: nisyscfg.properties.IndexedPropertyItems
        temperature_upper_critical: nisyscfg.properties.IndexedPropertyItems
        voltage_name: nisyscfg.properties.IndexedPropertyItems
        voltage_reading: nisyscfg.properties.IndexedPropertyItems
        voltage_nominal: nisyscfg.properties.IndexedPropertyItems
        voltage_lower_critical: nisyscfg.properties.IndexedPropertyItems
        voltage_upper_critical: nisyscfg.properties.IndexedPropertyItems
        user_led_name: nisyscfg.properties.IndexedPropertyItems
        user_switch_name: nisyscfg.properties.IndexedPropertyItems
        user_switch_state: nisyscfg.properties.IndexedPropertyItems
        user_led_state: nisyscfg.properties.IndexedPropertyItems
        expert_name: nisyscfg.properties.IndexedPropertyItems
        expert_resource_name: nisyscfg.properties.IndexedPropertyItems
        expert_user_alias: nisyscfg.properties.IndexedPropertyItems
        pxi: _PxiResourceProperties
        xnet: _XnetResourceProperties

    def __init__(self, handle: "nisyscfg.types.ResourceHandle") -> None:
        """Initialize the hardware resource wrapper."""
        self._handle: typing.Optional["nisyscfg.types.ResourceHandle"] = handle
        self._library = _library_singleton.get()
        self._property_accessor: "nisyscfg.properties.PropertyAccessor" = (
            nisyscfg.properties.PropertyAccessor(
                setter=self._set_property,
                getter=self._get_property,
                indexed_getter=self._get_indexed_property,
            )
        )

    def __del__(self) -> None:
        """Release the hardware resource handle."""
        self.close()

    def __repr__(self) -> str:
        """Return a string representation of the hardware resource."""
        return "HardwareResource(name={})".format(self.name)

    @property
    def name(self) -> str:
        """Returns a name that identifies a resource."""
        # PropertyBag dynamically adds indexed properties as attributes on
        # instances (e.g., expert_user_alias, expert_resource_name). Statically
        # annotate these two attributes here so mypy recognizes them.
        # They behave like nisyscfg.properties.IndexedPropertyItems at runtime.
        self.expert_user_alias: "nisyscfg.properties.IndexedPropertyItems"
        self.expert_resource_name: "nisyscfg.properties.IndexedPropertyItems"

        name = self.expert_user_alias[0]
        # If the resource doesn't have an alias, use the resource name instead
        if not name:
            name = self.expert_resource_name[0]
        return typing.cast(str, name)

    def close(self) -> None:
        """Closes reference to previously allocated resource.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        if self._handle:
            error_code = self._library.CloseHandle(self._handle)
            nisyscfg.errors.handle_error(self, error_code)
            self._handle = None

    def _get_property(self, id: int, c_type: type) -> typing.Any:
        # value/value_arg are C-interop temporaries.
        # use Any to avoid narrow mypy inference across branches.
        value: typing.Any
        value_arg: typing.Any
        if c_type == ctypes.c_char_p:
            value = nisyscfg.types.simple_string()
            value_arg = value
        elif issubclass(c_type, nisyscfg.enums.BaseEnum) or issubclass(
            c_type, nisyscfg.enums.BaseFlag
        ):
            value = ctypes.c_int()
            value_arg = ctypes.pointer(value)
        else:
            ctor = typing.cast("typing.Callable[[typing.Any], typing.Any]", c_type)
            value = ctor(0)
            value_arg = ctypes.pointer(value)

        error_code = self._library.GetResourceProperty(self._handle, id, value_arg)
        nisyscfg.errors.handle_error(self, error_code)

        if issubclass(c_type, nisyscfg.enums.BaseEnum) or issubclass(
            c_type, nisyscfg.enums.BaseFlag
        ):
            return c_type(value.value)

        if c_type == nisyscfg.types.TimestampUTC:
            return nisyscfg.timestamp._convert_ctype_to_datetime(value)

        return c_string_decode(value.value)

    def _get_indexed_property(
        self,
        id: int,
        index: int,
        c_type: typing.Any,
    ) -> typing.Any:
        value: typing.Any
        value_arg: typing.Any

        if c_type == ctypes.c_char_p:
            value = nisyscfg.types.simple_string()
            value_arg = value
        elif issubclass(c_type, nisyscfg.enums.BaseEnum) or issubclass(
            c_type, nisyscfg.enums.BaseFlag
        ):
            value = ctypes.c_int()
            value_arg = ctypes.pointer(value)
        else:
            ctor = typing.cast("typing.Callable[[], typing.Any]", c_type)
            value = ctor()
            value_arg = ctypes.pointer(value)

        error_code = self._library.GetResourceIndexedProperty(
            self._handle,
            id,
            index,
            value_arg,
        )
        nisyscfg.errors.handle_error(self, error_code)

        if issubclass(c_type, nisyscfg.enums.BaseEnum) or issubclass(
            c_type, nisyscfg.enums.BaseFlag
        ):
            enum_value = typing.cast(ctypes.c_int, value)
            return c_type(enum_value.value)

        if c_type == nisyscfg.types.TimestampUTC:
            return nisyscfg.timestamp._convert_ctype_to_datetime(value)

        return c_string_decode(value.value)

    def get_property(self, name: str, default: typing.Any = _NoDefault()) -> typing.Any:
        """Returns value of hardware resource property.

        Return the value for hardware resource property specified by the name,
        else default. If default is not given and the property does not exist,
        this function raises an nisyscfg.errors.LibraryError exception.
        """
        try:
            return reduce(getattr, name.split("."), self)
        except nisyscfg.errors.LibraryError as err:
            if err.code != nisyscfg.errors.Status.PROP_DOES_NOT_EXIST or isinstance(
                default, _NoDefault
            ):
                raise
            return default

    def _set_property(self, id: int, value: typing.Any, c_type: type, nisyscfg_type: int) -> None:
        if c_type == ctypes.c_char_p:
            value = c_string_encode(value)
        elif issubclass(c_type, nisyscfg.enums.BaseEnum) or issubclass(
            c_type, nisyscfg.enums.BaseFlag
        ):
            value = ctypes.c_int(value)
        elif c_type == nisyscfg.types.TimestampUTC:
            value = nisyscfg.timestamp._convert_datetime_to_ctype(value)
        else:
            ctor = typing.cast("typing.Callable[[typing.Any], typing.Any]", c_type)
            value = ctor(value)

        error_code = self._library.SetResourceProperty(self._handle, id, value)
        nisyscfg.errors.handle_error(self, error_code)

    def rename(
        self, new_name: str, overwrite_conflict: bool = False, update_dependencies: bool = False
    ) -> typing.Optional["HardwareResource"]:
        """Changes the display name of a resource.

        new_name - The user-specified new name for the resource.

        overwrite_conflict - Allows resource name changes to occur if there are
        any naming conflicts. If this value is True, the resource name change
        occurs even if another resource with the same name already exists. If
        this value is False (default), this function raises if another resource
        with the same name already exists. If this value is True and you choose
        a name that is already assigned to an existing resource, this function
        also changes the name of the existing resource.

        update_dependencies - Updates dependencies (for example: a task or
        channel) if the resource being renamed has them. Dependencies will be
        updated to refer to the new name by default. Select FALSE if you do not
        want to update these dependencies.
        Note: If overwrite_conflict is True and an existing resource was also
        renamed due to a conflict, the dependencies for that resource will not
        be updated. This option only affects the dependencies for the resource
        you are currently renaming.

        Returns HardwareResource whose name was overwritten. This will be None
        if no other resource was overwritten.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        name_already_existed = ctypes.c_int()
        overwritten_resource_handle = nisyscfg.types.ResourceHandle()
        error_code = self._library.RenameResource(
            self._handle,
            c_string_encode(new_name),
            overwrite_conflict,
            update_dependencies,
            ctypes.pointer(name_already_existed),
            ctypes.pointer(overwritten_resource_handle),
        )
        nisyscfg.errors.handle_error(self, error_code)

        # TODO(tkrebes): Ensure lifetime of HardwareResource does not exceed the
        # session.
        overwritten_resource = overwritten_resource_handle.value and HardwareResource(
            overwritten_resource_handle
        )

        # Do not return the bool 'name_already_existed' since it is equivalent
        # to 'overwritten_syscfg_resource == None'.
        return typing.cast(typing.Optional["HardwareResource"], overwritten_resource)

    def reset(self, mode: int = 0) -> None:
        """Executes a reset on a specified resource.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        error_code = self._library.ResetHardware(self._handle, mode)
        nisyscfg.errors.handle_error(self, error_code)

    def save_changes(self) -> SaveChangesResult:
        """Writes and saves property changes on a device.

        Returns tuple (restart_required, details)

            restart_required - Specifies whether the changes require a reboot.
            If True, call restart.

            details - A string containing results of any errors
            that may have occurred during execution.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        restart_required = ctypes.c_int()
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.SaveResourceChanges(
            self._handle, restart_required, ctypes.pointer(c_details)
        )
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(
            self, error_code_2  # pyright: ignore[reportPossiblyUnboundVariable]
        )

        return SaveChangesResult(
            restart_required=restart_required.value != 0,
            details=details,  # pyright: ignore[reportPossiblyUnboundVariable]
        )

    def self_calibrate(self) -> typing.Optional[str]:
        """Performs a self-calibration on a device.

        Self-calibration adjusts the calibration constants with respect to an
        onboard reference stored on the device. The new calibration constants
        are defined with respect to the calibration constants created during an
        external calibration to ensure that the measurements are traceable to
        these external standards. The new calibration constants do not affect
        the constants created during an external calibration because they are
        stored in a different area of the device memory. You can perform a self-
        calibration at any time to adjust the device for use in environments
        other than those in which the device was externally calibrated.

        Returns a string containing results of any errors that may have occurred
        during execution.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.SelfCalibrateHardware(self._handle, ctypes.pointer(c_details))
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(
            self, error_code_2  # pyright: ignore[reportPossiblyUnboundVariable]
        )

        return details  # pyright: ignore[reportPossiblyUnboundVariable]

    def self_test(self, mode: int = 0) -> typing.Optional[str]:
        """Verifies that system devices are able to perform basic I/O functions.

        No other tasks should run on the system while executing the self test
        because the driver may need exclusive access to some device resources.
        You do not need to disconnect devices from external equipment because
        the state of I/O lines are maintained throughout the test.

        mode - Reserved. This must be 0.

        Returns a string containing results of any errors that may have occurred
        during execution.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.SelfTestHardware(self._handle, mode, ctypes.pointer(c_details))
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(
            self, error_code_2  # pyright: ignore[reportPossiblyUnboundVariable]
        )

        return details  # pyright: ignore[reportPossiblyUnboundVariable]

    def upgrade_firmware(
        self,
        version: typing.Optional[str] = None,
        filepath: typing.Optional[str] = None,
        auto_stop_task: bool = True,
        force: bool = False,
        sync_call: bool = True,
    ) -> UpgradeFirmwareResult:
        """Updates the firmware on the target.

        version - Specifies the firmware version you want to apply to the
        target. Use '0' to install the latest available firmware.

        filepath - Specifies the firmware file you want to upload to the target.

        Note: Parameters version and filepath are mutually exclusive and you
        must specify one and only one.

        auto_stop_task - Specifies to automatically end all tasks running on the
        target, even if they are incomplete and switch to firmware update mode.
        The default is True.

        force - Specifies to overwrite the destination firmware image even if
        the version is the same as or older than the version of the destination
        firmware image. If False, the function checks the version of the
        firmware returned by the expert and, if the returned version is newer
        than the version you are upgrading, this function returns an error. If
        the firmware version is the same and this parameter is set to False, the
        function does not upgrade the firmware and returns success. If True,
        this function automatically upgrades the firmware, regardless of the
        version of the destination firmware image. The default is False.

        sync_call - Specifies whether to wait for the upgrade operation to
        finish before returning. If False, the upgrade operation may continue
        running even after this function returns. To check the status, query
        the firmware_status property. The default is True.

        Returns tuple (status, details)

            status - The status of the firmware update. If this output returns
            FirmwareStatus.READY_PENDING_USER_RESTART, call restart. You can
            view more information about additional results in the details
            output.

            details - Results of any errors that may have occurred when
            this function completed. This output also may return additional
            information about the value returned from status.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        if version and filepath:
            raise ValueError("version and filepath are mutually exclusive parameters")

        firmware_status = ctypes.c_int()
        c_details = ctypes.POINTER(ctypes.c_char)()
        if version:
            error_code = self._library.UpgradeFirmwareVersion(
                self._handle,
                c_string_encode(version),
                auto_stop_task,
                force,
                sync_call,
                ctypes.pointer(firmware_status),
                ctypes.pointer(c_details),
            )
        elif filepath:
            error_code = self._library.UpgradeFirmwareFromFile(
                self._handle,
                c_string_encode(filepath),
                auto_stop_task,
                force,
                sync_call,
                ctypes.pointer(firmware_status),
                ctypes.pointer(c_details),
            )
        else:
            raise ValueError(
                "upgrade_firmware() requires either version or filepath to be specified"
            )
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(
            self, error_code_2  # pyright: ignore[reportPossiblyUnboundVariable]
        )

        return UpgradeFirmwareResult(
            status=nisyscfg.enums.FirmwareStatus(firmware_status.value),
            details=details,  # pyright: ignore[reportPossiblyUnboundVariable]
        )

    @property
    def firmware_status(self) -> FirmwareStatusResult:
        """Returns the status of the firmware upgrade in progress.

        Returns tuple (percent_complete, status, details)

            percent_complete - The status, in percent, of the current step in
            the firmware upgrade. This parameter returns -1 if there is no
            firmware update in progress.

            status - The status of the firmware update. If this output
            returns FirmwareStatus.READY_PENDING_USER_RESTART, call restart. You
            can view more information about additional results in the details
            output.

            details - Results of any errors that may have occurred when this
            function completed. This output also may return additional
            information about the value returned from status.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        percent_complete = ctypes.c_int()
        firmware_status = ctypes.c_int()
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.CheckFirmwareStatus(
            self._handle, percent_complete, firmware_status, ctypes.pointer(c_details)
        )
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(
            self, error_code_2  # pyright: ignore[reportPossiblyUnboundVariable]
        )

        return FirmwareStatusResult(
            percent_complete=percent_complete.value,
            status=nisyscfg.enums.FirmwareStatus(firmware_status.value),
            details=details,  # pyright: ignore[reportPossiblyUnboundVariable]
        )

    def delete(
        self,
        mode: "nisyscfg.enums.DeleteValidationMode" = nisyscfg.enums.DeleteValidationMode.DELETE_IF_NO_DEPENDENCIES_EXIST,
    ) -> DeleteResult:
        """Permanently removes a hardware resource and its configuration data.

        Note: Not all devices can be deleted; consult your product documentation.

        mode - Specifies the conditions under which to delete the specified
        resource.
        ================================= ======================================
        Mode                              Description
        --------------------------------- --------------------------------------
        VALIDATE_BUT_DO_NOT_DELETE        Verify whether the resource can be
                                          deleted and whether it has
                                          dependencies.
        DELETE_IF_NO_DEPENDENCIES_EXIST   Delete the resource only if no
                                          dependencies exist. These could be
                                          tasks or child resources.
        DELETE_ITEM_AND_ANY_DEPENDENCIES  Delete this resource. If any
                                          dependencies exist, delete them too.
        DELETE_ITEM_BUT_KEEP_DEPENDENCIES Delete this resource. If any
                                          dependencies exist, leave them in an
                                          unusable state.
        ================================= ======================================

        Returns tuple (dependent_items_deleted, details)

            dependent_items_deleted - Returns whether resources other than the
            specified one were deleted. For example, this may happen if the
            resource is a simulated chassis that contained modules.

            details - A string containing results of any errors that may
            have occurred during execution.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        dependent_items_deleted = ctypes.c_int()
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.DeleteResource(
            self._handle, mode, dependent_items_deleted, ctypes.pointer(c_details)
        )
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(
            self, error_code_2  # pyright: ignore[reportPossiblyUnboundVariable]
        )

        return DeleteResult(
            dependent_items_deleted=dependent_items_deleted.value != 0,
            details=details,  # pyright: ignore[reportPossiblyUnboundVariable]
        )
