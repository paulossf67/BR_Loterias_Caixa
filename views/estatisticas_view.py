import customtkinter as ctk
from typing import List
from collections import Counter

from models.resultado import Resultado
from models.aposta import Aposta
from cores import Cores
from services.api_service import LOTERIAS
from services import estatisticas as est
from views.graficos import GraficoBarras, legenda

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}


class EstatisticasView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

    def render(self):
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent.content_frame,
                                                    fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.scroll_frame, text="📊  Estatísticas e Análise",
                       font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w")

        resultados = self.controller.get_resultados()
        apostas = self.controller.get_apostas()
        stats = self.controller.get_stats()

        if not resultados:
            ctk.CTkLabel(self.scroll_frame, text="Carregando dados...",
                         font=("Arial", 14, "italic"), text_color="gray").pack(pady=40)
            return

        self._render_painel_informacoes(stats)
        self._render_graficos(resultados, apostas)
        self._render_frequencia(resultados)
        self._render_porcentagem_acertos(apostas)
        self._render_numeros_quentes_frios(resultados)
        self._render_distribuicao(resultados)

    def _render_painel_informacoes(self, stats: dict):
        ctk.CTkLabel(self.scroll_frame, text="📈 Visão Geral",
                       font=("Arial", 16, "bold")).pack(pady=(15, 10), anchor="w", padx=20)

        info_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#e3f2fd", corner_radius=10,
                                  border_width=2, border_color=Cores.PRIMARIO)
        info_frame.pack(fill="x", pady=5, padx=20)

        texto = (f"Total de Resultados: {stats['total_resultados']} | "
                 f"Total de Apostas: {stats['total_apostas']} | "
                 f"Investido: R$ {stats['total_gasto']:,.2f} | "
                 f"Acertos: {stats['total_acertos']}")
        ctk.CTkLabel(info_frame, text=texto, font=("Arial", 13),
                       text_color="#1565c0").pack(pady=15, padx=15)

    def _titulo(self, texto):
        ctk.CTkLabel(self.scroll_frame, text=texto, font=("Arial", 16, "bold")).pack(
            pady=(20, 6), anchor="w", padx=20)

    def _vazio(self, texto):
        ctk.CTkLabel(self.scroll_frame, text=texto, font=("Arial", 12, "italic"),
                     text_color="gray").pack(anchor="w", padx=20)

    def _render_graficos(self, resultados: List[Resultado], apostas: List[Aposta]):
        tipos = [t for t in LOTERIAS if any(r.tipo_loteria == t for r in resultados)]
        self._titulo("📊 Frequência e atraso por número")
        if tipos:
            self._tipo_grafico = tipos[0]
            self.cmb_grafico = ctk.CTkComboBox(
                self.scroll_frame, values=[LOTERIAS_NOME[t] for t in tipos], width=220,
                command=lambda nome: self._trocar_loteria(nome, resultados))
            self.cmb_grafico.set(LOTERIAS_NOME[tipos[0]])
            self.cmb_grafico.pack(anchor="w", padx=20)
            self.area_freq = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            self.area_freq.pack(fill="x", padx=20, pady=5)
            self._desenhar_frequencia(resultados)

        self._titulo("🎯 Apostas por quantidade de acertos")
        dist = est.distribuicao_acertos(apostas)
        if dist:
            GraficoBarras(self.scroll_frame, [str(k) for k in dist],
                          [("Apostas", Cores.PRIMARIO, list(dist.values()))]
                          ).pack(fill="x", padx=20, pady=5)
        else:
            self._vazio("Nenhuma aposta conferida ainda.")

        self._titulo("💰 Investido x prêmios por mês")
        fin = est.financeiro_por_mes(apostas)
        if fin:
            legenda(self.scroll_frame, [("Investido", Cores.PERIGO), ("Prêmios", Cores.SUCESSO)]
                    ).pack(anchor="w", padx=20)
            GraficoBarras(self.scroll_frame, [m for m, _, _ in fin],
                          [("Investido", Cores.PERIGO, [i for _, i, _ in fin]),
                           ("Prêmios", Cores.SUCESSO, [p for _, _, p in fin])],
                          formato=lambda v: f"R$ {v:,.0f}").pack(fill="x", padx=20, pady=5)
        else:
            self._vazio("Sem apostas com data válida.")

    def _trocar_loteria(self, nome, resultados):
        self._tipo_grafico = next(k for k, v in LOTERIAS_NOME.items() if v == nome)
        self._desenhar_frequencia(resultados)

    def _desenhar_frequencia(self, resultados):
        for w in self.area_freq.winfo_children():
            w.destroy()
        tipo = self._tipo_grafico
        freq = est.frequencia_numeros(resultados, tipo)
        atraso = est.atraso_numeros(resultados, tipo)
        nums = list(freq)
        media = sum(freq.values()) / len(freq) if freq else 0
        destaques = {i: (Cores.ALERTA if freq[n] > media * 1.15
                         else Cores.PRIMARIO if freq[n] < media * 0.85 else "#9aa5ad")
                     for i, n in enumerate(nums)}
        ctk.CTkLabel(self.area_freq, text="Vezes sorteado (laranja = acima da média, azul = abaixo)",
                     font=("Arial", 11)).pack(anchor="w")
        GraficoBarras(self.area_freq, [str(n) for n in nums],
                      [("Sorteios", "#9aa5ad", [freq[n] for n in nums])],
                      destaques=destaques).pack(fill="x")
        ctk.CTkLabel(self.area_freq, text="Atraso (concursos desde a última vez que saiu)",
                     font=("Arial", 11)).pack(anchor="w", pady=(10, 0))
        GraficoBarras(self.area_freq, [str(n) for n in nums],
                      [("Atraso", Cores.DOCUMENTO, [atraso[n] for n in nums])]
                      ).pack(fill="x")

    def _render_frequencia(self, resultados: List[Resultado]):
        ctk.CTkLabel(self.scroll_frame, text="📈 Frequência por Tipo de Loteria",
                       font=("Arial", 16, "bold")).pack(pady=(20, 10), anchor="w", padx=20)

        for tipo in LOTERIAS.keys():
            tipos_resultados = [r for r in resultados if r.tipo_loteria == tipo]
            if not tipos_resultados:
                continue

            frame = ctk.CTkFrame(self.scroll_frame, fg_color="#f8f9fa", corner_radius=8)
            frame.pack(fill="x", pady=3, padx=20)

            nome = LOTERIAS_NOME.get(tipo, tipo)
            ctk.CTkLabel(frame, text=f"🎰 {nome}: {len(tipos_resultados)} concursos registrados",
                           font=("Arial", 13, "bold")).pack(pady=8, padx=10, anchor="w")

    def _render_porcentagem_acertos(self, apostas: List[Aposta]):
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

        # Distribuição de acertos
        distrib = {}
        for a in apostas:
            distrib[a.acertos] = distrib.get(a.acertos, 0) + 1

        frame2 = ctk.CTkFrame(self.scroll_frame, fg_color="#fff3e0", corner_radius=10,
                              border_width=2, border_color=Cores.ALERTA)
        frame2.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(frame2, text="Distribuição de Acertos:",
                       font=("Arial", 13, "bold"), text_color="#e65100").pack(
            pady=(10, 5), anchor="w", padx=15)

        for qtd, count in sorted(distrib.items()):
            bar_width = min(count / max(distrib.values()) * 100, 100)
            inner = ctk.CTkFrame(frame2, fg_color=Cores.PRIMARIO if qtd > 0 else "#ccc",
                                 corner_radius=4, height=20)
            inner.pack(fill="x", padx=20, pady=2)
            inner.pack_propagate(False)
            ctk.CTkLabel(inner, text=f"  {qtd} acertos: {count} apostas ({bar_width:.0f}%)",
                           font=("Arial", 12), text_color="white").pack(side="left")

    def _render_numeros_quentes_frios(self, resultados: List[Resultado]):
        ctk.CTkLabel(self.scroll_frame, text="🔥 Números Mais Sorteados",
                       font=("Arial", 16, "bold")).pack(pady=(20, 10), anchor="w", padx=20)

        all_nums = Counter()
        for r in resultados:
            for n in r.numeros_sorteados:
                all_nums[n] += 1

        if not all_nums:
            ctk.CTkLabel(self.scroll_frame, text="Dados insuficientes para análise.",
                         font=("Arial", 12, "italic"), text_color="gray").pack(pady=10)
            return

        top_quentes = all_nums.most_common(10)
        top_frios = sorted(all_nums.items(), key=lambda x: x[1])[:10]

        frame = ctk.CTkFrame(self.scroll_frame, fg_color="#fff3e0", corner_radius=10,
                             border_width=2, border_color=Cores.ALERTA)
        frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(frame, text="🔥 Quentes (mais sorteados)",
                       font=("Arial", 13, "bold"), text_color="#e65100").pack(
            pady=(10, 5), anchor="w", padx=15)
        nums_str = " | ".join(f"{n} ({c}x)" for n, c in top_quentes)
        ctk.CTkLabel(frame, text=nums_str, font=("Consolas", 13)).pack(pady=(0, 10), padx=15)

        frame2 = ctk.CTkFrame(self.scroll_frame, fg_color="#e3f2fd", corner_radius=10,
                              border_width=2, border_color=Cores.PRIMARIO)
        frame2.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(frame2, text="❄️ Frios (menos sorteados)",
                       font=("Arial", 13, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 5), anchor="w", padx=15)
        nums_str = " | ".join(f"{n} ({c}x)" for n, c in top_frios)
        ctk.CTkLabel(frame2, text=nums_str, font=("Consolas", 13)).pack(pady=(0, 10), padx=15)

    def _render_distribuicao(self, resultados: List[Resultado]):
        ctk.CTkLabel(self.scroll_frame, text="📅 Distribuição por Data",
                       font=("Arial", 16, "bold")).pack(pady=(20, 10), anchor="w", padx=20)

        from collections import defaultdict
        por_mes = defaultdict(int)
        for r in resultados:
            mes = r.data_sorteio.split("/")[-1] if "/" in r.data_sorteio else r.data_sorteio[-4:]
            por_mes[mes] += 1

        frame = ctk.CTkFrame(self.scroll_frame, fg_color="#f0f0f0", corner_radius=10)
        frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(frame, text="Concursos por período:",
                       font=("Arial", 12, "bold")).pack(pady=10, padx=15, anchor="w")
        for mes, count in sorted(por_mes.items()):
            ctk.CTkLabel(frame, text=f"  Mês {mes}: {count} concursos",
                           font=("Arial", 12)).pack(padx=20)