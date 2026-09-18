import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.aposta import Aposta
from models.resultado import Resultado
from services import regras
from services.api_service import APIService


def res(tipo="mega-sena", concurso=100, data="10/01/2026", nums=(1, 2, 3, 4, 5, 6), premiacao=None):
    return Resultado(tipo_loteria=tipo, concurso=concurso, data_sorteio=data,
                     numeros_sorteados=list(nums), premiacao=premiacao or {})


def test_contar_acertos():
    assert regras.contar_acertos([1, 2, 3, 40, 50, 60], [1, 2, 3, 4, 5, 6]) == 3


def test_premio_usa_rateio_real_e_faixa_valida():
    r = res(premiacao={4: 800.0, 5: 50000.0, 6: 9e6})
    assert regras.calcular_premio(r, 4) == 800.0
    assert regras.calcular_premio(r, 3) == 0.0          # faixa não premia
    assert regras.calcular_premio(res(), 4) == 0.0      # rateio desconhecido


def test_lotomania_zero_acertos_premia():
    assert regras.acerto_premia("lotomania", 0)
    assert not regras.acerto_premia("lotomania", 10)


def test_aposta_vale_para():
    a = Aposta(tipo_loteria="mega-sena", data_sorteio="100")
    assert regras.aposta_vale_para(a, res(concurso=100))
    assert not regras.aposta_vale_para(a, res(concurso=101))
    assert not regras.aposta_vale_para(a, res(tipo="quina", concurso=100))
    por_data = Aposta(tipo_loteria="mega-sena", data_sorteio="05/01/2026")
    assert regras.aposta_vale_para(por_data, res())
    assert not regras.aposta_vale_para(Aposta(tipo_loteria="mega-sena", data_sorteio="20/01/2026"), res())


def test_validar_aposta():
    assert regras.validar_aposta("mega-sena", [1, 2, 3, 4, 5, 6], 5.0)[0]
    assert not regras.validar_aposta("mega-sena", [1, 2, 3], 5.0)[0]
    assert not regras.validar_aposta("mega-sena", [1, 1, 3, 4, 5, 6], 5.0)[0]
    assert not regras.validar_aposta("mega-sena", [1, 2, 3, 4, 5, 61], 5.0)[0]
    assert not regras.validar_aposta("mega-sena", [1, 2, 3, 4, 5, 6], 0)[0]
    assert regras.validar_aposta("lotomania", list(range(50)), 3.0)[0]


def test_cpf_email():
    assert regras.validar_cpf("529.982.247-25")
    assert not regras.validar_cpf("111.111.111-11")
    assert not regras.validar_cpf("123")
    assert regras.validar_email("") and regras.validar_email("a@b.com")
    assert not regras.validar_email("abc")
    assert regras.mascarar_cpf("52998224725") == "***.982.247-**"


def test_parse_api_extrai_premiacao():
    api = APIService.__new__(APIService)
    data = {"numero": 7, "dataApuracao": "01/01/2026", "listaDezenas": ["06", "01"],
            "premiacao": [{"descricaoFaixa": "6 acertos", "valorPremio": 1000, "numeroDeGanhadores": 1},
                          {"descricaoFaixa": "4 acertos", "valorPremio": 500, "numeroDeGanhadores": 9}]}
    r = api._parse_api_response("mega-sena", data)
    assert r.premiacao == {6: 1000.0, 4: 500.0}
    assert r.numeros_sorteados == [1, 6]


def test_importacao_csv_e_controller(tmp_path):
    from controllers import Controller
    from services.database_service import DatabaseService
    from utils.importacao import ler_apostas_csv

    csv_path = tmp_path / "a.csv"
    csv_path.write_text("tipo_loteria;numeros;valor;data_sorteio\n"
                        "mega-sena;1 2 3 4 5 6;5,00;100\n"
                        "mega-sena;1 2 3;5,00;100\n"
                        "quina;x;1;2\n", encoding="utf-8")
    linhas, erros = ler_apostas_csv(str(csv_path))
    assert len(linhas) == 2 and len(erros) == 1

    c = Controller.__new__(Controller)
    c.data_service = DatabaseService(str(tmp_path / "t.db"))
    r = c.importar_apostas_csv(str(csv_path), id_jogador=7)
    assert r["importadas"] == 1 and len(r["erros"]) == 2
    assert c.data_service.get_apostas()[0].id_jogador == 7


def test_auto_conferir_calcula_premio(tmp_path):
    from controllers import Controller
    from services.database_service import DatabaseService

    c = Controller.__new__(Controller)
    c.data_service = DatabaseService(str(tmp_path / "t.db"))
    c.add_aposta("mega-sena", [1, 2, 3, 4, 10, 11], 5.0, "100")
    c.data_service.salvar_resultados([res(concurso=100, premiacao={4: 800.0})])
    assert c.auto_conferir() == {"novas": 1, "premiadas": 1}
    a = c.get_apostas()[0]
    assert (a.acertos, a.premio, a.conferencia_feita) == (4, 800.0, True)
    assert c.auto_conferir() == {"novas": 0, "premiadas": 0}


def test_estatisticas():
    from models.aposta import Aposta
    from services import estatisticas as est

    rs = [res(concurso=1, nums=(1, 2, 3, 4, 5, 6)), res(concurso=2, nums=(1, 2, 3, 4, 5, 7))]
    f = est.frequencia_numeros(rs, "mega-sena")
    assert f[1] == 2 and f[6] == 1 and f[60] == 0 and len(f) == 60
    at = est.atraso_numeros(rs, "mega-sena")
    assert at[7] == 0 and at[6] == 1 and at[60] == 2

    ap = [Aposta(data_aposta="05/01/2026", valor=5, premio=0, acertos=0, conferencia_feita=True),
          Aposta(data_aposta="20/01/2026", valor=5, premio=800, acertos=4, conferencia_feita=True),
          Aposta(data_aposta="02/02/2026", valor=3)]
    assert est.distribuicao_acertos(ap) == {0: 1, 4: 1}
    assert est.financeiro_por_mes(ap) == [("01/2026", 10.0, 800.0), ("02/2026", 3.0, 0.0)]


def test_bolao_divide_premio_e_teimosinha(tmp_path):
    import pytest
    from controllers import Controller
    from services.database_service import DatabaseService

    c = Controller.__new__(Controller)
    c.data_service = DatabaseService(str(tmp_path / "t.db"))
    with pytest.raises(ValueError):
        c.add_teimosinha("mega-sena", [1, 2, 3, 4, 5, 6], 5.0, 3)  # sem resultados

    c.data_service.salvar_resultados([res(concurso=100, premiacao={4: 800.0})])
    apostas = c.add_teimosinha("mega-sena", [1, 2, 3, 4, 10, 11], 5.0, 3, cotas=4)
    assert [a.data_sorteio for a in apostas] == ["101", "102", "103"]
    assert all(a.cotas == 4 for a in c.get_apostas())

    c.data_service.salvar_resultados([res(concurso=101, premiacao={4: 800.0}, nums=(1, 2, 3, 4, 5, 6))])
    c.auto_conferir()
    a101 = next(a for a in c.get_apostas() if a.data_sorteio == "101")
    assert a101.premio == 200.0  # 800 dividido em 4 cotas
    with pytest.raises(ValueError):
        c.add_aposta("mega-sena", [1, 2, 3, 4, 5, 6], 5.0, cotas=0)


def test_desdobramento_soma_combinacoes():
    # 7 números na Mega, 6 acertos entre eles: 1 sena + 6 quinas
    r = res(premiacao={4: 100.0, 5: 1000.0, 6: 50000.0})
    a = Aposta(tipo_loteria="mega-sena", numeros=[1, 2, 3, 4, 5, 6, 7])
    assert regras.premio_da_aposta(r, a, 6) == 50000.0 + 6 * 1000.0
    # 5 acertos entre 7: C(5,5)*C(2,1)=2 quinas + C(5,4)*C(2,2)=5 quadras
    assert regras.premio_da_aposta(r, a, 5) == 2 * 1000.0 + 5 * 100.0
    # aposta simples continua igual
    simples = Aposta(tipo_loteria="mega-sena", numeros=[1, 2, 3, 4, 5, 6])
    assert regras.premio_da_aposta(r, simples, 5) == 1000.0


def test_gerar_numeros_modos():
    import random
    from services import estatisticas as est

    rs = [res(concurso=i, nums=(1, 2, 3, 4, 5, 6)) for i in range(1, 30)]
    rng = random.Random(1)
    for modo in est.MODOS_GERACAO.values():
        nums = est.gerar_numeros(rs, "mega-sena", 6, modo, rng)
        assert regras.validar_aposta("mega-sena", nums, 5.0)[0], modo
    # sem histórico cai no aleatório
    assert len(est.gerar_numeros([], "mega-sena", 6, "quentes", rng)) == 6
    # ponderação favorece os mais sorteados
    hits = sum(n <= 6 for _ in range(300) for n in est.gerar_numeros(rs, "mega-sena", 6, "quentes", rng))
    assert hits / 300 > 6 * 0.3
    # lotomania inclui o 0 no universo
    assert regras.validar_aposta("lotomania", est.gerar_numeros([], "lotomania", 50), 3.0)[0]
