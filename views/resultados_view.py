import customtkinter as ctk
from typing import List, Optional

from models.resultado import Resultado
from models.aposta import Aposta
from cores import Cores


class ResultadosView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.scroll_frame = None

    def render(self):
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent.content_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.scroll_frame, text="📋  Resultados das Loterias",
                     font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(pady=(10, 20), anchor="w")

        filtro_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        filtro_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(filtro_frame, text="Filtrar por loteria:", font=("Arial", 13)).pack(side="left")
        self.cmb_loteria = ctk.CTkComboBox(filtro_frame, values=[
            "Todas", "mega-sena", "quina", "lotofacil", "lotomania", "timemania", "dupla-sena", "dia-de-sorte"
        ], width=200, command=self._filtrar)
        self.cmb_loteria.pack(side="left", padx=10)
        self.cmb_loteria.select("Todas")

        self.btn_atualizar = ctk.CTkButton(filtro_frame, text="🔄 Atualizar",
                                           command=self.controller.sync_and_refresh,
                                           fg_color=Cores.PRIMARIO, hover_color="#0d3c6b")
        self.btn_atualizar.pack(side="left", padx=10)

        self.resultados_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.resultados_frame.pack(fill="both", expand=True)

        self._carregar_resultados()

    def _carregar_resultados(self):
        for widget in self.resultados_frame.winfo_children():
            widget.destroy()

        resultados = self.controller.get_resultados()
        if not resultados:
            ctk.CTkLabel(self.resultados_frame, text="Nenhum resultado disponível.",
                         font=("Arial", 14, "italic"), text_color="gray").pack(pady=40)
            return

        for r in resultados[:30]:
            self._criar_card_resultado(r)

    def _criar_card_resultado(self, resultado: Resultado):
        card = ctk.CTkFrame(self.resultados_frame, fg_color="#f8f9fa", corner_radius=10,
                            border_width=1, border_color="#dee2e6")
        card.pack(fill="x", pady=5, padx=10)
        card.configure(cursor="hand2")
        card.bind("<Button-1>", lambda e, r=resultado: self._abrir_detalhes(r))

        header_frame = ctk.CTkFrame(card, fg_color=Cores.PRIMARIO, corner_radius=10)
        header_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(header_frame, text=f"🎰 {LOTERIAS_NOME.get(resultado.tipo_loteria, resultado.tipo_loteria)}",
                     font=("Arial", 14, "bold"), text_color="white").pack(side="left", padx=10)
        ctk.CTkLabel(header_frame, text=f"Concurso: #{resultado.concurso}",
                     font=("Arial", 13), text_color="white").pack(side="left", padx=10)
        ctk.CTkLabel(header_frame, text=resultado.data_sorteio,
                     font=("Arial", 12), text_color="white").pack(side="right", padx=10)

        numeros_frame = ctk.CTkFrame(card, fg_color="transparent")
        numeros_frame.pack(pady=8)

        numeros_str = resultado.numeros_por_extenso
        ctk.CTkLabel(numeros_frame, text=numeros_str,
                     font=("Consolas", 18, "bold"), text_color="#1f6aa5").pack(pady=5)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=(0, 10))

        info_text = f"🏆 Prêmio: R$ {resultado.premio_acumulado:,.2f}  |  👥 Ganhadores: {resultado.ganhadores}  |  💰 Arrecadação: R$ {resultado.arrecadacao_total:,.2f}"
        ctk.CTkLabel(info_frame, text=info_text, font=("Arial", 11), text_color="#555").pack()

    def _abrir_detalhes(self, resultado: Resultado):
        self.controller.mostrar_detalhes_resultado(resultado)

    def _filtrar(self, value):
        self._carregar_resultados()


LOTERIAS_NOME = {
    "mega-sena": "Mega-Sena",
    "quina": "Quina",
    "lotofacil": "Lotofácil",
    "lotomania": "Lotomania",
    "timemania": "Timemania",
    "dupla-sena": "Dupla Sena",
    "dia-de-sorte": "Dia de Sorte",
}