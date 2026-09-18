from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class Jogador:
    id: int = 0
    nome: str = ""
    cpf: str = ""
    email: str = ""
    data_cadastro: str = ""
    apostas: List[int] = field(default_factory=list)
    total_gasto: float = 0.0
    total_acertos: int = 0
    total_premios: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "email": self.email,
            "data_cadastro": self.data_cadastro,
            "apostas": self.apostas,
            "total_gasto": self.total_gasto,
            "total_acertos": self.total_acertos,
            "total_premios": self.total_premios,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Jogador":
        return cls(
            id=data.get("id", 0),
            nome=data.get("nome", ""),
            cpf=data.get("cpf", ""),
            email=data.get("email", ""),
            data_cadastro=data.get("data_cadastro", ""),
            apostas=data.get("apostas", []),
            total_gasto=data.get("total_gasto", 0.0),
            total_acertos=data.get("total_acertos", 0),
            total_premios=data.get("total_premios", 0.0),
        )