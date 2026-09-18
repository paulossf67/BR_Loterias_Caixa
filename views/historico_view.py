import customtkinter as ctk
from typing import List

from models.conferencia import Conferencia
from cores import Cores
from services.api_service import LOTERIAS

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}


class HistoricoView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

    def render(self):
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent.content_frame,
                                                    fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.scroll_frame, text="📜  Histórico de Conferências",
                       font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w")

        conferencias = self.controller.get_conferencias()

        stats_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 15))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        total = len(conferencias)
        ganharam = len([c for c in conferencias if c.qtd_acertos > 0])
        premio_total = sum(c.premio_ganho for c in conferencias)

        def stat_card(parent, row, col, title, value, color):
            card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10, height=80)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=title, font=("Arial", 12),
                         text_color="white").pack(pady=(12, 0))
            ctk.CTkLabel(card, text=str(value), font=("Arial", 18, "bold"),
                         text_color="white").pack()

        stat_card(stats_frame, 0, 0, "Total Conferências", total, "#1f6aa5")
        stat_card(stats_frame, 0, 1, "Com Acerto", ganharam, "#28a745")
        stat_card(stats_frame, 0, 2, "Prêmio Total", f"R$ {premio_total:,.2f}", "#6f42c1")

        self.hist_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.hist_frame.pack(fill="both", expand=True)

        self._carregar_historico(conferencias)

    def _carregar_historico(self, conferencias: List[Conferencia]):
        for widget in self.hist_frame.winfo_children():
            widget.destroy()

        if not conferencias:
            ctk.CTkLabel(self.hist_frame, text="Nenhuma conferência realizada ainda.\nVá em 'Conferir' para comparar suas apostas!",
                         font=("Arial", 16, "italic"), text_color="gray").pack(pady=60)
            return

        ctk.CTkLabel(self.hist_frame, text=f"Últimas {len(conferencias)} conferências:",
                       font=("Arial", 14, "bold")).pack(pady=(10, 5), anchor="w", padx=20)

        for c in conferencias:
            self._criar_card(c)

    def _criar_card(self, conf: Conferencia):
        cor = Cores.SUCESSO if conf.qtd_acertos > 0 else "#6c757d"
        card = ctk.CTkFrame(self.hist_frame, fg_color="#f8f9fa", corner_radius=8,
                            border_width=1, border_color="#dee2e6")
        card.pack(fill="x", pady=3, padx=20)

        header = ctk.CTkFrame(card, fg_color=cor, corner_radius=8, height=30)
        header.pack(fill="x", padx=5, pady=5)
        header.pack_propagate(False)

        nome = LOTERIAS_NOME.get(conf.tipo_loteria, conf.tipo_loteria)
        ctk.CTkLabel(header, text=f"🎰 {nome} #{conf.concurso}",
                       font=("Arial", 12, "bold"), text_color="white").pack(side="left", padx=10)
        ctk.CTkLabel(header, text=f"🎯 {conf.qtd_acertos} acerto(s)",
                       font=("Arial", 12, "bold"), text_color="white").pack(side="right", padx=10)

        nums_a = " | ".join(str(n) for n in (conf.numeros_apostados or []))
        nums_s = " | ".join(str(n) for n in (conf.numeros_sorteados or []))

        ctk.CTkLabel(card, text=f"Apostados: {nums_a}", font=("Consolas", 11),
                       text_color="#333").pack(pady=2, padx=10, anchor="w")
        ctk.CTkLabel(card, text=f"Sorteados: {nums_s}", font=("Consolas", 11),
                       text_color=Cores.PRIMARIO).pack(pady=(0, 5), padx=10, anchor="w")