[Setup]
AppName=MTSistem
AppVersion=1.0
DefaultDirName={pf}\MTSistem
DefaultGroupName=MTSistem
OutputDir=installer
OutputBaseFilename=MTSistem_Setup
Compression=lzma
SolidCompression=yes
SetupIconFile=Icones\logo.ico
WizardStyle=modern

[Files]
Source: "dist\MTSistem\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\MTSistem"; Filename: "{app}\MTSistem.exe"
Name: "{commondesktop}\MTSistem"; Filename: "{app}\MTSistem.exe"

[Run]
Filename: "{app}\MTSistem.exe"; Description: "Executar MTSistem"; Flags: nowait postinstall skipifsilent
