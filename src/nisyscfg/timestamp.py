"""Timestamp conversion helpers for NI System Configuration."""

import ctypes
from typing import Iterable

from hightime import datetime, timedelta

import nisyscfg
import nisyscfg._library_singleton
import nisyscfg.errors
import nisyscfg.types

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


def _convert_datetime_to_ctype(timestamp: datetime) -> ctypes.Array[ctypes.c_uint]:
    """Convert a hightime.datetime to a TimestampUTC ctypes array."""
    if timestamp == datetime(year=1904, month=1, day=1):
        return nisyscfg.types.TimestampUTC(0, 0, 0, 0)

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

    return timestamp_ctype
