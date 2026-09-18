from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Resultado:
    id: int = 0
    tipo_loteria: str = ""
    concurso: int = 0
    data_sorteio: str = ""
    data_apuração: str = ""
    numeros_sorteados: List[int] = field(default_factory=list)
    numeros_especiais: List[int] = field(default_factory=list)
    premio_acumulado: float = 0.0
    ganhadores: int = 0
    arrecadacao_total: float = 0.0
    premiacao: Dict[int, float] = field(default_factory=dict)  # acertos -> prêmio por ganhador

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo_loteria": self.tipo_loteria,
            "concurso": self.concurso,
            "data_sorteio": self.data_sorteio,
            "data_apuração": self.data_apuração,
            "numeros_sorteados": self.numeros_sorteados,
            "numeros_especiais": self.numeros_especiais,
            "premio_acumulado": self.premio_acumulado,
            "ganhadores": self.ganhadores,
            "arrecadacao_total": self.arrecadacao_total,
            "premiacao": self.premiacao,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Resultado":
        return cls(
            id=data.get("id", 0),
            tipo_loteria=data.get("tipo_loteria", ""),
            concurso=data.get("concurso", 0),
            data_sorteio=data.get("data_sorteio", ""),
            data_apuração=data.get("data_apuração", ""),
            numeros_sorteados=data.get("numeros_sorteados", []),
            numeros_especiais=data.get("numeros_especiais", []),
            premio_acumulado=data.get("premio_acumulado", 0.0),
            ganhadores=data.get("ganhadores", 0),
            arrecadacao_total=data.get("arrecadacao_total", 0.0),
            premiacao={int(k): float(v) for k, v in (data.get("premiacao") or {}).items()},
        )

    @property
    def numeros_por_extenso(self) -> str:
        return " / ".join(str(n) for n in self.numeros_sorteados)