from dataclasses import dataclass
from typing import List


@dataclass
class Conferência:
    id: int = 0
    id_aposta: int = 0
    tipo_loteria: str = ""
    concurso: int = 0
    data_conferida: str = ""
    numeros_apostados: List[int] = None
    numeros_sorteados: List[int] = None
    qtd_acertos: int = 0
    premio_ganho: float = 0.0
    status: str = "pendente"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "id_aposta": self.id_aposta,
            "tipo_loteria": self.tipo_loteria,
            "concurso": self.concurso,
            "data_conferida": self.data_conferida,
            "numeros_apostados": self.numeros_apostados or [],
            "numeros_sorteados": self.numeros_sorteados or [],
            "qtd_acertos": self.qtd_acertos,
            "premio_ganho": self.premio_ganho,
            "status": self.status,
        }