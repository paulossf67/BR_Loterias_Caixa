# Gera o executável (dist\LoteriasCaixa\LoteriasCaixa.exe). Requer: pip install -r requirements-dev.txt
pyinstaller --noconfirm --windowed --name LoteriasCaixa --collect-all customtkinter main.py
# O banco (data\loterias.db), backups e boletos são criados ao lado do .exe.
