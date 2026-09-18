"""
Sistema de Controle de Apostas e Resultados das Loterias da Caixa.
Interface gráfica com CustomTkinter.
"""
import logging
import random
import threading
import traceback
from datetime import datetime
from typing import List, Optional

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
        self.jogador_atual = None

        self.title("🎰  Loterias da Caixa - Sistema de Controle")
        self.geometry("1200x750")
        try:
            self.state("zoomed")
        except Exception:
            pass

        self.report_callback_exception = self._handle_callback_exception

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
    # LAYOUT PRINCIPAL
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

        self.btn_jogador = ctk.CTkButton(self.sidebar_frame, text="👤  Cadastro", anchor="w",
                                            command=self.abrir_cadastro)
        self.btn_jogador.pack(pady=5, padx=20, fill="x")

        self.btn_sincronizar = ctk.CTkButton(self.sidebar_frame, text="🔄  Sincronizar", anchor="w",
                                              command=self._sync_handler,
                                              fg_color="#28a745", hover_color="#1e7e34")
        self.btn_sincronizar.pack(pady=5, padx=20, fill="x")

        self.btn_sair = ctk.CTkButton(self.sidebar_frame, text="🚪  Sair", anchor="w",
                                       command=self.quit, fg_color=Cores.PERIGO, hover_color="#a83232")
        self.btn_sair.pack(side="bottom", pady=20, padx=20, fill="x")

    # ------------------------------------------------------------------ #
    # NAVEGAÇÃO
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
    # HANDLERS
    # ------------------------------------------------------------------ #
    def _sync_handler(self):
        with threading.Thread(target=self._sync_worker, daemon=True):
            threading.Thread(target=self._sync_worker, daemon=True).start()

    def _sync_worker(self):
        result = self.controller.sync_and_refresh()
        self.after(0, self._atualizar_apos_sync, result)

    def _atualizar_apos_sync(self, result):
        self.voltar_inicio()
        self._mostrar_toast(f"✅ Sync: {result['sync_count']} novos resultados | {len(result['errors'])} erros")

    def _mostrar_toast(self, mensagem: str):
        toast = ctk.CTkLabel(self.content_frame, text=mensagem,
                                  font=("Arial", 13, "bold"), text_color="white",
                                  fg_color=Cores.SUCESSO, corner_radius=8, padx=15, pady=10)
        toast.place(relx=0.5, rely=0.5, anchor="center")
        self.after(2000, lambda: toast.destroy())

    # ------------------------------------------------------------------ #
    # TELAS
    # ------------------------------------------------------------------ #
    def voltar_inicio(self):
        self.limpar_conteudo()
        self.current_view_name = "home"
        self.destacar_botao("home")

        scroll_home = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll_home.pack(fill="both", expand=True)

        primeiro_nome = self.usuario_nome.split()[0] if hasattr(self, 'usuario_nome') and self.usuario_nome.strip() else "Usuário"
        ctk.CTkLabel(scroll_home, text=f"Bem-vindo de volta, {primeiro_nome}!",
                       font=("Arial", 26, "bold")).pack(pady=(10, 20), anchor="w", padx=20)

        stats = self.controller.get_stats()
        apostas = self.controller.get_apostas()
        resultados = self.controller.get_resultados()

        total_apostas = stats["total_apostas"]
        total_gasto = stats["total_gasto"]
        total_acertos = stats["total_acertos"]
        total_resultados = stats["total_resultados"]

        summary_grid = ctk.CTkFrame(scroll_home, fg_color="transparent")
        summary_grid.pack(fill="x", padx=20)
        summary_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def stat_card(parent, row, col, title, value, color):
            card = ctk.CTkFrame(parent, fg_color=color, corner_radius=10, height=100)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            card.grid_propagate(False)
            ctk.CTkLabel(card, text=title, font=("Arial", 13), text_color="white").pack(pady=(12, 0))
            ctk.CTkLabel(card, text=str(value), font=("Arial", 20, "bold"), text_color="white").pack()
            return card

        stat_card(summary_grid, 0, 0, "Total Apostas", total_apostas, "#1f6aa5")
        stat_card(summary_grid, 0, 1, "Total Investido", f"R$ {total_gasto:,.2f}", "#28a745")
        stat_card(summary_grid, 0, 2, "Total Acertos", total_acertos, "#E0A800")
        stat_card(summary_grid, 0, 3, "Concursos", total_resultados, "#6f42c1")

        alertas_frame = ctk.CTkFrame(scroll_home, fg_color="transparent")
        alertas_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(alertas_frame, text="⚠️  Alertas", font=("Arial", 16, "bold")).pack(anchor="w", padx=10)

        alertas = self._buscar_alertas()
        if not alertas:
            ctk.CTkLabel(alertas_frame, text="Nenhum alerta para hoje.",
                         font=("Arial", 12, "italic"), text_color="gray").pack(pady=5, padx=10)
        else:
            for alerta in alertas:
                self._criar_card_alerta(alertas_frame, alerta)

        ctk.CTkLabel(scroll_home, text="🔥 Últimos Resultados",
                     font=("Arial", 18, "bold")).pack(pady=(20, 10), anchor="w", padx=20)

        ultimos = resultados[:5]
        if ultimos:
            for r in ultimos:
                self._criar_card_resultado_preview(scroll_home, r)
        else:
            ctk.CTkLabel(scroll_home, text="Nenhum resultado disponível.",
                         font=("Arial", 13, "italic"), text_color="gray").pack(pady=20)

        frases = [
            "O sucesso é a soma de pequenos esforços repetidos dia após dia.",
            "A persistência é o caminho do êxito!",
            "Sua única limitação é a sua imaginação.",
            "Grandes coisas nunca vêm de zonas de conforto.",
        ]
        ctk.CTkLabel(scroll_home, text=f'"{random.choice(frases)}"',
                       font=("Arial", 14, "italic"), text_color="gray50").pack(pady=40)

    def _buscar_alertas(self) -> list:
        alertas = []
        stats = self.controller.get_stats()
        apostas = self.controller.get_apostas()

        if stats["total_apostas"] == 0:
            alertas.append({
                "texto": "Nenhuma aposta cadastrada! Crie sua primeira aposta.",
                "cor": Cores.ALERTA,
            })

        if apostas:
            sem_conferir = [a for a in apostas if not a.conferencia_feita]
            if sem_conferir:
                alertas.append({
                    "texto": f"{len(sem_conferir)} aposta(s) sem conferência!",
                    "cor": Cores.PERIGO,
                })

        if stats["total_acertos"] == 0 and stats["total_apostas"] > 0:
            alertas.append({
                "texto": "Nenhum acerto registrado. Verifique suas apostas!",
                "cor": Cores.ALERTA,
            })

        return alertas

    def _criar_card_alerta(self, parent, alerta):
        cor = alerta.get("cor", Cores.ALERTA)
        card = ctk.CTkFrame(parent, fg_color=cor, corner_radius=6)
        card.pack(fill="x", pady=3, padx=10)
        ctk.CTkLabel(card, text=f"⚠  {alerta['texto']}", font=("Arial", 12),
                       text_color="white").pack(side="left", padx=15, pady=8)

    def _criar_card_resultado_preview(self, parent, resultado):
        card = ctk.CTkFrame(parent, fg_color="#f8f9fa", corner_radius=8,
                                border_width=1, border_color="#dee2e6")
        card.pack(fill="x", pady=3, padx=20)
        card.configure(cursor="hand2")

        header = ctk.CTkFrame(card, fg_color=Cores.PRIMARIO, corner_radius=8)
        header.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(header, text=f"🎰 {LOTERIAS_NOME.get(resultado.tipo_loteria, resultado.tipo_loteria)}",
                       font=("Arial", 13, "bold"), text_color="white").pack(side="left", padx=10)
        ctk.CTkLabel(header, text=f"#{resultado.concurso}  |  {resultado.data_sorteio}",
                       font=("Arial", 12), text_color="white").pack(side="left", padx=10)
        ctk.CTkLabel(header, text=f"R$ {resultado.premio_acumulado:,.2f}",
                       font=("Arial", 12, "bold"), text_color="white").pack(side="right", padx=10)

        nums_str = resultado.numeros_por_extenso
        ctk.CTkLabel(card, text=nums_str, font=("Consolas", 14, "bold"),
                       text_color=Cores.PRIMARIO).pack(pady=5)

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
    # CADASTRO DE JOGADOR
    # ------------------------------------------------------------------ #
    def abrir_cadastro(self):
        self.limpar_conteudo()
        self.current_view_name = "cadastro"

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="👤  Cadastro de Jogador",
                       font=("Arial", 24, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w", padx=20)

        form_frame = ctk.CTkFrame(scroll, fg_color="#f8f9fa", corner_radius=10)
        form_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(form_frame, text="Nome Completo:", font=("Arial", 13, "bold")).pack(
            pady=(15, 5), anchor="w", padx=15)
        self.entry_nome = ctk.CTkEntry(form_frame, placeholder_text="Digite seu nome",
                                            width=300, fg_color="white",
                                            text_color="#333333", border_width=0)
        self.entry_nome.pack(pady=(0, 10), padx=15, fill="x")

        ctk.CTkLabel(form_frame, text="CPF:", font=("Arial", 13, "bold")).pack(
            pady=(5, 5), anchor="w", padx=15)
        self.entry_cpf = ctk.CTkEntry(form_frame, placeholder_text="000.000.000-00",
                                           width=300, fg_color="white",
                                           text_color="#333333", border_width=0)
        self.entry_cpf.pack(pady=(0, 10), padx=15, fill="x")

        ctk.CTkLabel(form_frame, text="E-mail:", font=("Arial", 13, "bold")).pack(
            pady=(5, 5), anchor="w", padx=15)
        self.entry_email = ctk.CTkEntry(form_frame, placeholder_text="seu@email.com",
                                              width=300, fg_color="white",
                                              text_color="#333333", border_width=0)
        self.entry_email.pack(pady=(0, 15), padx=15, fill="x")

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="💾  Salvar Cadastro",
                         command=self.salvar_cadastro, fg_color=Cores.PRIMARIO,
                         hover_color="#0d3c6b").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙  Voltar",
                         command=self.voltar_inicio, fg_color=Cores.NEUTRO,
                         hover_color="#4a5258").pack(side="left", padx=10)

    def salvar_cadastro(self):
        nome = self.entry_nome.get().strip()
        cpf = self.entry_cpf.get().strip()
        email = self.entry_email.get().strip()

        if not nome or not cpf:
            self._mostrar_toast("❌ Nome e CPF são obrigatórios!")
            return

        jogador = self.controller.add_jogador(nome=nome, cpf=cpf, email=email)
        self.jogador_atual = jogador
        self.usuario_nome = nome

        self._mostrar_toast(f"✅ Cadastro salvo: {nome}!")
        self.after(1500, lambda: self.voltar_inicio())

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
        numeros = []
        import random
        numeros = sorted(random.sample(range(1, maximo + 1), qtd))

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

        self._mostrar_toast(f"✅ Aposta salva: {LOTERIAS_NOME.get(tipo, tipo)} | {len(numeros)} números | R$ {valor:.2f}")
        self.after(1500, lambda: self.abrir_apostas())

    # ------------------------------------------------------------------ #
    # EXPORTAÇÃO
    # ------------------------------------------------------------------ #
    def mostrar_exportacao(self, texto: str):
        self.limpar_conteudo()
        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="📄  Relatório de Apostas",
                       font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w", padx=20)

        frame_info = ctk.CTkFrame(scroll, fg_color="#e3f2fd", corner_radius=10,
                                      border_width=2, border_color=Cores.PRIMARIO)
        frame_info.pack(fill="x", pady=(0, 15), padx=20)
        ctk.CTkLabel(frame_info, text=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                                          f"Total de apostas: {len(self.controller.get_apostas())}",
                       font=("Arial", 12), text_color="#1565c0").pack(pady=15, padx=15)

        text_box = ctk.CTkTextbox(scroll, width=800, height=400, font=("Consolas", 12))
        text_box.pack(pady=10, padx=20, fill="both", expand=True)
        text_box.insert("1.0", texto)

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="📋 Copiar para Área de Transferência",
                         command=lambda: self._copiar_texto(texto),
                         fg_color=Cores.PRIMARIO).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="💾 Salvar em Arquivo",
                         command=lambda: self._salvar_arquivo(texto),
                         fg_color=Cores.SUCESSO).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="🔙 Voltar",
                         command=self.abrir_apostas,
                         fg_color=Cores.NEUTRO).pack(side="left", padx=10)

    def _copiar_texto(self, texto: str):
        self.clipboard_clear()
        self.clipboard_append(texto)
        self._mostrar_toast("✅ Texto copiado!")

    def _salvar_arquivo(self, texto: str):
        filename = f"relatorio_loterias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = f"G:/Python/BR_Loterias_Caixa/{filename}"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(texto)
            self._mostrar_toast(f"✅ Relatório salvo: {filepath}")
        except Exception as e:
            self._mostrar_toast(f"❌ Erro ao salvar: {str(e)}")

    # ------------------------------------------------------------------ #
    # RELÓGIO / STATUS
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