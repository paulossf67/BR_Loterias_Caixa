import random
from typing import List
from datetime import datetime
from math import comb


def gerar_numeros_aleatorios(qtd: int, maximo: int = 60) -> List[int]:
    """Gera uma lista de números aleatórios únicos para apostas."""
    if qtd > maximo:
        raise ValueError(f"Não é possível gerar {qtd} números únicos de 1 a {maximo}")
    return sorted(random.sample(range(1, maximo + 1), qtd))


def validar_numeros(numeros: List[int], qtd_esperada: int, maximo: int = 60) -> bool:
    """Valida se a lista de números é válida."""
    if len(numeros) != qtd_esperada:
        return False
    if any(n < 1 or n > maximo for n in numeros):
        return False
    if len(set(numeros)) != len(numeros):
        return False
    return True


def formatar_numeros(numeros: List[int], separador: str = " | ") -> str:
    """Formata lista de números como string."""
    return separador.join(str(n) for n in sorted(numeros))


def formatar_valor(valor: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {valor:,.2f}"


def calcular_probabilidade(qtd_numeros: int, total_numeros: int, faixa: int) -> float:
    """Calcula a probabilidade de acerto baseado nos parâmetros da loteria."""
    try:
        prob = comb(qtd_numeros, faixa) / comb(total_numeros, faixa)
        return prob * 100
    except Exception:
        return 0.0


def formatar_data_hora() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")