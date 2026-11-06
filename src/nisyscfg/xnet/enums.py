"""XNET-specific enumeration definitions for NI System Configuration."""

from nisyscfg.enums import BaseEnum


class EnetPortMode(BaseEnum):
    """Ethernet port operating modes."""

    DIRECT = 0
    TAP = 1


class EnetPhyState(BaseEnum):
    """Ethernet PHY state configuration options."""

    SLAVE = 0
    MASTER = 1
    AUTO = 2


class Blink(BaseEnum):
    """Blink state options."""

    DISABLE = 0
    ENABLE = 1


class Protocol(BaseEnum):
    """Supported communication protocols."""

    CAN = 0
    FLEXRAY = 1
    LIN = 2
    ETHERNET = 3
    UNKNOWN = 0xFFFFFFFE


class CanTransceiverCapability(BaseEnum):
    """CAN transceiver capability types."""

    HS = 0
    LS = 1
    XS = 3
    XS_WITH_HS_OR_LS = 4
    UNKNOWN = 0xFFFFFFFF


class DongleId(BaseEnum):
    """Supported XNET dongle identifiers."""

    LS_CAN = 1
    HS_CAN = 2
    SW_CAN = 3
    XS_CAN = 4
    LIN = 6
    DONGLELESS_DESIGN = 13
    UNKNOWN = 14


class DongleState(BaseEnum):
    """XNET dongle status values."""

    NO_DONGLE_NO_EXTERNAL_POWER = 1
    NO_DONGLE_HAS_EXTERNAL_POWER = 2
    HAS_DONGLE_NO_EXTERNAL_POWER = 3
    READY = 4
    BUSY = 5
    COMM_ERROR = 13
    OVERCURRENT = 14


class EnetLinkSpeed(BaseEnum):
    """Ethernet link speed values."""

    LINK_DOWN = 0
    HUNDRED_MEGABIT = 1
    GIGABIT = 2


class EnetJumboFrames(BaseEnum):
    """Ethernet jumbo frame support values."""

    DISABLE = 0
    ENABLE_9018_BYTES = 1


class EnetInterruptModeration(BaseEnum):
    """Ethernet interrupt moderation values."""

    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class EnetSleepCapability(BaseEnum):
    """Ethernet sleep capability values."""

    DISABLED_OR_NOT_AVAILABLE = 0
    ENABLED = 1


class EnetPhyPowerMode(BaseEnum):
    """Ethernet PHY power modes."""

    NORMAL = 0
    SLEEP = 1
