"""Importação de apostas a partir de CSV (colunas: tipo_loteria, numeros, valor, data_sorteio)."""
import csv
import re
from typing import List, Tuple


def ler_apostas_csv(caminho: str) -> Tuple[List[dict], List[str]]:
    """Lê o CSV e devolve (linhas válidas de estrutura, erros). Não valida regras de loteria."""
    apostas, erros = [], []
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        amostra = f.read(2048)
        f.seek(0)
        delim = ";" if amostra.count(";") > amostra.count(",") else ","
        for i, row in enumerate(csv.DictReader(f, delimiter=delim), start=2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            try:
                numeros = [int(n) for n in re.split(r"[\s,;|-]+", row["numeros"]) if n]
                valor = float(row["valor"].replace("R$", "").replace(",", ".").strip())
                apostas.append({"tipo_loteria": row["tipo_loteria"], "numeros": numeros,
                                "valor": valor, "data_sorteio": row.get("data_sorteio", "")})
            except (KeyError, ValueError) as e:
                erros.append(f"Linha {i}: dado ausente ou inválido ({e})")
    return apostas, erros
