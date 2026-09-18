"""
Sistema de Controle de Apostas e Resultados das Loterias da Caixa.
Interface gráfica com CustomTkinter.
"""
import logging
import random
import threading
import traceback

import customtkinter as ctk

try:
    import psutil
except ImportError:
    psutil = None

from cores import Cores
from controllers import AppController
from views.busca_mixin import BuscaMixin
from views.nova_aposta_mixin import NovaApostaMixin
from views.sistema_mixin import SistemaMixin

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


class App(BuscaMixin, NovaApostaMixin, SistemaMixin, ctk.CTk):
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
        self.after(3000, self._agendar_sync_automatico)

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

        self.lbl_creditos = ctk.CTkLabel(self.footer, text="Desenvolvido por: Paulo Sérgio dos Santos Fontes | Tel: (79) 98805 6632",
                                                font=("Arial", 11))
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

        self.btn_historico = ctk.CTkButton(self.sidebar_frame, text="📜  Histórico", anchor="w",
                                            command=self.abrir_historico)
        self.btn_historico.pack(pady=5, padx=20, fill="x")

        self.btn_relatorio = ctk.CTkButton(self.sidebar_frame, text="📋  Relatório", anchor="w",
                                            command=self.abrir_relatorio)
        self.btn_relatorio.pack(pady=5, padx=20, fill="x")

        self.btn_jogador = ctk.CTkButton(self.sidebar_frame, text="👤  Cadastro", anchor="w",
                                            command=self.abrir_cadastro)
        self.btn_jogador.pack(pady=5, padx=20, fill="x")

        self.btn_sincronizar = ctk.CTkButton(self.sidebar_frame, text="🔄  Sincronizar", anchor="w",
                                              command=self._sync_handler,
                                              fg_color="#28a745", hover_color="#1e7e34")
        self.btn_sincronizar.pack(pady=5, padx=20, fill="x")

        separator = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="#dee2e6")
        separator.pack(fill="x", padx=20, pady=15)

        self.tema_escuro = False
        self.btn_tema = ctk.CTkButton(self.sidebar_frame, text="🌙  Modo Escuro", anchor="w",
                                        command=self.toggle_tema,
                                        fg_color="#555555", hover_color="#333333")
        self.btn_tema.pack(pady=5, padx=20, fill="x")

        self.btn_sair = ctk.CTkButton(self.sidebar_frame, text="🚪  Sair", anchor="w",
                                       command=self.quit, fg_color=Cores.PERIGO, hover_color="#a83232")
        self.btn_sair.pack(side="bottom", pady=(5, 10), padx=20, fill="x")

        self.btn_sobre = ctk.CTkButton(self.sidebar_frame, text="ℹ️  Sobre", anchor="w",
                                        command=self.mostrar_sobre,
                                        fg_color="#6c757d", hover_color="#545b62")
        self.btn_sobre.pack(side="bottom", pady=5, padx=20, fill="x")

        self.btn_config = ctk.CTkButton(self.sidebar_frame, text="⚙️  Configurações", anchor="w",
                                         command=self.abrir_configuracoes,
                                         fg_color="#6c757d", hover_color="#545b62")
        self.btn_config.pack(side="bottom", pady=5, padx=20, fill="x")

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
            "historico": self.btn_historico,
            "relatorio": self.btn_relatorio,
        }
        cores_default = {
            "home": Cores.PRIMARIO,
            "resultados": Cores.PRIMARIO,
            "apostas": Cores.PRIMARIO,
            "conferencia": Cores.PRIMARIO,
            "estatisticas": Cores.PRIMARIO,
            "historico": Cores.PRIMARIO,
            "relatorio": Cores.PRIMARIO,
        }
        cor_ativa = "#0d3c6b"
        for name, btn in botoes.items():
            if btn:
                btn.configure(fg_color=cores_default.get(name, Cores.PRIMARIO))
        if btn_name in botoes and botoes[btn_name]:
            botoes[btn_name].configure(fg_color=cor_ativa)

    # ------------------------------------------------------------------ #
    # TEMA
    # ------------------------------------------------------------------ #
    def toggle_tema(self):
        self.tema_escuro = not self.tema_escuro
        if self.tema_escuro:
            ctk.set_appearance_mode("dark")
            self.btn_tema.configure(text="☀️  Modo Claro", fg_color="#E0A800", hover_color="#c69500")
        else:
            ctk.set_appearance_mode("light")
            self.btn_tema.configure(text="🌙  Modo Escuro", fg_color="#555555", hover_color="#333333")

    # ------------------------------------------------------------------ #
    # SOBRE
    # ------------------------------------------------------------------ #
    def mostrar_sobre(self):
        self.limpar_conteudo()
        self.current_view_name = "sobre"

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=40, pady=40)

        # Logo/Título
        ctk.CTkLabel(scroll, text="🎰",
                       font=("Arial", 80), text_color=Cores.PRIMARIO).pack(pady=(20, 10))
        ctk.CTkLabel(scroll, text="Loterias da Caixa",
                       font=("Arial", 32, "bold"), text_color=Cores.PRIMARIO).pack(pady=(0, 5))
        ctk.CTkLabel(scroll, text="Sistema de Controle de Apostas e Resultados",
                       font=("Arial", 16), text_color="#666").pack(pady=(0, 30))

        # Versão
        versao_frame = ctk.CTkFrame(scroll, fg_color="#e3f2fd", corner_radius=10,
                                     border_width=2, border_color=Cores.PRIMARIO)
        versao_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(versao_frame, text="📋 Informações do Sistema",
                       font=("Arial", 16, "bold"), text_color=Cores.PRIMARIO).pack(pady=(15, 5))
        ctk.CTkLabel(versao_frame, text="Versão: 1.0.0",
                       font=("Arial", 14), text_color="#333").pack()
        ctk.CTkLabel(versao_frame, text="Python 3.14+ | CustomTkinter | SQLite",
                       font=("Arial", 12), text_color="#666").pack(pady=(0, 15))

        # Desenvolvedor
        dev_frame = ctk.CTkFrame(scroll, fg_color="#e8f5e9", corner_radius=10,
                                  border_width=2, border_color=Cores.SUCESSO)
        dev_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(dev_frame, text="👨‍💻 Desenvolvedor",
                       font=("Arial", 16, "bold"), text_color=Cores.SUCESSO).pack(pady=(15, 5))
        ctk.CTkLabel(dev_frame, text="Paulo Sérgio dos Santos Fontes",
                       font=("Arial", 18, "bold"), text_color="#333").pack()
        ctk.CTkLabel(dev_frame, text="📞 Telefone: (79) 98805 6632",
                       font=("Arial", 14), text_color="#555").pack(pady=(5, 15))

        # Funcionalidades
        func_frame = ctk.CTkFrame(scroll, fg_color="#fff3e0", corner_radius=10,
                                   border_width=2, border_color=Cores.ALERTA)
        func_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(func_frame, text="✨ Funcionalidades",
                       font=("Arial", 16, "bold"), text_color="#e65100").pack(pady=(15, 10))

        funcionalidades = [
            "✅ 7 Loterias da Caixa",
            "✅ Gerenciamento de Apostas",
            "✅ Conferência Automática",
            "✅ Estatísticas e Análises",
            "✅ Histórico Completo",
            "✅ Relatórios Exportáveis",
            "✅ Busca Global",
            "✅ Tema Escuro/Claro",
            "✅ Banco de Dados SQLite",
        ]
        for f in funcionalidades:
            ctk.CTkLabel(func_frame, text=f, font=("Arial", 13),
                           text_color="#333").pack(anchor="w", padx=30)

        ctk.CTkLabel(func_frame, text="", font=("Arial", 5)).pack()

        # Agradecimentos
        ctk.CTkLabel(scroll, text="Desenvolvido com ❤️ por Paulo Sérgio dos Santos Fontes",
                       font=("Arial", 14, "bold"), text_color=Cores.PRIMARIO).pack(pady=30)

    # ------------------------------------------------------------------ #
    # HANDLERS
    # ------------------------------------------------------------------ #
    SYNC_INTERVALO_MS = 6 * 60 * 60 * 1000

    def _sync_handler(self):
        if getattr(self, "_sync_em_andamento", False):
            return
        self._sync_em_andamento = True
        threading.Thread(target=self._sync_worker, daemon=True).start()

    def _sync_worker(self):
        try:
            result = self.controller.sync_and_refresh()
        except Exception as e:
            logging.exception("Falha na sincronização")
            result = {"sync_count": 0, "errors": [str(e)], "conferidas": {}}
        self.after(0, self._atualizar_apos_sync, result)

    def _atualizar_apos_sync(self, result):
        self._sync_em_andamento = False
        self.voltar_inicio()
        erros = result.get("errors", [])
        conf = result.get("conferidas", {})
        msg = f"Sync: {result.get('sync_count', 0)} novos resultados"
        if conf.get("novas"):
            msg += f" | {conf['novas']} apostas conferidas ({conf['premiadas']} premiadas)"
        if erros:
            self._mostrar_toast(f"⚠️ {msg} | {len(erros)} erro(s) — veja o log", erro=True)
        else:
            self._mostrar_toast(f"✅ {msg}")

    def _agendar_sync_automatico(self):
        self._sync_handler()
        self.after(self.SYNC_INTERVALO_MS, self._agendar_sync_automatico)

    def _mostrar_toast(self, mensagem: str, erro: bool = False):
        toast = ctk.CTkLabel(self.content_frame, text=mensagem,
                                  font=("Arial", 13, "bold"), text_color="white",
                                  fg_color=Cores.PERIGO if erro else Cores.SUCESSO,
                                  corner_radius=8, padx=15, pady=10)
        toast.place(relx=0.5, rely=0.5, anchor="center")
        self.after(4000 if erro else 2000, lambda: toast.destroy())

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

    def mostrar_detalhes_resultado(self, resultado):
        self.limpar_conteudo()
        self.current_view_name = "detalhes_resultado"

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        nome = LOTERIAS_NOME.get(resultado.tipo_loteria, resultado.tipo_loteria)
        ctk.CTkLabel(scroll, text=f"🎰 {nome} - Detalhes",
                       font=("Arial", 24, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w")

        # Header com info principal
        header = ctk.CTkFrame(scroll, fg_color=Cores.PRIMARIO, corner_radius=10)
        header.pack(fill="x", pady=5)
        ctk.CTkLabel(header, text=f"Concurso #{resultado.concurso}",
                       font=("Arial", 16, "bold"), text_color="white").pack(side="left", padx=20)
        ctk.CTkLabel(header, text=f"Data: {resultado.data_sorteio}",
                       font=("Arial", 14), text_color="white").pack(side="right", padx=20)

        # Números sorteados
        nums_frame = ctk.CTkFrame(scroll, fg_color="#f8f9fa", corner_radius=10)
        nums_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(nums_frame, text="Números Sorteados:",
                       font=("Arial", 16, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(nums_frame, text=resultado.numeros_por_extenso,
                       font=("Consolas", 24, "bold"), text_color=Cores.PRIMARIO).pack(pady=10)

        # Info financeira
        info_frame = ctk.CTkFrame(scroll, fg_color="#e8f5e9", corner_radius=10,
                                  border_width=2, border_color=Cores.SUCESSO)
        info_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(info_frame, text="💰 Informações Financeiras",
                       font=("Arial", 14, "bold"), text_color=Cores.SUCESSO).pack(
            pady=(10, 5), anchor="w", padx=15)

        dados = [
            (f"Prêmio Acumulado: R$ {resultado.premio_acumulado:,.2f}"),
            (f"Ganhadores: {resultado.ganhadores}"),
            (f"Arrecadação Total: R$ {resultado.arrecadacao_total:,.2f}"),
        ]
        for dado in dados:
            ctk.CTkLabel(info_frame, text=f"  → {dado}",
                           font=("Arial", 13), text_color="#333").pack(anchor="w", padx=20)

        # Apostas que usaram esses números
        apostas = self.controller.get_apostas()
        apostas_match = []
        for a in apostas:
            if a.tipo_loteria == resultado.tipo_loteria:
                acertos = len(set(a.numeros) & set(resultado.numeros_sorteados))
                apostas_match.append((a, acertos))

        if apostas_match:
            match_frame = ctk.CTkFrame(scroll, fg_color="#fff3e0", corner_radius=10,
                                       border_width=2, border_color=Cores.ALERTA)
            match_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(match_frame, text="🎯 Suas Apostas Neste Concurso",
                           font=("Arial", 14, "bold"), text_color="#e65100").pack(
                pady=(10, 5), anchor="w", padx=15)

            for a, acertos in sorted(apostas_match, key=lambda x: x[1], reverse=True):
                cor = Cores.SUCESSO if acertos > 0 else Cores.NEUTRO
                nums = " | ".join(str(n) for n in a.numeros)
                ctk.CTkLabel(match_frame,
                               text=f"  🎯 {acertos} acerto(s): {nums}",
                               font=("Consolas", 13), text_color=cor).pack(anchor="w", padx=20)

        # Voltar
        ctk.CTkButton(scroll, text="🔙  Voltar aos Resultados",
                       command=self.abrir_resultados, fg_color=Cores.NEUTRO,
                       hover_color="#4a5258").pack(pady=20)

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
    # DETALHES DA APOSTA
    # ------------------------------------------------------------------ #
    def mostrar_detalhes_aposta(self, aposta):
        self.limpar_conteudo()
        self.current_view_name = "detalhes_aposta"

        from views.detalhes_aposta_view import DetalhesApostaView
        self.detalhes_view = DetalhesApostaView(self, self.controller)
        self.detalhes_view.render(aposta)

    # ------------------------------------------------------------------ #
    # CONFERÊNCIA
    # ------------------------------------------------------------------ #
    def abrir_conferencia(self):
        self.limpar_conteudo()
        self.current_view_name = "conferencia"
        self.destacar_botao("conferencia")

        from views.conferencia_view import ConferenciaView
        self.conferencia_view = ConferenciaView(self, self.controller)
        self.conferencia_view.render()

    def mostrar_tela_conferencia(self):
        self.abrir_conferencia()

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
    # HISTÓRICO
    # ------------------------------------------------------------------ #
    def abrir_historico(self):
        self.limpar_conteudo()
        self.current_view_name = "historico"
        self.destacar_botao("historico")

        from views.historico_view import HistoricoView
        self.historico_view = HistoricoView(self, self.controller)
        self.historico_view.render()

    # ------------------------------------------------------------------ #
    # RELATÓRIO
    # ------------------------------------------------------------------ #
    def abrir_relatorio(self):
        self.limpar_conteudo()
        self.current_view_name = "relatorio"
        self.destacar_botao("relatorio")

        from views.relatorio_view import RelatorioView
        self.relatorio_view = RelatorioView(self, self.controller)
        self.relatorio_view.render()

    # ------------------------------------------------------------------ #
    # CONFIGURAÇÕES
    # ------------------------------------------------------------------ #
    def abrir_configuracoes(self):
        self.limpar_conteudo()
        self.current_view_name = "config"

        from views.config_view import ConfigView
        self.config_view = ConfigView(self, self.controller)
        self.config_view.render()

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

        try:
            jogador = self.controller.add_jogador(nome=nome, cpf=cpf, email=email)
        except ValueError as e:
            self._mostrar_toast(f"❌ {e}")
            return
        self.jogador_atual = jogador
        self.usuario_nome = nome

        self._mostrar_toast(f"✅ Cadastro salvo: {nome}!")
        self.after(1500, lambda: self.voltar_inicio())



if __name__ == "__main__":
    app = App()
    app.mainloop()