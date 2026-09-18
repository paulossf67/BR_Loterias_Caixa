"""Busca global (resultados e apostas)."""
import customtkinter as ctk

from cores import Cores
from services.api_service import LOTERIAS

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}


class BuscaMixin:
    def _busca_global(self, event=None):
        termo = self.entry_global_search.get().strip()
        if not termo:
            return
        self.entry_global_search.delete(0, "end")
        self._mostrar_resultado_busca(termo)

    def _mostrar_resultado_busca(self, termo: str):
        self.limpar_conteudo()
        self.current_view_name = "busca"

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text=f'🔍  Resultados para: "{termo}"',
                       font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w")

        termo_lower = termo.lower()
        resultados_encontrados = []
        apostas_encontradas = []

        for r in self.controller.get_resultados():
            nome = LOTERIAS_NOME.get(r.tipo_loteria, "").lower()
            if (termo_lower in nome or
                termo_lower in str(r.concurso) or
                termo_lower in r.data_sorteio or
                termo_lower in " ".join(str(n) for n in r.numeros_sorteados)):
                resultados_encontrados.append(r)

        for a in self.controller.get_apostas():
            nome = LOTERIAS_NOME.get(a.tipo_loteria, "").lower()
            if (termo_lower in nome or
                termo_lower in str(a.data_sorteio) or
                termo_lower in " ".join(str(n) for n in a.numeros)):
                apostas_encontradas.append(a)

        ctk.CTkLabel(scroll, text=f"📋 {len(resultados_encontrados)} resultado(s) encontrado(s):",
                       font=("Arial", 16, "bold")).pack(pady=(10, 5), anchor="w", padx=20)

        for r in resultados_encontrados[:20]:
            self._criar_card_resultado_busca(scroll, r)

        ctk.CTkLabel(scroll, text=f"🎱 {len(apostas_encontradas)} aposta(s) encontrada(s):",
                       font=("Arial", 16, "bold")).pack(pady=(20, 5), anchor="w", padx=20)

        for a in apostas_encontradas[:20]:
            self._criar_card_aposta_busca(scroll, a)

        if not resultados_encontrados and not apostas_encontradas:
            ctk.CTkLabel(scroll, text="Nenhum resultado encontrado.",
                         font=("Arial", 16, "italic"), text_color="gray").pack(pady=40)

        ctk.CTkButton(scroll, text="🔙  Voltar ao Início",
                       command=self.voltar_inicio, fg_color=Cores.NEUTRO,
                       hover_color="#4a5258").pack(pady=20)

    def _criar_card_resultado_busca(self, parent, resultado):
        card = ctk.CTkFrame(parent, fg_color="#f8f9fa", corner_radius=10,
                            border_width=1, border_color="#dee2e6")
        card.pack(fill="x", pady=5, padx=20)

        nome = LOTERIAS_NOME.get(resultado.tipo_loteria, resultado.tipo_loteria)
        ctk.CTkLabel(card, text=f"🎰 {nome} #{resultado.concurso} - {resultado.data_sorteio}",
                       font=("Arial", 13, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(8, 3), anchor="w", padx=10)
        ctk.CTkLabel(card, text=resultado.numeros_por_extenso,
                       font=("Consolas", 14, "bold"), text_color="#333").pack(
            pady=(0, 8), padx=10)

    def _criar_card_aposta_busca(self, parent, aposta):
        card = ctk.CTkFrame(parent, fg_color="#f8f9fa", corner_radius=10,
                            border_width=1, border_color="#dee2e6")
        card.pack(fill="x", pady=5, padx=20)

        nome = LOTERIAS_NOME.get(aposta.tipo_loteria, aposta.tipo_loteria)
        nums = " | ".join(str(n) for n in aposta.numeros)
        ctk.CTkLabel(card, text=f"🎱 {nome} - R$ {aposta.valor:,.2f} | Acertos: {aposta.acertos}",
                       font=("Arial", 13, "bold"), text_color="#333").pack(
            pady=(8, 3), anchor="w", padx=10)
        ctk.CTkLabel(card, text=nums, font=("Consolas", 12),
                       text_color=Cores.PRIMARIO).pack(pady=(0, 8), padx=10)
