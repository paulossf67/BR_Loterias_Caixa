"""Exportação, relógio e status do sistema."""
import threading
from datetime import datetime

import customtkinter as ctk

try:
    import psutil
except ImportError:
    psutil = None

from cores import Cores


class SistemaMixin:
    # ------------------------------------------------------------------ #
    # EXPORTAÇÃO
    # ------------------------------------------------------------------ #
    def mostrar_exportacao(self, texto: str):
        self.limpar_conteudo()
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="📄  Relatório de Apostas",
                       font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w", padx=20)

        frame_info = ctk.CTkFrame(scroll, fg_color="#e3f2fd", corner_radius=10,
                                      border_width=2, border_color=Cores.PRIMARIO)
        frame_info.pack(fill="x", pady=(0, 15), padx=20)
        ctk.CTkLabel(frame_info, text=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                                          f"Total de apostas: {len(self.controller.get_apostas())}",
                       font=("Arial", 12), text_color="#1565c0").pack(pady=15, padx=15)

        text_box = ctk.CTkTextbox(scroll, width=800, height=400, font=("Consolas", 12))
        text_box.pack(pady=10, padx=20, fill="both", expand=True)
        text_box.insert("1.0", texto)

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="📋 Copiar para Área de Transferência",
                         command=lambda: self._copiar_texto(texto),
                         fg_color=Cores.PRIMARIO).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="💾 Salvar em Arquivo",
                         command=lambda: self._salvar_arquivo(texto),
                         fg_color=Cores.SUCESSO).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙 Voltar",
                         command=self.abrir_apostas,
                         fg_color=Cores.NEUTRO).pack(side="left", padx=10)

    def _copiar_texto(self, texto: str):
        self.clipboard_clear()
        self.clipboard_append(texto)
        self._mostrar_toast("✅ Texto copiado!")

    def _salvar_arquivo(self, texto: str):
        filename = f"relatorio_loterias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = f"G:/Python/BR_Loterias_Caixa/{filename}"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(texto)
            self._mostrar_toast(f"✅ Relatório salvo: {filepath}")
        except Exception as e:
            self._mostrar_toast(f"❌ Erro ao salvar: {str(e)}")

    # ------------------------------------------------------------------ #
    # RELÓGIO / STATUS
    # ------------------------------------------------------------------ #
    def atualizar_tempo(self):
        agora = datetime.now()
        self.lbl_hora.configure(text=agora.strftime("%H:%M:%S"))
        self.lbl_data.configure(text=agora.strftime("%d/%m/%Y"))
        self.after(1000, self.atualizar_tempo)

    def atualizar_status_sistema(self):
        if psutil:
            try:
                import os
                processo = psutil.Process(os.getpid())
                mem_mb = processo.memory_info().rss / 1024 / 1024
                cpu = processo.cpu_percent(interval=None)
                self.lbl_status_sistema.configure(text=f"CPU: {cpu:.1f}% | RAM: {mem_mb:.1f} MB")
            except Exception:
                self.lbl_status_sistema.configure(text="Erro ao ler status")
        else:
            self.lbl_status_sistema.configure(text="Instale 'psutil' para ver status")
        self.after(2000, self.atualizar_status_sistema)

    def atualizar_status_conexao(self):
        def checar():
            try:
                resp = self.controller.api_service.session.get(
                    "https://httpbin.org/get", timeout=5)
                net_ok = resp.status_code == 200
            except Exception:
                net_ok = False

            db_ok = True
            if self.winfo_exists():
                self.after(0, lambda: self._atualizar_status_conexao_ui(net_ok, db_ok))

        threading.Thread(target=checar, daemon=True).start()
        self.after(15000, self.atualizar_status_conexao)

    def _atualizar_status_conexao_ui(self, net_ok, db_ok):
        self.lbl_status_conexao.configure(text=f"NET: {'OK' if net_ok else 'OFF'} | DB: {'OK' if db_ok else 'OFF'}")
        if net_ok and db_ok:
            self.lbl_status_conexao.configure(text_color="#32a852")
        elif net_ok or db_ok:
            self.lbl_status_conexao.configure(text_color="#E0A800")
        else:
            self.lbl_status_conexao.configure(text_color="#d9534f")
