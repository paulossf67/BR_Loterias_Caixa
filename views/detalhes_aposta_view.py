import customtkinter as ctk
from typing import List, Optional

from models.aposta import Aposta
from models.conferencia import Conferencia
from cores import Cores
from services.api_service import LOTERIAS

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}


class DetalhesApostaView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.scroll_frame = None
        self.aposta: Optional[Aposta] = None

    def render(self, aposta: Aposta):
        self.aposta = aposta
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent.content_frame,
                                                    fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self._render_header()
        self._render_numeros_grandes()
        self._render_info_section()
        if aposta.conferencia_feita:
            self._render_comparacao()
        self._render_botoes_acao()

    def _render_header(self):
        nome = LOTERIAS_NOME.get(self.aposta.tipo_loteria, self.aposta.tipo_loteria)
        cor_status = Cores.SUCESSO if self.aposta.acertos > 0 else "#6c757d"
        status_text = "ACERTOU!" if self.aposta.acertos > 0 else "Pendente"

        header = ctk.CTkFrame(self.scroll_frame, fg_color=cor_status, corner_radius=10,
                              height=55)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text=f"🎰  {nome}",
                     font=("Arial", 20, "bold"), text_color="white").pack(
            side="left", padx=15)

        ctk.CTkLabel(header, text=f"Concurso #{self.aposta.data_sorteio}",
                     font=("Arial", 15), text_color="white").pack(
            side="left", padx=10)

        ctk.CTkLabel(header, text=f"{'✅ ' + status_text if self.aposta.acertos > 0 else '⏳ ' + status_text}",
                     font=("Arial", 14, "bold"), text_color="white").pack(
            side="right", padx=15)

    def _render_numeros_grandes(self):
        frame_label = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame_label.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(frame_label, text="Seus Números",
                     font=("Arial", 16, "bold"), text_color="#333").pack(anchor="w")

        frame_numeros = ctk.CTkFrame(self.scroll_frame, fg_color="#f8f9fa",
                                     corner_radius=12, border_width=1,
                                     border_color="#dee2e6")
        frame_numeros.pack(fill="x", pady=(0, 15))

        inner = ctk.CTkFrame(frame_numeros, fg_color="transparent")
        inner.pack(pady=20, padx=20)

        num_count = len(self.aposta.numeros)
        if num_count <= 7:
            circle_size = 60
        elif num_count <= 10:
            circle_size = 50
        elif num_count <= 15:
            circle_size = 42
        else:
            circle_size = 36

        cols = 10 if num_count > 10 else (num_count if num_count <= 6 else 8)

        for i, num in enumerate(self.aposta.numeros):
            circle = ctk.CTkFrame(inner, width=circle_size, height=circle_size,
                                  fg_color=Cores.PRIMARIO, corner_radius=circle_size // 2)
            circle.grid(row=i // cols, column=i % cols, padx=4, pady=4)
            circle.grid_propagate(False)

            ctk.CTkLabel(circle, text=str(num).zfill(2),
                         font=("Arial", 16 if circle_size >= 50 else 13, "bold"),
                         text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        max_col = min(num_count, cols)
        for c in range(max_col):
            inner.grid_columnconfigure(c, weight=1)

    def _render_info_section(self):
        ctk.CTkLabel(self.scroll_frame, text="Informações da Aposta",
                     font=("Arial", 16, "bold"), text_color="#333").pack(
            anchor="w", pady=(0, 8))

        info_card = ctk.CTkFrame(self.scroll_frame, fg_color="#f8f9fa",
                                 corner_radius=10, border_width=1,
                                 border_color="#dee2e6")
        info_card.pack(fill="x", pady=(0, 15))

        campos = [
            ("📅", "Data da Aposta", self.aposta.data_aposta or "—"),
            ("🎰", "Data do Sorteio", self.aposta.data_sorteio or "—"),
            ("💰", "Valor", f"R$ {self.aposta.valor:,.2f}"),
            ("🎯", "Acertos", str(self.aposta.acertos)),
            ("💵", "Prêmio", f"R$ {self.aposta.premio:,.2f}"),
            ("📊", "Status", "Conferido" if self.aposta.conferencia_feita else "Não conferido"),
        ]

        for i, (icon, label, valor) in enumerate(campos):
            row_bg = "#ffffff" if i % 2 == 0 else "#f1f3f5"
            row = ctk.CTkFrame(info_card, fg_color=row_bg, corner_radius=0, height=38)
            row.pack(fill="x")
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=f"  {icon}  {label}",
                         font=("Arial", 13), text_color="#555",
                         width=180, anchor="w").pack(side="left", padx=(10, 0))

            is_premio = label == "Prêmio"
            cor_valor = Cores.SUCESSO if is_premio and self.aposta.premio > 0 else "#333"
            ctk.CTkLabel(row, text=valor,
                         font=("Arial", 13, "bold"), text_color=cor_valor,
                         anchor="e").pack(side="right", padx=(0, 15))

    def _render_comparacao(self):
        conferencias = self.controller.get_conferencias()
        conf = None
        for c in conferencias:
            if c.id_aposta == self.aposta.id:
                conf = c
                break

        if conf is None:
            return

        apostados = set(conf.numeros_apostados or [])
        sorteados = set(conf.numeros_sorteados or [])
        acertos = apostados & sorteados
        nao_acertados_apostados = apostados - sorteados
        nao_acertados_sorteados = sorteados - apostados

        ctk.CTkLabel(self.scroll_frame, text="Resultado da Conferência",
                     font=("Arial", 16, "bold"), text_color="#333").pack(
            anchor="w", pady=(10, 8))

        if conf.qtd_acertos > 0:
            msg_cor = Cores.SUCESSO
            msg_text = f"🎉 Parabéns! Você acertou {conf.qtd_acertos} número(s)!"
        else:
            msg_cor = Cores.PERIGO
            msg_text = "😔 Não houve acertos nesta conferência."

        msg_card = ctk.CTkFrame(self.scroll_frame, fg_color=msg_cor,
                                corner_radius=10, height=45)
        msg_card.pack(fill="x", pady=(0, 10))
        msg_card.pack_propagate(False)
        ctk.CTkLabel(msg_card, text=msg_text,
                     font=("Arial", 14, "bold"), text_color="white").place(
            relx=0.5, rely=0.5, anchor="center")

        legenda = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        legenda.pack(fill="x", pady=(0, 8))
        for cor, texto in [
            (Cores.SUCESSO, "Acertou"),
            ("#adb5bd", "Não acertou (apostado)"),
            (Cores.PERIGO, "Sorteado (não apostado)"),
        ]:
            dot = ctk.CTkFrame(legenda, width=16, height=16, fg_color=cor,
                               corner_radius=8)
            dot.pack(side="left", padx=(0, 4))
            ctk.CTkLabel(legenda, text=texto, font=("Arial", 11),
                         text_color="#555").pack(side="left", padx=(0, 15))

        frameComparacao = ctk.CTkFrame(self.scroll_frame, fg_color="#f8f9fa",
                                       corner_radius=12, border_width=1,
                                       border_color="#dee2e6")
        frameComparacao.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(frameComparacao, text="Números Sorteados",
                     font=("Arial", 13, "bold"), text_color="#555").pack(
            pady=(12, 4))
        self._render_numeros_comparacao(frameComparacao, sorteados, apostados,
                                        is_drawn_row=True)

        sep = ctk.CTkFrame(frameComparacao, height=1, fg_color="#dee2e6")
        sep.pack(fill="x", padx=15, pady=8)

        ctk.CTkLabel(frameComparacao, text="Seus Números",
                     font=("Arial", 13, "bold"), text_color="#555").pack(
            pady=(4, 4))
        self._render_numeros_comparacao(frameComparacao, apostados, sorteados,
                                        is_drawn_row=False)

        ctk.CTkFrame(frameComparacao, height=10, fg_color="transparent").pack()

    def _render_numeros_comparacao(self, parent, numeros_set: set, outros_set: set,
                                  is_drawn_row: bool):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(pady=(0, 10), padx=15)

        numeros_ordenados = sorted(numeros_set)
        if not numeros_ordenados:
            ctk.CTkLabel(container, text="Nenhum número",
                         font=("Arial", 11, "italic"), text_color="gray").pack()
            return

        circle_size = 40
        cols = 10
        for i, num in enumerate(numeros_ordenados):
            if is_drawn_row:
                if num in outros_set:
                    cor = Cores.SUCESSO
                else:
                    cor = Cores.PERIGO
            else:
                if num in outros_set:
                    cor = Cores.SUCESSO
                else:
                    cor = "#adb5bd"

            circle = ctk.CTkFrame(container, width=circle_size, height=circle_size,
                                  fg_color=cor, corner_radius=circle_size // 2)
            circle.grid(row=i // cols, column=i % cols, padx=3, pady=3)
            circle.grid_propagate(False)

            ctk.CTkLabel(circle, text=str(num).zfill(2),
                         font=("Arial", 14, "bold"), text_color="white").place(
                relx=0.5, rely=0.5, anchor="center")

        max_col = min(len(numeros_ordenados), cols)
        for c in range(max_col):
            container.grid_columnconfigure(c, weight=1)

    def _render_botoes_acao(self):
        ctk.CTkLabel(self.scroll_frame, text="Ações",
                     font=("Arial", 16, "bold"), text_color="#333").pack(
            anchor="w", pady=(15, 8))

        btn_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(btn_frame, text="🖨️ Imprimir Registro",
                      command=lambda: self.controller.imprimir_boleto(self.aposta),
                      fg_color=Cores.DOCUMENTO, hover_color="#563389",
                      height=40, width=200).pack(side="left", padx=(0, 10))

        if not self.aposta.conferencia_feita:
            ctk.CTkButton(btn_frame, text="✅ Conferir",
                          command=lambda: self.controller.conferir_apostas(),
                          fg_color=Cores.ALERTA, hover_color="#c69500",
                          height=40, width=200).pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="🗑️ Excluir",
                      command=self._confirmar_exclusao,
                      fg_color=Cores.PERIGO, hover_color="#a83232",
                      height=40, width=200).pack(side="left", padx=(0, 10))

        ctk.CTkButton(btn_frame, text="← Voltar",
                      command=self._voltar,
                      fg_color=Cores.NEUTRO, hover_color="#4a5258",
                      height=40, width=160).pack(side="right")

    def _confirmar_exclusao(self):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Confirmar Exclusão")
        dialog.geometry("420x220")
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.configure(fg_color="#f8f9fa")

        ctk.CTkLabel(dialog, text="🗑️ Confirmar Exclusão",
                     font=("Arial", 18, "bold"), text_color=Cores.PERIGO).pack(
            pady=(20, 5))

        nome = LOTERIAS_NOME.get(self.aposta.tipo_loteria, self.aposta.tipo_loteria)
        ctk.CTkLabel(dialog,
                     text=f"Deseja excluir a aposta de\n{nome} #{self.aposta.data_sorteio}?",
                     font=("Arial", 13), text_color="#333").pack(pady=(5, 15))

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack()

        def confirmar():
            self.controller.remover_aposta(self.aposta.id)
            dialog.destroy()
            self._voltar()

        ctk.CTkButton(btn_row, text="Sim, Excluir",
                      command=confirmar,
                      fg_color=Cores.PERIGO, hover_color="#a83232",
                      width=140).pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text="Cancelar",
                      command=dialog.destroy,
                      fg_color=Cores.NEUTRO, hover_color="#4a5258",
                      width=140).pack(side="left", padx=10)

    def _voltar(self):
        self.parent.abrir_apostas()
