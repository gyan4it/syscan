; SysScan Agent Installer Script
; Requires NSIS (http://nsis.sourceforge.net)

;--------------------------------
; Installer Settings
;--------------------------------

Name "SysScan Agent"
OutFile "SysScanAgent_Setup.exe"
InstallDir "$PROGRAMFILES\SysScan"
RequestExecutionLevel admin  ; Require admin rights

;--------------------------------
; Pages
;--------------------------------

Page directory  ; Installation directory selection
Page instfiles  ; Installation progress

;--------------------------------
; Sections
;--------------------------------

Section "MainSection" Sec01
    ; Set output path to installation directory
    SetOutPath "$INSTDIR"
    
    ; Copy main executable
    File "SysCanAgent.exe"
    
    ; Copy dependencies (if any)
    ; File "..\venv\Lib\site-packages\..."
    
    ; Create desktop shortcut
    CreateShortcut "$DESKTOP\SysScan Agent.lnk" "$INSTDIR\SysScanAgent.exe"
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\SysScan"
    CreateShortcut "$SMPROGRAMS\SysScan\SysScan Agent.lnk" "$INSTDIR\SysScanAgent.exe"
    CreateShortcut "$SMPROGRAMS\SysScan\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    ; Add to Windows startup (runs automatically)
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" \
        "SysScanAgent" '"$INSTDIR\SysScanAgent.exe"'
    
    ; Create uninstaller
    WriteUninstaller "uninstall.exe"
    
    ; Add uninstall information to Control Panel
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SysScan" \
        "DisplayName" "SysScan Agent"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SysScan" \
        "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SysScan" \
        "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SysScan" \
        "Publisher" "SysScan Project"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SysScan" \
        "DisplayVersion" "1.0.0"
    WriteRegDword HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SysScan" \
        "NoModify" 1
    WriteRegDword HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SysScan" \
        "NoRepair" 1

SectionEnd

;--------------------------------
; Uninstaller Section
;--------------------------------

Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\SysScanAgent.exe"
    ; Delete "$INSTDIR\...\"
    
    ; Remove shortcuts
    Delete "$DESKTOP\SysScan Agent.lnk"
    Delete "$SMPROGRAMs\SysScan\SysScan Agent.lnk"
    Delete "$SMPROGRAMs\SysScan\Uninstall.lnk"
    RMDir "$SMPROGRAMs\SysScan"
    
    ; Remove from startup
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Run\SysScanAgent"
    
    ; Remove uninstall registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\SysScan"
    
    ; Remove installation directory (if empty)
    RMDir "$INSTDIR"

SectionEnd

;--------------------------------
; Functions
;--------------------------------

Function .onInstSuccess
    ; Start agent after installation
    Exec '"$INSTDIR\SysScanAgent.exe"'
    
    ; Open web UI in browser
    ExecShell "open" "http://localhost:5000"
FunctionEnd
