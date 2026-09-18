from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Aposta:
    id: int = 0
    tipo_loteria: str = ""
    data_aposta: str = ""
    numeros: List[int] = field(default_factory=list)
    valor: float = 0.0
    data_sorteio: str = ""
    acertos: int = 0
    premio: float = 0.0
    conferencia_feita: bool = False
    id_jogador: int = 0
    cotas: int = 1  # bolão: nº de participantes que dividem o prêmio

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo_loteria": self.tipo_loteria,
            "data_aposta": self.data_aposta,
            "numeros": self.numeros,
            "valor": self.valor,
            "data_sorteio": self.data_sorteio,
            "acertos": self.acertos,
            "premio": self.premio,
            "conferencia_feita": self.conferencia_feita,
            "id_jogador": self.id_jogador,
            "cotas": self.cotas,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Aposta":
        return cls(
            id=data.get("id", 0),
            tipo_loteria=data.get("tipo_loteria", ""),
            data_aposta=data.get("data_aposta", ""),
            numeros=data.get("numeros", []),
            valor=data.get("valor", 0.0),
            data_sorteio=data.get("data_sorteio", ""),
            acertos=data.get("acertos", 0),
            premio=data.get("premio", 0.0),
            conferencia_feita=data.get("conferencia_feita", False),
            id_jogador=data.get("id_jogador", 0),
            cotas=data.get("cotas", 1) or 1,
        )

    @property
    def quantidade_numeros(self) -> int:
        return len(self.numeros)