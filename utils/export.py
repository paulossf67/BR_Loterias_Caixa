import csv
import os
from datetime import datetime
from typing import List


def _formatar_valor(valor: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _ensure_dir(filepath: str):
    """Garante que o diretório do arquivo existe."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)


def _open_csv(filepath: str):
    """Abre arquivo CSV com BOM UTF-8 para compatibilidade com Excel."""
    return open(filepath, "w", newline="", encoding="utf-8-sig")


def exportar_apostas_csv(apostas: list, filepath: str) -> str:
    """Exporta apostas para CSV.

    Args:
        apostas: Lista de objetos Aposta (ou dicts).
        filepath: Caminho do arquivo CSV de saída.

    Returns:
        Caminho do arquivo criado.
    """
    _ensure_dir(filepath)

    headers = [
        "ID", "Tipo Loteria", "Data Aposta", "Números",
        "Valor", "Data Sorteio", "Acertos", "Prêmio",
        "Conferência Feita"
    ]

    with _open_csv(filepath) as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)

        for a in apostas:
            numeros_str = " | ".join(str(n) for n in a.numeros) if hasattr(a, "numeros") else ""
            writer.writerow([
                a.id if hasattr(a, "id") else a.get("id", ""),
                a.tipo_loteria if hasattr(a, "tipo_loteria") else a.get("tipo_loteria", ""),
                a.data_aposta if hasattr(a, "data_aposta") else a.get("data_aposta", ""),
                numeros_str,
                _formatar_valor(a.valor if hasattr(a, "valor") else a.get("valor", 0)),
                a.data_sorteio if hasattr(a, "data_sorteio") else a.get("data_sorteio", ""),
                a.acertos if hasattr(a, "acertos") else a.get("acertos", 0),
                _formatar_valor(a.premio if hasattr(a, "premio") else a.get("premio", 0)),
                "Sim" if (a.conferencia_feita if hasattr(a, "conferencia_feita") else a.get("conferencia_feita", False)) else "Não",
            ])

    return filepath


def exportar_resultados_csv(resultados: list, filepath: str) -> str:
    """Exporta resultados para CSV.

    Args:
        resultados: Lista de objetos Resultado (ou dicts).
        filepath: Caminho do arquivo CSV de saída.

    Returns:
        Caminho do arquivo criado.
    """
    _ensure_dir(filepath)

    headers = [
        "ID", "Tipo Loteria", "Concurso", "Data Sorteio",
        "Data Apuração", "Números Sorteados", "Números Especiais",
        "Prêmio Acumulado", "Ganhadores", "Arrecadação Total"
    ]

    with _open_csv(filepath) as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)

        for r in resultados:
            nums_sorteados = " | ".join(
                str(n) for n in (r.numeros_sorteados if hasattr(r, "numeros_sorteados") else r.get("numeros_sorteados", []))
            )
            nums_especiais = " | ".join(
                str(n) for n in (r.numeros_especiais if hasattr(r, "numeros_especiais") else r.get("numeros_especiais", []))
            )
            writer.writerow([
                r.id if hasattr(r, "id") else r.get("id", ""),
                r.tipo_loteria if hasattr(r, "tipo_loteria") else r.get("tipo_loteria", ""),
                r.concurso if hasattr(r, "concurso") else r.get("concurso", ""),
                r.data_sorteio if hasattr(r, "data_sorteio") else r.get("data_sorteio", ""),
                r.data_apuração if hasattr(r, "data_apuração") else r.get("data_apuração", r.get("data_apuracao", "")),
                nums_sorteados,
                nums_especiais,
                _formatar_valor(r.premio_acumulado if hasattr(r, "premio_acumulado") else r.get("premio_acumulado", 0)),
                r.ganhadores if hasattr(r, "ganhadores") else r.get("ganhadores", 0),
                _formatar_valor(r.arrecadacao_total if hasattr(r, "arrecadacao_total") else r.get("arrecadacao_total", 0)),
            ])

    return filepath


def exportar_conferencias_csv(conferencias: list, filepath: str) -> str:
    """Exporta conferências para CSV.

    Args:
        conferencias: Lista de objetos Conferencia (ou dicts).
        filepath: Caminho do arquivo CSV de saída.

    Returns:
        Caminho do arquivo criado.
    """
    _ensure_dir(filepath)

    headers = [
        "ID", "ID Aposta", "Tipo Loteria", "Concurso",
        "Data Conferida", "Números Apostados", "Números Sorteados",
        "Qtd Acertos", "Prêmio Ganho", "Status"
    ]

    with _open_csv(filepath) as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(headers)

        for c in conferencias:
            nums_apostados = " | ".join(
                str(n) for n in (c.numeros_apostados if hasattr(c, "numeros_apostados") else c.get("numeros_apostados", []))
            )
            nums_sorteados = " | ".join(
                str(n) for n in (c.numeros_sorteados if hasattr(c, "numeros_sorteados") else c.get("numeros_sorteados", []))
            )
            writer.writerow([
                c.id if hasattr(c, "id") else c.get("id", ""),
                c.id_aposta if hasattr(c, "id_aposta") else c.get("id_aposta", ""),
                c.tipo_loteria if hasattr(c, "tipo_loteria") else c.get("tipo_loteria", ""),
                c.concurso if hasattr(c, "concurso") else c.get("concurso", ""),
                c.data_conferida if hasattr(c, "data_conferida") else c.get("data_conferida", ""),
                nums_apostados,
                nums_sorteados,
                c.qtd_acertos if hasattr(c, "qtd_acertos") else c.get("qtd_acertos", 0),
                _formatar_valor(c.premio_ganho if hasattr(c, "premio_ganho") else c.get("premio_ganho", 0)),
                c.status if hasattr(c, "status") else c.get("status", ""),
            ])

    return filepath


def exportar_tudo_csv(apostas: list, resultados: list, conferencias: list, diretorio: str) -> dict:
    """Exporta todos os dados para arquivos CSV separados em um diretório.

    Args:
        apostas: Lista de apostas.
        resultados: Lista de resultados.
        conferencias: Lista de conferências.
        diretorio: Diretório de saída para os arquivos.

    Returns:
        Dict com os caminhos dos arquivos criados.
    """
    os.makedirs(diretorio, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    arquivos = {
        "apostas": os.path.join(diretorio, f"apostas_{timestamp}.csv"),
        "resultados": os.path.join(diretorio, f"resultados_{timestamp}.csv"),
        "conferencias": os.path.join(diretorio, f"conferencias_{timestamp}.csv"),
    }

    exportar_apostas_csv(apostas, arquivos["apostas"])
    exportar_resultados_csv(resultados, arquivos["resultados"])
    exportar_conferencias_csv(conferencias, arquivos["conferencias"])

    return arquivos
