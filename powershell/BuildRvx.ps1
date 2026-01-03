[CmdletBinding(PositionalBinding=$false)]
param(
  [switch][Alias("y")]$Youtube,
  [switch][Alias("m")]$YoutubeMusic
)

if (-Not $Youtube -and -Not $YoutubeMusic) {
  Write-Error -Message "Missing params. Must provide either -Youtube/-y or -YoutubeMusic/-m"
  Exit 1
}

if ($Youtube) {
  $package_name = "com.google.android.youtube"
  $apk_prefix = "youtube"
} elseif ($YoutubeMusic) {
  $package_name = "com.google.android.apps.youtube.music"
  $apk_prefix = "youtube-music"
}

function Get-LatestVersionGithub($repo) {
  Invoke-WebRequest -Uri "https://api.github.com/repos/${repo}/releases/latest"
    | ConvertFrom-Json
    | Select-Object -First 1
    | Select-Object -ExpandProperty tag_name
    | ForEach-Object { $_.TrimStart("v") }
}

function Get-YoutubeVersion($patches_json_url, $package_name) {
  Invoke-WebRequest -Uri $patches_json_url
    | ConvertFrom-Json
    | Where-Object { $_.compatiblePackages.$package_name }
    | ForEach-Object { $_.compatiblePackages.$package_name[-1] }
    | Sort-Object -Descending
    | Select-Object -First 1
}

function Get-FromApkMirror($repo, $version, $output) {
  $jsonString = @"
    {
      "options": {
        "arch": "arm64-v8a"
      },
      "apps": [
        {
          "org": "google-inc",
          "repo": "${repo}",
          "outFile": "${output}",
          "version": "${version}"
        }
      ]
    }
"@

  $jsonString | Set-Content -Path "apps.json" -Encoding UTF8

  # https://github.com/tanishqmanuja/apkmirror-downloader
  .\apkmd.exe apps.json
}

$patches_repo = "inotia00/revanced-patches"
$cli_repo = "inotia00/revanced-cli"

$patches_version = Get-LatestVersionGithub $patches_repo
$cli_version = Get-LatestVersionGithub $cli_repo

$patches_file = "patches-${patches_version}.rvp"
$patcher_cli_file = "revanced-cli-${cli_version}-all.jar"

$patches_json = "https://raw.githubusercontent.com/${patches_repo}/refs/heads/revanced-extended/patches.json"
$patches_url = "https://github.com/${patches_repo}/releases/download/v${patches_version}/${patches_file}"
$patcher_cli_url = "https://github.com/${cli_repo}/releases/download/v${cli_version}/${patcher_cli_file}"

$apk_version = Get-YoutubeVersion $patches_json $package_name
$orig_apk_file = "${apk_prefix}-${apk_version}.apk"
$patched_apk_file = "${apk_prefix}-patched-${apk_version}.apk"

Write-Host "Patches repo:         $patches_repo"
Write-Host "Patches version:      $patches_version"
Write-Host "CLI version:          $cli_version"
Write-Host "APK:                  $apk_prefix"
Write-Host "APK version:          $apk_version"


$ProgressPreference = "SilentlyContinue"
if (-Not (Test-Path $patches_file)) {
  Write-Host "Downloading patches file"
  Invoke-WebRequest -Uri $patches_url -OutFile $patches_file
}

if (-Not (Test-Path $patcher_cli_file)) {
  Write-Host "Downloading CLI file"
  Invoke-WebRequest -Uri $patcher_cli_url -OutFile $patcher_cli_file
}

if (-Not (Test-Path $orig_apk_file)) {
  Write-Host "Downloading $apk_prefix apk"
  Get-FromApkMirror $apk_prefix $apk_version $orig_apk_file
}
$ProgressPreference = "Continue"

Write-Host "Patching $orig_apk_file"
java -jar $patcher_cli_file patch `
    --purge `
    --patches $patches_file `
    --out $patched_apk_file `
    $orig_apk_file

# adb devices
# adb install $youtube_patched_apk
# adb kill-server

# http://linuxfocus.org/~guido/windows-survival-kit/ftpdmin.html
Write-Host "Starting FTP server"
.\ftpdmin.exe -g (Get-Location).Path
