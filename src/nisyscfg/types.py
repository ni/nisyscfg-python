# This file is code generated
"""Generated ctypes aliases and handle types for NI System Configuration."""

import ctypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Tuple, TypeAlias

    # Statically, expose a private alias for timestamp values. Use a private
    # name so runtime code can still call the ctypes constructor named
    # `TimestampUTC` without mypy thinking it's the type alias.
    _TimestampUTCType: TypeAlias = Tuple[int, int, int, int]

simple_string = ctypes.c_char * 1024

UInt64 = ctypes.c_ulonglong
ResourceHandle = ctypes.c_void_p
EnumResourceHandle = ctypes.c_void_p
EnumSoftwareFeedHandle = ctypes.c_void_p
SessionHandle = ctypes.c_void_p
# At runtime, TimestampUTC must be the ctypes array type used by the C API.
# Statically we use a Tuple[int, int, int, int], but at runtime the C API
# expects a ctypes array. Silence the type-checker for the runtime assignment.
TimestampUTC = ctypes.c_uint * 4
EnumSoftwareComponentHandle = ctypes.c_void_p
EnumDependencyHandle = ctypes.c_void_p
SoftwareSetHandle = ctypes.c_void_p
FilterHandle = ctypes.c_void_p
EnumExpertHandle = ctypes.c_void_p
EnumSystemHandle = ctypes.c_void_p
EnumSoftwareSetHandle = ctypes.c_void_p
