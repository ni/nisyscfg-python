from __future__ import absolute_import

import locale
import sys
from typing import Optional, Union, overload

if sys.platform.startswith("win"):
    # On Windows, nisyscfg uses the system code page for the decoding of C-strings
    def get_syscfg_locale() -> str:
        """Return the string encoding used to exchange text with NI System Configuration."""
        return locale.getlocale()[1] or locale.getdefaultlocale()[1] or "ascii"

else:
    # On other OSes, nisyscfg uses ISO-8859-1 (Latin1) for the decoding of C-strings
    def get_syscfg_locale() -> str:
        """Return the string encoding used to exchange text with NI System Configuration."""
        return "ISO-8859-1"


def c_string_encode(value: Optional[Union[str, bytes]]) -> Optional[bytes]:
    """Encode a Python string for use with the C API."""
    if isinstance(value, str):
        return value.encode(get_syscfg_locale())
    return value


@overload
def c_string_decode(value: None) -> None: ...


@overload
def c_string_decode(value: Union[bytes, str]) -> str: ...


def c_string_decode(value: Optional[Union[bytes, str]]) -> Optional[str]:
    """Decode a string returned by the C API."""
    if isinstance(value, bytes):
        return value.decode(get_syscfg_locale())
    return value
