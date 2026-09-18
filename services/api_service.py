import json
import os
import requests
from typing import List

from models.resultado import Resultado
from models.aposta import Aposta
from models.jogador import Jogador
from models.conferencia import Conferência


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

LOTERIAS = {
    "mega-sena": {"nome": "Mega-Sena", "numeros": 6, "faixa": 4},
    "quina": {"nome": "Quina", "numeros": 5, "faixa": 4},
    "lotofacil": {"nome": "Lotofácil", "numeros": 15, "faixa": 11},
    "lotomania": {"nome": "Lotomania", "numeros": 20, "faixa": 10},
    "timemania": {"nome": "Timemania", "numeros": 10, "faixa": 7},
    "dupla-sena": {"nome": "Dupla Sena", "numeros": 6, "faixa": 4},
    "dia-de-sorte": {"nome": "Dia de Sorte", "numeros": 7, "faixa": 6},
}


class DataService:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.resultados_file = os.path.join(DATA_DIR, "resultados.json")
        self.apostas_file = os.path.join(DATA_DIR, "apostas.json")
        self.jogadores_file = os.path.join(DATA_DIR, "jogadores.json")
        self.conferencias_file = os.path.join(DATA_DIR, "conferências.json")

    def _load_json(self, filepath: str) -> list:
        if not os.path.exists(filepath):
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_json(self, filepath: str, data: list):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_resultados(self) -> List[Resultado]:
        dados = self._load_json(self.resultados_file)
        return [Resultado.from_dict(d) for d in dados]

    def salvar_resultados(self, resultados: List[Resultado]):
        dados = [r.to_dict() for r in resultados]
        self._save_json(self.resultados_file, dados)

    def get_apostas(self) -> List[Aposta]:
        dados = self._load_json(self.apostas_file)
        return [Aposta.from_dict(d) for d in dados]

    def salvar_apostas(self, apostas: List[Aposta]):
        dados = [a.to_dict() for a in apostas]
        self._save_json(self.apostas_file, dados)

    def add_aposta(self, aposta: Aposta) -> Aposta:
        apostas = self.get_apostas()
        aposta.id = max([a.id for a in apostas], default=0) + 1
        apostas.append(aposta.to_dict())
        self._save_json(self.apostas_file, apostas)
        return aposta

    def remover_aposta(self, aposta_id: int) -> bool:
        apostas = self.get_apostas()
        original_len = len(apostas)
        apostas = [a for a in apostas if a.get("id") != aposta_id]
        if len(apostas) < original_len:
            self._save_json(self.apostas_file, apostas)
            return True
        return False

    def get_jogadores(self) -> List[Jogador]:
        dados = self._load_json(self.jogadores_file)
        return [Jogador.from_dict(d) for d in dados]

    def salvar_jogadores(self, jogadores: List[Jogador]):
        dados = [j.to_dict() for j in jogadores]
        self._save_json(self.jogadores_file, dados)

    def add_jogador(self, jogador: Jogador) -> Jogador:
        jogadores = self.get_jogadores()
        jogador.id = max([j.id for j in jogadores], default=0) + 1
        jogadores.append(jogador.to_dict())
        self._save_json(self.jogadores_file, jogadores)
        return jogador

    def get_conferencias(self) -> List[Conferência]:
        dados = self._load_json(self.conferencias_file)
        return [Conferência.from_dict(d) for d in dados]

    def salvar_conferencias(self, conferencias: List[Conferência]):
        dados = [c.to_dict() for c in conferencias]
        self._save_json(self.conferencias_file, dados)


class APIService:
    BASE_URL = "https://loterias-api.herokuapp.com"
    FALLBACK_BASE = "https://api.caixa.gov.br/loterias"

    def __init__(self):
        self.data_service = DataService()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def fetch_resultados(self, tipo_loteria: str = None) -> List[Resultado]:
        resultados = []
        tipos = [tipo_loteria] if tipo_loteria else list(LOTERIAS.keys())

        for tipo in tipos:
            try:
                resultado = self._fetch_tipo(tipo)
                if resultado:
                    resultados.extend(resultado)
            except Exception:
                pass

        if not resultados:
            resultados = self.data_service.get_resultados()

        return resultados

    def _fetch_tipo(self, tipo: str) -> List[Resultado]:
        resultados = []
        try:
            url = f"{self.BASE_URL}/{tipo}/ultimos"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                dados = resp.json()
                for item in dados:
                    r = Resultado(
                        tipo_loteria=tipo,
                        concurso=item.get("concurso", 0),
                        data_sorteio=item.get("data", ""),
                        numeros_sorteados=item.get("numeros", []),
                        numeros_especiais=item.get("especiais", []),
                        premio_acumulado=item.get("premio", 0.0),
                        ganhadores=item.get("ganhadores", 0),
                        arrecadacao_total=item.get("arrecadacao", 0.0),
                    )
                    resultados.append(r)
                return resultados
        except Exception:
            pass

        try:
            url = f"{self.FALLBACK_BASE}/{tipo}/ultimos"
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                dados = resp.json()
                for item in dados:
                    r = Resultado(
                        tipo_loteria=tipo,
                        concurso=item.get("concurso", 0),
                        data_sorteio=item.get("data", ""),
                        numeros_sorteados=item.get("numeros", []),
                        numeros_especiais=item.get("especiais", []),
                        premio_acumulado=item.get("premio", 0.0),
                        ganhadores=item.get("ganhadores", 0),
                        arrecadacao_total=item.get("arrecadacao", 0.0),
                    )
                    resultados.append(r)
                return resultados
        except Exception:
            pass

        return resultados

    def sync_data(self):
        resultados = self.fetch_resultados()
        if resultados:
            existing = self.data_service.get_resultados()
            existing_dict = {(r.tipo_loteria, r.concurso): r for r in existing}
            for r in resultados:
                key = (r.tipo_loteria, r.concurso)
                if key not in existing_dict:
                    existing.append(r)
            self.data_service.salvar_resultados(existing)
        return resultados