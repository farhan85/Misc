<#
.SYNOPSIS
Applies ReVanced patches to a given Youtube APK file.

.Description
Downloads ReVanced patches from GitHub and patches a given Youtube APK file.
You will need to check the realease notes in GitHub to know which YouTube version can be patched.
This script will download the patches, but you'll have to download the specific YouTube apk.

Prequisites:
- revanced-cli.jar is located in the same directory
- Youtube apk is downloaded
- adb is installed

.PARAMETER PatchesVersion
The ReVanced patches version to retrieve.

.PARAMETER IntegrationsVersion
The ReVanced integrations version to retrieve.

.PARAMETER YoutubeApk
Filename of the YouTube apk file.

.PARAMETER OutFile
Filename of patched YouTube apk file.

.INPUTS
None. You cannot pipe objects to this command.

.OUTPUTS
None. Script progress is output to terminal.

.EXAMPLE
BuildRevanced -p 2.166.0 -i 0.100.1 -y YouTube_18.05.40.apk

.EXAMPLE
BuildRevanced -p 2.166.0 -i 0.100.1 -y YouTube_18.05.40.apk -o Youtube_Patched.apk

.EXAMPLE
BuildRevanced -PatchesVersion 2.166.0 -IntegrationsVersion 0.100.1 -YoutubeApk YouTube_18.05.40.apk -OutFile Youtube_Patched.apk

.LINK
https://github.com/revanced/revanced-cli

.LINK
https://github.com/revanced/revanced-patches

.LINK
https://github.com/revanced/revanced-integrations
#>

[CmdletBinding(PositionalBinding=$false)]
param(
    [string][Alias("p")]$PatchesVersion="2.166.0",
    [string][Alias("i")]$IntegrationsVersion="0.100.1",
    [string][Alias("y")]$YoutubeApk="YouTube_18.05.40.apk",
    [string][Alias("o")]$OutFile="Youtube_Patched.apk"
)

Write-Host @"
Check if the release notes contains a new Youtube verson from here:
https://github.com/revanced/revanced-patches/releases
Look for "youtube: bump compatibility to"
If there's a new version, then download the specific Youtube apk from APKMirror/APKPure.

Connect your phone:
- Enable USB debugging:
    Settings > Developer options > USB Debugging (turn on)
- Verify:
    adb start-server
    adb devices

"@

$response = Read-Host "Have you downloaded the apk file and updated the version numbers in the script? [y/Y]"
if ($response.ToUpper() -ne 'Y') {
  exit
}

Write-Host "Downloading patches file"
$patchesFile = "revanced-patches-${PatchesVersion}.jar"
$patchesUrl = "https://github.com/revanced/revanced-patches/releases/download/v${PatchesVersion}/${patchesFile}"
Invoke-WebRequest -Uri $patchesUrl -OutFile $patchesFile | Out-Host

Write-Host "Downloading integrations file"
$integrationsFile = "revanced-integrations-${IntegrationsVersion}.apk"
$integrationsUrl = "https://github.com/revanced/revanced-integrations/releases/download/v${IntegrationsVersion}/${integrationsFile}"
Invoke-WebRequest -Uri $integrationsUrl -OutFile $integrationsFile | Out-Host

Write-Host "Patching $YoutubeApk"
java -jar revanced-cli.jar `
    --clean `
    --bundle $patchesFile `
    --merge $integrationsFile `
    --apk $YoutubeApk `
    --out $OutFile `
    | Out-Host

Write-Host "Installing on phone"
adb install $OutFile
adb kill-server