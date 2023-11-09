; -- helpr.iss --
; Creates icon in the Programs folder of the Start Menu and creates a desktop icon.

[Setup]
WizardStyle=modern
AppName=HELPR
AppVersion=1.0.0
AppCopyright=Copyright 2023 National Technology & Engineering Solutions of Sandia, LLC (NTESS).\nUnder the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.\n\nYou should have received a copy of the BSD License along with HELPR.
AppPublisher=Sandia National Laboratories
AppPublisherURL=https://helpr.sandia.gov/

WizardSmallImageFile=icon55.bmp
WizardImageFile=icon410x797.bmp
DefaultDirName={autopf}\Sandia National Laboratories\HELPR
UsePreviousAppDir=no
DisableDirPage=auto
LicenseFile=license_win.rtf
AllowNoIcons=yes

DefaultGroupName=Sandia National Laboratories\HELPR
DisableProgramGroupPage=auto

UninstallDisplayIcon={app}\HELPR.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
SetupIconFile=icon.ico

[Files]
Source: "dist\HELPR\*"; DestDir: "{app}"; Excludes: "*.pyc"; Flags: ignoreversion recursesubdirs;
; Source: "MyProg.chm"; DestDir: "{app}"
; Source: "Readme.txt"; DestDir: "{app}"; Flags: isreadme

[Icons]
Name: "{group}\HELPR"; Filename: "{app}\HELPR.exe"
Name: "{autodesktop}\HELPR"; Filename: "{app}\HELPR.exe"