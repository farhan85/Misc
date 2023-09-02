<#
.SYNOPSIS
Applies ReVanced (or Revanced Extended) patches to a given Youtube APK file.

.Description
Downloads ReVanced patches from GitHub and patches a given Youtube APK file.
You will need to check the realease notes in GitHub to know which YouTube version can be patched.
This script will download the patches, but you'll have to download the specific YouTube apk.

Prequisites:
- Youtube apk is downloaded (this script can help find the correct version to use)
- adb is installed

Example usage:

# 1. Determine the correct Youtube APK version to use (this will output all the version numbers needed)
PS > BuildRevanced

# 2. Download APK file...

# 3. Patch APK file (supplying the version numbers displayed above)
PS > BuildRevanced -p 2.166.0 -i 0.100.1 -c 2.20.1 -y YouTube_18.05.40.apk -o Youtube_Patched.apk

# or let the script automatically get the version numbers again
PS > BuildRevanced -y YouTube_18.05.40.apk -o Youtube_Patched.apk

.PARAMETER RevancedExtended
Apply Revanced Extended patches

.PARAMETER RexPatches
Apply YT-Revanced ReX patches

.PARAMETER PatchesVersion
The ReVanced patches version to retrieve.

.PARAMETER IntegrationsVersion
The ReVanced integrations version to retrieve.

.PARAMETER CliVersion
The ReVanced CLI version to retrieve.

.PARAMETER YoutubeApk
Filename of the YouTube apk file.

.PARAMETER OutFile
Filename of patched YouTube apk file.

.INPUTS
None. You cannot pipe objects to this command.

.OUTPUTS
None. Script progress is output to terminal.

.LINK
https://github.com/revanced/revanced-cli

.LINK
https://github.com/revanced/revanced-patches

.LINK
https://github.com/revanced/revanced-integrations
#>

[CmdletBinding(PositionalBinding=$false)]
param(
    [switch][Alias("e")]$RevancedExtended,
    [switch][Alias("x")]$RexPatches,
    [string][Alias("p")]$PatchesVersion,
    [string][Alias("i")]$IntegrationsVersion,
    [string][Alias("c")]$CliVersion,
    [string][Alias("y")]$YoutubeApk="YouTube_18.05.40.apk",
    [string][Alias("o")]$OutFile="Youtube_Patched.apk"
)

if ($RevancedExtended) {
  $patchesRepo = "inotia00/revanced-patches"
  $integrationsRepo = "inotia00/revanced-integrations"
  $cliRepo = "inotia00/revanced-cli"
} else if ($RexPatches) {
  $patchesRepo = "YT-Advanced/ReX-patches"
  $integrationsRepo = "YT-Advanced/ReX-integrations"
  $cliRepo = "inotia00/revanced-cli"
} else {
  $patchesRepo = "revanced/revanced-patches"
  $integrationsRepo = "revanced/revanced-integrations"
  $cliRepo = "revanced/revanced-cli"
}

function Get-LatestVersion {
  param ($Repo)
  $releases = "https://api.github.com/repos/${repo}/releases/latest"

  $ProgressPreference = "SilentlyContinue"
  $tag = (Invoke-WebRequest $releases | ConvertFrom-Json)[0].tag_name
  $ProgressPreference = "Continue"
  return $tag
}

if (-Not $PatchesVersion) {
  $PatchesVersion = (Get-LatestVersion -Repo $patchesRepo).TrimStart("v")
}

if (-Not $IntegrationsVersion) {
  $IntegrationsVersion = (Get-LatestVersion -Repo $integrationsRepo).TrimStart("v")
}

if (-Not $CliVersion) {
  $CliVersion = (Get-LatestVersion -Repo $cliRepo).TrimStart("v")
}

Write-Output "Patches version: $PatchesVersion"
Write-Output "Integrations version: $IntegrationsVersion"
Write-Output "CLI version: $CliVersion"
Write-Output "APK file to be patched: $YoutubeApk"

if (-Not $YoutubeApk) {
  Write-Host "Youtube APK filename not given. Determining the version needed."
  Write-Host "Dowloading patches.json file"
  $patchesJsonUrl = "https://github.com/${patchesRepo}/releases/download/v${PatchesVersion}/patches.json"
  $patchesJson = Invoke-WebRequest -Uri $patchesJsonUrl  | ConvertFrom-Json
  $versionSet = New-Object System.Collections.Generic.HashSet[string]
  foreach ($item in $patchesJson) {
    foreach ($package in $item.compatiblePackages) {
      if ($package.name -eq "com.google.android.youtube") {
        foreach ($version in $package.versions) {
          [void] $versionSet.add($version)
        }
      }
    }
  }
  $versionList = [System.Collections.ArrayList]@($versionSet)
  $latestVersion = @($versionList | Sort-Object -Descending)[0]
  Write-Output "Required Youtube version: $latestVersion"
  Start-Process "https://duckduckgo.com/?q=youtube+${latestVersion}+apkpure"
  exit
}

if (-Not (Test-Path $YoutubeApk)) {
  Write-Output "ERROR - File not found: $YoutubeApk"
  exit
}

$patchesFile = "revanced-patches-${PatchesVersion}.jar"
$integrationsFile = "revanced-integrations-${IntegrationsVersion}.apk"
$cliFile = "revanced-cli-${CliVersion}-all.jar"

$ProgressPreference = "SilentlyContinue"
if (-Not (Test-Path $patchesFile)) {
  Write-Host "Downloading patches file"
  $patchesUrl = "https://github.com/${patchesRepo}/releases/download/v${PatchesVersion}/${patchesFile}"
  Invoke-WebRequest -Uri $patchesUrl -OutFile $patchesFile
}

if (-Not (Test-Path $integrationsFile)) {
  Write-Host "Downloading integrations file"
  $integrationsUrl = "https://github.com/${integrationsRepo}/releases/download/v${IntegrationsVersion}/${integrationsFile}"
  Invoke-WebRequest -Uri $integrationsUrl -OutFile $integrationsFile
}

if (-Not (Test-Path $cliFile)) {
  Write-Host "Downloading patcher CLI file"
  $cliUrl = "https://github.com/${cliRepo}/releases/download/v${CliVersion}/${cliFile}"
  Invoke-WebRequest -Uri $cliUrl -OutFile $cliFile
}
$ProgressPreference = "Continue"

Write-Host "Patching $YoutubeApk"
if ($CliVersion.StartsWith("2")) {
  java -jar $cliFile `
      --clean `
      --bundle $patchesFile `
      --merge $integrationsFile `
      --apk $YoutubeApk `
      --out $OutFile
} else {
  java -jar $cliFile patch `
      --purge `
      --patch-bundle $patchesFile `
      --merge $integrationsFile `
      --out $OutFile `
      $YoutubeApk
}

Write-Host @"
Connect your phone:
- Enable USB debugging:
    Settings > Developer options > USB Debugging (turn on)
- Verify:
    adb start-server
    adb devices
"@

$response = Read-Host "Phone connected and ADB server running? [y/Y]"
if ($response.ToUpper() -ne 'Y') {
  exit
}

Write-Host "Installing on phone"
adb install $OutFile
adb kill-server
