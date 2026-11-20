# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased
- Added
  - Python 3.14, Python 3.14 free-threaded (3.14t), and Python 3.15 support.
  - Type checking support, including type annotations and .pyi type stubs.
- Changed
- Removed
  - Python 3.9 and Python 3.10 support.
  - The six dependency.

## 0.2.1
- Fixed
  - [Corrected the types of filter enums](https://github.com/tkrebes/nisyscfg-python/pull/68).

## 0.2.0
- Added
  - [`LedState.SOLID_RED` and `LedState.BLINKING_RED`, introduced in NI System Configuration 24.8](https://github.com/tkrebes/nisyscfg-python/pull/60).
  - [`set_system_image` function to system session](https://github.com/tkrebes/nisyscfg-python/pull/62).
- Changed
  - [Raised the minimum supported Python version to 3.9 and added Python 3.12 and 3.13 support](https://github.com/tkrebes/nisyscfg-python/pull/63).

## 0.1.1
- Fixed
  - [Library loading on Linux](https://github.com/tkrebes/nisyscfg-python/pull/58).

## 0.1.0
- Added
  - [`CHASSIS_LED_BLINK_PATTERN` PXI property](https://github.com/tkrebes/nisyscfg-python/pull/50).
  - [`self_calibrate` to `HardwareResource`](https://github.com/tkrebes/nisyscfg-python/pull/54).
- Changed
  - [Raised the minimum supported Python version to 3.7, added Python 3.11 support, and dropped PyPy3 support](https://github.com/tkrebes/nisyscfg-python/pull/49).
  - [Changed PXI bitmask enums to `enum.IntFlag`](https://github.com/tkrebes/nisyscfg-python/pull/51).
- Documentation
  - [Fixed a typo in a README example](https://github.com/tkrebes/nisyscfg-python/pull/56).

## 0.0.5
- Fixed
  - [Corrected the C type for `item_type` in `component_info`](https://github.com/tkrebes/nisyscfg-python/pull/40).
  - [Fixed handling of timestamp properties](https://github.com/tkrebes/nisyscfg-python/pull/41).
- Added
  - [XNET Ethernet sleep, PHY power mode, and IP stack info properties, and the `Protocol.ETHERNET` and `EnetPhyState.AUTO` enum values](https://github.com/tkrebes/nisyscfg-python/pull/41).
- Changed
  - [`xnet.Protocol.UNKNOWN` value changed from `-2` to `0xFFFFFFFE`](https://github.com/tkrebes/nisyscfg-python/pull/41).

## 0.0.4
- Fixed
  - [`LibraryWarning` raising `AttributeError` when constructed](https://github.com/tkrebes/nisyscfg-python/pull/34).
  - [`Session.resource`, which broke getting and setting system resource properties](https://github.com/tkrebes/nisyscfg-python/pull/34).

## 0.0.3
- Added
  - [Python 3.9 and 3.10 to the supported versions list](https://github.com/tkrebes/nisyscfg-python/pull/33).
- Changed
  - [Renamed `SYS_CFG_ACCESS` to `SYSTEM_CONFIGURATION_WEB_ACCESS`](https://github.com/tkrebes/nisyscfg-python/pull/32).

## 0.0.2
- Fixed
  - Python 3.5 support.
- Changed
  - Reworked `IndexedPropertyItems` to access properties without querying a count property.

## 0.0.1
- Initial release.
