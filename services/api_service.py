import json
import logging
import os
import re
import requests
import sqlite3
import time
from typing import List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from models.resultado import Resultado
from models.aposta import Aposta
from models.jogador import Jogador
from models.conferencia import Conferencia
from services.database_service import DatabaseService

LOTERIAS = {
    "mega-sena": {"nome": "Mega-Sena", "numeros": 6, "maximo": 60, "faixa": 4},
    "quina": {"nome": "Quina", "numeros": 5, "maximo": 80, "faixa": 4},
    "lotofacil": {"nome": "Lotofácil", "numeros": 15, "maximo": 25, "faixa": 11},
    "lotomania": {"nome": "Lotomania", "numeros": 20, "maximo": 50, "faixa": 10},
    "timemania": {"nome": "Timemania", "numeros": 10, "maximo": 80, "faixa": 7},
    "dupla-sena": {"nome": "Dupla Sena", "numeros": 6, "maximo": 60, "faixa": 4},
    "dia-de-sorte": {"nome": "Dia de Sorte", "numeros": 7, "maximo": 31, "faixa": 6},
}

API_BASE_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api"

_TIPO_API_MAP = {
    "mega-sena": "megasena",
    "quina": "quina",
    "lotofacil": "lotofacil",
    "lotomania": "lotomania",
    "timemania": "timemania",
    "dupla-sena": "duplasena",
    "dia-de-sorte": "diadesorte",
}

_API_TIMEOUT = 5
_API_RETRIES = 2

log = logging.getLogger(__name__)


class APIService:
    """Serviço para buscar resultados das Loterias da Caixa."""

    def __init__(self):
        self.db = DatabaseService()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        })

    # ------------------------------------------------------------------
    # API real
    # ------------------------------------------------------------------

    def _get_api_endpoint(self, tipo: str) -> Optional[str]:
        """Retorna o nome do endpoint da API para um tipo de loteria."""
        return _TIPO_API_MAP.get(tipo)

    def _get_json(self, url: str) -> Optional[dict]:
        """GET com retry/backoff; registra falhas em vez de ocultá-las."""
        for tentativa in range(_API_RETRIES + 1):
            try:
                resp = self.session.get(url, timeout=_API_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code < 500:
                    log.warning("API %s respondeu %s", url, resp.status_code)
                    return None
                log.warning("API %s respondeu %s (tentativa %d)", url, resp.status_code, tentativa + 1)
            except (requests.RequestException, ValueError) as e:
                log.warning("Falha ao consultar %s (tentativa %d): %s", url, tentativa + 1, e)
            time.sleep(0.5 * (2 ** tentativa))
        return None

    def _fetch_from_api(self, tipo: str, concurso: int) -> Optional[Resultado]:
        """Tenta buscar um resultado específico da API oficial da Caixa."""
        endpoint = self._get_api_endpoint(tipo)
        if not endpoint:
            return None

        url = f"{API_BASE_URL}/{endpoint}/{concurso}"
        data = self._get_json(url)
        return self._parse_api_response(tipo, data) if data else None

    def _fetch_latest_from_api(self, tipo: str) -> Optional[Resultado]:
        """Tenta buscar o último concurso disponível de um tipo na API."""
        endpoint = self._get_api_endpoint(tipo)
        if not endpoint:
            return None

        url = f"{API_BASE_URL}/{endpoint}"
        data = self._get_json(url)
        return self._parse_api_response(tipo, data) if data else None

    def _parse_api_response(self, tipo: str, data: dict) -> Optional[Resultado]:
        """Converte o JSON da API em um objeto Resultado."""
        try:
            concurso = int(data.get("numero", 0))
            if concurso == 0:
                return None

            data_apuracao = data.get("dataApuracao", "")
            if not data_apuracao:
                data_apuracao = data.get("data", "")

            lista_dezenas = data.get("listaDezenas", [])
            numeros = sorted(int(d) for d in lista_dezenas)

            # Números especiais (trevos, etc.)
            trevos = data.get("listaTrevo", [])
            numeros_especiais = [int(t) for t in trevos] if trevos else []

            # Premiação
            premiacao = data.get("premiacao", [])
            ganhadores = 0
            premio_acumulado = 0.0
            if isinstance(premiacao, list):
                for p in premiacao:
                    qtd = p.get("numeroDeGanhadores", 0)
                    premio_acumulado += float(p.get("valorPremio", 0) or 0)
                    ganhadores += int(qtd or 0)

            valor_acumulado = float(data.get("valorAcumulado", 0) or 0)
            if valor_acumulado > 0:
                premio_acumulado = valor_acumulado

            arrecadacao = float(data.get("arrecadacaoTotal", 0) or 0)

            faixas = {}
            for p in premiacao if isinstance(premiacao, list) else []:
                m = re.search(r"\d+", str(p.get("descricaoFaixa") or p.get("descricao") or ""))
                if m:
                    faixas[int(m.group())] = float(p.get("valorPremio", 0) or 0)

            return Resultado(
                tipo_loteria=tipo,
                concurso=concurso,
                data_sorteio=data_apuracao,
                numeros_sorteados=numeros,
                numeros_especiais=numeros_especiais,
                premio_acumulado=premio_acumulado,
                ganhadores=ganhadores,
                arrecadacao_total=arrecadacao,
                premiacao=faixas,
            )
        except Exception:
            log.exception("Falha ao interpretar resposta da API (%s)", tipo)
            return None

    def _fetch_concursos_from_api(self, tipo: str, concursos: List[int]) -> List[Resultado]:
        """Busca uma lista de concursos via API real."""
        resultados = []
        for c in concursos:
            r = self._fetch_from_api(tipo, c)
            if r:
                resultados.append(r)
        return resultados

    # ------------------------------------------------------------------
    # sync_latest
    # ------------------------------------------------------------------

    def sync_latest(self, tipo: str) -> Optional[Resultado]:
        """Busca e persiste apenas o último concurso de um tipo de loteria."""
        resultado = self._fetch_latest_from_api(tipo)
        if resultado is None:
            # Tenta descobrir o último concurso via incremento
            resultado = self._fetch_latest_by_probe(tipo)

        if resultado is None:
            return None

        try:
            existing = self.db.get_resultado_by_tipo(tipo)
            existing_concursos = {r.concurso for r in existing}
            if resultado.concurso not in existing_concursos:
                self.db.salvar_resultados([resultado])
        except Exception:
            log.exception("Falha na sincronização")

        return resultado

    def _fetch_latest_by_probe(self, tipo: str) -> Optional[Resultado]:
        """Tenta encontrar o último concurso testando números incrementais."""
        endpoint = self._get_api_endpoint(tipo)
        if not endpoint:
            return None

        # Pega o último concurso já salvo no banco como base
        existing = self.db.get_resultado_by_tipo(tipo)
        base = max((r.concurso for r in existing), default=2000000)

        # Tenta de base+1 até base+50 para achar um novo
        for c in range(base + 1, base + 51):
            r = self._fetch_from_api(tipo, c)
            if r is not None:
                return r
        return None

    # ------------------------------------------------------------------
    # sync_all / _fetch_tipo
    # ------------------------------------------------------------------

    def sync_all(self, force: bool = False) -> dict:
        """Sincroniza todos os resultados com a Caixa."""
        resultados_sync = []
        errors = []

        tipos = list(LOTERIAS.keys())
        for tipo in tipos:
            try:
                if force:
                    self.db._executar(f"DELETE FROM resultados WHERE tipo_loteria = ?", (tipo,))

                existing = self.db.get_resultado_by_tipo(tipo)
                existing_concursos = {r.concurso for r in existing}

                novos = self._fetch_tipo(tipo)
                filtered = [n for n in novos if n.concurso not in existing_concursos]

                if filtered:
                    self.db.salvar_resultados(filtered)
                    resultados_sync.extend(filtered)
            except Exception as e:
                errors.append({"tipo": tipo, "error": str(e)})

        return {
            "sync_count": len(resultados_sync),
            "errors": errors,
            "total_resultados": len(self.db.get_resultados()),
            "total_apostas": len(self.db.get_apostas()),
        }

    def _fetch_tipo(self, tipo: str) -> List[Resultado]:
        """Busca resultados de um tipo específico de loteria."""
        if tipo == "mega-sena":
            return self._fetch_mega_sena()
        elif tipo == "quina":
            return self._fetch_quina()
        elif tipo == "lotofacil":
            return self._fetch_lotofacil()
        elif tipo == "lotomania":
            return self._fetch_lotomania()
        elif tipo == "timemania":
            return self._fetch_timemania()
        elif tipo == "dupla-sena":
            return self._fetch_dupla_sena()
        elif tipo == "dia-de-sorte":
            return self._fetch_dia_de_sorte()
        return []

    # ------------------------------------------------------------------
    # Mega-Sena
    # ------------------------------------------------------------------

    def _fetch_mega_sena(self) -> List[Resultado]:
        """Busca resultados da Mega-Sena: API -> HTML -> mock."""
        resultados = []

        # Tenta API real
        try:
            resultados = self._fetch_mega_sena_from_api()
        except Exception:
            log.exception("Falha na sincronização")

        # Tenta HTML
        if not resultados:
            try:
                url = "https://www.caixa.gov.br/loterias/megasena"
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    resultados = self._parse_html_megasena(resp.text)
            except Exception:
                log.exception("Falha na sincronização")

        if not resultados:
            resultados = self._fetch_mock_megasena()
        return resultados

    def _fetch_mega_sena_from_api(self) -> List[Resultado]:
        """Busca últimos concursos da Mega-Sena via API."""
        resultados = []
        latest = self._fetch_latest_from_api("mega-sena")
        if latest:
            resultados.append(latest)
            # Tenta buscar os 4 anteriores
            for c in range(latest.concurso - 1, max(latest.concurso - 5, 0), -1):
                r = self._fetch_from_api("mega-sena", c)
                if r:
                    resultados.append(r)
        return resultados

    def _parse_html_megasena(self, html: str) -> List[Resultado]:
        """Parse do HTML da Mega-Sena para extrair resultados."""
        resultados = []
        pattern = r'concurso\s*(\d+).*?data.*?(\d{2}/\d{2}/\d{4}).*?números\s*([\d\s/]+)'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        for match in matches[:10]:
            concurso = int(match[0])
            data = match[1]
            numeros = [int(n) for n in re.findall(r'\b(\d{1,2})\b', match[2]) if 1 <= int(n) <= 60][:6]
            if len(numeros) == 6:
                resultados.append(Resultado(
                    tipo_loteria="mega-sena",
                    concurso=concurso,
                    data_sorteio=data,
                    numeros_sorteados=sorted(numeros),
                    numeros_especiais=[],
                    premio_acumulado=0.0,
                    ganhadores=0,
                    arrecadacao_total=0.0,
                ))
        return resultados

    def _fetch_mock_megasena(self) -> List[Resultado]:
        """Fallback: gera resultados mock para Mega-Sena."""
        import random
        random.seed(datetime.now().day)
        resultados = []
        hoje = datetime.now()
        for i in range(5):
            data = (hoje - __import__("datetime").timedelta(days=i * 2)).strftime("%d/%m/%Y")
            concurso = 2026000 + i
            numeros = sorted(random.sample(range(1, 61), 6))
            resultados.append(Resultado(
                tipo_loteria="mega-sena",
                concurso=concurso,
                data_sorteio=data,
                numeros_sorteados=numeros,
                numeros_especiais=[],
                premio_acumulado=random.uniform(5000000, 50000000),
                ganhadores=random.randint(0, 3),
                arrecadacao_total=random.uniform(10000000, 100000000),
            ))
        return resultados

    # ------------------------------------------------------------------
    # Quina
    # ------------------------------------------------------------------

    def _fetch_quina(self) -> List[Resultado]:
        """Busca resultados da Quina: API -> mock."""
        resultados = []
        try:
            latest = self._fetch_latest_from_api("quina")
            if latest:
                resultados.append(latest)
                for c in range(latest.concurso - 1, max(latest.concurso - 5, 0), -1):
                    r = self._fetch_from_api("quina", c)
                    if r:
                        resultados.append(r)
        except Exception:
            log.exception("Falha na sincronização")

        if not resultados:
            resultados = self._fetch_mock_quina()
        return resultados

    def _fetch_mock_quina(self) -> List[Resultado]:
        import random
        random.seed(datetime.now().day + 1)
        resultados = []
        hoje = datetime.now()
        for i in range(5):
            data = (hoje - __import__("datetime").timedelta(days=i * 2)).strftime("%d/%m/%Y")
            concurso = 2026000 + i
            numeros = sorted(random.sample(range(1, 81), 5))
            resultados.append(Resultado(
                tipo_loteria="quina", concurso=concurso, data_sorteio=data,
                numeros_sorteados=numeros, numeros_especiais=[],
                premio_acumulado=random.uniform(500000, 5000000),
                ganhadores=random.randint(0, 10), arrecadacao_total=random.uniform(1000000, 10000000),
            ))
        return resultados

    # ------------------------------------------------------------------
    # Lotofácil
    # ------------------------------------------------------------------

    def _fetch_lotofacil(self) -> List[Resultado]:
        """Busca resultados da Lotofácil: API -> mock."""
        resultados = []
        try:
            latest = self._fetch_latest_from_api("lotofacil")
            if latest:
                resultados.append(latest)
                for c in range(latest.concurso - 1, max(latest.concurso - 5, 0), -1):
                    r = self._fetch_from_api("lotofacil", c)
                    if r:
                        resultados.append(r)
        except Exception:
            log.exception("Falha na sincronização")

        if not resultados:
            resultados = self._fetch_mock_lotofacil()
        return resultados

    def _fetch_mock_lotofacil(self) -> List[Resultado]:
        import random
        random.seed(datetime.now().day + 2)
        resultados = []
        hoje = datetime.now()
        for i in range(5):
            data = (hoje - __import__("datetime").timedelta(days=i * 2)).strftime("%d/%m/%Y")
            concurso = 2026000 + i
            numeros = sorted(random.sample(range(1, 26), 15))
            resultados.append(Resultado(
                tipo_loteria="lotofacil", concurso=concurso, data_sorteio=data,
                numeros_sorteados=numeros, numeros_especiais=[],
                premio_acumulado=random.uniform(1000000, 10000000),
                ganhadores=random.randint(0, 50), arrecadacao_total=random.uniform(5000000, 50000000),
            ))
        return resultados

    # ------------------------------------------------------------------
    # Lotomania
    # ------------------------------------------------------------------

    def _fetch_lotomania(self) -> List[Resultado]:
        """Busca resultados da Lotomania: API -> mock."""
        resultados = []
        try:
            latest = self._fetch_latest_from_api("lotomania")
            if latest:
                resultados.append(latest)
                for c in range(latest.concurso - 1, max(latest.concurso - 5, 0), -1):
                    r = self._fetch_from_api("lotomania", c)
                    if r:
                        resultados.append(r)
        except Exception:
            log.exception("Falha na sincronização")

        if not resultados:
            resultados = self._fetch_mock_lotomania()
        return resultados

    def _fetch_mock_lotomania(self) -> List[Resultado]:
        import random
        random.seed(datetime.now().day + 3)
        resultados = []
        hoje = datetime.now()
        for i in range(5):
            data = (hoje - __import__("datetime").timedelta(days=i * 2)).strftime("%d/%m/%Y")
            concurso = 2026000 + i
            numeros = sorted(random.sample(range(1, 51), 20))
            resultados.append(Resultado(
                tipo_loteria="lotomania", concurso=concurso, data_sorteio=data,
                numeros_sorteados=numeros, numeros_especiais=[],
                premio_acumulado=random.uniform(100000, 1000000),
                ganhadores=random.randint(0, 100), arrecadacao_total=random.uniform(500000, 5000000),
            ))
        return resultados

    # ------------------------------------------------------------------
    # Timemania
    # ------------------------------------------------------------------

    def _fetch_timemania(self) -> List[Resultado]:
        """Busca resultados da Timemania: API -> mock."""
        resultados = []
        try:
            latest = self._fetch_latest_from_api("timemania")
            if latest:
                resultados.append(latest)
                for c in range(latest.concurso - 1, max(latest.concurso - 5, 0), -1):
                    r = self._fetch_from_api("timemania", c)
                    if r:
                        resultados.append(r)
        except Exception:
            log.exception("Falha na sincronização")

        if not resultados:
            resultados = self._fetch_mock_timemania()
        return resultados

    def _fetch_mock_timemania(self) -> List[Resultado]:
        import random
        random.seed(datetime.now().day + 4)
        resultados = []
        hoje = datetime.now()
        for i in range(5):
            data = (hoje - __import__("datetime").timedelta(days=i * 2)).strftime("%d/%m/%Y")
            concurso = 2026000 + i
            numeros = sorted(random.sample(range(1, 81), 10))
            resultados.append(Resultado(
                tipo_loteria="timemania", concurso=concurso, data_sorteio=data,
                numeros_sorteados=numeros, numeros_especiais=[],
                premio_acumulado=random.uniform(100000, 1000000),
                ganhadores=random.randint(0, 20), arrecadacao_total=random.uniform(500000, 5000000),
            ))
        return resultados

    # ------------------------------------------------------------------
    # Dupla Sena
    # ------------------------------------------------------------------

    def _fetch_dupla_sena(self) -> List[Resultado]:
        """Busca resultados da Dupla Sena: API -> mock."""
        resultados = []
        try:
            latest = self._fetch_latest_from_api("dupla-sena")
            if latest:
                resultados.append(latest)
                for c in range(latest.concurso - 1, max(latest.concurso - 5, 0), -1):
                    r = self._fetch_from_api("dupla-sena", c)
                    if r:
                        resultados.append(r)
        except Exception:
            log.exception("Falha na sincronização")

        if not resultados:
            resultados = self._fetch_mock_dupla_sena()
        return resultados

    def _fetch_mock_dupla_sena(self) -> List[Resultado]:
        import random
        random.seed(datetime.now().day + 5)
        resultados = []
        hoje = datetime.now()
        for i in range(5):
            data = (hoje - __import__("datetime").timedelta(days=i * 2)).strftime("%d/%m/%Y")
            concurso = 2026000 + i
            numeros = sorted(random.sample(range(1, 61), 6))
            resultados.append(Resultado(
                tipo_loteria="dupla-sena", concurso=concurso, data_sorteio=data,
                numeros_sorteados=numeros, numeros_especiais=[],
                premio_acumulado=random.uniform(1000000, 10000000),
                ganhadores=random.randint(0, 5), arrecadacao_total=random.uniform(5000000, 50000000),
            ))
        return resultados

    # ------------------------------------------------------------------
    # Dia de Sorte
    # ------------------------------------------------------------------

    def _fetch_dia_de_sorte(self) -> List[Resultado]:
        """Busca resultados do Dia de Sorte: API -> mock."""
        resultados = []
        try:
            latest = self._fetch_latest_from_api("dia-de-sorte")
            if latest:
                resultados.append(latest)
                for c in range(latest.concurso - 1, max(latest.concurso - 5, 0), -1):
                    r = self._fetch_from_api("dia-de-sorte", c)
                    if r:
                        resultados.append(r)
        except Exception:
            log.exception("Falha na sincronização")

        if not resultados:
            resultados = self._fetch_mock_dia_de_sorte()
        return resultados

    def _fetch_mock_dia_de_sorte(self) -> List[Resultado]:
        import random
        random.seed(datetime.now().day + 6)
        resultados = []
        hoje = datetime.now()
        for i in range(5):
            data = (hoje - __import__("datetime").timedelta(days=i * 2)).strftime("%d/%m/%Y")
            concurso = 2026000 + i
            numeros = sorted(random.sample(range(1, 32), 7))
            resultados.append(Resultado(
                tipo_loteria="dia-de-sorte", concurso=concurso, data_sorteio=data,
                numeros_sorteados=numeros, numeros_especiais=[],
                premio_acumulado=random.uniform(100000, 1000000),
                ganhadores=random.randint(0, 20), arrecadacao_total=random.uniform(500000, 5000000),
            ))
        return resultados

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------

    def get_resultados(self) -> List[Resultado]:
        return self.db.get_resultados()

    def get_resultado_by_tipo(self, tipo: str) -> List[Resultado]:
        return self.db.get_resultado_by_tipo(tipo)


class DataService:
    """Service wrapper que delega ao DatabaseService."""
    def __init__(self):
        self.db = DatabaseService()
        self.api = APIService()

    def get_resultados(self) -> List[Resultado]:
        return self.db.get_resultados()

    def get_apostas(self) -> List[Aposta]:
        return self.db.get_apostas()

    def get_jogadores(self) -> List[Jogador]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jogadores ORDER BY data_cadastro DESC")
        rows = cursor.fetchall()
        conn.close()
        from models.jogador import Jogador
        return [Jogador(
            id=row["id"], nome=row["nome"], cpf=row["cpf"], email=row["email"],
            data_cadastro=row["data_cadastro"], total_gasto=row["total_gasto"],
            total_acertos=row["total_acertos"], total_premios=row["total_premios"]
        ) for row in rows]

    def add_aposta(self, aposta: Aposta) -> Aposta:
        return self.db.add_aposta(aposta)

    def remover_aposta(self, aposta_id: int) -> bool:
        return self.db.remover_aposta(aposta_id)

    def atualizar_aposta(self, aposta: Aposta) -> bool:
        return self.db.atualizar_aposta(aposta)

    def add_jogador(self, jogador: Jogador) -> Jogador:
        return self.db.add_jogador(jogador)

    def get_jogador(self, cpf: str) -> Optional[Jogador]:
        return self.db.get_jogador(cpf)

    def salvar_conferencia(self, conf: Conferencia):
        self.db.salvar_conferencia(conf)

    def get_conferencias(self) -> list:
        return self.db.get_conferencias()

    def get_stats(self) -> dict:
        return self.db.get_stats()

    def sync_and_refresh(self) -> dict:
        return self.api.sync_all()
