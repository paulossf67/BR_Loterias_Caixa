"""
Sistema de Controle de Apostas e Resultados das Loterias da Caixa.
Interface gráfica com CustomTkinter.
"""
import json
import logging
import random
import threading
import traceback
from datetime import datetime

import customtkinter as ctk

try:
    import psutil
except ImportError:
    psutil = None

from cores import Cores
from controllers import AppController
from services.api_service import LOTERIAS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

LOTERIAS_NOME = {
    "mega-sena": "Mega-Sena",
    "quina": "Quina",
    "lotofacil": "Lotofácil",
    "lotomania": "Lotomania",
    "timemania": "Timemania",
    "dupla-sena": "Dupla Sena",
    "dia-de-sorte": "Dia de Sorte",
}
NUMEROS_POR_LOTERIA = {
    "mega-sena": (6, 60),
    "quina": (5, 80),
    "lotofacil": (15, 25),
    "lotomania": (20, 50),
    "timemania": (10, 80),
    "dupla-sena": (6, 60),
    "dia-de-sorte": (7, 31),
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.controller = AppController(self)
        self.current_view_name = "home"
        self.tela_nova_aposta_widgets = {}

        self.title("🎰  Loterias da Caixa - Sistema de Controle")
        self.geometry("1200x750")
        try:
            self.state("zoomed")
        except Exception:
            pass

        self.report_callback_exception = self._handle_callback_exception
        self.usuario_nome = "Usuário"

        self._montar_cabecalho()
        self._montar_rodape()
        self._montar_layout_principal()

        self.atualizar_tempo()
        self.atualizar_status_sistema()
        self.atualizar_status_conexao()

        self.voltar_inicio()

    def _handle_callback_exception(self, exc_type, exc_value, exc_traceback):
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logging.error(f"Erro não tratado em callback da UI:\n{tb_str}")

    # ------------------------------------------------------------------ #
    # CABEÇALHO
    # ------------------------------------------------------------------ #
    def _montar_cabecalho(self):
        self.header = ctk.CTkFrame(self, corner_radius=0, height=60, fg_color=Cores.PRIMARIO)
        self.header.pack(side="top", fill="x")

        self.lbl_hora = ctk.CTkLabel(self.header, text="", font=("Arial", 16), text_color="white")
        self.lbl_hora.pack(side="left", padx=20)

        self.lbl_titulo = ctk.CTkLabel(self.header, text="🎰  LOTERIAS DA CAIXA",
                                        font=("Arial", 20, "bold"), text_color="white")
        self.lbl_titulo.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_data = ctk.CTkLabel(self.header, text="", font=("Arial", 16), text_color="white")
        self.lbl_data.pack(side="right", padx=20)

        self.entry_global_search = ctk.CTkEntry(self.header, placeholder_text="Busca rápida",
                                                 width=280, fg_color="white",
                                                 text_color="#333333", border_width=0)
        self.entry_global_search.pack(side="right", padx=10)
        self.entry_global_search.bind("<Return>", self._busca_global)

        btn_busca = ctk.CTkButton(self.header, text="🔍", width=40, command=self._busca_global,
                                   fg_color="#14508c", hover_color="#0d3c6b", text_color="white")
        btn_busca.pack(side="right")

    def _busca_global(self, event=None):
        termo = self.entry_global_search.get().strip()
        if not termo:
            return
        print(f"Buscar: {termo}")
        self.entry_global_search.delete(0, "end")

    # ------------------------------------------------------------------ #
    # RODAPÉ
    # ------------------------------------------------------------------ #
    def _montar_rodape(self):
        self.footer = ctk.CTkFrame(self, corner_radius=0, height=30)
        self.footer.pack(side="bottom", fill="x")

        self.lbl_status_sistema = ctk.CTkLabel(self.footer, text="CPU: - | RAM: -", font=("Arial", 12))
        self.lbl_status_sistema.pack(side="left", padx=20)

        self.lbl_status_conexao = ctk.CTkLabel(self.footer, text="Verificando...",
                                                font=("Arial", 12, "bold"))
        self.lbl_status_conexao.pack(side="left", padx=20)

        self.lbl_creditos = ctk.CTkLabel(self.footer, text="Loterias da Caixa v1.0",
                                           font=("Arial", 12))
        self.lbl_creditos.pack(side="right", padx=20)

    # ------------------------------------------------------------------ #
    # LAYOUT PRINCIPAL (sidebar + conteúdo)
    # ------------------------------------------------------------------ #
    def _montar_layout_principal(self):
        self.main_container = ctk.CTkFrame(self, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        self.sidebar_frame = ctk.CTkFrame(self.main_container, width=200, corner_radius=0)
        self.sidebar_frame.pack(side="left", fill="y")

        self.content_frame = ctk.CTkFrame(self.main_container, corner_radius=0,
                                           fg_color="transparent")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.sidebar_frame, text="MENU PRINCIPAL", font=("Arial", 13, "bold"),
                      text_color=Cores.PRIMARIO).pack(pady=(20, 15))

        self.btn_inicio = ctk.CTkButton(self.sidebar_frame, text="🏠  Início", anchor="w",
                                         command=self.voltar_inicio)
        self.btn_inicio.pack(pady=(0, 10), padx=20, fill="x")

        self.btn_resultados = ctk.CTkButton(self.sidebar_frame, text="📋  Resultados", anchor="w",
                                              command=self.abrir_resultados)
        self.btn_resultados.pack(pady=5, padx=20, fill="x")

        self.btn_apostas = ctk.CTkButton(self.sidebar_frame, text="🎱  Minhas Apostas", anchor="w",
                                           command=self.abrir_apostas)
        self.btn_apostas.pack(pady=5, padx=20, fill="x")

        self.btn_conferencia = ctk.CTkButton(self.sidebar_frame, text="✅  Conferir", anchor="w",
                                              command=self.abrir_conferencia)
        self.btn_conferencia.pack(pady=5, padx=20, fill="x")

        self.btn_estatisticas = ctk.CTkButton(self.sidebar_frame, text="📊  Estatísticas", anchor="w",
                                               command=self.abrir_estatisticas)
        self.btn_estatisticas.pack(pady=5, padx=20, fill="x")

        self.btn_sincronizar = ctk.CTkButton(self.sidebar_frame, text="🔄  Sincronizar", anchor="w",
                                              command=self.controller.sync_and_refresh,
                                              fg_color="#28a745", hover_color="#1e7e34")
        self.btn_sincronizar.pack(pady=5, padx=20, fill="x")

        self.btn_sair = ctk.CTkButton(self.sidebar_frame, text="🚪  Sair do Sistema", anchor="w",
                                       command=self.quit, fg_color=Cores.PERIGO, hover_color="#a83232")
        self.btn_sair.pack(side="bottom", pady=20, padx=20, fill="x")

    # ------------------------------------------------------------------ #
    # NAVEGAÇÃO ENTRE TELAS
    # ------------------------------------------------------------------ #
    def limpar_conteudo(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def destacar_botao(self, btn_name):
        botoes = {
            "home": self.btn_inicio,
            "resultados": self.btn_resultados,
            "apostas": self.btn_apostas,
            "conferencia": self.btn_conferencia,
            "estatisticas": self.btn_estatisticas,
        }
        cores_default = {
            "home": Cores.PRIMARIO,
            "resultados": Cores.PRIMARIO,
            "apostas": Cores.PRIMARIO,
            "conferencia": Cores.PRIMARIO,
            "estatisticas": Cores.PRIMARIO,
        }
        cor_ativa = "#0d3c6b"
        for name, btn in botoes.items():
            if btn:
                btn.configure(fg_color=cores_default.get(name, Cores.PRIMARIO))
        if btn_name in botoes and botoes[btn_name]:
            botoes[btn_name].configure(fg_color=cor_ativa)

    # ------------------------------------------------------------------ #
    # TELAS
    # ------------------------------------------------------------------ #
    def voltar_inicio(self):
        self.limpar_conteudo()
        self.current_view_name = "home"
        self.destacar_botao("home")

        scroll_home = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll_home.pack(fill="both", expand=True)

        primeiro_nome = self.usuario_nome.split()[0] if self.usuario_nome.strip() else "Usuário"
        ctk.CTkLabel(scroll_home, text=f"Bem-vindo de volta, {primeiro_nome}!",
                     font=("Arial", 26, "bold")).pack(pady=(10, 20), anchor="w", padx=20)

        summary_grid = ctk.CTkFrame(scroll_home, fg_color="transparent")
        summary_grid.pack(fill="x", padx=20)
        summary_grid.grid_columnconfigure((0, 1, 2), weight=1)

        apostas = self.controller.get_apostas()
        resultados = self.controller.get_resultados()
        total_apostas = len(apostas)
        total_gasto = sum(a.valor for a in apostas)
        total_acertos = sum(a.acertos for a in apostas)
        ultimo_concurso = len(resultados)

        def stat_card(parent, row, col, title, value, color):
            card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10, height=100)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=title, font=("Arial", 14), text_color="white").pack(pady=(15, 0))
            lbl_valor = ctk.CTkLabel(card, text=str(value), font=("Arial", 22, "bold"), text_color="white")
            lbl_valor.pack()
            return lbl_valor

        stat_card(summary_grid, 0, 0, "Total de Apostas", total_apostas, "#1f6aa5")
        stat_card(summary_grid, 0, 1, "Total Investido", f"R$ {total_gasto:,.2f}", "#28a745")
        stat_card(summary_grid, 0, 2, "Total Acertos", total_acertos, "#E0A800")

        info_frame = ctk.CTkFrame(scroll_home, fg_color="#e3f2fd", corner_radius=10,
                                   border_width=2, border_color=Cores.PRIMARIO)
        info_frame.pack(fill="x", padx=20, pady=15)

        info_text = f"Últimos concursos: {ultimo_concurso} | Loterias: {len(LOTERIAS)} | " \
                    f"Próximo sorteio disponível"
        ctk.CTkLabel(info_frame, text=info_text, font=("Arial", 13),
                     text_color="#1565c0").pack(pady=15, padx=15)

        ctk.CTkLabel(scroll_home, text="Ações Rápidas", font=("Arial", 18, "bold")) \
            .pack(pady=(30, 10), anchor="w", padx=20)

        ações_frame = ctk.CTkFrame(scroll_home, fg_color="transparent")
        ações_frame.pack(fill="x", padx=20)

        ctk.CTkButton(ações_frame, text="🎱  Nova Aposta", width=200, height=50,
                       command=self.mostrar_tela_nova_aposta, fg_color=Cores.PRIMARIO).pack(
            side="left", padx=10, pady=5)
        ctk.CTkButton(ações_frame, text="✅  Conferir Apostas", width=200, height=50,
                       command=self.abrir_conferencia, fg_color=Cores.ALERTA).pack(
            side="left", padx=10, pady=5)
        ctk.CTkButton(ações_frame, text="📋  Ver Resultados", width=200, height=50,
                       command=self.abrir_resultados, fg_color=Cores.PRIMARIO).pack(
            side="left", padx=10, pady=5)

        frases = [
            "O sucesso é a soma de pequenos esforços repetidos dia após dia.",
            "A persistência é o caminho do êxito!",
            "Sua única limitação é a sua imaginação.",
            "Grandes coisas nunca vêm de zonas de conforto.",
        ]
        ctk.CTkLabel(scroll_home, text=f'"{random.choice(frases)}"',
                     font=("Arial", 14, "italic"), text_color="gray50").pack(pady=40)

    # ------------------------------------------------------------------ #
    # RESULTADOS
    # ------------------------------------------------------------------ #
    def abrir_resultados(self):
        self.limpar_conteudo()
        self.current_view_name = "resultados"
        self.destacar_botao("resultados")

        from views.resultados_view import ResultadosView
        self.resultados_view = ResultadosView(self, self.controller)
        self.resultados_view.render()

    # ------------------------------------------------------------------ #
    # APOSTAS
    # ------------------------------------------------------------------ #
    def abrir_apostas(self):
        self.limpar_conteudo()
        self.current_view_name = "apostas"
        self.destacar_botao("apostas")

        from views.apostas_view import ApostasView
        self.apostas_view = ApostasView(self, self.controller)
        self.apostas_view.render()

    # ------------------------------------------------------------------ #
    # CONFERÊNCIA
    # ------------------------------------------------------------------ #
    def abrir_conferencia(self):
        self.limpar_conteudo()
        self.current_view_name = "conferencia"
        self.destacar_botao("conferencia")

        from views.conferencia_view import ConferênciaView
        self.conferencia_view = ConferênciaView(self, self.controller)
        self.conferencia_view.render()

    # ------------------------------------------------------------------ #
    # ESTATÍSTICAS
    # ------------------------------------------------------------------ #
    def abrir_estatisticas(self):
        self.limpar_conteudo()
        self.current_view_name = "estatisticas"
        self.destacar_botao("estatisticas")

        from views.estatisticas_view import EstatisticasView
        self.estatisticas_view = EstatisticasView(self, self.controller)
        self.estatisticas_view.render()

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
        self.cmb_loteria.select("mega-sena")

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

        # Botões
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="🎲  Gerar Números Aleatórios",
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
        numeros = gerar_numeros_aleatorios(qtd, maximo)

        for widget in self.numeros_frame.winfo_children():
            widget.destroy()

        self.numeros_selecionados = numeros
        self.qtd_numeros = qtd
        self.maximo_numeros = maximo

        for i, n in enumerate(numeros):
            lbl = ctk.CTkLabel(self.numeros_frame, text=str(n),
                                font=("Arial", 20, "bold"), width=40, height=40,
                                fg_color=Cores.PRIMARIO, text_color="white",
                                corner_radius=20)
            lbl.grid(row=i // 10, column=i % 10, padx=3, pady=3)

        ctk.CTkLabel(self.numeros_frame, text=f"({len(numeros)} números de 1 a {maximo})",
                     font=("Arial", 12, "italic"), text_color="gray").grid(
            row=(len(numeros) - 1) // 10 + 1, column=0, columnspan=10, pady=5)

    def salvar_aposta(self):
        tipo = self.cmb_loteria.get()
        numeros = getattr(self, 'numeros_selecionados', [])
        valor_str = self.entry_valor.get().replace(",", ".").replace("R$", "").strip()

        try:
            valor = float(valor_str)
        except ValueError:
            valor = 6.0

        if not numeros:
            self.gerar_numeros()
            numeros = self.numeros_selecionados

        qtd, maximo = NUMEROS_POR_LOTERIA.get(tipo, (6, 60))
        if not validar_numeros(numeros, qtd, maximo):
            self.gerar_numeros()
            numeros = self.numeros_selecionados

        data_sorteio = datetime.now().strftime("%d/%m/%Y")
        aposta = self.controller.add_aposta(tipo, numeros, valor, data_sorteio)

        confirm = ctk.CTkEntry(self.content_frame, placeholder_text="Aposta salva com sucesso!",
                                width=400, fg_color="#c8e6c9", text_color="#1b5e20",
                                border_width=2, font=("Arial", 14, "bold"))
        confirm.pack(pady=20)

        self.after(2000, lambda: confirm.destroy())
        self.after(2500, lambda: self.abrir_apostas())

    # ------------------------------------------------------------------ #
    # CONFERÊNCIA
    # ------------------------------------------------------------------ #
    def mostrar_tela_conferencia(self):
        self.abrir_conferencia()

    def mostrar_exportacao(self, texto: str):
        self.limpar_conteudo()
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="📄  Relatório de Apostas",
                     font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w", padx=20)

        text_box = ctk.CTkTextbox(scroll, width=800, height=400, font=("Consolas", 12))
        text_box.pack(pady=10, padx=20, fill="both", expand=True)
        text_box.insert("1.0", texto)

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="📋 Copiar", command=lambda: self.app.clipboard_append(texto),
                       fg_color=Cores.PRIMARIO).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙 Voltar", command=self.abrir_apostas,
                       fg_color=Cores.NEUTRO).pack(side="left", padx=10)

    # ------------------------------------------------------------------ #
    # RELÓGIO / STATUS (rodapé)
    # ------------------------------------------------------------------ #
    def atualizar_tempo(self):
        agora = datetime.now()
        self.lbl_hora.configure(text=agora.strftime("%H:%M:%S"))
        self.lbl_data.configure(text=agora.strftime("%d/%m/%Y"))
        self.after(1000, self.atualizar_tempo)

    def atualizar_status_sistema(self):
        if psutil:
            try:
                import os
                processo = psutil.Process(os.getpid())
                mem_mb = processo.memory_info().rss / 1024 / 1024
                cpu = processo.cpu_percent(interval=None)
                self.lbl_status_sistema.configure(text=f"CPU: {cpu:.1f}% | RAM: {mem_mb:.1f} MB")
            except Exception:
                self.lbl_status_sistema.configure(text="Erro ao ler status")
        else:
            self.lbl_status_sistema.configure(text="Instale 'psutil' para ver status")
        self.after(2000, self.atualizar_status_sistema)

    def atualizar_status_conexao(self):
        def checar():
            try:
                resp = self.controller.api_service.session.get(
                    "https://httpbin.org/get", timeout=5)
                net_ok = resp.status_code == 200
            except Exception:
                net_ok = False

            db_ok = True
            if self.winfo_exists():
                self.after(0, lambda: self._atualizar_status_conexao_ui(net_ok, db_ok))

        threading.Thread(target=checar, daemon=True).start()
        self.after(15000, self.atualizar_status_conexao)

    def _atualizar_status_conexao_ui(self, net_ok, db_ok):
        self.lbl_status_conexao.configure(text=f"NET: {'OK' if net_ok else 'OFF'} | DB: {'OK' if db_ok else 'OFF'}")
        if net_ok and db_ok:
            self.lbl_status_conexao.configure(text_color="#32a852")
        elif net_ok or db_ok:
            self.lbl_status_conexao.configure(text_color="#E0A800")
        else:
            self.lbl_status_conexao.configure(text_color="#d9534f")


if __name__ == "__main__":
    app = App()
    app.mainloop()