"""Session and system management functionality for NI System Configuration."""

from __future__ import annotations

import ctypes
import pathlib
import tempfile
import zipfile
from contextlib import ExitStack
from typing import Any, List, NamedTuple, Optional, Union, cast

import nisyscfg
import nisyscfg._library_singleton
import nisyscfg.component_info
import nisyscfg.dependency_info
import nisyscfg.expert_info
import nisyscfg.filter
import nisyscfg.hardware_resource
import nisyscfg.properties
import nisyscfg.pxi.properties
import nisyscfg.software_feed
import nisyscfg.system_info
import nisyscfg.xnet.properties
from nisyscfg._lib import c_string_decode, c_string_encode

InstallAllResult = NamedTuple(
    "InstallAllResult",
    [
        ("installed_components", nisyscfg.component_info.ComponentInfoIterator),
        ("broken_dependencies", nisyscfg.dependency_info.DependencyInfoIterator),
    ],
)

SaveChangesResult = NamedTuple(
    "SaveChangesResult",
    [
        ("restart_required", bool),
        ("details", Optional[str]),
    ],
)


@nisyscfg.properties.PropertyBag(nisyscfg.properties.System)
class Session(object):
    """Initializes a system configuration session with a specific system.

    This function communicates to the device at the specified address. If the
    device is no longer online, but it has previously been discovered in
    Measurement & Automation Explorer (MAX), this function succeeds, allowing
    you to retrieve cached information about the device.

    target - Specifies the IP address (ex. "224.102.13.24" ), MAC address
    (ex. "00:80:12:34:56:AB" ), or DNS name (ex. "myhost" ) of the target on a
    local or Real-Time system. The target defaults to the local system. Values
    such as a None, an empty string, and the strings localhost or 127.0.0.1
    also mean the local system.

    username - Specifies the username for the system you are initializing.
    Leave this parameter None if your target is running LabWindows/CVI 2009
    Real-Time Module or earlier or if you are connecting to the local
    system.

    password - Specifies the password for the system you are initializing.
    Leave this parameter None if no password has been set or if you are
    connecting to the local system.

    language - Specifies the language:

    * ``DEFAULT`` chooses based on local Windows settings.
    * ``ENGLISH``, ``FRENCH``, ``GERMAN``, ``JAPANESE``, ``KOREAN``, or
      ``CHINESE_SIMPLIFIED`` selects the corresponding language.

    force_property_refresh - Forces properties to be refreshed every time they
    are read by default. If FALSE, properties are queried once and cached in
    memory, which can optimize performance.

    timeout - Specifies the time, in seconds, that the function waits before the
    operation times out. When the operation succeeds, the session handle that is
    returned is set to the default, which is defined as 300 (5 minutes).

    Raises an nisyscfg.errors.LibraryError exception in the event of an error.
    """

    def __init__(
        self,
        target: Union[None, str] = None,
        username: Union[None, str] = None,
        password: Union[None, str] = None,
        language: nisyscfg.enums.Locale = nisyscfg.enums.Locale.DEFAULT,
        force_property_refresh: bool = True,
        timeout: float = 300.0,
    ) -> None:
        """Initialize a system configuration session."""
        self._children: List[Any] = []
        self._session: Any = nisyscfg.types.SessionHandle()
        self._library = nisyscfg._library_singleton.get()
        self._property_accessor = nisyscfg.properties.PropertyAccessor(
            setter=self._set_property,
            getter=self._get_property,
        )
        error_code = self._library.InitializeSession(
            c_string_encode(target),
            c_string_encode(username),
            c_string_encode(password),
            language,
            force_property_refresh,
            int(timeout * 1000),
            None,  # expert_enum_handle
            ctypes.pointer(self._session),
        )
        nisyscfg.errors.handle_error(self, error_code)
        self.target_name = target

    def __del__(self) -> None:
        """Close the session when the object is destroyed."""
        self.close()

    def __enter__(self) -> "Session":
        """Return the session context manager instance."""
        return self

    def __exit__(self, type: Any, value: Any, traceback: Any) -> None:
        """Close the session when exiting a context manager."""
        self.close()

    def _get_status_description(
        self, status: Union[int, "nisyscfg.errors.Status"]
    ) -> Optional[str]:
        c_detailed_description = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.GetStatusDescription(
            self._session, status, ctypes.pointer(c_detailed_description)
        )
        detailed_description: Optional[str] = ""
        error_code_2 = 0
        if c_detailed_description:
            detailed_description = c_string_decode(
                ctypes.cast(c_detailed_description, ctypes.c_char_p).value
            )
            error_code_2 = self._library.FreeDetailedString(c_detailed_description)
        nisyscfg.errors.handle_error(self, error_code, is_error_handling=True)
        nisyscfg.errors.handle_error(self, error_code_2, is_error_handling=True)
        return detailed_description

    def close(self) -> None:
        """Closes references to previously allocated session, filters, resources and enumerators.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        self._children.reverse()
        for child in self._children:
            cast(Any, child).close()
        if self._session:
            error_code = self._library.CloseHandle(self._session)
            nisyscfg.errors.handle_error(self, error_code)
            self._session = None

    def get_system_experts(
        self, expert_names: Union[str, List[str]] = ""
    ) -> nisyscfg.expert_info.ExpertInfoIterator:
        """Returns the experts available on the system.

        Args:
            expert_names: A case-insensitive comma-separated string or list of
                expert names to query. If empty, all supported experts are
                queried.

        Raises:
            nisyscfg.errors.LibraryError: If retrieving the system experts
                fails.
        """
        expert_handle = nisyscfg.types.EnumExpertHandle()
        if isinstance(expert_names, list):
            expert_names = ",".join(expert_names)
        error_code = self._library.GetSystemExperts(
            self._session, c_string_encode(expert_names), ctypes.pointer(expert_handle)
        )
        nisyscfg.errors.handle_error(self, error_code)
        iter = nisyscfg.expert_info.ExpertInfoIterator(expert_handle)
        self._children.append(iter)
        return iter

    def find_hardware(
        self,
        filter: Union[None, nisyscfg.filter.Filter] = None,
        mode: nisyscfg.enums.FilterMode = nisyscfg.enums.FilterMode.MATCH_VALUES_ALL,
        expert_names: Union[str, List[str]] = "",
    ) -> nisyscfg.hardware_resource.HardwareResourceIterator:
        """Returns an iterator of hardware in a specified system.

        Args:
            filter: Specifies a filter you can use to limit the results to hardware
                matching specific properties. The default is no filter.
            mode: Determines how filter properties are matched:

                * ``MATCH_VALUES_ALL`` requires all specified properties to
                  match.
                * ``MATCH_VALUES_ANY`` requires any specified property to
                  match.
                * ``MATCH_VALUES_NONE`` requires none of the specified
                  properties to match.
                * ``ALL_PROPERTIES_EXIST`` matches specified properties
                  regardless of value.

                Defaults to ``MATCH_VALUES_ALL``.
            expert_names: A case-insensitive comma-separated string or list of
                expert names to query. If empty, all supported experts are
                queried.

        Raises:
            nisyscfg.errors.LibraryError: If the native hardware search fails.
        """
        if filter is None:

            class DummyFilter(object):
                _handle: Optional["nisyscfg.types.FilterHandle"] = None

            # Use a local variable narrowed to the Filter type so subsequent
            # attribute access (._handle) is well-typed. We cast the dummy to
            # the Filter interface to preserve runtime behavior while satisfying
            # the type checker.
            flt = cast(nisyscfg.filter.Filter, DummyFilter())
        else:
            flt = filter
        resource_handle = nisyscfg.types.EnumResourceHandle()
        if isinstance(expert_names, list):
            expert_names = ",".join(expert_names)
        error_code = self._library.FindHardware(
            self._session,
            mode,
            flt._handle,
            c_string_encode(expert_names),
            ctypes.pointer(resource_handle),
        )
        nisyscfg.errors.handle_error(self, error_code)
        iter = nisyscfg.hardware_resource.HardwareResourceIterator(self._session, resource_handle)
        self._children.append(iter)
        return iter

    def find_systems(
        self,
        device_class: str = "",
        detect_online_systems: bool = True,
        cache_mode: nisyscfg.enums.IncludeCachedResults = nisyscfg.enums.IncludeCachedResults.NONE,
        find_output_mode: nisyscfg.enums.SystemNameFormat = nisyscfg.enums.SystemNameFormat.HOSTNAME_IP,
        timeout: float = 4.0,
        only_installable_systems: bool = False,
    ) -> nisyscfg.system_info.SystemInfoIterator:
        """Retrieves systems on the network.

        device_class - Specifies the class of device for which you are
        searching. Common values are "PXI" and "cRIO". To specify multiple
        classes, use a comma to separate the values.

        detect_online_systems - Detects systems that are online. This option
        checks for all local online systems by default. You must set this
        parameter to TRUE on Real-Time targets. On Windows operating systems,
        set this parameter to FALSE if you only want to return previously
        detected results.

        cache_mode - Specifies cached results:

        * ``NONE`` returns only systems from a new scan. Systems previously
          added to MAX on a remote subnet are not returned because they cannot
          be detected on the local subnet.
        * ``ONLY_IF_ONLINE`` includes previously discovered systems that are
          online.
        * ``ALL`` (default) includes all previously discovered systems.

        find_output_mode - Specifies the "preferred" output format of hostname
        and IP addresses for systems on the network. The Initialize function
        accepts these formats:

        * ``HOSTNAME`` includes only the hostname.
        * ``HOSTNAME_IP`` (default) includes the hostname and IP address.
        * ``HOSTNAME_MAC`` includes the hostname and MAC address.
        * ``IP`` includes only the IP address.
        * ``IP_HOSTNAME`` includes the IP address and hostname.
        * ``IP_MAC`` includes the IP address and MAC address.
        * ``MAC`` includes only the MAC address.
        * ``MAC_HOSTNAME`` includes the MAC address and hostname.
        * ``MAC_IP`` includes the MAC address and IP address.

        Note: In some cases this parameter may return a system that is not in
        the requested format. For example, if you request the default
        HOSTNAME_IP but an unconfigured system is detected, that system is
        returned as IP_MAC.

        timeout - The time, in seconds, the function waits before it times out.
        The default is 4 s. In some cases, the operation may take longer to
        time out.

        only_installable_systems - Detects only the systems that support the
        ability to install software remotely. This includes all Real-Time
        systems.

        Returns an interator that yields the system names in the format
        requested from the input parameter

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        system_handle = nisyscfg.types.EnumSystemHandle()
        error_code = self._library.FindSystems(
            self._session,
            c_string_encode(device_class),
            nisyscfg.enums.Bool(detect_online_systems),
            cache_mode,
            find_output_mode,
            int(timeout * 1000),
            nisyscfg.enums.Bool(only_installable_systems),
            ctypes.pointer(system_handle),
        )
        nisyscfg.errors.handle_error(self, error_code)

        return nisyscfg.system_info.SystemInfoIterator(system_handle)

    def create_filter(self) -> nisyscfg.filter.Filter:
        """Creates a hardware filter used to query for specific resources in a system.

        After creating a filter, set one or more properties to limit the set of  detected resources.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        filter = nisyscfg.filter.Filter(self._session)
        self._children.append(filter)
        return filter

    def restart(
        self,
        sync_call: bool = True,
        install_mode: bool = False,
        flush_dns: bool = False,
        timeout: float = 90.0,
    ) -> str:
        """Reboots a system or network device.

        sync_call - Waits until the reboot has finished before the function
        operation is completed, by default. Select FALSE to not wait until the
        reboot is finished before the function completes its operation.

        install_mode - Does not reboot the system into install mode by default.
        To reboot into install mode, select TRUE. The default is FALSE, reboot
        into normal mode.

        flush_dns - Does not clear the DNS cache by default. DNS clients
        temporarily store system hostnames. Flushing the DNS allows you to clear
        those names from memory. This parameter applies to the local Windows
        system.

        timeout - The time, in seconds, that the function waits to establish a
        connection before it returns an error. The default is 90 s.

        Returns the new IP address of the rebooted system. This IP address may
        differ from the previous IP address if the system acquires a different
        IP address from the DHCP server.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        new_ip_address = nisyscfg.types.simple_string()
        error_code = self._library.Restart(
            self._session,
            sync_call,
            install_mode,
            flush_dns,
            int(timeout * 1000),
            new_ip_address,
        )
        nisyscfg.errors.handle_error(self, error_code)
        return c_string_decode(new_ip_address.value)

    def get_filtered_base_system_images(
        self,
        repository_path: Union[None, str] = None,
        device_class: Union[None, str] = None,
        os: Union[None, str] = None,
        product_id: int = 0,
    ) -> Optional[nisyscfg.component_info.ComponentInfoIterator]:
        """Retrieves a collection of base system images available from a repository path.

        These include a base operating system and are intended to be used
        with format().

        repository_path - Specifies the location that contains installable
        components.

        device_class - Specifies the type of device for which you are
        searching. Common values are PXI and cRIO. To specify multiple classes,
        use a comma to separate the values.

        os - Specifies the operating system.

        product_id - Specifies the bus-specific product identifier code. This
        is not the product's sellable model number.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        software_component_handle = nisyscfg.types.EnumSoftwareComponentHandle()
        error_code = self._library.GetFilteredBaseSystemImages(
            c_string_encode(repository_path),
            c_string_encode(device_class),
            c_string_encode(os),
            ctypes.c_uint(product_id),
            ctypes.pointer(software_component_handle),
        )
        nisyscfg.errors.handle_error(self, error_code)
        if software_component_handle:
            iter = nisyscfg.component_info.ComponentInfoIterator(software_component_handle)
            self._children.append(iter)
            return iter
        return None

    def format(
        self,
        auto_restart: bool = True,
        file_system: nisyscfg.enums.FileSystemMode = nisyscfg.enums.FileSystemMode.DEFAULT,
        network_settings: nisyscfg.enums.NetworkInterfaceSettings = nisyscfg.enums.NetworkInterfaceSettings.RESET_PRIMARY_RESET_OTHERS,
        system_image_id: Union[None, str] = None,
        system_image_version: Union[None, str] = None,
        timeout: float = 90.0,
    ) -> None:
        """Erase all data from the primary hard drive and format the system.

        The system is formatted using the specified base system image, network
        settings, and filesystem. The operation will fail if you choose not to
        restart the target automatically and the target's boot flow requires it
        to be in safe mode or restart after the operation.

        Args:
            auto_restart: Restarts the system before and/or after formatting
                as required by the target's boot flow. Formatting fails if a
                restart is required and automatic restart is disabled.
            file_system: Filesystem mode for the primary hard drive. Not all
                systems support every mode:

                * ``DEFAULT`` uses the target's existing format.
                * ``FAT`` uses the File Allocation Table file system.
                * ``RELIANCE`` uses the Reliance transactional file system, developed
                  by Datalight, which is tolerant of crashes and power interruptions.
                * ``UBIFS`` uses the Unsorted Block Image File System.
                * ``EXT4`` uses the Ext4 file system.
            network_settings: Network adapter settings to apply:

                * ``RESET_PRIMARY_RESET_OTHERS`` restores factory settings on
                  the primary adapter and disables all other adapters.
                * ``PRESERVE_PRIMARY_RESET_OTHERS`` preserves the primary
                  adapter's settings and disables all other adapters.
                * ``PRESERVE_PRIMARY_PRESERVE_OTHERS`` preserves settings on
                  all adapters.

                Preserve options may not be supported for targets on a remote
                subnet.
            system_image_id: The system image ID.
            system_image_version: The system image version.
            timeout: Base time, in seconds, before the formatting operation times
                out. The default is 90 seconds. The timeout increases by 90 seconds
                if a restart after formatting is required, and by another 90 seconds
                if the system is not in safe mode.

        Raises:
            nisyscfg.errors.LibraryError: If the native format operation fails.
        """
        error_code = self._library.FormatWithBaseSystemImage(
            self._session,
            nisyscfg.enums.Bool(auto_restart),
            file_system,
            network_settings,
            c_string_encode(system_image_id),
            c_string_encode(system_image_version),
            ctypes.c_uint(int(timeout * 1000)),
        )
        nisyscfg.errors.handle_error(self, error_code)

    def get_available_software_components(
        self,
        item_types: nisyscfg.enums.IncludeComponentTypes = nisyscfg.enums.IncludeComponentTypes.ALL_VISIBLE,
    ) -> Optional[nisyscfg.component_info.ComponentInfoIterator]:
        """Retrieve software components available for installation.

        Args:
            item_types: Selects which software component types to include:

                * ``ALL_VISIBLE`` includes standard, startup, and essential
                  components.
                * ``ALL_VISIBLE_AND_HIDDEN`` includes visible and hidden
                  components.
                * ``ONLY_STANDARD`` includes standard components only.
                * ``ONLY_STARTUP`` includes startup applications only.

                Hidden software is not listed by default.

        Returns:
            An iterator of available software components, or ``None`` if no
            components are available.

        Raises:
            nisyscfg.errors.LibraryError: If retrieving available software
                components fails.
        """
        software_component_handle = nisyscfg.types.EnumSoftwareComponentHandle()
        error_code = self._library.GetAvailableSoftwareComponents(
            self._session, item_types, ctypes.pointer(software_component_handle)
        )
        nisyscfg.errors.handle_error(self, error_code)
        if software_component_handle:
            iter = nisyscfg.component_info.ComponentInfoIterator(software_component_handle)
            self._children.append(iter)
            return iter
        return None

    def get_installed_software_components(
        self,
        item_types: nisyscfg.enums.IncludeComponentTypes = nisyscfg.enums.IncludeComponentTypes.ALL_VISIBLE,
        cached: bool = False,
    ) -> Optional[nisyscfg.component_info.ComponentInfoIterator]:
        """Retrieve installed software components.

        Args:
            item_types: Selects which software component types to include:

                * ``ALL_VISIBLE`` includes standard, startup, and essential
                  components.
                * ``ALL_VISIBLE_AND_HIDDEN`` includes visible and hidden
                  components.
                * ``ONLY_STANDARD`` includes standard components only.
                * ``ONLY_STARTUP`` includes startup applications only.

                Hidden software is not listed by default.
            cached: Return information already read from the specified
                real-time system if ``True``. By default, the system is
                contacted again for the information.

        Returns:
            An iterator of installed software components, or ``None`` if no
            components are installed.

        Raises:
            nisyscfg.errors.LibraryError: If retrieving installed software
                components fails.
        """
        software_component_handle = nisyscfg.types.EnumSoftwareComponentHandle()
        error_code = self._library.GetInstalledSoftwareComponents(
            self._session, item_types, cached, ctypes.pointer(software_component_handle)
        )
        nisyscfg.errors.handle_error(self, error_code)
        if software_component_handle:
            iter = nisyscfg.component_info.ComponentInfoIterator(software_component_handle)
            self._children.append(iter)
            return iter
        return None

    def add_software_feed(self, name: str, uri: str, enabled: bool, trusted: bool) -> None:
        """Adds a software feed to the system.

        Note: This requires Secure Shell Server (sshd) to be enabled on the
        target.

        name - Name of the feed for identification purposes.

        uri - Location of the feed, such as "file://..." or "http://...". NI
        feeds often start with "http://download.ni.com/".

        enabled - Whether the feed is enabled.

        trusted - Whether the feed is trusted. A trusted feed will not be
        cryptographically verified by the package manager to be a safe and
        secure source of packages. Feeds are not trusted by default. A system
        administrator may have reason to trust the feed regardless.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        error_code = self._library.AddSoftwareFeed(
            self._session,
            c_string_encode(name),
            c_string_encode(uri),
            nisyscfg.enums.Bool(enabled),
            nisyscfg.enums.Bool(trusted),
        )
        nisyscfg.errors.handle_error(self, error_code)

    def modify_software_feed(
        self, old_name: str, new_name: str, uri: str, enabled: bool, trusted: bool
    ) -> None:
        """Modifies an existing software feed by name.

        Note: This requires Secure Shell Server (sshd) to be enabled on the
        target.

        old_name - Name of the feed to modify. This feed must exist on the system.

        new_name - New name of the feed. This feed must not exist on the
        system. If not specified, the feed name will remain unchanged.

        uri - New location of the feed, such as "file://..." or "http://...".
        NI feeds often start with "http://download.ni.com/".

        enabled - New enabled state.

        trusted - New trusted state. A trusted feed will not be
        cryptographically verified by the package manager to be a safe and
        secure source of packages. Feeds are not trusted by default. A system
        administrator may have reason to trust the feed regardless.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        error_code = self._library.ModifySoftwareFeed(
            self._session,
            c_string_encode(old_name),
            c_string_encode(new_name),
            c_string_encode(uri),
            nisyscfg.enums.Bool(enabled),
            nisyscfg.enums.Bool(trusted),
        )
        nisyscfg.errors.handle_error(self, error_code)

    def remove_software_feed(self, name: str) -> None:
        """Removes an existing software feed by name.

        Note: This requires Secure Shell Server (sshd) to be enabled on the
        target.

        name - Name of the feed to remove. This feed must exist on the system.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        error_code = self._library.RemoveSoftwareFeed(self._session, c_string_encode(name))
        nisyscfg.errors.handle_error(self, error_code)

    def install_all(
        self, auto_restart: bool = True, deselect_conflicts: bool = True
    ) -> InstallAllResult:
        """Installs software on a Real-Time system.

        Args:
            auto_restart: Restarts the system into install mode before the
                operation and back to a running state afterward as needed. If
                automatic restart is disabled, the system must already be in
                install mode.
            deselect_conflicts: If ``True``, automatically deselects
                conflicting components. If ``False``, installation fails if
                conflicting components exist.

        Returns:
            A :class:`nisyscfg.system.InstallAllResult` containing iterators
            for the installed components and any broken dependencies.

        Raises:
            nisyscfg.errors.LibraryError: If the native install operation fails.
        """
        installed_component_handle = nisyscfg.types.EnumSoftwareFeedHandle()
        broken_dependency_handle = nisyscfg.types.EnumDependencyHandle()
        error_code = self._library.InstallAll(
            self._session,
            auto_restart,
            deselect_conflicts,
            ctypes.pointer(installed_component_handle),
            ctypes.pointer(broken_dependency_handle),
        )
        nisyscfg.errors.handle_error(self, error_code)

        result = InstallAllResult(
            installed_components=nisyscfg.component_info.ComponentInfoIterator(
                installed_component_handle
            ),
            broken_dependencies=nisyscfg.dependency_info.DependencyInfoIterator(
                broken_dependency_handle
            ),
        )

        self._children.append(result.installed_components)
        self._children.append(result.broken_dependencies)

        return result

    def uninstall_all(self, auto_restart: bool = True) -> None:
        """Uninstalls all software from a specified system.

        auto_restart - Restarts the system before and/or after the operation as
        required by the target's boot flow. The operation will fail if you
        choose not to restart the target automatically and the target's boot
        flow requires it to be in safe mode or restart after the operation.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        error_code = self._library.UninstallAll(self._session, auto_restart)
        nisyscfg.errors.handle_error(self, error_code)

    def _install_uninstall(
        self,
        components_to_install: Union[None, List[str]] = None,
        components_to_uninstall: Union[None, List[str]] = None,
        auto_restart: bool = True,
        auto_select_dependencies: bool = True,
        auto_select_recommends: bool = True,
        item_types: nisyscfg.enums.IncludeComponentTypes = nisyscfg.enums.IncludeComponentTypes.ALL_VISIBLE,
    ) -> nisyscfg.dependency_info.DependencyInfoIterator:
        """Allows you to install components, uninstall components, or both simultaneously.

        Components can be installed and uninstalled in the same operation as long
        as the selected components do not overlap with each other.

        Args:
            components_to_install: IDs or titles of software components to
                install.
            components_to_uninstall: IDs of software components to uninstall.
            auto_restart: Restarts the system into install mode before the
                operation and back to a running state afterward as needed. If
                automatic restart is disabled, the system must already be in
                install mode.
            auto_select_dependencies: If ``True``, automatically selects
                components required by the components being installed.
            auto_select_recommends: If ``True``, automatically selects
                recommended components.
            item_types: Selects component types available for installation:

                * ``ALL_VISIBLE`` includes standard, startup, and essential
                  components.
                * ``ALL_VISIBLE_AND_HIDDEN`` includes visible and hidden
                  components.
                * ``ONLY_STANDARD`` includes standard components only.
                * ``ONLY_STARTUP`` includes startup applications only.

                Hidden software is not listed by default. This option does not
                affect which components are selected for uninstallation.

        Returns:
            An iterator of broken dependencies, which are software components
            that cannot operate without another software component installed.

        Raises:
            nisyscfg.errors.Error: If a requested component to install is not
                available on the target.
            nisyscfg.errors.LibraryError: If the native install/uninstall
                operation fails.
        """
        software_to_install = nisyscfg.component_info.EnumSoftwareComponent()

        if components_to_install:
            for component_name in components_to_install:
                component = self._get_latest_component(component_name, item_types)
                software_to_install.add_component(
                    component.id,
                    component.version,
                    nisyscfg.enums.VersionSelectionMode.EXACT,
                )

        if components_to_uninstall:
            c_components_to_uninstall = (ctypes.c_char_p * len(components_to_uninstall))(
                *map(c_string_encode, components_to_uninstall)
            )
        else:
            c_components_to_uninstall = (ctypes.c_char_p * 0)()

        broken_dependency_handle = nisyscfg.types.EnumDependencyHandle()

        error_code = self._library.InstallUninstallComponents2(
            self._session,
            auto_restart,
            auto_select_dependencies,
            auto_select_recommends,
            software_to_install._handle,
            len(c_components_to_uninstall),
            ctypes.cast(c_components_to_uninstall, ctypes.POINTER(ctypes.POINTER(ctypes.c_char))),
            ctypes.pointer(broken_dependency_handle),
        )
        nisyscfg.errors.handle_error(self, error_code)

        broken_dependencies = nisyscfg.dependency_info.DependencyInfoIterator(
            broken_dependency_handle
        )
        self._children.append(broken_dependencies)

        return broken_dependencies

    def install(
        self,
        components: Union[None, List[str]] = None,
        auto_restart: bool = True,
        auto_select_dependencies: bool = True,
        auto_select_recommends: bool = True,
        item_types: nisyscfg.enums.IncludeComponentTypes = nisyscfg.enums.IncludeComponentTypes.ALL_VISIBLE,
    ) -> nisyscfg.dependency_info.DependencyInfoIterator:
        """Allows you to install components.

        Args:
            components: IDs or titles of software components to install.
            auto_restart: Restarts the system into install mode before the
                operation and back to a running state afterward as needed. If
                automatic restart is disabled, the system must already be in
                install mode.
            auto_select_dependencies: If ``True``, automatically selects
                components required by the components being installed.
            auto_select_recommends: If ``True``, automatically selects
                recommended components.
            item_types: Selects component types available for installation:

                * ``ALL_VISIBLE`` includes standard, startup, and essential
                  components.
                * ``ALL_VISIBLE_AND_HIDDEN`` includes visible and hidden
                  components.
                * ``ONLY_STANDARD`` includes standard components only.
                * ``ONLY_STARTUP`` includes startup applications only.

                Hidden software is not listed by default.

        Returns:
            An iterator of broken dependencies, which are software components
            that cannot operate without another software component installed.

        Raises:
            nisyscfg.errors.Error: If a requested component to install is not
                available on the target.
            nisyscfg.errors.LibraryError: If the native install operation fails.
        """
        return self._install_uninstall(
            components_to_install=components,
            auto_restart=auto_restart,
            auto_select_dependencies=auto_select_dependencies,
            auto_select_recommends=auto_select_recommends,
            item_types=item_types,
        )

    def uninstall(
        self,
        components: Union[None, List[str]] = None,
        auto_restart: bool = True,
        auto_select_dependencies: bool = True,
        auto_select_recommends: bool = True,
        item_types: nisyscfg.enums.IncludeComponentTypes = nisyscfg.enums.IncludeComponentTypes.ALL_VISIBLE,
    ) -> nisyscfg.dependency_info.DependencyInfoIterator:
        """Allows you to uninstall components.

        Args:
            components: IDs of software components to uninstall.
            auto_restart: Restarts the system into install mode before the
                operation and back to a running state afterward as needed. If
                automatic restart is disabled, the system must already be in
                install mode.
            auto_select_dependencies: Controls whether required dependencies
                are selected automatically for the operation.
            auto_select_recommends: Controls whether recommended components
                are selected automatically for the operation.
            item_types: Selects component types when installing components.
                This option does not filter components selected for
                uninstallation.

        Returns:
            An iterator of broken dependencies, which are software components
            that cannot operate without another software component installed.

        Raises:
            nisyscfg.errors.LibraryError: If the native uninstall operation fails.
        """
        return self._install_uninstall(
            components_to_uninstall=components,
            auto_restart=auto_restart,
            auto_select_dependencies=auto_select_dependencies,
            auto_select_recommends=auto_select_recommends,
            item_types=item_types,
        )

    def _get_latest_component(
        self,
        component_name: str,
        item_types: nisyscfg.enums.IncludeComponentTypes = nisyscfg.enums.IncludeComponentTypes.ALL_VISIBLE,
    ) -> nisyscfg.component_info.ComponentInfo:
        components = [
            component
            for component in cast(
                nisyscfg.component_info.ComponentInfoIterator,
                self.get_available_software_components(item_types),
            )
            if (component.title == component_name) or (component.id == component_name)
        ]

        if not components:
            raise nisyscfg.errors.Error(
                'Component "{component_name}" not available for install on target "{self.target_name}".'.format(
                    component_name=component_name, self=self
                )
            )

        return max(components, key=lambda comp: comp.version.split("."))

    def get_software_feeds(
        self,
    ) -> Optional[nisyscfg.software_feed.SoftwareFeedIterator]:
        """Retrieves a list of configured software feeds.

        A feed represents a location that the package manager uses to find and
        download available software.

        Note: This requires Secure Shell Server (sshd) to be enabled on the
        target.

        Raises an nisyscfg.errors.LibraryError exception in the event of an
        error.
        """
        software_feed_handle = nisyscfg.types.EnumSoftwareFeedHandle()
        error_code = self._library.GetSoftwareFeeds(
            self._session, ctypes.pointer(software_feed_handle)
        )
        nisyscfg.errors.handle_error(self, error_code)
        if software_feed_handle:
            iter = nisyscfg.software_feed.SoftwareFeedIterator(software_feed_handle)
            self._children.append(iter)
            return iter
        return None

    @property
    def resource(self) -> nisyscfg.hardware_resource.HardwareResource:
        """System resource properties."""
        if not hasattr(self, "_resource"):
            resource_handle = self._get_property(16941086, nisyscfg.types.ResourceHandle)
            self._resource = nisyscfg.hardware_resource.HardwareResource(resource_handle)
            self._children.append(self._resource)
        return self._resource

    def _get_property(self, id: int, c_type: Any) -> Any:
        # The C API uses different ctypes return locations based on type. Keep
        # the implementation dynamically typed but expose a typed signature
        # to satisfy mypy for callers.
        value: Any
        value_arg: Any
        if c_type == ctypes.c_char_p:
            value = nisyscfg.types.simple_string()
            value_arg = value
        elif issubclass(c_type, nisyscfg.enums.BaseEnum) or issubclass(
            c_type, nisyscfg.enums.BaseFlag
        ):
            value = ctypes.c_int()
            value_arg = ctypes.pointer(value)
        else:
            value = c_type(0)
            value_arg = ctypes.pointer(value)

        error_code = self._library.GetSystemProperty(self._session, id, value_arg)
        nisyscfg.errors.handle_error(self, error_code)

        if issubclass(c_type, nisyscfg.enums.BaseEnum) or issubclass(
            c_type, nisyscfg.enums.BaseFlag
        ):
            return c_type(value.value)

        if issubclass(c_type, ctypes.c_void_p):
            return value

        return c_string_decode(value.value)

    def _set_property(self, id: int, value: Any, c_type: Any, nisyscfg_type: int) -> None:
        if c_type == ctypes.c_char_p:
            value = c_string_encode(value)
        elif issubclass(c_type, nisyscfg.enums.BaseEnum) or issubclass(
            c_type, nisyscfg.enums.BaseFlag
        ):
            value = ctypes.c_int(value)
        else:
            value = c_type(value)

        error_code = self._library.SetSystemProperty(self._session, id, value)
        nisyscfg.errors.handle_error(self, error_code)

    def save_changes(self) -> SaveChangesResult:
        """Saves changes made to systems.

        Returns:
            nisyscfg.system.SaveChangesResult: A result containing whether the
                changes require a reboot and any additional operation details
                returned by the API.

        Raises:
            nisyscfg.errors.LibraryError: If saving system changes fails.
        """
        restart_required = ctypes.c_int()
        c_details = ctypes.POINTER(ctypes.c_char)()
        error_code = self._library.SaveSystemChanges(
            self._session, restart_required, ctypes.pointer(c_details)
        )
        details: Optional[str] = ""
        error_code_2 = 0
        if c_details:
            details = c_string_decode(ctypes.cast(c_details, ctypes.c_char_p).value)
            error_code_2 = self._library.FreeDetailedString(c_details)
        nisyscfg.errors.handle_error(self, error_code)
        nisyscfg.errors.handle_error(self, error_code_2)
        return SaveChangesResult(restart_required=restart_required.value != 0, details=details)

    def set_system_image(
        self,
        source: str | pathlib.Path,
        auto_restart: bool = True,
        encryption_passphrase: str | None = None,
        exclude_paths: List[str] | None = None,
        original_system_only: bool = False,
        network_settings: nisyscfg.enums.NetworkInterfaceSettings = nisyscfg.enums.NetworkInterfaceSettings.PRESERVE_PRIMARY_PRESERVE_OTHERS,
    ) -> None:
        """Applies an image to a system.

        The system image is a copy of the contents and software on the primary
        hard drive of a specified target system. Applying the image to the
        system restores it to the state captured when the image was created.
        This image can exist as a folder or a zipped archive.

        source - The path to the system image file or folder.

        auto_restart - Restarts the system into install mode by default before
        the operation is performed, and restarts back to a running state after
        the operation is complete. If you choose not to restart automatically,
        and the system is not in install mode, the resulting image may not be
        valid.

        encryption_passphrase - A passphrase used to encrypt a portion of the
        image that contains sensitive information.

        exclude_paths - Specifies the list of files and folders to exclude from
        the target image. Files on the blacklist will not be copied from the
        image to the target and they will not be removed from the target.

        original_system_only - Verifies that the target system has the same MAC
        address as the system from which the image was originally created.
        Selecting True will allow you to restore an image from the exact same
        target from which the image was created only. This option is False by
        default. When the option is False, this operation can also apply the
        system image to other targets of the same device class.

        network_settings - Resets the primary network adapter and disables
        secondary adapters by default.
        """
        source = pathlib.Path(source)
        if not source.exists():
            raise FileNotFoundError(f"The source {source} does not exist.")
        if exclude_paths is not None:
            raise NotImplementedError("Excluding paths is not implemented yet.")

        with ExitStack() as stack:
            if source.is_dir():
                source_folder = str(source)
            else:
                source_folder = str(stack.enter_context(tempfile.TemporaryDirectory()))
                try:
                    zip_ref = stack.enter_context(zipfile.ZipFile(source, "r"))
                except zipfile.BadZipFile:
                    raise nisyscfg.errors.InvalidSystemImageError(
                        f"{source} is not a valid zip file."
                    )
                zip_ref.extractall(source_folder)

            error_code = self._library.SetSystemImageFromFolder2(
                self._session,
                nisyscfg.enums.Bool(auto_restart),
                c_string_encode(source_folder),
                c_string_encode(encryption_passphrase),
                len(exclude_paths) if exclude_paths else 0,
                exclude_paths,
                nisyscfg.enums.Bool(original_system_only),
                network_settings,
            )
            nisyscfg.errors.handle_error(self, error_code)
