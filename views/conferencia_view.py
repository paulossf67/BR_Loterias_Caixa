import customtkinter as ctk
from typing import List, Optional

from models.resultado import Resultado
from models.aposta import Aposta
from cores import Cores
from services.api_service import LOTERIAS

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}


class ConferênciaView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.resultado_selecionado: Optional[Resultado] = None
        self.apostas_frame = None
        self.cmb_concurso = None
        self.lbl_numeros = None

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

        ctk.CTkLabel(frame, text="Resultado da vez:", font=("Arial", 14, "bold")).pack(
            side="left")

        resultados = self.controller.get_resultados()
        options = ["Selecione..."]
        if resultados:
            options = [f"{LOTERIAS_NOME.get(r.tipo_loteria, r.tipo_loteria)} "
                       f"#{r.concurso} - {r.data_sorteio}" for r in resultados]

        self.cmb_concurso = ctk.CTkComboBox(frame, values=options, width=300,
                                            command=self._on_concurso_selecionado)
        self.cmb_concurso.pack(side="left", padx=10)
        self.cmb_concurso.select(0)

        if resultados:
            self.resultado_selecionado = resultados[0]
            self.lbl_numeros = ctk.CTkLabel(frame,
                                            text=f"🎱 {resultados[0].numeros_por_extenso}",
                                            font=("Consolas", 14, "bold"),
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
            self.lbl_numeros.configure(
                text=f"🎱 {self.resultado_selecionado.numeros_por_extenso}")
            self._render_apostas_para_conferencia()

    def _render_apostas_para_conferencia(self):
        if self.apostas_frame:
            for widget in self.apostas_frame.winfo_children():
                widget.destroy()

        apostas = self.controller.get_apostas()
        if not apostas:
            ctk.CTkLabel(self.scroll_frame, text="Nenhuma aposta cadastrada.",
                         font=("Arial", 14, "italic"), text_color="gray").pack(pady=20)
            return

        if not self.resultado_selecionado:
            ctk.CTkLabel(self.scroll_frame, text="Selecione um concurso para conferir.",
                         font=("Arial", 14, "italic"), text_color="gray").pack(pady=20)
            return

        ctk.CTkLabel(self.scroll_frame, text=f"Confronto vs {self.resultado_selecionado.tipo_loteria} #{self.resultado_selecionado.concurso}",
                       font=("Arial", 16, "bold")).pack(pady=(10, 10), anchor="w", padx=20)

        # Criar cabeçalho com resumo
        resumo_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#f0f0f0", corner_radius=8)
        resumo_frame.pack(fill="x", pady=5, padx=20)
        total_apostas = len(apostas)
        total_acertos = 0
        total_premio = 0.0

        for a in apostas:
            acertos = len(set(a.numeros) & set(self.resultado_selecionado.numeros_sorteados))
            total_acertos += acertos
            if acertos > 0:
                total_premio += a.valor * {6: 1000, 5: 50, 4: 10, 3: 5, 2: 2, 1: 1}.get(acertos, 0)

        ctk.CTkLabel(resumo_frame,
                       text=f"Total: {total_apostas} apostas | {total_acertos} acertos | Prêmio estimado: R$ {total_premio:,.2f}",
                       font=("Arial", 13, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=10, padx=15)

        for a in sorted(apostas, key=lambda x: x.acertos if hasattr(x, 'acertos') else 0, reverse=True):
            self._criar_card_conferencia(a, self.resultado_selecionado)

    def _criar_card_conferencia(self, aposta: Aposta, resultado: Resultado):
        acertos = len(set(aposta.numeros) & set(resultado.numeros_sorteados))
        cor_fundo = "#c8e6c9" if acertos > 0 else "#ffcdd2"
        cor_borda = Cores.SUCESSO if acertos > 0 else Cores.PERIGO

        card = ctk.CTkFrame(self.apostas_frame, fg_color=cor_fundo, corner_radius=10,
                            border_width=2, border_color=cor_borda)
        card.pack(fill="x", pady=5, padx=20)

        header = ctk.CTkFrame(card, fg_color=cor_borda, corner_radius=10)
        header.pack(fill="x", padx=5, pady=5)

        nome = LOTERIAS_NOME.get(aposta.tipo_loteria, aposta.tipo_loteria)
        ctk.CTkLabel(header, text=f"🎰 {nome} - Concurso {aposta.data_sorteio}",
                       font=("Arial", 13, "bold"), text_color="white").pack(
            side="left", padx=10)
        ctk.CTkLabel(header, text=f"🎯 {acertos} acerto(s)",
                       font=("Arial", 13, "bold"), text_color="white").pack(
            side="right", padx=10)

        nums_apostados = " | ".join(str(n) for n in aposta.numeros)
        ctk.CTkLabel(card, text=f"Seus números: {nums_apostados}",
                       font=("Consolas", 13)).pack(pady=5, padx=10, anchor="w")

        nums_sorteados = resultado.numeros_por_extenso
        ctk.CTkLabel(card, text=f"Sorteados: {nums_sorteados}",
                       font=("Consolas", 13), text_color="#333").pack(
            pady=(0, 5), padx=10)

        if acertos > 0:
            premio = self._calcular_premio(acertos, aposta.valor)
            ctk.CTkLabel(card, text=f"💵 Prêmio estimado: R$ {premio:,.2f}",
                           font=("Arial", 13, "bold"), text_color=Cores.SUCESSO).pack(
                pady=(0, 8), padx=10)

        # Marcar como conferido
        if not aposta.conferencia_feita:
            aposta.conferencia_feita = True
            self.controller.salvar_conferencia(self._criar_conferencia(aposta, resultado, acertos))

    def _criar_conferencia(self, aposta: Aposta, resultado: Resultado, acertos: int):
        from models.conferencia import Conferência
        premio = self._calcular_premio(acertos, aposta.valor)
        return Conferência(
            id_aposta=aposta.id,
            tipo_loteria=aposta.tipo_loteria,
            concurso=resultado.concurso,
            data_conferida=aposta.data_sorteio,
            numeros_apostados=aposta.numeros,
            numeros_sorteados=resultado.numeros_sorteados,
            qtd_acertos=acertos,
            premio_ganho=aposta.premio,
            status="concluído" if acertos > 0 else "pendente"
        )

    def _calcular_acertos(self, meus_numeros: list, sorteados: list) -> int:
        return len(set(meus_numeros) & set(sorteados))

    def _calcular_premio(self, acertos: int, valor_aposta: float) -> float:
        multiplicadores = {6: 1000, 5: 50, 4: 10, 3: 5, 2: 2, 1: 1, 0: 0}
        return valor_aposta * multiplicadores.get(acertos, 0)