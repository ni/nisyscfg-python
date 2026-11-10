import ctypes
import platform
import threading
from typing import Any, Dict, Optional

from nisyscfg import _library, errors


class CTypesLibrary(object):
    """Wrap ctypes library instances used by NI System Configuration."""

    def __init__(self, cdll: Any, windll: Optional[Any] = None) -> None:
        """Initialize the ctypes library wrapper."""
        self._cdll: Any = cdll
        self._windll: Optional[Any] = windll
        if self._windll is None:
            self._windll = self._cdll

    @property
    def cdll(self) -> Any:
        """Return the loaded CDLL instance."""
        return self._cdll

    @property
    def windll(self) -> Any:
        """Return the loaded WinDLL instance."""
        return self._windll


_instance: Optional[_library.Library] = None
_instance_lock = threading.Lock()
_library_info: Dict[str, Dict[str, Dict[str, str]]] = {
    "Linux": {"64bit": {"name": "libnisyscfg.so", "type": "cdll"}},
    "Windows": {
        "32bit": {"name": "nisyscfg.dll", "type": "dual"},
        "64bit": {"name": "nisyscfg.dll", "type": "cdll"},
    },
}


def _get_library_name() -> str:
    try:
        return _library_info[platform.system()][platform.architecture()[0]]["name"]
    except KeyError:
        raise errors.UnsupportedPlatformError


def _get_library_type() -> str:
    try:
        return _library_info[platform.system()][platform.architecture()[0]]["type"]
    except KeyError:
        raise errors.UnsupportedPlatformError


def get() -> _library.Library:
    """Return the singleton NI System Configuration library instance."""
    global _instance

    with _instance_lock:
        if _instance is None:
            try:
                library_type = _get_library_type()
                if library_type == "dual":
                    ctypes_library = CTypesLibrary(
                        ctypes.CDLL(_get_library_name(), ctypes.RTLD_GLOBAL),
                        ctypes.WinDLL(_get_library_name()),  # type: ignore[attr-defined]
                    )
                else:
                    assert library_type == "cdll"
                    ctypes_library = CTypesLibrary(
                        ctypes.CDLL(_get_library_name(), ctypes.RTLD_GLOBAL)
                    )
            except OSError:
                raise errors.LibraryNotInstalledError()
            _instance = _library.Library(ctypes_library)
    return _instance
