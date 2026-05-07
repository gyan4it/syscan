# SysCanAgent PowerShell Installer Script
# Alternative to NSIS - works without external tools

param(
    [string]$InstallDir = "$env:ProgramFiles\SysCan",
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

if ($Uninstall) {
    Write-Host "Uninstalling SysCanAgent..." -ForegroundColor Yellow
    
    # Remove files
    if (Test-Path $InstallDir) {
        Remove-Item -Path $InstallDir -Recurse -Force
        Write-Host "Removed: $InstallDir" -ForegroundColor Green
    }
    
    # Remove registry entries
    $regPaths = @(
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SysCanAgent",
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SysCanAgent"
    )
    
    foreach ($regPath in $regPaths) {
        if (Test-Path $regPath) {
            Remove-Item -Path $regPath -Recurse -Force
            Write-Host "Removed registry: $regPath" -ForegroundColor Green
        }
    }
    
    # Remove Start Menu shortcut
    $startMenu = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\SysCan"
    if (Test-Path $startMenu) {
        Remove-Item -Path $startMenu -Recurse -Force
        Write-Host "Removed Start Menu folder" -ForegroundColor Green
    }
    
    Write-Host "Uninstallation complete!" -ForegroundColor Green
    exit 0
}

# Installation
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "SysCan Agent Installer" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Check admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: Administrator rights required!" -ForegroundColor Red
    Write-Host "Right-click and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Create install directory
if (-not (Test-Path $InstallDir)) {
    New-Item -Path $InstallDir -ItemType Directory -Force | Out-Null
    Write-Host "Created: $InstallDir" -ForegroundColor Green
}

# Copy EXE
$sourceExe = "SysCanAgent.exe"
if (-not (Test-Path $sourceExe)) {
    # Try to find it
    $found = Get-ChildItem -Path . -Recurse -Filter "SysCanAgent.exe" | Select-Object -First 1
    if ($found) {
        $sourceExe = $found.FullName
    } else {
        Write-Host "ERROR: SysCanAgent.exe not found!" -ForegroundColor Red
        exit 1
    }
}

Copy-Item -Path $sourceExe -Destination "$InstallDir\SysCanAgent.exe" -Force
Write-Host "Installed: $InstallDir\SysCanAgent.exe" -ForegroundColor Green

# Create Start Menu shortcut
$startMenuDir = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\SysCan"
if (-not (Test-Path $startMenuDir)) {
    New-Item -Path $startMenuDir -ItemType Directory -Force | Out-Null
}

$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$startMenuDir\SysCan Agent.lnk")
$Shortcut.TargetPath = "$InstallDir\SysCanAgent.exe"
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "SysCan Background Agent"
$Shortcut.Save()
Write-Host "Created Start Menu shortcut" -ForegroundColor Green

# Add to registry (for Programs & Features)
$regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SysCanAgent"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty -Path $regPath -Name "DisplayName" -Value "SysCan Agent"
Set-ItemProperty -Path $regPath -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$InstallDir\install.ps1`" -Uninstall"
Set-ItemProperty -Path $regPath -Name "Publisher" -Value "SysCan Project"
Set-ItemProperty -Path $regPath -Name "DisplayVersion" -Value "1.0.0"
Set-ItemProperty -Path $regPath -Name "InstallLocation" -Value $InstallDir
Write-Host "Added to Programs & Features" -ForegroundColor Green

# Copy this installer script to install dir
Copy-Item -Path $MyInvocation.MyCommand.Path -Destination "$InstallDir\install.ps1" -Force

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "SysCan Agent installed to: $InstallDir" -ForegroundColor Yellow
Write-Host "Start Menu: Programs > SysCan > SysCan Agent" -ForegroundColor Yellow
Write-Host "Uninstall: Use 'Programs & Features' or run: .\install.ps1 -Uninstall" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan
