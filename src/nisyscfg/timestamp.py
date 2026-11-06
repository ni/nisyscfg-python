"""Timestamp conversion helpers for NI System Configuration."""

import ctypes
from typing import TYPE_CHECKING, Iterable

from hightime import datetime, timedelta

import nisyscfg
import nisyscfg._library_singleton
import nisyscfg.errors
import nisyscfg.types

# Type-only import for the C-style timestamp alias used by mypy
if TYPE_CHECKING:
    from typing import cast as _type_cast

    from nisyscfg.types import _TimestampUTCType

    def _cast_to_ts(v: object) -> "_TimestampUTCType":
        return _type_cast(_TimestampUTCType, v)

else:

    def _cast_to_ts(v: object):
        return v


# International Atomic Time epoch
tai_epoch = datetime(year=1970, month=1, day=1)


def is_blank_timestamp(timestamp: Iterable[int]) -> bool:
    """Return whether the timestamp contains only zero values."""
    return all(num == 0 for num in timestamp)


def _convert_ctype_to_datetime(timestamp: Iterable[int]) -> datetime:
    # This method returns 1 Jan 1904 if blank datetime is found(zero timestamp value).
    # Else it converts the timestamp to datetime and returns
    if is_blank_timestamp(timestamp):
        return datetime(year=1904, month=1, day=1)
    else:
        library = nisyscfg._library_singleton.get()
        seconds_since_tai_epoch = ctypes.c_uint64()
        fractional_seconds = ctypes.c_double()

        error_code = library.ValuesFromTimestamp(
            timestamp,
            ctypes.pointer(seconds_since_tai_epoch),
            ctypes.pointer(fractional_seconds),
        )
        nisyscfg.errors.handle_error(None, error_code, is_error_handling=True)

        return (
            tai_epoch
            + timedelta(seconds=seconds_since_tai_epoch.value)
            + timedelta(seconds=fractional_seconds.value)
        )


def _convert_datetime_to_ctype(timestamp: datetime) -> "_TimestampUTCType":
    if timestamp == datetime(year=1904, month=1, day=1):
        # Construct a ctypes array and return it. For static checking, wrap with
        # _cast_to_ts which is a no-op at runtime and a typed cast when TYPE_CHECKING.
        return _cast_to_ts(nisyscfg.types.TimestampUTC(0, 0, 0, 0))
    else:
        library = nisyscfg._library_singleton.get()

        time_since_tai_epoch = timestamp - tai_epoch
        seconds_since_tai_epoch = time_since_tai_epoch.days * 86400 + time_since_tai_epoch.seconds
        fractional_seconds = (
            (time_since_tai_epoch.microseconds / 10**6)
            + (time_since_tai_epoch.femtoseconds / 10**15)
            + (time_since_tai_epoch.yoctoseconds / 10**24)
        )
        timestamp_ctype = nisyscfg.types.TimestampUTC()

        error_code = library.TimestampFromValues(
            seconds_since_tai_epoch,
            fractional_seconds,
            ctypes.pointer(timestamp_ctype),
        )
        nisyscfg.errors.handle_error(None, error_code, is_error_handling=True)

        return _cast_to_ts(timestamp_ctype)
