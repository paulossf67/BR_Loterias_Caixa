; Instalador do Controle de Apostas Lotéricas (Inno Setup 6)
; Gere antes o executável com ./build.ps1; depois compile este arquivo (ver build_installer.ps1).
#define AppName "Controle de Apostas Lotéricas"
#define AppExe "ControleApostasLotericas.exe"
#define AppVersion "1.0.0"

[Setup]
AppId={{6F0B7E52-3C1D-4B0A-9E55-CA5A10B07E01}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Paulo Sérgio dos Santos Fontes
; Instala na pasta do usuário: o app grava banco, boletos e exportações ao lado do .exe
PrivilegesRequired=lowest
DefaultDirName={autopf}\ControleApostasLotericas
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=Instalador_ControleApostasLotericas_{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExe}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "dist\ControleApostasLotericas\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName}"; Flags: nowait postinstall skipifsilent

; Os dados do usuário (data\, boletos\, exports\) são criados após a instalação e
; NÃO são removidos na desinstalação, para não apagar apostas e backups.
