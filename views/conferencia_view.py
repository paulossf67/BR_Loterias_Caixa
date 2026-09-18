import customtkinter as ctk
from typing import List, Optional

from models.resultado import Resultado
from models.aposta import Aposta
from cores import Cores

LOTERIAS_NOME = {
    "mega-sena": "Mega-Sena",
    "quina": "Quina",
    "lotofacil": "Lotofácil",
    "lotomania": "Lotomania",
    "timemania": "Timemania",
    "dupla-sena": "Dupla Sena",
    "dia-de-sorte": "Dia de Sorte",
}


class ConferênciaView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.resultado_selecionado: Optional[Resultado] = None
        self.resultado_frame = None

    def render(self):
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent.content_frame,
                                                    fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.scroll_frame, text="✅  Conferir Apostas",
                     font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w")

        info_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#e3f2fd", corner_radius=10,
                                   border_width=2, border_color=Cores.PRIMARIO)
        info_frame.pack(fill="x", pady=(0, 20), padx=20)
        ctk.CTkLabel(info_frame, text="Selecione um resultado e confira suas apostas "
                                       "contra os números sorteados.",
                     font=("Arial", 13), text_color="#1565c0").pack(pady=15, padx=15)

        self._render_selecao_resultado()

    def _render_selecao_resultado(self):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 15), padx=20)

        ctk.CTkLabel(frame, text="Resultado da vez:", font=("Arial", 14, "bold")).pack(side="left")

        self.cmb_concurso = ctk.CTkComboBox(frame, values=["Selecione..."], width=150,
                                             command=self._on_concurso_selecionado)
        self.cmb_concurso.pack(side="left", padx=10)

        resultados = self.controller.get_resultados()
        if resultados:
            options = [f"{LOTERIAS_NOME.get(r.tipo_loteria, r.tipo_loteria)} "
                       f"#{r.concurso} - {r.data_sorteio}"
                       for r in resultados]
            self.cmb_concurso.configure(values=options)
            self.cmb_concurso.select(0)
            self.resultado_selecionado = resultados[0]
            self.lbl_numeros = ctk.CTkLabel(frame, text=f"Números: "
                                                          f"{resultados[0].numeros_por_extenso}",
                                             font=("Consolas", 14, "bold"),
                                             text_color=Cores.PRIMARIO)
            self.lbl_numeros.pack(side="left", padx=20)
        else:
            self.lbl_numeros = ctk.CTkLabel(frame, text="", font=("Consolas", 14, "bold"),
                                             text_color=Cores.PRIMARIO)
            self.lbl_numeros.pack(side="left", padx=20)

        self.apostas_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.apostas_frame.pack(fill="both", expand=True, padx=20)
        self._render_apostas_para_conferencia()

    def _on_concurso_selecionado(self, value):
        if not value or value == "Selecione...":
            return
        self.resultado_selecionado = self.controller.get_resultado_by_string(value)
        if self.resultado_selecionado:
            self.lbl_numeros.configure(text=f"Números sorteados: "
                                             f"{self.resultado_selecionado.numeros_por_extenso}")
            self._render_apostas_para_conferencia()

    def _render_apostas_para_conferencia(self):
        for widget in self.apostas_frame.winfo_children():
            widget.destroy()

        apostas = self.controller.get_apostas()
        if not apostas:
            ctk.CTkLabel(self.apostas_frame, text="Nenhuma aposta cadastrada.",
                         font=("Arial", 14, "italic"), text_color="gray").pack(pady=20)
            return

        if not self.resultado_selecionado:
            ctk.CTkLabel(self.apostas_frame, text="Selecione um concurso para conferir.",
                         font=("Arial", 14, "italic"), text_color="gray").pack(pady=20)
            return

        ctk.CTkLabel(self.apostas_frame, text="Confronto:",
                     font=("Arial", 16, "bold")).pack(pady=(10, 10), anchor="w", padx=20)

        for a in apostas:
            self._criar_card_conferencia(a, self.resultado_selecionado)

    def _criar_card_conferencia(self, aposta: Aposta, resultado: Resultado):
        acertos = self._calcular_acertos(aposta.numeros, resultado.numeros_sorteados)
        cor_fundo = "#c8e6c9" if acertos > 0 else "#ffcdd2"
        cor_borda = Cores.SUCESSO if acertos > 0 else Cores.PERIGO

        card = ctk.CTkFrame(self.apostas_frame, fg_color=cor_fundo, corner_radius=10,
                             border_width=2, border_color=cor_borda)
        card.pack(fill="x", pady=5, padx=20)

        header = ctk.CTkFrame(card, fg_color=cor_borda, corner_radius=10)
        header.pack(fill="x", padx=5, pady=5)

        nome = LOTERIAS_NOME.get(aposta.tipo_loteria, aposta.tipo_loteria)
        ctk.CTkLabel(header, text=f"🎰 {nome} - Concurso {aposta.data_sorteio}",
                      font=("Arial", 13, "bold"), text_color="white").pack(side="left", padx=10)
        ctk.CTkLabel(header, text=f"🎯 {acertos} acerto(s)",
                      font=("Arial", 13, "bold"), text_color="white").pack(side="right", padx=10)

        nums_apostados = " | ".join(str(n) for n in aposta.numeros)
        ctk.CTkLabel(card, text=f"Seus números: {nums_apostados}",
                      font=("Consolas", 13)).pack(pady=5, padx=10, anchor="w")

        nums_sorteados = resultado.numeros_por_extenso
        ctk.CTkLabel(card, text=f"Sorteados: {nums_sorteados}",
                      font=("Consolas", 13), text_color="#333").pack(pady=(0, 5), padx=10)

        if acertos > 0:
            premio = self._calcular_premio(acertos, aposta.valor)
            ctk.CTkLabel(card, text=f"💵 Prêmio estimado: R$ {premio:,.2f}",
                          font=("Arial", 13, "bold"), text_color=Cores.SUCESSO).pack(
                pady=(0, 8), padx=10)

    def _calcular_acertos(self, meus_numeros: list, sorteados: list) -> int:
        return len(set(meus_numeros) & set(sorteados))

    def _calcular_premio(self, acertos: int, valor_aposta: float) -> float:
        multiplicadores = {6: 1000, 5: 50, 4: 10, 3: 5, 2: 2, 1: 1, 0: 0}
        return valor_aposta * multiplicadores.get(acertos, 0)