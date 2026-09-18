"""Script para popular o banco de dados local com dados de exemplo."""
import json
import os
import random
from datetime import datetime, timedelta

from models.resultado import Resultado
from models.aposta import Aposta
from models.jogador import Jogador
from models.conferencia import Conferencia

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

LOTERIAS_CONFIG = {
    "mega-sena": {"numeros": 6, "maximo": 60},
    "quina": {"numeros": 5, "maximo": 80},
    "lotofacil": {"numeros": 15, "maximo": 25},
    "lotomania": {"numeros": 20, "maximo": 50},
    "timemania": {"numeros": 10, "maximo": 80},
    "dupla-sena": {"numeros": 6, "maximo": 60},
    "dia-de-sorte": {"numeros": 7, "maximo": 31},
}


def _data_aleatoria(inicio, fim):
    delta = (fim - inicio).days
    d = inicio + timedelta(days=random.randint(0, delta))
    return d.strftime("%d/%m/%Y")


def seed_data(db):
    """Popula o banco apenas se estiver vazio."""
    stats = db.get_stats()
    if stats["total_resultados"] > 0:
        print("[OK] Banco já possui dados, seed ignorado")
        return

    random.seed(42)

    # --- Jogador ---
    jogador = Jogador(
        nome="Paulo Sérgio dos Santos Fontes",
        cpf="123.456.789-00",
        email="paulo@test.com",
        data_cadastro="01/07/2026",
    )
    db.add_jogador(jogador)

    # --- Resultados (50 apostas) ---
    resultados = []
    hoje = datetime(2026, 9, 18)
    inicio = datetime(2026, 7, 1)

    id_counter = 1
    for tipo, config in LOTERIAS_CONFIG.items():
        qtd = 7 if tipo != "quina" else 8
        for concurso in range(1, qtd + 1):
            data = _data_aleatoria(inicio, hoje)
            numeros = sorted(random.sample(range(1, config["maximo"] + 1), config["numeros"]))
            resultado = Resultado(
                id=id_counter,
                tipo_loteria=tipo,
                concurso=concurso * 1000 + list(LOTERIAS_CONFIG.keys()).index(tipo),
                data_sorteio=data,
                data_apuração=data,
                numeros_sorteados=numeros,
                numeros_especiais=[],
                premio_acumulado=round(random.uniform(1_000_000, 50_000_000), 2),
                ganhadores=random.randint(0, 5),
                arrecadacao_total=round(random.uniform(5_000_000, 100_000_000), 2),
            )
            resultados.append(resultado)
            id_counter += 1

    db.salvar_resultados(resultados)

    # --- Apostas (5 apostas, tipos diferentes, datas realistas) ---
    aposta_configs = [
        {"tipo": "lotofacil", "conferida": True},
        {"tipo": "dupla-sena", "conferida": True},
        {"tipo": "dia-de-sorte", "conferida": False},
        {"tipo": "timemania", "conferida": False},
        {"tipo": "mega-sena", "conferida": False},
    ]

    apostas_seed = []
    for i, cfg in enumerate(aposta_configs):
        tipo = cfg["tipo"]
        config = LOTERIAS_CONFIG[tipo]
        numeros = sorted(random.sample(range(1, config["maximo"] + 1), config["numeros"]))
        data = _data_aleatoria(inicio, hoje)
        valor = round(random.uniform(4.50, 50.00), 2)

        conferida = cfg["conferida"]
        if conferida:
            acertos = random.randint(max(3, config["numeros"] - 4), config["numeros"])
        else:
            acertos = 0

        premio = 0.0
        if conferida and acertos >= 3:
            premio = round(valor * {6: 1500, 5: 80, 4: 12, 3: 5}.get(acertos, 1), 2)

        aposta = Aposta(
            id=i + 1,
            tipo_loteria=tipo,
            data_aposta=data,
            numeros=numeros,
            valor=valor,
            data_sorteio=data,
            acertos=acertos,
            premio=premio,
            conferencia_feita=conferida,
        )
        apostas_seed.append(aposta)

    for aposta in apostas_seed:
        db.add_aposta(aposta)

    # --- Conferências para apostas conferidas ---
    for aposta in apostas_seed:
        if aposta.conferencia_feita:
            resultado_match = next(
                (r for r in resultados if r.tipo_loteria == aposta.tipo_loteria),
                None,
            )
            conf = Conferencia(
                id_aposta=aposta.id,
                tipo_loteria=aposta.tipo_loteria,
                concurso=resultado_match.concurso if resultado_match else 0,
                data_conferida=aposta.data_aposta,
                numeros_apostados=aposta.numeros,
                numeros_sorteados=resultado_match.numeros_sorteados if resultado_match else [],
                qtd_acertos=aposta.acertos,
                premio_ganho=aposta.premio,
                status="conferido",
            )
            db.salvar_conferencia(conf)

    print(f"[OK] Seed concluído: {len(resultados)} resultados, {len(apostas_seed)} apostas, 1 jogador")
