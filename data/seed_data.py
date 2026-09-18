"""Script para popular o banco de dados local com dados de exemplo."""
import json
import os
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

LOTERIAS_NOME = {
    "mega-sena": "Mega-Sena",
    "quina": "Quina",
    "lotofacil": "Lotofácil",
    "lotomania": "Lotomania",
    "timemania": "Timemania",
    "dupla-sena": "Dupla Sena",
    "dia-de-sorte": "Dia de Sorte",
}


def gerar_dados_exemplo():
    hoje = datetime.now()
    resultados = []
    apostas = []

    loterias_config = {
        "mega-sena": {"numeros": 6, "maximo": 60},
        "quina": {"numeros": 5, "maximo": 80},
        "lotofacil": {"numeros": 15, "maximo": 25},
        "lotomania": {"numeros": 20, "maximo": 50},
        "timemania": {"numeros": 10, "maximo": 80},
        "dupla-sena": {"numeros": 6, "maximo": 60},
        "dia-de-sorte": {"numeros": 7, "maximo": 31},
    }

    random.seed(42)

    for i, (tipo, config) in enumerate(loterias_config.items()):
        for concurso in range(i * 3 + 1, i * 3 + 8):
            data = (hoje - timedelta(days=(i * 7) + (7 - concurso) * 2)).strftime("%d/%m/%Y")
            numeros = sorted(random.sample(range(1, config["maximo"] + 1), config["numeros"]))

            resultado = {
                "id": len(resultados) + 1,
                "tipo_loteria": tipo,
                "concurso": concurso * 1000 + i,
                "data_sorteio": data,
                "data_apuração": data,
                "numeros_sorteados": numeros,
                "numeros_especiais": [],
                "premio_acumulado": random.uniform(1000000, 50000000),
                "ganhadores": random.randint(0, 5),
                "arrecadacao_total": random.uniform(5000000, 100000000),
            }
            resultados.append(resultado)

    for i in range(5):
        tipo = random.choice(list(loterias_config.keys()))
        config = loterias_config[tipo]
        numeros = sorted(random.sample(range(1, config["maximo"] + 1), config["numeros"]))
        data = (hoje - timedelta(days=random.randint(1, 30))).strftime("%d/%m/%Y")
        valor = round(random.uniform(2.5, 50.0), 2)
        acertos = random.randint(0, config["numeros"])

        aposta = {
            "id": i + 1,
            "tipo_loteria": tipo,
            "data_aposta": data,
            "numeros": numeros,
            "valor": valor,
            "data_sorteio": data,
            "acertos": acertos,
            "premio": round(valor * {6: 1000, 5: 50, 4: 10, 3: 5, 2: 2, 1: 1}.get(acertos, 0), 2) if acertos > 0 else 0.0,
            "conferência_feita": True,
        }
        apostas.append(aposta)

    with open(os.path.join(DATA_DIR, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    with open(os.path.join(DATA_DIR, "apostas.json"), "w", encoding="utf-8") as f:
        json.dump(apostas, f, ensure_ascii=False, indent=2)

    print(f"[OK] Dados criados: {len(resultados)} resultados, {len(apostas)} apostas")
    return resultados, apostas


if __name__ == "__main__":
    gerar_dados_exemplo()