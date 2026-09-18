from typing import List, Optional
import threading
import shutil
from datetime import datetime

from services import regras
from utils.paths import BASE_DIR
from models.resultado import Resultado
from models.aposta import Aposta
from models.jogador import Jogador
from models.conferencia import Conferencia
from services.api_service import APIService, DataService, LOTERIAS
from services.database_service import DatabaseService
from utils.helpers import gerar_numeros_aleatorios, validar_numeros, formatar_valor
from utils.boleto import gerar_boleto_html, salvar_boleto, abrir_boleto
from utils.importacao import ler_apostas_csv
from utils.export import exportar_apostas_csv, exportar_resultados_csv, exportar_conferencias_csv, exportar_tudo_csv


class Controller:
    def __init__(self):
        self.data_service = DataService()
        self.api_service = APIService()

    def get_resultados(self) -> List[Resultado]:
        return self.data_service.get_resultados()

    def get_apostas(self) -> List[Aposta]:
        return self.data_service.get_apostas()

    def get_jogadores(self) -> List[Jogador]:
        return self.data_service.get_jogadores()

    def get_conferencias(self) -> List[Conferencia]:
        return self.data_service.get_conferencias()

    def get_stats(self) -> dict:
        return self.data_service.get_stats()

    def sync_and_refresh(self) -> dict:
        result = self.data_service.sync_and_refresh()
        result["conferidas"] = self.auto_conferir()
        return result

    def auto_conferir(self) -> dict:
        """Confere apostas com o resultado correspondente; recalcula as que já têm rateio."""
        resultados = self.get_resultados()
        novas = premiadas = 0
        for a in self.get_apostas():
            r = regras.resultado_da_aposta(a, resultados)
            if not r or (a.conferencia_feita and not r.premiacao):
                continue
            acertos = regras.contar_acertos(a.numeros, r.numeros_sorteados)
            premio = regras.premio_da_aposta(r, a, acertos)
            if a.conferencia_feita and (a.acertos, a.premio) == (acertos, premio):
                continue
            if not a.conferencia_feita:
                novas += 1
                self.salvar_conferencia(Conferencia(
                    id_aposta=a.id, tipo_loteria=a.tipo_loteria, concurso=r.concurso,
                    data_conferida=datetime.now().strftime("%d/%m/%Y"),
                    numeros_apostados=a.numeros, numeros_sorteados=r.numeros_sorteados,
                    qtd_acertos=acertos, premio_ganho=premio,
                    status="concluído" if premio > 0 else "pendente"))
            a.acertos, a.premio, a.conferencia_feita = acertos, premio, True
            self.atualizar_aposta(a)
            premiadas += premio > 0
        return {"novas": novas, "premiadas": premiadas}

    def get_resultado_by_string(self, texto: str) -> Optional[Resultado]:
        resultados = self.get_resultados()
        for r in resultados:
            if f"{LOTERIAS.get(r.tipo_loteria, r.tipo_loteria)} #{r.concurso}" in texto:
                return r
        return None

    def add_aposta(self, tipo_loteria: str, numeros: List[int], valor: float,
                   data_sorteio: str = "", id_jogador: int = 0,
                   cotas: int = 1) -> Aposta:
        if cotas < 1:
            raise ValueError("Bolão: informe ao menos 1 cota.")
        ok, erro = regras.validar_aposta(tipo_loteria, numeros, valor)
        if not ok:
            raise ValueError(erro)
        aposta = Aposta(
            tipo_loteria=tipo_loteria,
            data_aposta=datetime.now().strftime("%d/%m/%Y"),
            numeros=numeros,
            valor=valor,
            id_jogador=id_jogador,
            cotas=cotas,
            data_sorteio=data_sorteio or datetime.now().strftime("%d/%m/%Y"),
        )
        return self.data_service.add_aposta(aposta)

    def remover_aposta(self, aposta_id: int) -> bool:
        return self.data_service.remover_aposta(aposta_id)

    def atualizar_aposta(self, aposta: Aposta) -> bool:
        return self.data_service.atualizar_aposta(aposta)

    def add_jogador(self, nome: str, cpf: str, email: str = "") -> Jogador:
        if not nome.strip():
            raise ValueError("Nome é obrigatório.")
        if not regras.validar_cpf(cpf):
            raise ValueError("CPF inválido.")
        if not regras.validar_email(email):
            raise ValueError("E-mail inválido.")
        jogador = Jogador(nome=nome, cpf=cpf, email=email)
        return self.data_service.add_jogador(jogador)

    def get_jogador(self, cpf: str) -> Optional[Jogador]:
        return self.data_service.get_jogador(cpf)

    def conferir_apostas(self, resultado: Resultado) -> List[dict]:
        """Confere apenas apostas da mesma loteria/concurso do resultado."""
        conferidas = []
        for a in self.get_apostas():
            if not regras.aposta_vale_para(a, resultado):
                continue
            acertos = regras.contar_acertos(a.numeros, resultado.numeros_sorteados)
            conferidas.append({
                "aposta": a,
                "acertos": acertos,
                "premio": regras.premio_da_aposta(resultado, a, acertos),
            })
        return conferidas

    def calcular_premio(self, resultado: Resultado, acertos: int) -> float:
        return regras.calcular_premio(resultado, acertos)

    def add_teimosinha(self, tipo_loteria: str, numeros: List[int], valor: float,
                       concursos: int, id_jogador: int = 0, cotas: int = 1) -> List[Aposta]:
        """Mesma aposta para os próximos N concursos (uma aposta por concurso)."""
        if not 1 <= concursos <= 24:
            raise ValueError("Teimosinha: de 1 a 24 concursos.")
        do_tipo = [r.concurso for r in self.get_resultados() if r.tipo_loteria == tipo_loteria]
        if not do_tipo:
            raise ValueError("Sincronize os resultados antes: o próximo concurso é desconhecido.")
        ok, erro = regras.validar_aposta(tipo_loteria, numeros, valor)
        if not ok:
            raise ValueError(erro)
        proximo = max(do_tipo) + 1
        return [self.add_aposta(tipo_loteria, numeros, valor, str(proximo + i), id_jogador, cotas)
                for i in range(concursos)]

    def importar_apostas_csv(self, caminho: str, id_jogador: int = 0) -> dict:
        linhas, erros = ler_apostas_csv(caminho)
        importadas = 0
        for n, l in enumerate(linhas, start=1):
            try:
                self.add_aposta(l["tipo_loteria"], l["numeros"], l["valor"],
                                l["data_sorteio"], id_jogador)
                importadas += 1
            except ValueError as e:
                erros.append(f"Aposta {n}: {e}")
        return {"importadas": importadas, "erros": erros}

    def exportar_apostas(self) -> str:
        apostas = self.get_apostas()
        texto = "=== RELATÓRIO DE APOSTAS ===\n\n"
        texto += f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        for a in apostas:
            nome = LOTERIAS.get(a.tipo_loteria, a.tipo_loteria)
            nums = " | ".join(str(n) for n in a.numeros)
            texto += f"{nome} #{a.data_sorteio}\n"
            texto += f"  Números: {nums}\n"
            texto += f"  Valor: {formatar_valor(a.valor)}\n"
            texto += f"  Acertos: {a.acertos} | Prêmio: {formatar_valor(a.premio)}\n\n"
        return texto

    def salvar_conferencia(self, conf: Conferencia):
        self.data_service.salvar_conferencia(conf)

    def imprimir_boleto(self, aposta: Aposta):
        jogador = None
        jogadores = self.get_jogadores()
        if jogadores:
            jogador = jogadores[0]
        return abrir_boleto(aposta, jogador)

    def exportar_csv(self, diretorio: str = None) -> dict:
        if diretorio is None:
            import os
            diretorio = os.path.join(BASE_DIR, "exports")
        return exportar_tudo_csv(self.get_apostas(), self.get_resultados(),
                                  self.get_conferencias(), diretorio)

    def backup_database(self) -> str:
        import os
        db = DatabaseService()
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(db.db_path))), "data", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"loterias_backup_{timestamp}.db")
        shutil.copy2(db.db_path, backup_path)
        return backup_path

    def restore_database(self, backup_path: str) -> bool:
        import os
        db = DatabaseService()
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db.db_path)
            return True
        return False

    def limpar_dados(self):
        db = DatabaseService()
        conn = db.get_connection()
        cursor = conn.cursor()
        for tabela in ["apostas", "conferencias", "resultados", "jogadores"]:
            cursor.execute(f"DELETE FROM {tabela}")
        conn.commit()
        conn.close()

    def get_db_info(self) -> dict:
        import os
        db = DatabaseService()
        size = os.path.getsize(db.db_path) if os.path.exists(db.db_path) else 0
        stats = self.get_stats()
        return {
            "db_path": db.db_path,
            "db_size_mb": round(size / 1024 / 1024, 2),
            "total_resultados": stats["total_resultados"],
            "total_apostas": stats["total_apostas"],
            "total_jogadores": len(self.get_jogadores()),
            "total_conferencias": len(self.get_conferencias()),
        }


class AppController:
    def __init__(self, app):
        self.app = app
        self.controller = Controller()
        self.current_view_name = None

    def get_resultados(self):
        return self.controller.get_resultados()

    def get_apostas(self):
        return self.controller.get_apostas()

    def get_jogadores(self):
        return self.controller.get_jogadores()

    def get_stats(self):
        return self.controller.get_stats()

    def get_conferencias(self):
        return self.controller.get_conferencias()

    def sync_and_refresh(self):
        with threading.Thread(target=self._sync_worker, daemon=True):
            self._sync_worker()

    def _sync_worker(self):
        result = self.controller.sync_and_refresh()
        if hasattr(self.app, 'voltar_inicio'):
            self.app.after(0, self.app.voltar_inicio)
        return result

    def get_resultado_by_string(self, texto: str):
        return self.controller.get_resultado_by_string(texto)

    def add_aposta(self, tipo_loteria: str, numeros: list, valor: float, data_sorteio: str = "",
                   id_jogador: int = 0, cotas: int = 1):
        return self.controller.add_aposta(tipo_loteria, numeros, valor, data_sorteio, id_jogador, cotas)

    def add_teimosinha(self, tipo_loteria: str, numeros: list, valor: float, concursos: int,
                       id_jogador: int = 0, cotas: int = 1):
        return self.controller.add_teimosinha(tipo_loteria, numeros, valor, concursos, id_jogador, cotas)

    def remover_aposta(self, aposta_id: int):
        return self.controller.remover_aposta(aposta_id)

    def atualizar_aposta(self, aposta: Aposta):
        return self.controller.atualizar_aposta(aposta)

    def add_jogador(self, nome: str, cpf: str, email: str = ""):
        return self.controller.add_jogador(nome, cpf, email)

    def get_jogador(self, cpf: str):
        return self.controller.get_jogador(cpf)

    def conferir_resultado(self, resultado):
        return self.controller.conferir_apostas(resultado)

    def importar_apostas_csv(self, caminho: str):
        jogador = getattr(self.app, "jogador_atual", None)
        return self.controller.importar_apostas_csv(caminho, getattr(jogador, "id", 0))

    def nova_aposta(self):
        self.app.mostrar_tela_nova_aposta()

    def conferir_apostas(self):
        self.app.mostrar_tela_conferencia()

    def exportar_apostas(self):
        texto = self.controller.exportar_apostas()
        self.app.mostrar_exportacao(texto)

    def imprimir_boleto(self, aposta: Aposta):
        try:
            caminho = self.controller.imprimir_boleto(aposta)
            self.app._mostrar_toast(f"Registro aberto: {caminho}")
        except Exception as e:
            self.app._mostrar_toast(f"Erro ao gerar registro: {str(e)}")

    def exportar_csv(self):
        try:
            arquivos = self.controller.exportar_csv()
            self.app._mostrar_toast(f"CSV exportado: {len(arquivos)} arquivos")
            return arquivos
        except Exception as e:
            self.app._mostrar_toast(f"Erro ao exportar CSV: {str(e)}")
            return []

    def backup_database(self):
        try:
            caminho = self.controller.backup_database()
            self.app._mostrar_toast(f"Backup criado: {caminho}")
            return caminho
        except Exception as e:
            self.app._mostrar_toast(f"Erro ao criar backup: {str(e)}")
            return None

    def restore_database(self, backup_path: str):
        try:
            ok = self.controller.restore_database(backup_path)
            if ok:
                self.app._mostrar_toast("Backup restaurado com sucesso!")
            return ok
        except Exception as e:
            self.app._mostrar_toast(f"Erro ao restaurar: {str(e)}")
            return False

    def limpar_dados(self):
        try:
            self.controller.limpar_dados()
            self.app._mostrar_toast("Dados limpos com sucesso!")
            return True
        except Exception as e:
            self.app._mostrar_toast(f"Erro ao limpar: {str(e)}")
            return False

    def get_db_info(self):
        return self.controller.get_db_info()