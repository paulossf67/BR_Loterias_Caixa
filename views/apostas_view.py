import customtkinter as ctk
from typing import List
from datetime import datetime

from models.aposta import Aposta
from cores import Cores
from services.api_service import LOTERIAS

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}


class ApostasView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.scroll_frame = None
        self.stats_frame = None
        self.apostas_frame = None

    def render(self):
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent.content_frame,
                                                    fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.scroll_frame, text="🎱  Minhas Apostas",
                       font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w")

        self._render_stats()

        acoes_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        acoes_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(acoes_frame, text="➕ Nova Aposta",
                        command=self.controller.nova_aposta,
                        fg_color=Cores.PRIMARIO, hover_color="#0d3c6b").pack(
            side="left", padx=5)
        ctk.CTkButton(acoes_frame, text="🖨️ Imprimir Selecionada",
                        command=self._imprimir_selecionada,
                        fg_color="#007bff", hover_color="#0056b3").pack(
            side="left", padx=5)
        ctk.CTkButton(acoes_frame, text="📊 Conferir",
                        command=self.controller.conferir_apostas,
                        fg_color=Cores.ALERTA, hover_color="#c69500").pack(
            side="left", padx=5)
        ctk.CTkButton(acoes_frame, text="📄 Exportar",
                        command=self.controller.exportar_apostas,
                        fg_color=Cores.DOCUMENTO, hover_color="#563389").pack(
            side="left", padx=5)

        self.apostas_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.apostas_frame.pack(fill="both", expand=True)

        self._carregar_apostas()

    def _render_stats(self):
        if self.scroll_frame:
            for w in self.scroll_frame.winfo_children():
                if hasattr(w, '_eh_stats_frame') and w._eh_stats_frame:
                    w.destroy()

        apostas = self.controller.get_apostas()
        total_gasto = sum(a.valor for a in apostas)
        total_apostas = len(apostas)
        total_acertos = sum(a.acertos for a in apostas)
        premio_total = sum(a.premio for a in apostas)

        self.stats_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 15))
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.stats_frame._eh_stats_frame = True

        def stat_card(parent, row, col, title, value, color):
            card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10, height=80)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=title, font=("Arial", 12),
                         text_color="white").pack(pady=(12, 0))
            ctk.CTkLabel(card, text=str(value), font=("Arial", 18, "bold"),
                         text_color="white").pack()

        stat_card(self.stats_frame, 0, 0, "Total Apostas", total_apostas, "#1f6aa5")
        stat_card(self.stats_frame, 0, 1, "Total Investido", f"R$ {total_gasto:,.2f}", "#28a745")
        stat_card(self.stats_frame, 0, 2, "Total Acertos", total_acertos, "#E0A800")
        stat_card(self.stats_frame, 0, 3, "Prêmio Total", f"R$ {premio_total:,.2f}", "#6f42c1")

    def _carregar_apostas(self):
        for widget in self.apostas_frame.winfo_children():
            widget.destroy()

        apostas = self.controller.get_apostas()
        if not apostas:
            ctk.CTkLabel(self.apostas_frame,
                         text="Nenhuma aposta cadastrada.\nClique em 'Nova Aposta' para começar!",
                         font=("Arial", 16, "italic"), text_color="gray").pack(pady=60)
            return

        for a in apostas:
            self._criar_card_aposta(a)

    def _criar_card_aposta(self, aposta: Aposta):
        cor_header = Cores.SUCESSO if aposta.acertos > 0 else "#6c757d"
        card = ctk.CTkFrame(self.apostas_frame, fg_color="#f8f9fa", corner_radius=10,
                            border_width=1, border_color="#dee2e6")
        card.pack(fill="x", pady=5, padx=10)

        header = ctk.CTkFrame(card, fg_color=cor_header, corner_radius=10, height=35)
        header.pack(fill="x", padx=5, pady=5)
        header.pack_propagate(False)

        nome = LOTERIAS_NOME.get(aposta.tipo_loteria, aposta.tipo_loteria)
        ctk.CTkLabel(header, text=f"🎰 {nome}  |  Concurso #{aposta.data_sorteio}",
                       font=("Arial", 13, "bold"), text_color="white").pack(
            side="left", padx=10)
        status = "✅ ACERTOU!" if aposta.acertos > 0 else "⏳ Pendente"
        ctk.CTkLabel(header, text=status, font=("Arial", 12, "bold"),
                       text_color="white").pack(side="right", padx=10)

        numeros_str = " | ".join(str(n) for n in aposta.numeros)
        ctk.CTkLabel(card, text=f"🎱 {numeros_str}", font=("Consolas", 14),
                       text_color="#333").pack(pady=8, padx=10)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=(0, 5))

        info = (f"💰 Valor: R$ {aposta.valor:,.2f}  |  "
                f"🎯 Acertos: {aposta.acertos}  |  "
                f"💵 Prêmio: R$ {aposta.premio:,.2f}")
        ctk.CTkLabel(info_frame, text=info, font=("Arial", 11),
                       text_color="#555").pack(side="left")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 8))
        btn_frame.pack_propagate(False)

        ctk.CTkButton(btn_frame, text="🖨️ Registro", width=80,
                        command=lambda a=aposta: self.controller.imprimir_boleto(a),
                        fg_color="#007bff", hover_color="#0056b3").pack(
            side="left", padx=5)
        ctk.CTkButton(btn_frame, text="👁️ Detalhes", width=80,
                        command=lambda a=aposta: self.parent.mostrar_detalhes_aposta(a),
                        fg_color=Cores.PRIMARIO, hover_color="#0d3c6b").pack(
            side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑️ Excluir", width=80,
                        command=lambda id=aposta.id: self.controller.remover_aposta(id),
                        fg_color=Cores.PERIGO, hover_color="#a83232").pack(
            side="right", padx=5)

    def _imprimir_selecionada(self):
        apostas = self.controller.get_apostas()
        if not apostas:
            self.parent._mostrar_toast("Nenhuma aposta para imprimir")
            return
        self.controller.imprimir_boleto(apostas[0])