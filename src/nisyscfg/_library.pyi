from __future__ import annotations

# These arguments cross a dynamic ctypes boundary; fixed arity and method names
# are declared here while the C-compatible argument values remain heterogeneous.
class Library:
    def __init__(self, ctypes_library: object) -> None: ...
    def AddComponentToEnum(
        self, componentEnumHandle: object, ID: object, version: object, mode: object
    ) -> int: ...
    def AddSoftwareFeed(
        self,
        sessionHandle: object,
        feedName: object,
        uri: object,
        enabled: object,
        trusted: object,
    ) -> int: ...
    def CheckFirmwareStatus(
        self,
        resourceHandle: object,
        percentComplete: object,
        firmwareStatus: object,
        detailedResult: object,
    ) -> int: ...
    def CloseHandle(self, syscfgHandle: object) -> int: ...
    def CreateComponentsEnum(self, componentEnumHandle: object) -> int: ...
    def CreateFilter(self, sessionHandle: object, filterHandle: object) -> int: ...
    def DeleteResource(
        self,
        resourceHandle: object,
        mode: object,
        dependentItemsDeleted: object,
        detailedResult: object,
    ) -> int: ...
    def FindHardware(
        self,
        sessionHandle: object,
        filterMode: object,
        filterHandle: object,
        expertNames: object,
        resourceEnumHandle: object,
    ) -> int: ...
    def FindSystems(
        self,
        sessionHandle: object,
        deviceClass: object,
        detectOnlineSystems: object,
        cacheMode: object,
        findOutputMode: object,
        timeoutMsec: object,
        onlyInstallableSystems: object,
        systemEnumHandle: object,
    ) -> int: ...
    def FormatWithBaseSystemImage(
        self,
        sessionHandle: object,
        autoRestart: object,
        fileSystem: object,
        networkSettings: object,
        systemImageID: object,
        systemImageVersion: object,
        timeoutMsec: object,
    ) -> int: ...
    def FreeDetailedString(self, str: object) -> int: ...
    def GetAvailableSoftwareComponents(
        self, sessionHandle: object, itemTypes: object, componentEnumHandle: object
    ) -> int: ...
    def GetFilteredBaseSystemImages(
        self,
        repositoryPath: object,
        deviceClass: object,
        operatingSystem: object,
        productID: object,
        systemImageEnumHandle: object,
    ) -> int: ...
    def GetInstalledSoftwareComponents(
        self,
        sessionHandle: object,
        itemTypes: object,
        cached: object,
        componentEnumHandle: object,
    ) -> int: ...
    def GetResourceIndexedProperty(
        self, resourceHandle: object, propertyID: object, index: object, value: object
    ) -> int: ...
    def GetResourceProperty(
        self, resourceHandle: object, propertyID: object, value: object
    ) -> int: ...
    def GetSystemProperty(
        self, sessionHandle: object, propertyID: object, value: object
    ) -> int: ...
    def GetSoftwareFeeds(self, sessionHandle: object, feedEnumHandle: object) -> int: ...
    def GetStatusDescription(
        self, sessionHandle: object, status: object, detailedDescription: object
    ) -> int: ...
    def GetSystemExperts(
        self, sessionHandle: object, expertNames: object, expertEnumHandle: object
    ) -> int: ...
    def InitializeSession(
        self,
        targetName: object,
        username: object,
        password: object,
        language: object,
        forcePropertyRefresh: object,
        connectTimeoutMsec: object,
        expertEnumHandle: object,
        sessionHandle: object,
    ) -> int: ...
    def InstallAll(
        self,
        sessionHandle: object,
        autoRestart: object,
        deselectConflicts: object,
        installedComponentEnumHandle: object,
        brokenDependencyEnumHandle: object,
    ) -> int: ...
    def InstallUninstallComponents2(
        self,
        sessionHandle: object,
        autoRestart: object,
        autoSelectDependencies: object,
        autoSelectRecommends: object,
        componentToInstallEnumHandle: object,
        numComponentsToUninstall: object,
        componentIDsToUninstall: object,
        brokenDependencyEnumHandle: object,
    ) -> int: ...
    def ModifySoftwareFeed(
        self,
        sessionHandle: object,
        feedName: object,
        newFeedName: object,
        uri: object,
        enabled: object,
        trusted: object,
    ) -> int: ...
    def NextComponentInfo(
        self,
        componentEnumHandle: object,
        ID: object,
        version: object,
        title: object,
        itemType: object,
        detailedDescription: object,
    ) -> int: ...
    def NextDependencyInfo(
        self,
        dependencyEnumHandle: object,
        dependerID: object,
        dependerVersion: object,
        dependerTitle: object,
        dependerDetailedDescription: object,
        dependeeID: object,
        dependeeVersion: object,
        dependeeTitle: object,
        dependeeDetailedDescription: object,
    ) -> int: ...
    def NextExpertInfo(
        self, expertEnumHandle: object, expertName: object, displayName: object, version: object
    ) -> int: ...
    def NextResource(
        self, sessionHandle: object, resourceEnumHandle: object, resourceHandle: object
    ) -> int: ...
    def NextSoftwareFeed(
        self,
        feedEnumHandle: object,
        feedName: object,
        uri: object,
        enabled: object,
        trusted: object,
    ) -> int: ...
    def NextSystemInfo(self, systemEnumHandle: object, system: object) -> int: ...
    def RemoveSoftwareFeed(self, sessionHandle: object, feedName: object) -> int: ...
    def RenameResource(
        self,
        resourceHandle: object,
        newName: object,
        overwriteConflict: object,
        updateDependencies: object,
        nameAlreadyExisted: object,
        overwrittenResourceHandle: object,
    ) -> int: ...
    def ResetHardware(self, resourceHandle: object, mode: object) -> int: ...
    def Restart(
        self,
        sessionHandle: object,
        waitForRestartToFinish: object,
        installMode: object,
        flushDNS: object,
        timeoutMsec: object,
        newIpAddress: object,
    ) -> int: ...
    def SaveResourceChanges(
        self, resourceHandle: object, changesRequireRestart: object, detailedResult: object
    ) -> int: ...
    def SaveSystemChanges(
        self, sessionHandle: object, changesRequireRestart: object, detailedResult: object
    ) -> int: ...
    def SelfCalibrateHardware(self, resourceHandle: object, detailedResult: object) -> int: ...
    def SelfTestHardware(
        self, resourceHandle: object, mode: object, detailedResult: object
    ) -> int: ...
    def SetFilterPropertyWithType(
        self, filterHandle: object, propertyID: object, propertyType: object, args: object
    ) -> int: ...
    def SetResourceProperty(
        self, resourceHandle: object, propertyID: object, args: object
    ) -> int: ...
    def SetSystemProperty(self, sessionHandle: object, propertyID: object, args: object) -> int: ...
    def SetSystemImageFromFolder2(
        self,
        sessionHandle: object,
        autoRestart: object,
        sourceFolder: object,
        encryptionPassphrase: object,
        numBlacklistEntries: object,
        blacklistFilesDirectories: object,
        originalSystemOnly: object,
        networkSettings: object,
    ) -> int: ...
    def TimestampFromValues(
        self, secondsSinceEpoch1970: object, fractionalSeconds: object, timestamp: object
    ) -> int: ...
    def UninstallAll(self, sessionHandle: object, autoRestart: object) -> int: ...
    def UpgradeFirmwareFromFile(
        self,
        resourceHandle: object,
        firmwareFile: object,
        autoStopTasks: object,
        alwaysOverwrite: object,
        waitForOperationToFinish: object,
        firmwareStatus: object,
        detailedResult: object,
    ) -> int: ...
    def UpgradeFirmwareVersion(
        self,
        resourceHandle: object,
        firmwareVersion: object,
        autoStopTasks: object,
        alwaysOverwrite: object,
        waitForOperationToFinish: object,
        firmwareStatus: object,
        detailedResult: object,
    ) -> int: ...
    def ValuesFromTimestamp(
        self, timestamp: object, secondsSinceEpoch1970: object, fractionalSeconds: object
    ) -> int: ...
