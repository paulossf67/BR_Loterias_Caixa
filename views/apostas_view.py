import customtkinter as ctk
from typing import List
from datetime import datetime

from models.aposta import Aposta
from cores import Cores


class ApostasView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.lista_loterias = [
            "mega-sena", "quina", "lotofacil", "lotomania",
            "timemania", "dupla-sena", "dia-de-sorte"
        ]

    def render(self):
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent.content_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.scroll_frame, text="🎱  Minhas Apostas",
                     font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(pady=(10, 20), anchor="w")

        stats_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 15))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        apostas = self.controller.get_apostas()
        total_gasto = sum(a.valor for a in apostas)
        total_apostas = len(apostas)
        total_acertos = sum(a.acertos for a in apostas)

        def stat_card(parent, row, col, title, value, color):
            card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10, height=80)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=title, font=("Arial", 12), text_color="white").pack(pady=(10, 0))
            ctk.CTkLabel(card, text=str(value), font=("Arial", 18, "bold"), text_color="white").pack()

        stat_card(stats_frame, 0, 0, "Total de Apostas", total_apostas, "#1f6aa5")
        stat_card(stats_frame, 0, 1, "Total Investido", f"R$ {total_gasto:,.2f}", "#28a745")
        stat_card(stats_frame, 0, 2, "Total Acertos", total_acertos, "#E0A800")

        acoes_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        acoes_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(acoes_frame, text="➕ Nova Aposta", command=self.controller.nova_aposta,
                      fg_color=Cores.PRIMARIO, hover_color="#0d3c6b").pack(side="left", padx=5)
        ctk.CTkButton(acoes_frame, text="📊 Conferir Apostas", command=self.controller.conferir_apostas,
                      fg_color=Cores.ALERTA, hover_color="#c69500").pack(side="left", padx=5)
        ctk.CTkButton(acoes_frame, text="📄 Exportar", command=self.controller.exportar_apostas,
                      fg_color=Cores.DOCUMENTO, hover_color="#563389").pack(side="left", padx=5)

        self.apostas_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.apostas_frame.pack(fill="both", expand=True)

        self._carregar_apostas()

    def _carregar_apostas(self):
        for widget in self.apostas_frame.winfo_children():
            widget.destroy()

        apostas = self.controller.get_apostas()
        if not apostas:
            ctk.CTkLabel(self.apostas_frame, text="Nenhuma aposta cadastrada.\nClique em 'Nova Aposta' para começar!",
                         font=("Arial", 16, "italic"), text_color="gray").pack(pady=60)
            return

        for a in apostas:
            self._criar_card_aposta(a)

    def _criar_card_aposta(self, aposta: Aposta):
        card = ctk.CTkFrame(self.apostas_frame, fg_color="#f8f9fa", corner_radius=10,
                            border_width=1, border_color="#dee2e6")
        card.pack(fill="x", pady=5, padx=10)

        header = ctk.CTkFrame(card, fg_color=Cores.PRIMARIO if aposta.acertos > 0 else "#6c757d",
                              corner_radius=10, height=35)
        header.pack(fill="x", padx=5, pady=5)
        header.pack_propagate(False)

        nome = LOTERIAS_NOME.get(aposta.tipo_loteria, aposta.tipo_loteria)
        ctk.CTkLabel(header, text=f"🎰 {nome}  |  Concurso #{aposta.data_sorteio}",
                     font=("Arial", 13, "bold"), text_color="white").pack(side="left", padx=10)
        status = "✅ ACERTOU!" if aposta.acertos > 0 else "⏳ Pendente"
        ctk.CTkLabel(header, text=status, font=("Arial", 12, "bold"),
                     text_color="white").pack(side="right", padx=10)

        numeros_str = " | ".join(str(n) for n in aposta.numeros)
        ctk.CTkLabel(card, text=f"🎱 {numeros_str}", font=("Consolas", 14),
                     text_color="#333").pack(pady=8, padx=10)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=(0, 5))

        info = f"💰 Valor: R$ {aposta.valor:,.2f}  |  🎯 Acertos: {aposta.acertos}  |  💵 Prêmio: R$ {aposta.premio:,.2f}"
        ctk.CTkLabel(info_frame, text=info, font=("Arial", 11), text_color="#555").pack(side="left")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 8))
        btn_frame.pack_propagate(False)

        ctk.CTkButton(btn_frame, text="🗑️ Excluir", width=80, command=lambda id=aposta.id: self.controller.remover_aposta(id),
                      fg_color=Cores.PERIGO, hover_color="#a83232").pack(side="right", padx=5)


LOTERIAS_NOME = {
    "mega-sena": "Mega-Sena",
    "quina": "Quina",
    "lotofacil": "Lotofácil",
    "lotomania": "Lotomania",
    "timemania": "Timemania",
    "dupla-sena": "Dupla Sena",
    "dia-de-sorte": "Dia de Sorte",
}