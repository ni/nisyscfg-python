# This file is code generated
"""Enumeration definitions used by NI System Configuration."""

from enum import IntEnum, IntFlag
from typing import SupportsInt


class BaseEnum(IntEnum):
    """Base class for NI System Configuration enumerations."""

    @classmethod
    def from_param(cls: type["BaseEnum"], obj: SupportsInt | str) -> int:
        """Convert an enum value for use with ctypes."""
        return int(obj)


class BaseFlag(IntFlag):
    """Base class for NI System Configuration flag enumerations."""

    @classmethod
    def from_param(cls: type["BaseFlag"], obj: SupportsInt | str) -> int:
        """Convert a flag value for use with ctypes."""
        return int(obj)


class IncludeCachedResults(BaseEnum):
    """Options for including cached system discovery results."""

    NONE = 0
    ONLY_IF_ONLINE = 1
    ALL = 3


class SystemNameFormat(BaseEnum):
    """System name display formats."""

    HOSTNAME = 16
    HOSTNAME_IP = 18
    HOSTNAME_MAC = 19
    IP = 32
    IP_HOSTNAME = 33
    IP_MAC = 35
    MAC = 48
    MAC_HOSTNAME = 49
    MAC_IP = 50


class FileSystemMode(BaseEnum):
    """Supported file system modes."""

    DEFAULT = 0
    FAT = 1
    RELIANCE = 2
    UBIFS = 16384
    EXT4 = 32768


class NetworkInterfaceSettings(BaseEnum):
    """Network interface configuration options."""

    RESET_PRIMARY_RESET_OTHERS = 0
    PRESERVE_PRIMARY_RESET_OTHERS = 1
    PRESERVE_PRIMARY_PRESERVE_OTHERS = 2
    PRESERVE_PRIMARY_APPLY_OTHERS = 3
    APPLY_PRIMARY_RESET_OTHERS = 4
    APPLY_PRIMARY_PRESERVE_OTHERS = 5
    APPLY_PRIMARY_APPLY_OTHERS = 6


class ComponentType(BaseEnum):
    """Component classification types."""

    STANDARD = 0
    HIDDEN = 1
    SYSTEM = 2
    UNKNOWN = 3
    STARTUP = 4
    IMAGE = 5
    ESSENTIAL = 6


class IncludeComponentTypes(BaseEnum):
    """Component inclusion filter options."""

    ALL_VISIBLE = 0
    ALL_VISIBLE_AND_HIDDEN = 1
    ONLY_STANDARD = 2
    ONLY_STARTUP = 3


class VersionSelectionMode(BaseEnum):
    """Software version selection modes."""

    HIGHEST = 0
    EXACT = 1


class ImportMode(BaseEnum):
    """Configuration import modes."""

    MERGE_ITEMS = 0
    DELETE_CONFIG_FIRST = 1048576
    PRESERVE_CONFLICT_ITEMS = 2097152


class ReportType(BaseEnum):
    """Report output formats."""

    XML = 0
    HTML = 1
    TECHNICAL_SUPPORT_ZIP = 2


class BusType(BaseEnum):
    """Bus types for devices."""

    BUILT_IN = 0
    PCI_PXI = 1
    USB = 2
    GPIB = 3
    VXI = 4
    SERIAL = 5
    TCP_IP = 6
    COMPACT_RIO = 7
    SCXI = 8
    COMPACT_DAQ = 9
    SWITCH_BLOCK = 10
    SCC = 11
    FIRE_WIRE = 12
    ACCESSORY = 13
    CAN = 14
    SWITCH_BLOCK_DEVICE = 15


class HasDriverType(BaseEnum):
    """Types of driver availability."""

    UNKNOWN = -1
    NOT_INSTALLED = 0
    INSTALLED = 1


class IsPresentType(BaseEnum):
    """Types of device presence status."""

    INITIALIZING = -2
    UNKNOWN = -1
    NOT_PRESENT = 0
    PRESENT = 1


class IpAddressMode(BaseEnum):
    """IP address configuration modes."""

    STATIC = 1
    DHCP_OR_LINK_LOCAL = 2
    LINK_LOCAL_ONLY = 4
    DHCP_ONLY = 8


class Bool(BaseEnum):
    """Boolean values."""

    FALSE = 0
    TRUE = 1


class Locale(BaseEnum):
    """Supported locale identifiers."""

    DEFAULT = 0
    CHINESE_SIMPLIFIED = 2052
    ENGLISH = 1033
    FRENCH = 1036
    GERMAN = 1031
    JAPANESE = 1041
    KOREAN = 1042


class FilterMode(BaseEnum):
    """Filter matching modes."""

    MATCH_VALUES_ALL = 1
    MATCH_VALUES_ANY = 2
    MATCH_VALUES_NONE = 3
    ALL_PROPERTIES_EXIST = 4


class ServiceType(BaseEnum):
    """Service types for network discovery."""

    MDNS_NI_TCP = 0
    MDNS_NI_REALTIME = 1
    MDNS_NI_SYSAPI = 2
    MDNS_NI_HTTP = 3
    LOCAL_SYSTEM = 4
    LOCAL_NET_INTERFACE = 5
    LOCAL_TIME_KEEPER = 6
    LOCAL_TIME_SOURCE = 7
    MDNS_LXI = 8
    LOCAL_FPGA = 9


class AdapterType(BaseEnum):
    """Network adapter types."""

    ETHERNET = 1
    WLAN = 2


class AdapterMode(BaseEnum):
    """Network adapter modes."""

    DISABLED = 1
    TCP_IP_ETHERNET = 2
    DETERMINISTIC = 4
    ETHER_CAT = 8
    TCP_IP_WLAN = 32
    TCP_IP_ACCESS_POINT = 64


class LinkSpeed(BaseEnum):
    """Network link speeds."""

    NONE = 0
    AUTO = 1
    TEN_MEGABIT_HALF = 2
    TEN_MEGABIT_FULL = 4
    HUNDRED_MEGABIT_HALF = 8
    HUNDRED_MEGABIT_FULL = 16
    GIGABIT_HALF = 32
    GIGABIT_FULL = 64
    WLAN80211A = 131072
    WLAN80211B = 262144
    WLAN80211G = 524288
    WLAN80211N = 1048576
    WLAN80211N_5GHZ = 2097152


class PacketDetection(BaseEnum):
    """Packet detection methods."""

    NONE = 0
    LINE_INTERRUPT = 1
    POLLING = 2
    SIGNALED_INTERRUPT = 4


class ConnectionType(BaseEnum):
    """Wireless connection types."""

    NONE = 0
    INFRASTRUCTURE = 1
    AD_HOC = 2


class SecurityType(BaseEnum):
    """Wireless security types."""

    NONE = 0
    NOT_SUPPORTED = 1
    OPEN = 2
    WEP = 4
    WPA_PSK = 8
    WPA_EAP = 16
    WPA2_PSK = 32
    WPA2_EAP = 64


class EapType(BaseEnum):
    """EAP types for wireless security."""

    NONE = 0
    EAP_TLS = 1
    EAP_TTLS = 2
    EAP_FAST = 4
    LEAP = 8
    PEAP = 16


class FirmwareStatus(BaseEnum):
    """Firmware update status codes."""

    READY_PENDING_AUTO_RESTART = -4
    VERIFYING_NEW_IMAGE = -3
    WRITING_FLASHING_NEW_IMAGE = -2
    UPDATE_MODE_WAITING_FOR_IMAGE = -1
    CORRUPT_CANNOT_RUN = 0
    NONE_INSTALLED = 1
    INSTALLED_NORMAL_OPERATION = 2
    READY_PENDING_USER_RESTART = 3
    READY_PENDING_USER_ACTION = 4
    UPDATE_ATTEMPT_FAILED = 5


class DeleteValidationMode(BaseEnum):
    """Validation modes for deleting items from the configuration."""

    VALIDATE_BUT_DO_NOT_DELETE = -1
    DELETE_IF_NO_DEPENDENCIES_EXIST = 0
    DELETE_ITEM_AND_ANY_DEPENDENCIES = 1
    DELETE_ITEM_BUT_KEEP_DEPENDENCIES = 2


class AccessType(BaseEnum):
    """Access control modes."""

    LOCAL_ONLY = 0
    LOCAL_AND_REMOTE = 1


class LedState(BaseEnum):
    """LED state values."""

    OFF = 0
    SOLID_GREEN = 1
    SOLID_YELLOW = 2
    SOLID_RED = 16
    BLINKING_GREEN = 4
    BLINKING_YELLOW = 8
    BLINKING_RED = 32


class SwitchState(BaseEnum):
    """Switch state values."""

    DISABLED = 0
    ENABLED = 1


class FirmwareUpdateMode(BaseEnum):
    """Firmware update modes."""

    NONE = 0
    MANUAL = 1
    DRIVER_MANAGED = 2


class ModuleProgramMode(BaseEnum):
    """Module programming modes."""

    NONE = 0
    REALTIME_CPU = 1
    REALTIME_SCAN = 2
    LABVIEW_FPGA = 4


class PropertyType(BaseEnum):
    """Property data types."""

    BOOL = 1
    INT = 2
    UNSIGNED_INT = 3
    DOUBLE = 4
    STRING = 6
    TIMESTAMP = 7
