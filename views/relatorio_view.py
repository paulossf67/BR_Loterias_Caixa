import customtkinter as ctk
from datetime import datetime
from collections import defaultdict

from cores import Cores
from services.api_service import LOTERIAS

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}


class RelatorioView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

    def render(self):
        self.parent.limpar_conteudo()
        self.scroll_frame = ctk.CTkScrollableFrame(self.parent.content_frame,
                                                    fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self.scroll_frame, text="📊  Relatório Completo",
                       font=("Arial", 22, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 20), anchor="w")

        stats = self.controller.get_stats()
        apostas = self.controller.get_apostas()
        resultados = self.controller.get_resultados()

        self._render_resumo_geral(stats)
        self._render_resumo_financeiro(apostas)
        self._render_resumo_por_loteria(apostas, resultados)
        self._render_resumo_temporal(apostas)
        self._render_botao_exportar()

    def _render_resumo_geral(self, stats: dict):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="#e3f2fd", corner_radius=10,
                             border_width=2, border_color=Cores.PRIMARIO)
        frame.pack(fill="x", pady=5, padx=20)
        ctk.CTkLabel(frame, text="📋 Resumo Geral",
                       font=("Arial", 16, "bold"), text_color=Cores.PRIMARIO).pack(
            pady=(10, 5), anchor="w", padx=15)

        dados = [
            f"Total de Resultados: {stats['total_resultados']}",
            f"Total de Apostas: {stats['total_apostas']}",
            f"Total Investido: R$ {stats['total_gasto']:,.2f}",
            f"Total de Acertos: {stats['total_acertos']}",
        ]
        for d in dados:
            ctk.CTkLabel(frame, text=f"  → {d}", font=("Arial", 13),
                           text_color="#333").pack(anchor="w", padx=20)

    def _render_resumo_financeiro(self, apostas: list):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="#e8f5e9", corner_radius=10,
                             border_width=2, border_color=Cores.SUCESSO)
        frame.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(frame, text="💰 Resumo Financeiro",
                       font=("Arial", 16, "bold"), text_color=Cores.SUCESSO).pack(
            pady=(10, 5), anchor="w", padx=15)

        total_gasto = sum(a.valor for a in apostas)
        total_premio = sum(a.premio for a in apostas)
        lucro = total_premio - total_gasto

        dados = [
            f"Total Investido: R$ {total_gasto:,.2f}",
            f"Total em Prêmios: R$ {total_premio:,.2f}",
            f"{'🟢 Lucro' if lucro >= 0 else '🔴 Prejuízo'}: R$ {abs(lucro):,.2f}",
            f"ROI: {(total_premio/total_gasto*100) if total_gasto > 0 else 0:.1f}%",
        ]
        for d in dados:
            ctk.CTkLabel(frame, text=f"  → {d}", font=("Arial", 13),
                           text_color="#333").pack(anchor="w", padx=20)

    def _render_resumo_por_loteria(self, apostas: list, resultados: list):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="#fff3e0", corner_radius=10,
                             border_width=2, border_color=Cores.ALERTA)
        frame.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(frame, text="🎰 Resumo por Loteria",
                       font=("Arial", 16, "bold"), text_color="#e65100").pack(
            pady=(10, 5), anchor="w", padx=15)

        por_loteria = defaultdict(lambda: {"apostas": 0, "gasto": 0, "acertos": 0, "premio": 0})
        for a in apostas:
            por_loteria[a.tipo_loteria]["apostas"] += 1
            por_loteria[a.tipo_loteria]["gasto"] += a.valor
            por_loteria[a.tipo_loteria]["acertos"] += a.acertos
            por_loteria[a.tipo_loteria]["premio"] += a.premio

        por_loteria_res = defaultdict(int)
        for r in resultados:
            por_loteria_res[r.tipo_loteria] += 1

        for tipo in LOTERIAS.keys():
            dados = por_loteria.get(tipo, {"apostas": 0, "gasto": 0, "acertos": 0, "premio": 0})
            nome = LOTERIAS_NOME.get(tipo, tipo)
            texto = (f"  🎰 {nome}: {dados['apostas']} apostas | "
                     f"R$ {dados['gasto']:,.2f} | "
                     f"{dados['acertos']} acertos | "
                     f"R$ {dados['premio']:,.2f}")
            ctk.CTkLabel(frame, text=texto, font=("Arial", 12),
                           text_color="#333").pack(anchor="w", padx=15)

    def _render_resumo_temporal(self, apostas: list):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="#f0f0f0", corner_radius=10)
        frame.pack(fill="x", pady=10, padx=20)
        ctk.CTkLabel(frame, text="📅 Apostas por Período",
                       font=("Arial", 16, "bold"), text_color="#333").pack(
            pady=(10, 5), anchor="w", padx=15)

        por_mes = defaultdict(int)
        meses_nomes = {
            "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
            "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
            "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
        }
        for a in apostas:
            partes = a.data_aposta.split("/")
            if len(partes) == 3:
                mes = partes[1]
                ano = partes[2]
                chave = f"{meses_nomes.get(mes, mes)}/{ano}"
            else:
                chave = a.data_aposta[:7] if len(a.data_aposta) >= 7 else a.data_aposta
            por_mes[chave] += 1

        if not por_mes:
            ctk.CTkLabel(frame, text="  Nenhuma aposta registrada",
                           font=("Arial", 12), text_color="gray").pack(anchor="w", padx=20)
        else:
            for periodo, count in sorted(por_mes.items()):
                ctk.CTkLabel(frame, text=f"  {periodo}: {count} aposta(s)",
                               font=("Arial", 12)).pack(anchor="w", padx=20)

    def _render_botao_exportar(self):
        frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        frame.pack(fill="x", pady=20)

        ctk.CTkButton(frame, text="📄 Exportar Relatório Completo",
                        command=self._exportar_completo,
                        fg_color=Cores.DOCUMENTO, hover_color="#563389").pack(side="left", padx=10)
        ctk.CTkButton(frame, text="📋 Copiar Resumo",
                        command=self._copiar_resumo,
                        fg_color=Cores.PRIMARIO, hover_color="#0d3c6b").pack(side="left", padx=10)
        ctk.CTkButton(frame, text="📊 Exportar CSV",
                        command=self._exportar_csv,
                        fg_color="#28a745", hover_color="#1e7e34").pack(side="left", padx=10)

    def _exportar_completo(self):
        texto = self._gerar_texto_completo()
        filename = f"G:/Python/BR_Loterias_Caixa/relatorio_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(texto)
            self.parent._mostrar_toast(f"✅ Relatório salvo: {filename}")
        except Exception as e:
            self.parent._mostrar_toast(f"❌ Erro: {str(e)}")

    def _copiar_resumo(self):
        texto = self._gerar_texto_completo()
        self.parent.clipboard_clear()
        self.parent.clipboard_append(texto)
        self.parent._mostrar_toast("Relatorio copiado!")

    def _exportar_csv(self):
        try:
            arquivos = self.controller.exportar_csv()
            if arquivos:
                self.parent._mostrar_toast(f"CSV exportado: {len(arquivos)} arquivos em exports/")
            else:
                self.parent._mostrar_toast("Nenhum arquivo exportado")
        except Exception as e:
            self.parent._mostrar_toast(f"Erro ao exportar: {str(e)}")

    def _gerar_texto_completo(self) -> str:
        stats = self.controller.get_stats()
        apostas = self.controller.get_apostas()
        resultados = self.controller.get_resultados()

        texto = "=" * 60 + "\n"
        texto += "  RELATÓRIO COMPLETO - LOTERIAS DA CAIXA\n"
        texto += f"  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        texto += "=" * 60 + "\n\n"

        texto += "RESUMO GERAL\n"
        texto += f"  Resultados: {stats['total_resultados']}\n"
        texto += f"  Apostas: {stats['total_apostas']}\n"
        texto += f"  Investido: R$ {stats['total_gasto']:,.2f}\n"
        texto += f"  Acertos: {stats['total_acertos']}\n\n"

        total_gasto = sum(a.valor for a in apostas)
        total_premio = sum(a.premio for a in apostas)
        lucro = total_premio - total_gasto

        texto += "RESUMO FINANCEIRO\n"
        texto += f"  Investido: R$ {total_gasto:,.2f}\n"
        texto += f"  Prêmios: R$ {total_premio:,.2f}\n"
        texto += f"  {'Lucro' if lucro >= 0 else 'Prejuízo'}: R$ {abs(lucro):,.2f}\n\n"

        texto += "APOSTAS\n"
        texto += "-" * 60 + "\n"
        for a in apostas:
            nome = LOTERIAS_NOME.get(a.tipo_loteria, a.tipo_loteria)
            nums = " | ".join(str(n) for n in a.numeros)
            texto += f"  {nome} #{a.data_sorteio}\n"
            texto += f"    Números: {nums}\n"
            texto += f"    Valor: R$ {a.valor:,.2f} | Acertos: {a.acertos} | Prêmio: R$ {a.premio:,.2f}\n\n"

        texto += "=" * 60 + "\n"
        texto += "  FIM DO RELATÓRIO\n"
        texto += "=" * 60 + "\n"
        return texto