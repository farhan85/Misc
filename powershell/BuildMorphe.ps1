[CmdletBinding(PositionalBinding=$false)]
param(
  [switch][Alias("y")]$Youtube,
  [switch][Alias("m")]$YoutubeMusic
)

if ($Youtube) {
  $package_name = "com.google.android.youtube"
  $apk_prefix = "youtube"
  $apk_arch = "universal"
} elseif ($YoutubeMusic) {
  $package_name = "com.google.android.apps.youtube.music"
  $apk_prefix = "youtube-music"
  $apk_arch = "arm64-v8a"
} else {
  Write-Error -Message "Missing params. Must provide either:"
  Write-Error -Message "  -Youtube/-y"
  Write-Error -Message "  -YoutubeMusic/-m"
  Exit 1
}

$tokenPath = "$PSScriptRoot\github_token.txt"
if (-not (Test-Path -Path $tokenPath)) {
    Write-Error "Error: Missing GitHub token file"
    Exit 1
}

# Generate new token: https://github.com/settings/personal-access-tokens/new
$githubToken = (Get-Content -Path $tokenPath -Raw).Trim()

$githubHeaders = @{
  "Authorization"        = "Bearer $githubToken"
  "Accept"               = "application/vnd.github.v3+json"
  "X-GitHub-Api-Version" = "2022-11-28"
}

function Get-LatestVersionGithub($repo) {
  Invoke-RestMethod -Uri "https://api.github.com/repos/${repo}/releases/latest" -Headers $githubHeaders -Method Get
    | Select-Object -First 1
    | Select-Object -ExpandProperty tag_name
    | ForEach-Object { $_.TrimStart("v") }
}

function Get-YoutubeVersion($patches_json_url, $package_name) {
  return (Invoke-RestMethod -Uri $patches_json_url -Headers $githubHeaders -Method Get).patches.compatiblePackages |
    Where-Object { $_.packageName -eq $package_name } |
    ForEach-Object { $_.targets } |
    Where-Object { $_.isExperimental -eq $false } |
    Sort-Object { [version]$_.version } -Descending |
    Select-Object -First 1 |
    Select-Object -ExpandProperty version
}

function Get-FromApkMirror($repo, $version, $output) {
  $appsConfig = @{
    apps = @(@{
      org = "google-inc"
      repo = $repo
      version = $version
      arch = $apk_arch
      outFile = $output
    })
  }

  $appsConfig | ConvertTo-Json | Set-Content -Path "apps.json" -Encoding UTF8

  # https://github.com/tanishqmanuja/apkmirror-downloader
  .\apkmd.exe apps.json
}

$patches_repo = "MorpheApp/morphe-patches"
$cli_repo = "MorpheApp/morphe-desktop"

$patches_version = Get-LatestVersionGithub $patches_repo
$cli_version = Get-LatestVersionGithub $cli_repo

$patches_file = "patches-${patches_version}.mpp"
$patcher_cli_file = "morphe-desktop-${cli_version}-all.jar"

$patches_json = "https://raw.githubusercontent.com/${patches_repo}/refs/heads/main/patches-list.json"
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
  Invoke-WebRequest -Uri $patches_url -Headers $githubHeaders -Method Get -OutFile $patches_file
}

if (-Not (Test-Path $patcher_cli_file)) {
  Write-Host "Downloading CLI file"
  Invoke-WebRequest -Uri $patcher_cli_url -Headers $githubHeaders -Method Get -OutFile $patcher_cli_file
}

if (-Not (Test-Path $orig_apk_file)) {
  Write-Host "Downloading $apk_prefix apk"
  Get-FromApkMirror $apk_prefix $apk_version $orig_apk_file
}
$ProgressPreference = "Continue"

Write-Host "Patching $orig_apk_file"
java -jar $patcher_cli_file patch `
    -p $patches_file `
    -o $patched_apk_file `
    $orig_apk_file

# adb devices
# adb install $youtube_patched_apk
# adb kill-server

# http://linuxfocus.org/~guido/windows-survival-kit/ftpdmin.html
Write-Host "Starting FTP server"
.\ftpdmin.exe -g (Get-Location).Path
