[Setup]
AppName=ManteMoustache
AppVersion=1.0
DefaultDirName={autopf}\ManteMoustache
DefaultGroupName=ManteMoustache
OutputBaseFilename=Setup_ManteMoustache

[Files]
; Instala todos tus archivos normales en la carpeta de programa
Source: "dist\ManteMoustache\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs



[Icons]
Name: "{group}\ManteMoustache"; Filename: "{app}\ManteMoustache.exe"
Name: "{commondesktop}\ManteMoustache"; Filename: "{app}\ManteMoustache.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
