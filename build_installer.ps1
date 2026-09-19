# Gera o instalador (installer\Instalador_ControleApostasLotericas_<versão>.exe).
# Requer o Inno Setup 6 (winget install JRSoftware.InnoSetup) e o executável gerado por ./build.ps1.
$iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe") |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 não encontrado." }
if (-not (Test-Path dist\ControleApostasLotericas\ControleApostasLotericas.exe)) { ./build.ps1 }
& $iscc installer.iss
