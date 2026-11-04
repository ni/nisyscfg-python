"""Hardware resource access and management functionality."""

import ctypes
import typing
from functools import reduce
from typing import TYPE_CHECKING, Protocol

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

    import nisyscfg.pxi.enums
    import nisyscfg.xnet.enums

    class _XnetResourceProperties(Protocol):
        blink: nisyscfg.xnet.enums.Blink
        protocol: nisyscfg.xnet.enums.Protocol

    class _PxiResourceProperties(Protocol):
        fan_mode: nisyscfg.pxi.enums.FanModes
        power_supply_name: nisyscfg.properties.IndexedPropertyItems


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
        expert_name: nisyscfg.properties.IndexedPropertyItems
        provides_link_name: str
        current_time: hightime.datetime
        is_device: bool
        product_name: str
        temperature_name: nisyscfg.properties.IndexedPropertyItems
        temperature_reading: nisyscfg.properties.IndexedPropertyItems
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

        Raises:
            nisyscfg.errors.LibraryError: An error occurs while closing the
                resource.
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
            ctor = typing.cast(typing.Callable[[typing.Any], typing.Any], c_type)
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
            ctor = typing.cast(typing.Callable[[], typing.Any], c_type)
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
            ctor = typing.cast(typing.Callable[[typing.Any], typing.Any], c_type)
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
        # Preserve existing runtime behavior from main.
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

        Returns:
            nisyscfg.hardware_resource.SaveChangesResult: A result containing
                whether the changes require a restart and details of any errors.

        Raises:
            nisyscfg.errors.LibraryError: An error occurs while saving the
                changes.
        """
        restart_required = ctypes.c_int()
        details: typing.Optional[str] = ""
        error_code_2 = 0
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.SaveResourceChanges(
            self._handle, restart_required, ctypes.pointer(c_details)
        )
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(self, error_code_2)

        return SaveChangesResult(restart_required=restart_required.value != 0, details=details)

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
        details: typing.Optional[str] = ""
        error_code_2 = 0
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.SelfCalibrateHardware(self._handle, ctypes.pointer(c_details))
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(self, error_code_2)

        return details

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
        details: typing.Optional[str] = ""
        error_code_2 = 0
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.SelfTestHardware(self._handle, mode, ctypes.pointer(c_details))
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(self, error_code_2)

        return details

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
        details: typing.Optional[str] = ""
        error_code_2 = 0
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(self, error_code_2)

        return UpgradeFirmwareResult(
            status=nisyscfg.enums.FirmwareStatus(firmware_status.value), details=details
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
        details: typing.Optional[str] = ""
        error_code_2 = 0
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(self, error_code_2)

        return FirmwareStatusResult(
            percent_complete=percent_complete.value,
            status=nisyscfg.enums.FirmwareStatus(firmware_status.value),
            details=details,
        )

    def delete(
        self,
        mode: "nisyscfg.enums.DeleteValidationMode" = nisyscfg.enums.DeleteValidationMode.DELETE_IF_NO_DEPENDENCIES_EXIST,
    ) -> DeleteResult:
        """Permanently removes a hardware resource and its configuration data.

        Note: Not all devices can be deleted; consult your product documentation.

        Args:
            mode: Deletion conditions: ``VALIDATE_BUT_DO_NOT_DELETE`` checks
                whether deletion is allowed and whether dependencies exist;
                ``DELETE_IF_NO_DEPENDENCIES_EXIST`` deletes only when there
                are no dependencies; ``DELETE_ITEM_AND_ANY_DEPENDENCIES``
                deletes the resource and its dependencies; and
                ``DELETE_ITEM_BUT_KEEP_DEPENDENCIES`` deletes the resource but
                leaves dependencies unusable.

        Returns:
            nisyscfg.hardware_resource.DeleteResult: Whether dependent
                resources were deleted and details of any errors.

        Raises:
            nisyscfg.errors.LibraryError: If deleting the resource fails.
        """
        dependent_items_deleted = ctypes.c_int()
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.DeleteResource(
            self._handle, mode, dependent_items_deleted, ctypes.pointer(c_details)
        )
        details: typing.Optional[str] = ""
        error_code_2 = 0
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(self, error_code_2)

        return DeleteResult(
            dependent_items_deleted=dependent_items_deleted.value != 0, details=details
        )
