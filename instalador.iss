; Instalador da Caixa de Ferramentas (Inno Setup 6)
; Gera um .exe de "um clique" que instala a Caixa + as 16 ferramentas (por usuário, sem admin).
; Compilar com:  ISCC.exe instalador.iss   (depois de rodar build_suite.py)

#define AppName "Caixa de Ferramentas"
#define AppVer "1.0.0"
#define AppPublisher "caionicfilho89-dot"
#define MainExe "Caixa.exe"

[Setup]
AppId={{C41A0B0C-CA10-4CA1-A070-CA1X0FERRAM}}
AppName={#AppName}
AppVersion={#AppVer}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\Programs\Caixa de Ferramentas
DefaultGroupName=Caixa de Ferramentas
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=instalador
OutputBaseFilename=CaixaDeFerramentas-Setup-{#AppVer}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#MainExe}

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Atalhos:"
Name: "startupicon"; Description: "Abrir a Caixa junto com o Windows"; GroupDescription: "Início:"; Flags: unchecked

[Files]
Source: "dist\Caixa\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Caixa de Ferramentas"; Filename: "{app}\{#MainExe}"
Name: "{group}\Desinstalar Caixa de Ferramentas"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Caixa de Ferramentas"; Filename: "{app}\{#MainExe}"; Tasks: desktopicon
Name: "{userstartup}\Caixa de Ferramentas"; Filename: "{app}\{#MainExe}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MainExe}"; Description: "Abrir a Caixa de Ferramentas agora"; Flags: nowait postinstall skipifsilent
