"""Regras de negócio das loterias: validação, faixas de premiação e conferência."""
import re
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

# Configuração por loteria: quantidade de números da aposta simples,
# maior número e quantidades de acertos que premiam.
REGRAS = {
    "mega-sena": {"min": 6, "max_qtd": 20, "maximo": 60, "premiam": (4, 5, 6)},
    "quina": {"min": 5, "max_qtd": 15, "maximo": 80, "premiam": (2, 3, 4, 5)},
    "lotofacil": {"min": 15, "max_qtd": 20, "maximo": 25, "premiam": (11, 12, 13, 14, 15)},
    "lotomania": {"min": 50, "max_qtd": 50, "minimo": 0, "maximo": 99, "premiam": (0, 16, 17, 18, 19, 20)},
    "timemania": {"min": 10, "max_qtd": 10, "maximo": 80, "premiam": (3, 4, 5, 6, 7)},
    "dupla-sena": {"min": 6, "max_qtd": 15, "maximo": 50, "premiam": (3, 4, 5, 6)},
    "dia-de-sorte": {"min": 7, "max_qtd": 15, "maximo": 31, "premiam": (4, 5, 6, 7)},
}


def contar_acertos(numeros: Iterable[int], sorteados: Iterable[int]) -> int:
    return len(set(numeros) & set(sorteados))


def acerto_premia(tipo: str, acertos: int) -> bool:
    regra = REGRAS.get(tipo)
    return bool(regra) and acertos in regra["premiam"]


def calcular_premio(resultado, acertos: int) -> float:
    """Prêmio real por ganhador, conforme o rateio do concurso.

    Retorna 0.0 quando a faixa não premia ou o rateio não é conhecido.
    """
    if not acerto_premia(resultado.tipo_loteria, acertos):
        return 0.0
    return float((getattr(resultado, "premiacao", None) or {}).get(acertos, 0.0))


def premio_da_aposta(resultado, aposta, acertos: int) -> float:
    """Prêmio da aposta; em bolão, a parte que cabe a esta cota."""
    return calcular_premio(resultado, acertos) / max(getattr(aposta, "cotas", 1) or 1, 1)


def _parse_data(texto: str) -> Optional[datetime]:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime((texto or "").strip()[:10], fmt)
        except ValueError:
            continue
    return None


def aposta_vale_para(aposta, resultado) -> bool:
    """A aposta deve ser da mesma loteria e do concurso (ou data) do resultado."""
    if aposta.tipo_loteria != resultado.tipo_loteria:
        return False
    ref = (aposta.data_sorteio or "").strip()
    if ref.isdigit():
        return int(ref) == resultado.concurso
    d_aposta, d_res = _parse_data(ref), _parse_data(resultado.data_sorteio)
    if d_aposta and d_res:
        return d_aposta <= d_res
    return True


def validar_aposta(tipo: str, numeros: List[int], valor: float) -> Tuple[bool, str]:
    regra = REGRAS.get(tipo)
    if not regra:
        return False, f"Loteria desconhecida: {tipo}"
    if len(set(numeros)) != len(numeros):
        return False, "Há números repetidos."
    if not regra["min"] <= len(numeros) <= regra["max_qtd"]:
        return False, f"Escolha de {regra['min']} a {regra['max_qtd']} números."
    menor = regra.get("minimo", 1)
    if any(n < menor or n > regra["maximo"] for n in numeros):
        return False, f"Os números devem estar entre {menor} e {regra['maximo']}."
    if valor <= 0:
        return False, "O valor da aposta deve ser maior que zero."
    return True, ""


def validar_cpf(cpf: str) -> bool:
    d = re.sub(r"\D", "", cpf or "")
    if len(d) != 11 or d == d[0] * 11:
        return False
    for i in (9, 10):
        soma = sum(int(d[j]) * (i + 1 - j) for j in range(i))
        if (soma * 10 % 11) % 10 != int(d[i]):
            return False
    return True


def validar_email(email: str) -> bool:
    return not email or re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def mascarar_cpf(cpf: str) -> str:
    d = re.sub(r"\D", "", cpf or "")
    return f"***.{d[3:6]}.{d[6:9]}-**" if len(d) == 11 else cpf


def resultado_da_aposta(aposta, resultados: Iterable):
    """Resultado que vale para a aposta: o concurso indicado ou o primeiro sorteio após a data."""
    candidatos = [r for r in resultados if aposta_vale_para(aposta, r)]
    if not candidatos:
        return None
    if (aposta.data_sorteio or "").strip().isdigit():
        return candidatos[0]
    return min(candidatos, key=lambda r: _parse_data(r.data_sorteio) or datetime.max)
