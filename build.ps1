# Gera o executável (dist\ControleApostasLotericas\ControleApostasLotericas.exe). Requer: pip install -r requirements-dev.txt
pyinstaller --noconfirm --windowed --name ControleApostasLotericas --collect-all customtkinter main.py
# O banco (data\loterias.db), backups e boletos são criados ao lado do .exe.
