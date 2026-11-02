"""Software component information and enumeration helpers."""

import ctypes
import typing
from typing import Any, Optional

import nisyscfg._library_singleton
import nisyscfg.enums
import nisyscfg.errors
from nisyscfg._lib import c_string_decode, c_string_encode

ComponentInfo = typing.NamedTuple(
    "ComponentInfo",
    [
        ("id", str),
        ("version", str),
        ("title", str),
        ("type", nisyscfg.enums.ComponentType),
        ("details", typing.Optional[str]),
    ],
)


class ComponentInfoIterator(object):
    """Iterates over software component information."""

    def __init__(self, handle: Optional[Any]) -> None:
        """Initialize the iterator with a component enumeration handle."""
        self._handle: Optional[Any] = handle
        # _library is untyped at runtime; keep the type as Any to avoid
        # leaking implementation details while satisfying type checking.
        self._library: Any = nisyscfg._library_singleton.get()

    def __del__(self) -> None:
        """Release resources associated with the iterator."""
        self.close()

    def __iter__(self) -> "ComponentInfoIterator":
        """Return the iterator instance."""
        return self

    def __next__(self) -> ComponentInfo:
        """Return the next software component."""
        if not self._handle:
            raise StopIteration()
        id = nisyscfg.types.simple_string()
        version = nisyscfg.types.simple_string()
        title = nisyscfg.types.simple_string()
        item_type = ctypes.c_int()
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.NextComponentInfo(
            self._handle, id, version, title, ctypes.pointer(item_type), c_details
        )
        if error_code == nisyscfg.errors.Status.END_OF_ENUM:
            raise StopIteration()
        nisyscfg.errors.handle_error(self, error_code)

        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code = self._library.FreeDetailedString(c_details)
            nisyscfg.errors.handle_error(self, error_code)
        else:
            details = None

        return ComponentInfo(
            id=c_string_decode(id.value),
            version=c_string_decode(version.value),
            title=c_string_decode(title.value),
            type=nisyscfg.enums.ComponentType(item_type.value),
            details=details,
        )

    def close(self) -> None:
        """Close the component enumeration handle."""
        if self._handle:
            error_code = self._library.CloseHandle(self._handle)
            nisyscfg.errors.handle_error(self, error_code)
            self._handle = None


class EnumSoftwareComponent(object):
    """Represents a software component enumeration."""

    def __init__(self) -> None:
        """Create a new software component enumeration."""
        # EnumSoftwareComponentHandle is a ctypes.c_void_p alias; allow None
        # to be stored when the handle is closed by typing as Optional.
        self._handle: typing.Optional[ctypes.c_void_p] = (
            nisyscfg.types.EnumSoftwareComponentHandle()
        )
        # _library is untyped at runtime; keep the type as Any to avoid
        # leaking implementation details while satisfying type checking.
        self._library: Any = nisyscfg._library_singleton.get()
        error_code = self._library.CreateComponentsEnum(ctypes.pointer(self._handle))
        nisyscfg.errors.handle_error(self, error_code)

    def __del__(self) -> None:
        """Release resources associated with the enumeration."""
        self.close()

    def close(self) -> None:
        """Close the software component enumeration."""
        if self._handle:
            error_code = self._library.CloseHandle(self._handle)
            nisyscfg.errors.handle_error(self, error_code)
            self._handle = None

    def add_component(
        self,
        id: str,
        version: str = "",
        mode: nisyscfg.enums.VersionSelectionMode = nisyscfg.enums.VersionSelectionMode.HIGHEST,
    ) -> None:
        """Adds a software component.

        id - ID of the software component to be added to the enumeration.

        version - Desired version of the software component being added to the
        enumeration. This field is optional as long as the version selection
        mode is set to Highest.

        mode - Choose whether an exact version or the highest version of the
        software component specified by id should be added to the enumeration.

        Raises an nisyscfg.errors.LibraryError exception in the event of an error.
        """
        error_code = self._library.AddComponentToEnum(
            self._handle,
            c_string_encode(id),
            c_string_encode(version),
            mode,
        )
        nisyscfg.errors.handle_error(self, error_code)
