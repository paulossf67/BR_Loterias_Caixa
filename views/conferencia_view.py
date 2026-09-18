import customtkinter as ctk
from typing import List, Optional

from models.resultado import Resultado
from models.aposta import Aposta
from cores import Cores
from services.api_service import LOTERIAS

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}


class ConferenciaView:
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
        self.cmb_concurso.set(options[0])

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

        if not self.controller.get_apostas():
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
        conferidas = self.controller.conferir_resultado(self.resultado_selecionado)
        if not conferidas:
            ctk.CTkLabel(self.apostas_frame,
                         text="Nenhuma aposta desta loteria/concurso para conferir.",
                         font=("Arial", 14, "italic"), text_color="gray").pack(pady=20)
            return

        total_premio = sum(c["premio"] for c in conferidas)
        total_premiadas = sum(1 for c in conferidas if c["premio"] > 0)
        ctk.CTkLabel(resumo_frame,
                       text=f"Total: {len(conferidas)} apostas | {total_premiadas} premiada(s) | Prêmio: R$ {total_premio:,.2f}",
                       font=("Arial", 13, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=10, padx=15)

        for c in sorted(conferidas, key=lambda x: x["acertos"], reverse=True):
            self._criar_card_conferencia(c["aposta"], self.resultado_selecionado,
                                         c["acertos"], c["premio"])
        self._registrar_conferencias(conferidas)

    def _criar_card_conferencia(self, aposta: Aposta, resultado: Resultado,
                                acertos: int, premio: float):
        premiada = premio > 0
        cor_fundo = "#c8e6c9" if premiada else "#ffcdd2"
        cor_borda = Cores.SUCESSO if premiada else Cores.PERIGO

        card = ctk.CTkFrame(self.apostas_frame, fg_color=cor_fundo, corner_radius=10,
                            border_width=2, border_color=cor_borda)
        card.pack(fill="x", pady=5, padx=20)

        header = ctk.CTkFrame(card, fg_color=cor_borda, corner_radius=10)
        header.pack(fill="x", padx=5, pady=5)

        nome = LOTERIAS_NOME.get(aposta.tipo_loteria, aposta.tipo_loteria)
        ctk.CTkLabel(header, text=f"🎰 {nome} - Concurso {resultado.concurso}",
                       font=("Arial", 13, "bold"), text_color="white").pack(
            side="left", padx=10)
        ctk.CTkLabel(header, text=f"🎯 {acertos} acerto(s)",
                       font=("Arial", 13, "bold"), text_color="white").pack(
            side="right", padx=10)

        nums_apostados = " | ".join(str(n) for n in aposta.numeros)
        ctk.CTkLabel(card, text=f"Seus números: {nums_apostados}",
                       font=("Consolas", 13)).pack(pady=5, padx=10, anchor="w")
        ctk.CTkLabel(card, text=f"Sorteados: {resultado.numeros_por_extenso}",
                       font=("Consolas", 13), text_color="#333").pack(
            pady=(0, 5), padx=10)

        if premiada:
            ctk.CTkLabel(card, text=f"💵 Prêmio: R$ {premio:,.2f}",
                           font=("Arial", 13, "bold"), text_color=Cores.SUCESSO).pack(
                pady=(0, 8), padx=10)

    def _registrar_conferencias(self, conferidas: list):
        """Persiste as conferências novas (uma vez por aposta), sem redesenhar a tela."""
        for c in conferidas:
            aposta = c["aposta"]
            if aposta.conferencia_feita:
                continue
            aposta.acertos, aposta.premio = c["acertos"], c["premio"]
            aposta.conferencia_feita = True
            self.controller.salvar_conferencia(
                self._criar_conferencia(aposta, self.resultado_selecionado,
                                        c["acertos"], c["premio"]))
            self.controller.atualizar_aposta(aposta)

    def _criar_conferencia(self, aposta: Aposta, resultado: Resultado, acertos: int, premio: float):
        from models.conferencia import Conferencia
        return Conferencia(
            id_aposta=aposta.id,
            tipo_loteria=aposta.tipo_loteria,
            concurso=resultado.concurso,
            data_conferida=aposta.data_sorteio,
            numeros_apostados=aposta.numeros,
            numeros_sorteados=resultado.numeros_sorteados,
            qtd_acertos=acertos,
            premio_ganho=premio,
            status="concluído" if premio > 0 else "pendente"
        )
