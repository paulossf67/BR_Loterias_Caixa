"""Nova aposta e geração de números."""
from datetime import datetime

import customtkinter as ctk

from cores import Cores
from services.api_service import LOTERIAS
from services.regras import REGRAS
from services import estatisticas as est
from services.estatisticas import MODOS_GERACAO
from utils.helpers import validar_numeros

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}
NUMEROS_POR_LOTERIA = {k: (r["min"], r["maximo"]) for k, r in REGRAS.items()}


class NovaApostaMixin:
    # ------------------------------------------------------------------ #
    # TELA NOVA APOSTA
    # ------------------------------------------------------------------ #
    def mostrar_tela_nova_aposta(self):
        self.limpar_conteudo()
        self.current_view_name = "nova_aposta"

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="🎱  Nova Aposta",
                       font=("Arial", 24, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w", padx=20)

        # Seleção de loteria
        frame_loteria = ctk.CTkFrame(scroll, fg_color="#f8f9fa", corner_radius=10)
        frame_loteria.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame_loteria, text="Loteria:", font=("Arial", 14, "bold")).pack(
            pady=(15, 5), anchor="w", padx=15)

        self.cmb_loteria = ctk.CTkComboBox(frame_loteria, values=list(LOTERIAS.keys()),
                                                 width=300, command=self._on_loteria_selecionada)
        self.cmb_loteria.pack(pady=(0, 15), padx=15, fill="x")
        self.cmb_loteria.set("mega-sena")

        # Modo de geração
        frame_modo = ctk.CTkFrame(scroll, fg_color="#f8f9fa", corner_radius=10)
        frame_modo.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame_modo, text="Como gerar os números?",
                     font=("Arial", 14, "bold")).pack(pady=(15, 5), anchor="w", padx=15)
        self.cmb_modo = ctk.CTkComboBox(frame_modo, values=list(MODOS_GERACAO), width=300,
                                        state="readonly", command=lambda v: self.gerar_numeros())
        self.cmb_modo.set("Aleatório")
        self.cmb_modo.pack(pady=(0, 5), padx=15, anchor="w")
        ctk.CTkLabel(frame_modo, text="Os modos estatísticos só dão mais peso ao sorteio; "
                     "todo número continua com a mesma chance real de sair.",
                     font=("Arial", 11), text_color="gray").pack(pady=(0, 15), padx=15, anchor="w")

        # Seleção de números
        frame_numeros = ctk.CTkFrame(scroll, fg_color="#f8f9fa", corner_radius=10)
        frame_numeros.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame_numeros, text="Números:", font=("Arial", 14, "bold")).pack(
            pady=(15, 10), anchor="w", padx=15)

        self.numeros_frame = ctk.CTkFrame(frame_numeros, fg_color="transparent")
        self.numeros_frame.pack(pady=(0, 15), padx=15, fill="x")

        self.gerar_numeros()

        # Valor da aposta
        frame_valor = ctk.CTkFrame(scroll, fg_color="#f8f9fa", corner_radius=10)
        frame_valor.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame_valor, text="Valor da aposta (R$):", font=("Arial", 14, "bold")).pack(
            pady=(15, 5), anchor="w", padx=15)

        self.entry_valor = ctk.CTkEntry(frame_valor, placeholder_text="6.00",
                                              width=200, fg_color="white",
                                              text_color="#333333", border_width=0)
        self.entry_valor.pack(pady=(0, 15), padx=15)
        self.entry_valor.insert(0, "6.00")

        # Bolão e teimosinha
        frame_extra = ctk.CTkFrame(scroll, fg_color="#f8f9fa", corner_radius=10)
        frame_extra.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame_extra, text="Bolão – nº de cotas (o prêmio é dividido):",
                     font=("Arial", 14, "bold")).pack(pady=(15, 5), anchor="w", padx=15)
        self.entry_cotas = ctk.CTkEntry(frame_extra, width=200, fg_color="white",
                                        text_color="#333333", border_width=0)
        self.entry_cotas.pack(pady=(0, 10), padx=15, anchor="w")
        self.entry_cotas.insert(0, "1")
        ctk.CTkLabel(frame_extra, text="Teimosinha – repetir por quantos concursos (1 a 24):",
                     font=("Arial", 14, "bold")).pack(pady=(5, 5), anchor="w", padx=15)
        self.entry_concursos = ctk.CTkEntry(frame_extra, width=200, fg_color="white",
                                            text_color="#333333", border_width=0)
        self.entry_concursos.pack(pady=(0, 15), padx=15, anchor="w")
        self.entry_concursos.insert(0, "1")

        # Botões
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="🎲  Gerar Números",
                         command=self.gerar_numeros, fg_color=Cores.PRIMARIO,
                         hover_color="#0d3c6b").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="💰  Salvar Aposta",
                         command=self.salvar_aposta, fg_color=Cores.SUCESSO,
                         hover_color="#1e7e34").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙  Voltar",
                         command=self.voltar_inicio, fg_color=Cores.NEUTRO,
                         hover_color="#4a5258").pack(side="left", padx=10)

    def _on_loteria_selecionada(self, value):
        self.gerar_numeros()

    def gerar_numeros(self):
        tipo = self.cmb_loteria.get() if hasattr(self, 'cmb_loteria') else "mega-sena"
        qtd, maximo = NUMEROS_POR_LOTERIA.get(tipo, (6, 60))
        modo = MODOS_GERACAO.get(self.cmb_modo.get(), "aleatorio") if hasattr(self, "cmb_modo") else "aleatorio"
        numeros = est.gerar_numeros(self.controller.get_resultados(), tipo, qtd, modo)

        for widget in self.numeros_frame.winfo_children():
            widget.destroy()

        self.numeros_selecionados = numeros
        self.qtd_numeros = qtd
        self.maximo_numeros = maximo

        cols = 10
        for i, n in enumerate(numeros):
            lbl = ctk.CTkLabel(self.numeros_frame, text=str(n),
                                   font=("Arial", 20, "bold"), width=38, height=38,
                                   fg_color=Cores.PRIMARIO, text_color="white",
                                   corner_radius=20)
            lbl.grid(row=i // cols, column=i % cols, padx=2, pady=2)

    def salvar_aposta(self):
        tipo = self.cmb_loteria.get()
        numeros = getattr(self, 'numeros_selecionados', [])
        valor_str = self.entry_valor.get().replace(",", ".").replace("R$", "").strip()

        try:
            valor = float(valor_str)
        except ValueError:
            self._mostrar_toast("❌ Valor da aposta inválido.")
            return

        if not numeros:
            self.gerar_numeros()
            numeros = self.numeros_selecionados

        qtd, maximo = NUMEROS_POR_LOTERIA.get(tipo, (6, 60))
        if not validar_numeros(numeros, qtd, maximo):
            self.gerar_numeros()
            numeros = self.numeros_selecionados

        try:
            cotas = int(self.entry_cotas.get().strip() or 1)
            concursos = int(self.entry_concursos.get().strip() or 1)
        except ValueError:
            self._mostrar_toast("❌ Cotas e concursos devem ser números inteiros.", erro=True)
            return

        id_jogador = getattr(self.jogador_atual, "id", 0)
        try:
            if concursos > 1:
                self.controller.add_teimosinha(tipo, numeros, valor, concursos, id_jogador, cotas)
            else:
                data_sorteio = datetime.now().strftime("%d/%m/%Y")
                self.controller.add_aposta(tipo, numeros, valor, data_sorteio, id_jogador, cotas)
        except ValueError as e:
            self._mostrar_toast(f"❌ {e}", erro=True)
            return

        self._mostrar_toast(f"✅ Aposta salva: {LOTERIAS_NOME.get(tipo, tipo)} | {len(numeros)} números | R$ {valor:.2f}")
        self.after(1500, lambda: self.abrir_apostas())
