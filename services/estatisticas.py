"""Cálculos estatísticos puros (sem interface) usados pelos gráficos."""
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Tuple

from services.regras import REGRAS, _parse_data


def frequencia_numeros(resultados: Iterable, tipo: str) -> Dict[int, int]:
    """Quantas vezes cada número foi sorteado; inclui números nunca sorteados com 0."""
    cont = Counter()
    for r in resultados:
        if r.tipo_loteria == tipo:
            cont.update(r.numeros_sorteados)
    regra = REGRAS.get(tipo)
    if regra:
        for n in range(regra.get("minimo", 1), regra["maximo"] + 1):
            cont.setdefault(n, 0)
    return dict(sorted(cont.items()))


def atraso_numeros(resultados: Iterable, tipo: str) -> Dict[int, int]:
    """Concursos passados desde a última vez que cada número saiu."""
    rs = sorted((r for r in resultados if r.tipo_loteria == tipo),
                key=lambda r: r.concurso, reverse=True)
    atraso = {n: len(rs) for n in frequencia_numeros(rs, tipo)}
    vistos = set()
    for i, r in enumerate(rs):
        for n in r.numeros_sorteados:
            if n not in vistos:
                vistos.add(n)
                atraso[n] = i
    return atraso


def distribuicao_acertos(apostas: Iterable) -> Dict[int, int]:
    """Nº de apostas conferidas por quantidade de acertos."""
    cont = Counter(a.acertos for a in apostas if a.conferencia_feita)
    return dict(sorted(cont.items()))


def financeiro_por_mes(apostas: Iterable) -> List[Tuple[str, float, float]]:
    """(mês 'MM/AAAA', total investido, total de prêmios), em ordem cronológica."""
    inv, pre = defaultdict(float), defaultdict(float)
    for a in apostas:
        d = _parse_data(a.data_aposta)
        if not d:
            continue
        chave = d.strftime("%Y-%m")
        inv[chave] += a.valor
        pre[chave] += a.premio
    return [(f"{k[5:]}/{k[:4]}", inv[k], pre[k]) for k in sorted(inv)]
