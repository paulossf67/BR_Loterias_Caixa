import sqlite3
import json
import os
from utils.paths import BASE_DIR
from datetime import datetime
from typing import List, Optional

from models.resultado import Resultado
from models.aposta import Aposta
from models.jogador import Jogador
from models.conferencia import Conferencia

DB_PATH = os.path.join(BASE_DIR, "data", "loterias.db")


class DatabaseService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._criar_tabelas()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _criar_tabelas(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resultados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_loteria TEXT NOT NULL,
                concurso INTEGER NOT NULL,
                data_sorteio TEXT NOT NULL,
                data_apuracao TEXT,
                numeros_sorteados TEXT NOT NULL,
                numeros_especiais TEXT DEFAULT '[]',
                premio_acumulado REAL DEFAULT 0.0,
                ganhadores INTEGER DEFAULT 0,
                arrecadacao_total REAL DEFAULT 0.0,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS apostas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_loteria TEXT NOT NULL,
                data_aposta TEXT NOT NULL,
                numeros TEXT NOT NULL,
                valor REAL NOT NULL,
                data_sorteio TEXT NOT NULL,
                acertos INTEGER DEFAULT 0,
                premio REAL DEFAULT 0.0,
                conferencia_feita INTEGER DEFAULT 0,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jogadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf TEXT UNIQUE,
                email TEXT,
                data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP,
                total_gasto REAL DEFAULT 0.0,
                total_acertos INTEGER DEFAULT 0,
                total_premios REAL DEFAULT 0.0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conferencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_aposta INTEGER,
                tipo_loteria TEXT,
                concurso INTEGER,
                data_conferida TEXT,
                numeros_apostados TEXT,
                numeros_sorteados TEXT,
                qtd_acertos INTEGER DEFAULT 0,
                premio_ganho REAL DEFAULT 0.0,
                status TEXT DEFAULT 'pendente',
                FOREIGN KEY (id_aposta) REFERENCES apostas(id)
            )
        """)

        # Migração: coluna de premiação por faixa
        colunas = {r["name"] for r in cursor.execute("PRAGMA table_info(resultados)")}
        if "premiacao" not in colunas:
            cursor.execute("ALTER TABLE resultados ADD COLUMN premiacao TEXT DEFAULT '{}'")

        colunas = {r["name"] for r in cursor.execute("PRAGMA table_info(apostas)")}
        if "cotas" not in colunas:
            cursor.execute("ALTER TABLE apostas ADD COLUMN cotas INTEGER DEFAULT 1")
        if "id_jogador" not in colunas:
            cursor.execute("ALTER TABLE apostas ADD COLUMN id_jogador INTEGER DEFAULT 0")

        conn.commit()
        conn.close()

    # === RESULTADOS ===
    def salvar_resultados(self, resultados: List[Resultado]):
        conn = self.get_connection()
        cursor = conn.cursor()
        for r in resultados:
            cursor.execute("""
                INSERT OR REPLACE INTO resultados 
                (id, tipo_loteria, concurso, data_sorteio, data_apuracao, 
                 numeros_sorteados, numeros_especiais, premio_acumulado, 
                 ganhadores, arrecadacao_total, premiacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.id, r.tipo_loteria, r.concurso, r.data_sorteio, r.data_apuração,
                json.dumps(r.numeros_sorteados), json.dumps(r.numeros_especiais),
                r.premio_acumulado, r.ganhadores, r.arrecadacao_total,
                json.dumps({str(k): v for k, v in r.premiacao.items()})
            ))
        conn.commit()
        conn.close()

    def get_resultados(self) -> List[Resultado]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resultados ORDER BY data_sorteio DESC")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_resultado(row) for row in rows]

    def get_resultado_by_tipo(self, tipo: str) -> List[Resultado]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resultados WHERE tipo_loteria = ? ORDER BY data_sorteio DESC", (tipo,))
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_resultado(row) for row in rows]

    def _row_to_resultado(self, row) -> Resultado:
        return Resultado(
            id=row["id"],
            tipo_loteria=row["tipo_loteria"],
            concurso=row["concurso"],
            data_sorteio=row["data_sorteio"],
            data_apuração=row["data_apuracao"],
            numeros_sorteados=json.loads(row["numeros_sorteados"]),
            numeros_especiais=json.loads(row["numeros_especiais"]),
            premio_acumulado=row["premio_acumulado"],
            ganhadores=row["ganhadores"],
            arrecadacao_total=row["arrecadacao_total"],
            premiacao={int(k): float(v) for k, v in json.loads(row["premiacao"] or "{}").items()},
        )

    # === APOSTAS ===
    def add_aposta(self, aposta: Aposta) -> Aposta:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO apostas (tipo_loteria, data_aposta, numeros, valor, 
                                 data_sorteio, acertos, premio, conferencia_feita, id_jogador, cotas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            aposta.tipo_loteria, aposta.data_aposta, json.dumps(aposta.numeros),
            aposta.valor, aposta.data_sorteio, aposta.acertos, aposta.premio,
            int(aposta.conferencia_feita), aposta.id_jogador, aposta.cotas
        ))
        aposta.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return aposta

    def get_apostas(self) -> List[Aposta]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apostas ORDER BY data_aposta DESC")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_aposta(row) for row in rows]

    def remover_aposta(self, aposta_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conferencias WHERE id_aposta = ?", (aposta_id,))
        cursor.execute("DELETE FROM apostas WHERE id = ?", (aposta_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def atualizar_aposta(self, aposta: Aposta) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE apostas SET 
                acertos = ?, premio = ?, conferencia_feita = ?
            WHERE id = ?
        """, (aposta.acertos, aposta.premio, int(aposta.conferencia_feita), aposta.id))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def _row_to_aposta(self, row) -> Aposta:
        return Aposta(
            id=row["id"],
            id_jogador=row["id_jogador"] or 0,
            cotas=row["cotas"] or 1,
            tipo_loteria=row["tipo_loteria"],
            data_aposta=row["data_aposta"],
            numeros=json.loads(row["numeros"]),
            valor=row["valor"],
            data_sorteio=row["data_sorteio"],
            acertos=row["acertos"],
            premio=row["premio"],
            conferencia_feita=bool(row["conferencia_feita"]),
        )

    # === JOGADORES ===
    def add_jogador(self, jogador: Jogador) -> Jogador:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO jogadores (nome, cpf, email) VALUES (?, ?, ?)
            """, (jogador.nome, jogador.cpf, jogador.email))
            jogador.id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM jogadores WHERE cpf = ?", (jogador.cpf,))
            row = cursor.fetchone()
            if row:
                jogador.id = row["id"]
            conn.commit()
        conn.close()
        return jogador

    def get_jogador(self, cpf: str) -> Optional[Jogador]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jogadores WHERE cpf = ?", (cpf,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Jogador(
                id=row["id"], nome=row["nome"], cpf=row["cpf"],
                email=row["email"], data_cadastro=row["data_cadastro"],
                total_gasto=row["total_gasto"], total_acertos=row["total_acertos"],
                total_premios=row["total_premios"]
            )
        return None

    def get_jogadores(self) -> List[Jogador]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jogadores ORDER BY data_cadastro DESC")
        rows = cursor.fetchall()
        conn.close()
        return [Jogador(
            id=row["id"], nome=row["nome"], cpf=row["cpf"],
            email=row["email"], data_cadastro=row["data_cadastro"],
            total_gasto=row["total_gasto"], total_acertos=row["total_acertos"],
            total_premios=row["total_premios"]
        ) for row in rows]

    # === CONFERÊNCIAS ===
    def salvar_conferencia(self, conf: Conferencia):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conferencias 
            (id_aposta, tipo_loteria, concurso, data_conferida, 
             numeros_apostados, numeros_sorteados, qtd_acertos, premio_ganho, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conf.id_aposta, conf.tipo_loteria, conf.concurso, conf.data_conferida,
            json.dumps(conf.numeros_apostados or []), json.dumps(conf.numeros_sorteados or []),
            conf.qtd_acertos, conf.premio_ganho, conf.status
        ))
        conn.commit()
        conn.close()

    def get_conferencias(self) -> List[Conferencia]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conferencias ORDER BY data_conferida DESC")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_conferencia(row) for row in rows]

    def _row_to_conferencia(self, row) -> Conferencia:
        return Conferencia(
            id=row["id"],
            id_aposta=row["id_aposta"],
            tipo_loteria=row["tipo_loteria"],
            concurso=row["concurso"],
            data_conferida=row["data_conferida"],
            numeros_apostados=json.loads(row["numeros_apostados"]),
            numeros_sorteados=json.loads(row["numeros_sorteados"]),
            qtd_acertos=row["qtd_acertos"],
            premio_ganho=row["premio_ganho"],
            status=row["status"],
        )

    # === STATS ===
    def get_stats(self) -> dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM apostas")
        total_apostas = cursor.fetchone()["COUNT(*)"]
        
        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM apostas")
        total_gasto = cursor.fetchone()["COALESCE(SUM(valor), 0)"]
        
        cursor.execute("SELECT COALESCE(SUM(acertos), 0) FROM apostas")
        total_acertos = cursor.fetchone()["COALESCE(SUM(acertos), 0)"]
        
        cursor.execute("SELECT COUNT(*) FROM resultados")
        total_resultados = cursor.fetchone()["COUNT(*)"]
        
        cursor.execute("SELECT tipo_loteria, COUNT(*) as cnt FROM resultados GROUP BY tipo_loteria")
        loteria_counts = {row["tipo_loteria"]: row["cnt"] for row in cursor.fetchall()}
        
        conn.close()
        return {
            "total_apostas": total_apostas,
            "total_gasto": total_gasto,
            "total_acertos": total_acertos,
            "total_resultados": total_resultados,
            "loteria_counts": loteria_counts,
        }

    def close(self):
        pass  # Connections are opened and closed per operation