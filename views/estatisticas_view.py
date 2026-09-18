import customtkinter as ctk
from typing import List

from models.resultado import Resultado
from models.aposta import Aposta
from cores import Cores


class EstatisticasView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

    def render(self):
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent.content_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.scroll_frame, text="📊  Estatísticas e Análise",
                     font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(pady=(10, 20), anchor="w")

        resultados = self.controller.get_resultados()
        apostas = self.controller.get_apostas()

        if not resultados:
            ctk.CTkLabel(self.scroll_frame, text="Carregando dados...",
                         font=("Arial", 14, "italic"), text_color="gray").pack(pady=40)
            return

        # Frequência de números
        self._render_frequencia(resultados)
        self._render_porcentagem_acertos(apostas, resultados)
        self._render_numeros_quentes_frios(resultados)

    def _render_frequencia(self, resultados: List[Resultado]):
        ctk.CTkLabel(self.scroll_frame, text="📈 Frequência por Tipo de Loteria",
                     font=("Arial", 16, "bold")).pack(pady=(15, 10), anchor="w", padx=20)

        for tipo in ["mega-sena", "quina", "lotofacil", "lotomania", "timemania", "dupla-sena", "dia-de-sorte"]:
            tipos_resultados = [r for r in resultados if r.tipo_loteria == tipo]
            if not tipos_resultados:
                continue

            frame = ctk.CTkFrame(self.scroll_frame, fg_color="#f8f9fa", corner_radius=8)
            frame.pack(fill="x", pady=3, padx=20)

            nome = LOTERIAS_NOME.get(tipo, tipo)
            ctk.CTkLabel(frame, text=f"{nome}: {len(tipos_resultados)} concursos registrados",
                         font=("Arial", 13, "bold")).pack(pady=8, padx=10, anchor="w")

    def _render_porcentagem_acertos(self, apostas: List[Aposta], resultados: List[Resultado]):
        if not apostas:
            return

        ctk.CTkLabel(self.scroll_frame, text="🎯 Histórico de Acertos",
                     font=("Arial", 16, "bold")).pack(pady=(20, 10), anchor="w", padx=20)

        total = len(apostas)
        acertaram = len([a for a in apostas if a.acertos > 0])
        pct = (acertaram / total * 100) if total > 0 else 0

        frame = ctk.CTkFrame(self.scroll_frame, fg_color="#e8f5e9", corner_radius=10,
                             border_width=2, border_color=Cores.SUCESSO)
        frame.pack(fill="x", pady=5, padx=20)

        ctk.CTkLabel(frame, text=f"Taxa de Acerto: {pct:.1f}% ({acertaram}/{total} apostas)",
                     font=("Arial", 18, "bold"), text_color=Cores.SUCESSO).pack(pady=15)

    def _render_numeros_quentes_frios(self, resultados: List[Resultado]):
        ctk.CTkLabel(self.scroll_frame, text="🔥 Números Mais Sorteados",
                     font=("Arial", 16, "bold")).pack(pady=(20, 10), anchor="w", padx=20)

        from collections import Counter
        all_nums = Counter()
        for r in resultados:
            for n in r.numeros_sorteados:
                all_nums[n] += 1

        if not all_nums:
            ctk.CTkLabel(self.scroll_frame, text="Dados insuficientes para análise.",
                         font=("Arial", 12, "italic"), text_color="gray").pack(pady=10)
            return

        top_quentes = all_nums.most_common(10)
        top_frios = all_nums.most_common()[-10:]

        frame = ctk.CTkFrame(self.scroll_frame, fg_color="#fff3e0", corner_radius=10,
                             border_width=2, border_color=Cores.ALERTA)
        frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(frame, text="🔥 Quentes", font=("Arial", 13, "bold"), text_color="#e65100").pack(pady=(10, 5), anchor="w", padx=10)
        nums_str = " | ".join(f"{n} ({c}x)" for n, c in top_quentes)
        ctk.CTkLabel(frame, text=nums_str, font=("Consolas", 13)).pack(pady=(0, 10), padx=10)

        frame2 = ctk.CTkFrame(self.scroll_frame, fg_color="#e3f2fd", corner_radius=10,
                              border_width=2, border_color=Cores.PRIMARIO)
        frame2.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(frame2, text="❄️ Frios", font=("Arial", 13, "bold"), text_color=Cores.PRIMARIO).pack(pady=(10, 5), anchor="w", padx=10)
        nums_str = " | ".join(f"{n} ({c}x)" for n, c in top_frios)
        ctk.CTkLabel(frame2, text=nums_str, font=("Consolas", 13)).pack(pady=(0, 10), padx=10)


LOTERIAS_NOME = {
    "mega-sena": "Mega-Sena",
    "quina": "Quina",
    "lotofacil": "Lotofácil",
    "lotomania": "Lotomania",
    "timemania": "Timemania",
    "dupla-sena": "Dupla Sena",
    "dia-de-sorte": "Dia de Sorte",
}