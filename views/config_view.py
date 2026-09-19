from services.regras import mascarar_cpf
from utils.paths import BASE_DIR
import os
import shutil
import sqlite3
from datetime import datetime

import customtkinter as ctk

from cores import Cores


VERSAO = "1.0.0"
DESENVOLVEDOR = "Paulo Sérgio dos Santos Fontes"
TELEFONE = "(79) 98805 6632"
DB_FILENAME = "loterias.db"
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")


class ConfigView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.scroll_frame = None

    def render(self):
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.parent.content_frame, fg_color="transparent"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self.scroll_frame,
            text="⚙️  Configurações",
            font=("Arial", 22, "bold"),
            text_color=Cores.PRIMARIO,
        ).pack(pady=(10, 20), anchor="w")

        self._render_valor_padrao()
        self._render_jogadores()
        self._render_backup()
        self._render_limpar_dados()
        self._render_estatisticas()
        self._render_sobre()

    # ------------------------------------------------------------------ #
    # VALOR PADRÃO DA APOSTA
    # ------------------------------------------------------------------ #
    def _render_valor_padrao(self):
        frame = ctk.CTkFrame(
            self.scroll_frame, fg_color="#f8f9fa", corner_radius=10,
            border_width=1, border_color="#dee2e6",
        )
        frame.pack(fill="x", pady=8, padx=10)

        ctk.CTkLabel(
            frame, text="💰  Valor Padrão da Aposta",
            font=("Arial", 16, "bold"), text_color=Cores.PRIMARIO,
        ).pack(pady=(15, 5), anchor="w", padx=15)

        ctk.CTkLabel(
            frame,
            text="Valor utilisé como padrão ao criar novas apostas:",
            font=("Arial", 12), text_color="#666",
        ).pack(anchor="w", padx=15)

        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x", padx=15, pady=(5, 15))

        ctk.CTkLabel(
            entry_frame, text="R$", font=("Arial", 14, "bold"), text_color="#333",
        ).pack(side="left", padx=(0, 5))

        self.entry_valor_padrao = ctk.CTkEntry(
            entry_frame, width=120, fg_color="white",
            text_color="#333333", border_width=1,
        )
        self.entry_valor_padrao.pack(side="left")
        self.entry_valor_padrao.insert(0, "5.00")

        ctk.CTkButton(
            entry_frame, text="Salvar", width=80,
            fg_color=Cores.PRIMARIO, hover_color="#0d3c6b",
            command=self._salvar_valor_padrao,
        ).pack(side="left", padx=10)

    def _salvar_valor_padrao(self):
        valor = self.entry_valor_padrao.get().replace(",", ".").strip()
        try:
            float(valor)
            self.parent._mostrar_toast(f"✅ Valor padrão definido: R$ {valor}")
        except ValueError:
            self.parent._mostrar_toast("❌ Valor inválido!")

    # ------------------------------------------------------------------ #
    # JOGADORES
    # ------------------------------------------------------------------ #
    def _render_jogadores(self):
        frame = ctk.CTkFrame(
            self.scroll_frame, fg_color="#f8f9fa", corner_radius=10,
            border_width=1, border_color="#dee2e6",
        )
        frame.pack(fill="x", pady=8, padx=10)

        ctk.CTkLabel(
            frame, text="👤  Jogadores",
            font=("Arial", 16, "bold"), text_color=Cores.PRIMARIO,
        ).pack(pady=(15, 5), anchor="w", padx=15)

        jogadores = self.controller.get_jogadores()
        qtd = len(jogadores)

        ctk.CTkLabel(
            frame,
            text=f"Jogadores cadastrados: {qtd}",
            font=("Arial", 13), text_color="#333",
        ).pack(anchor="w", padx=15)

        if jogadores:
            for j in jogadores[:5]:
                ctk.CTkLabel(
                    frame,
                    text=f"  • {j.nome} — CPF: {mascarar_cpf(j.cpf)}",
                    font=("Arial", 12), text_color="#555",
                ).pack(anchor="w", padx=25)

        ctk.CTkButton(
            frame, text="➕ Cadastrar Jogador", width=180,
            fg_color=Cores.PRIMARIO, hover_color="#0d3c6b",
            command=self._abrir_cadastro,
        ).pack(pady=(10, 15), padx=15, anchor="w")

    def _abrir_cadastro(self):
        self.parent.abrir_cadastro()

    # ------------------------------------------------------------------ #
    # BACKUP
    # ------------------------------------------------------------------ #
    def _render_backup(self):
        frame = ctk.CTkFrame(
            self.scroll_frame, fg_color="#f8f9fa", corner_radius=10,
            border_width=1, border_color="#dee2e6",
        )
        frame.pack(fill="x", pady=8, padx=10)

        ctk.CTkLabel(
            frame, text="💾  Backup do Banco",
            font=("Arial", 16, "bold"), text_color=Cores.PRIMARIO,
        ).pack(pady=(15, 5), anchor="w", padx=15)

        db_path = os.path.join(DATA_DIR, DB_FILENAME)
        if os.path.exists(db_path):
            tamanho = os.path.getsize(db_path)
            texto_tam = f"{tamanho / 1024:.1f} KB" if tamanho < 1024 * 1024 else f"{tamanho / (1024 * 1024):.2f} MB"
            ctk.CTkLabel(
                frame, text=f"Banco atual: {texto_tam}",
                font=("Arial", 12), text_color="#555",
            ).pack(anchor="w", padx=15)
        else:
            ctk.CTkLabel(
                frame, text="Banco não encontrado.",
                font=("Arial", 12), text_color=Cores.PERIGO,
            ).pack(anchor="w", padx=15)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(10, 15))

        ctk.CTkButton(
            btn_frame, text="📦 Criar Backup", width=150,
            fg_color=Cores.SUCESSO, hover_color="#1e7e34",
            command=self._criar_backup,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="📥 Restaurar Backup", width=160,
            fg_color=Cores.ALERTA, hover_color="#c69500",
            command=self._restaurar_backup,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="📄 Importar Apostas (CSV)", width=190,
            fg_color=Cores.PRIMARIO, command=self._importar_csv,
        ).pack(side="left")

    def _importar_csv(self):
        from tkinter import filedialog
        caminho = filedialog.askopenfilename(
            title="Importar apostas (colunas: tipo_loteria, numeros, valor, data_sorteio)",
            filetypes=[("CSV", "*.csv")])
        if not caminho:
            return
        try:
            r = self.controller.importar_apostas_csv(caminho)
        except Exception as e:
            self.parent._mostrar_toast(f"❌ Erro ao importar: {e}", erro=True)
            return
        msg = f"{r['importadas']} aposta(s) importada(s)"
        if r["erros"]:
            msg += f" | {len(r['erros'])} erro(s): {r['erros'][0]}"
        self.parent._mostrar_toast(("⚠️ " if r["erros"] else "✅ ") + msg, erro=bool(r["erros"]))

    def _criar_backup(self):
        db_path = os.path.join(DATA_DIR, DB_FILENAME)
        if not os.path.exists(db_path):
            self.parent._mostrar_toast("❌ Banco de dados não encontrado!")
            return

        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"loterias_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)

        try:
            shutil.copy2(db_path, backup_path)
            self.parent._mostrar_toast(f"✅ Backup criado: {backup_name}")
        except Exception as e:
            self.parent._mostrar_toast(f"❌ Erro ao criar backup: {e}")

    def _restaurar_backup(self):
        db_path = os.path.join(DATA_DIR, DB_FILENAME)

        if not os.path.exists(BACKUP_DIR):
            self.parent._mostrar_toast("❌ Nenhum backup encontrado!")
            return

        backups = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")],
            reverse=True,
        )
        if not backups:
            self.parent._mostrar_toast("❌ Nenhum backup encontrado!")
            return

        latest = os.path.join(BACKUP_DIR, backups[0])
        try:
            shutil.copy2(latest, db_path)
            self.parent._mostrar_toast(f"✅ Backup restaurado: {backups[0]}")
        except Exception as e:
            self.parent._mostrar_toast(f"❌ Erro ao restaurar: {e}")

    # ------------------------------------------------------------------ #
    # LIMPAR DADOS
    # ------------------------------------------------------------------ #
    def _render_limpar_dados(self):
        frame = ctk.CTkFrame(
            self.scroll_frame, fg_color="#fff3e0", corner_radius=10,
            border_width=1, border_color=Cores.PERIGO,
        )
        frame.pack(fill="x", pady=8, padx=10)

        ctk.CTkLabel(
            frame, text="🗑️  Limpar Dados",
            font=("Arial", 16, "bold"), text_color=Cores.PERIGO,
        ).pack(pady=(15, 5), anchor="w", padx=15)

        ctk.CTkLabel(
            frame,
            text="Remove todas as apostas, resultados e conferências do banco.",
            font=("Arial", 12), text_color="#666",
        ).pack(anchor="w", padx=15)

        ctk.CTkButton(
            frame, text="⚠️ Limpar Todos os Dados", width=200,
            fg_color=Cores.PERIGO, hover_color="#a83232",
            command=self._confirmar_limpar_dados,
        ).pack(pady=(10, 15), padx=15, anchor="w")

    def _confirmar_limpar_dados(self):
        popup = ctk.CTkToplevel(self.parent)
        popup.title("Confirmação")
        popup.geometry("420x200")
        popup.transient(self.parent)
        popup.grab_set()

        ctk.CTkLabel(
            popup, text="⚠️ Tem certeza?",
            font=("Arial", 18, "bold"), text_color=Cores.PERIGO,
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            popup,
            text="Todos os dados serão removidos permanentemente!\nRecomenda-se criar um backup antes.",
            font=("Arial", 13), text_color="#333",
        ).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(
            btn_frame, text="Sim, Limpar", width=120,
            fg_color=Cores.PERIGO, hover_color="#a83232",
            command=lambda: self._executar_limpar_dados(popup),
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame, text="Cancelar", width=120,
            fg_color=Cores.NEUTRO, hover_color="#4a5258",
            command=popup.destroy,
        ).pack(side="left", padx=10)

    def _executar_limpar_dados(self, popup):
        db_path = os.path.join(DATA_DIR, DB_FILENAME)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM apostas")
            cursor.execute("DELETE FROM conferencias")
            cursor.execute("DELETE FROM resultados")
            cursor.execute("DELETE FROM jogadores")
            conn.commit()
            conn.close()
            popup.destroy()
            self.parent._mostrar_toast("✅ Todos os dados foram removidos!")
            self.render()
        except Exception as e:
            popup.destroy()
            self.parent._mostrar_toast(f"❌ Erro ao limpar: {e}")

    # ------------------------------------------------------------------ #
    # ESTATÍSTICAS DO SISTEMA
    # ------------------------------------------------------------------ #
    def _render_estatisticas(self):
        frame = ctk.CTkFrame(
            self.scroll_frame, fg_color="#f8f9fa", corner_radius=10,
            border_width=1, border_color="#dee2e6",
        )
        frame.pack(fill="x", pady=8, padx=10)

        ctk.CTkLabel(
            frame, text="📊  Estatísticas do Sistema",
            font=("Arial", 16, "bold"), text_color=Cores.PRIMARIO,
        ).pack(pady=(15, 5), anchor="w", padx=15)

        stats = self.controller.get_stats()
        db_path = os.path.join(DATA_DIR, DB_FILENAME)

        db_size = "N/A"
        if os.path.exists(db_path):
            tamanho = os.path.getsize(db_path)
            db_size = f"{tamanho / 1024:.1f} KB" if tamanho < 1024 * 1024 else f"{tamanho / (1024 * 1024):.2f} MB"

        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(5, 15))
        info_frame.grid_columnconfigure((0, 1), weight=1)

        items = [
            ("Tamanho do Banco", db_size),
            ("Total de Apostas", str(stats.get("total_apostas", 0))),
            ("Total de Resultados", str(stats.get("total_resultados", 0))),
            ("Total Investido", f"R$ {stats.get('total_gasto', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
            ("Total de Acertos", str(stats.get("total_acertos", 0))),
            ("Jogadores Cadastrados", str(len(self.controller.get_jogadores()))),
        ]

        for i, (label, value) in enumerate(items):
            row, col = divmod(i, 2)
            item_frame = ctk.CTkFrame(info_frame, fg_color="white", corner_radius=8)
            item_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            ctk.CTkLabel(
                item_frame, text=label, font=("Arial", 11), text_color="#888",
            ).pack(pady=(8, 0), padx=10)
            ctk.CTkLabel(
                item_frame, text=value, font=("Arial", 15, "bold"), text_color="#333",
            ).pack(pady=(2, 10), padx=10)

        # Listar backups
        backups_frame = ctk.CTkFrame(frame, fg_color="transparent")
        backups_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            backups_frame, text="Backups disponíveis:",
            font=("Arial", 12, "bold"), text_color="#555",
        ).pack(anchor="w")

        if os.path.exists(BACKUP_DIR):
            backups = sorted(
                [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db")],
                reverse=True,
            )
            if backups:
                for b in backups[:5]:
                    b_path = os.path.join(BACKUP_DIR, b)
                    b_tam = os.path.getsize(b_path)
                    tam_str = f"{b_tam / 1024:.1f} KB" if b_tam < 1024 * 1024 else f"{b_tam / (1024 * 1024):.2f} MB"
                    ctk.CTkLabel(
                        backups_frame,
                        text=f"  • {b} ({tam_str})",
                        font=("Arial", 11), text_color="#666",
                    ).pack(anchor="w")
            else:
                ctk.CTkLabel(
                    backups_frame, text="  Nenhum backup encontrado.",
                    font=("Arial", 11, "italic"), text_color="#999",
                ).pack(anchor="w")
        else:
            ctk.CTkLabel(
                backups_frame, text="  Nenhum backup encontrado.",
                font=("Arial", 11, "italic"), text_color="#999",
            ).pack(anchor="w")

    # ------------------------------------------------------------------ #
    # SOBRE
    # ------------------------------------------------------------------ #
    def _render_sobre(self):
        frame = ctk.CTkFrame(
            self.scroll_frame, fg_color="#e3f2fd", corner_radius=10,
            border_width=2, border_color=Cores.PRIMARIO,
        )
        frame.pack(fill="x", pady=8, padx=10)

        ctk.CTkLabel(
            frame, text="ℹ️  Sobre o Sistema",
            font=("Arial", 16, "bold"), text_color=Cores.PRIMARIO,
        ).pack(pady=(15, 5), anchor="w", padx=15)

        ctk.CTkLabel(
            frame, text="🎰  Controle de Apostas Lotéricas",
            font=("Arial", 20, "bold"), text_color=Cores.PRIMARIO,
        ).pack(pady=(10, 2))

        ctk.CTkLabel(
            frame, text="Sistema de Controle de Apostas e Resultados",
            font=("Arial", 12), text_color="#666",
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            frame, text=f"Versão: {VERSAO}",
            font=("Arial", 13, "bold"), text_color="#333",
        ).pack()

        ctk.CTkLabel(
            frame, text=f"Desenvolvido por: {DESENVOLVEDOR}",
            font=("Arial", 13), text_color="#555",
        ).pack(pady=(5, 0))

        ctk.CTkLabel(
            frame, text=f"Telefone: {TELEFONE}",
            font=("Arial", 12), text_color="#555",
        ).pack()

        ctk.CTkLabel(
            frame,
            text="Python | CustomTkinter | SQLite",
            font=("Arial", 11), text_color="#888",
        ).pack(pady=(10, 15))
