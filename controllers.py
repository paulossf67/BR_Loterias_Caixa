from typing import List, Optional
import threading
from datetime import datetime

from models.resultado import Resultado
from models.aposta import Aposta
from models.jogador import Jogador
from models.conferencia import Conferência
from services.api_service import APIService, DataService, LOTERIAS
from utils.helpers import gerar_numeros_aleatorios, validar_numeros, formatar_valor


class Controller:
    def __init__(self):
        self.data_service = DataService()
        self.api_service = APIService()

    def get_resultados(self) -> List[Resultado]:
        return self.data_service.get_resultados()

    def get_apostas(self) -> List[Aposta]:
        return self.data_service.get_apostas()

    def get_jogadores(self) -> List[Jogador]:
        return self.data_service.get_jogadores()

    def get_conferencias(self) -> List[Conferência]:
        return self.data_service.get_conferencias()

    def get_stats(self) -> dict:
        return self.data_service.get_stats()

    def sync_and_refresh(self) -> dict:
        return self.data_service.sync_and_refresh()

    def get_resultado_by_string(self, texto: str) -> Optional[Resultado]:
        resultados = self.get_resultados()
        for r in resultados:
            if f"{LOTERIAS.get(r.tipo_loteria, r.tipo_loteria)} #{r.concurso}" in texto:
                return r
        return None

    def add_aposta(self, tipo_loteria: str, numeros: List[int], valor: float,
                   data_sorteio: str = "") -> Aposta:
        aposta = Aposta(
            tipo_loteria=tipo_loteria,
            data_aposta=datetime.now().strftime("%d/%m/%Y"),
            numeros=numeros,
            valor=valor,
            data_sorteio=data_sorteio or datetime.now().strftime("%d/%m/%Y"),
        )
        return self.data_service.add_aposta(aposta)

    def remover_aposta(self, aposta_id: int) -> bool:
        return self.data_service.remover_aposta(aposta_id)

    def add_jogador(self, nome: str, cpf: str, email: str = "") -> Jogador:
        jogador = Jogador(nome=nome, cpf=cpf, email=email)
        return self.data_service.add_jogador(jogador)

    def get_jogador(self, cpf: str) -> Optional[Jogador]:
        return self.data_service.get_jogador(cpf)

    def conferir_apostas(self, resultado: Resultado) -> List[dict]:
        apostas = self.get_apostas()
        resultados = []
        for a in apostas:
            acertos = len(set(a.numeros) & set(resultado.numeros_sorteados))
            resultado_conferido = {
                "aposta": a,
                "acertos": acertos,
                "premio": self._calcular_premio(acertos, a.valor),
            }
            resultados.append(resultado_conferido)
        return resultados

    def _calcular_premio(self, acertos: int, valor_aposta: float) -> float:
        multiplicadores = {6: 1000, 5: 50, 4: 10, 3: 5, 2: 2, 1: 1, 0: 0}
        return valor_aposta * multiplicadores.get(acertos, 0)

    def exportar_apostas(self) -> str:
        apostas = self.get_apostas()
        texto = "=== RELATÓRIO DE APOSTAS ===\n\n"
        texto += f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        for a in apostas:
            nome = LOTERIAS.get(a.tipo_loteria, a.tipo_loteria)
            nums = " | ".join(str(n) for n in a.numeros)
            texto += f"{nome} #{a.data_sorteio}\n"
            texto += f"  Números: {nums}\n"
            texto += f"  Valor: {formatar_valor(a.valor)}\n"
            texto += f"  Acertos: {a.acertos} | Prêmio: {formatar_valor(a.premio)}\n\n"
        return texto

    def salvar_conferencia(self, conf: Conferência):
        self.data_service.salvar_conferencia(conf)


class AppController:
    def __init__(self, app):
        self.app = app
        self.controller = Controller()
        self.current_view_name = None

    def get_resultados(self):
        return self.controller.get_resultados()

    def get_apostas(self):
        return self.controller.get_apostas()

    def get_jogadores(self):
        return self.controller.get_jogadores()

    def get_stats(self):
        return self.controller.get_stats()

    def get_conferencias(self):
        return self.controller.get_conferencias()

    def sync_and_refresh(self):
        with threading.Thread(target=self._sync_worker, daemon=True):
            self._sync_worker()

    def _sync_worker(self):
        result = self.controller.sync_and_refresh()
        if hasattr(self.app, 'voltar_inicio'):
            self.app.after(0, self.app.voltar_inicio)
        return result

    def get_resultado_by_string(self, texto: str):
        return self.controller.get_resultado_by_string(texto)

    def add_aposta(self, tipo_loteria: str, numeros: list, valor: float, data_sorteio: str = ""):
        return self.controller.add_aposta(tipo_loteria, numeros, valor, data_sorteio)

    def remover_aposta(self, aposta_id: int):
        return self.controller.remover_aposta(aposta_id)

    def add_jogador(self, nome: str, cpf: str, email: str = ""):
        return self.controller.add_jogador(nome, cpf, email)

    def get_jogador(self, cpf: str):
        return self.controller.get_jogador(cpf)

    def nova_aposta(self):
        self.app.mostrar_tela_nova_aposta()

    def conferir_apostas(self):
        self.app.mostrar_tela_conferencia()

    def exportar_apostas(self):
        texto = self.controller.exportar_apostas()
        self.app.mostrar_exportacao(texto)