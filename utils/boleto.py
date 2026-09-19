"""
Gerador de Boleto de Aposta - Controle de Apostas Lotéricas
Gera um boleto HTML formatado para impressão
"""
import os
from utils.paths import BASE_DIR
from datetime import datetime
from typing import Optional

from services.api_service import LOTERIAS

LOTERIAS_NOME = {k: v["nome"] for k, v in LOTERIAS.items()}


def gerar_boleto_html(aposta, jogador=None) -> str:
    """Gera o HTML do boleto de aposta para impressão."""
    nome_loteria = LOTERIAS_NOME.get(aposta.tipo_loteria, aposta.tipo_loteria)
    config = LOTERIAS.get(aposta.tipo_loteria, {})
    max_num = config.get("maximo", 60)
    qtd_num = config.get("numeros", 6)

    numeros_html = ""
    for i, num in enumerate(aposta.numeros):
        numeros_html += f'<span class="num">{num:02d}</span>'
        if (i + 1) % 10 == 0:
            numeros_html += '<br>'

    jogador_nome = jogador.nome if jogador else "Não informado"
    jogador_cpf = jogador.cpf if jogador else "---"
    jogador_email = jogador.email if jogador else "---"

    barcode_code = f"{aposta.tipo_loteria.upper()[:3]}-{aposta.data_sorteio.replace('/', '')}-{aposta.id:06d}-{aposta.valor:.2f}"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Registro de controle - {nome_loteria}</title>
<style>
@page {{
    size: A5 portrait;
    margin: 10mm;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: 'Arial', 'Helvetica', sans-serif;
    background: #f0f2f5;
    display: flex;
    justify-content: center;
    padding: 20px;
}}

.boleto {{
    width: 148mm;
    min-height: 210mm;
    background: white;
    border: 1px solid #ccc;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 48, 135, 0.12);
}}

.boleto::before {{
    content: 'NÃO É APOSTA OFICIAL';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-35deg);
    font-size: 42px;
    font-weight: bold;
    color: rgba(198, 40, 40, 0.09);
    white-space: nowrap;
    pointer-events: none;
    z-index: 0;
    letter-spacing: 6px;
}}

.aviso-oficial {{
    margin: 10px 15px 0;
    padding: 9px 12px;
    background: #fdecea;
    border: 2px solid #c62828;
    border-radius: 6px;
    color: #8e1b1b;
    font-size: 10.5px;
    line-height: 1.45;
    text-align: center;
    position: relative;
    z-index: 1;
}}

.aviso-oficial strong {{ font-size: 12px; }}

.header-bar {{
    height: 8px;
    background: linear-gradient(90deg, #003087 0%, #0050d4 40%, #1a73e8 60%, #003087 100%);
    width: 100%;
}}

.header {{
    text-align: center;
    padding: 14px 15px 10px;
    border-bottom: 2px solid #003087;
    position: relative;
    z-index: 1;
}}

.header .caixa-logo {{
    font-size: 10px;
    color: #003087;
    letter-spacing: 3px;
    text-transform: uppercase;
    font-weight: 600;
    margin-bottom: 4px;
}}

.header h1 {{
    font-size: 17px;
    color: #003087;
    margin-bottom: 3px;
    letter-spacing: 0.5px;
}}

.header h2 {{
    font-size: 21px;
    color: #1a1a1a;
    font-weight: 800;
    letter-spacing: 1px;
}}

.header .concurso {{
    font-size: 13px;
    color: #555;
    margin-top: 5px;
    font-weight: 600;
}}

.header .concurso span {{
    color: #003087;
    font-weight: 700;
}}

.content {{
    position: relative;
    z-index: 1;
    padding: 12px 15px 0;
}}

.section {{
    margin-bottom: 10px;
    padding: 8px 10px;
    border: 1px solid #e0e4ea;
    border-radius: 6px;
    background: #fafbfc;
}}

.section-title {{
    font-size: 9px;
    color: #003087;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 700;
    margin-bottom: 6px;
    padding-bottom: 4px;
    border-bottom: 1px solid #e8ecf0;
}}

.numeros-container {{
    text-align: center;
    padding: 12px 8px;
    background: linear-gradient(135deg, #f0f4ff 0%, #e8edf8 100%);
    border: 2px solid #003087;
    border-radius: 10px;
    margin: 10px 0;
    position: relative;
}}

.numeros-container::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #003087, #1a73e8, #003087);
    border-radius: 8px 8px 0 0;
}}

.numeros-container .title {{
    font-size: 10px;
    color: #003087;
    margin-bottom: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}}

.num {{
    display: inline-block;
    width: 36px;
    height: 36px;
    line-height: 36px;
    text-align: center;
    background: linear-gradient(145deg, #0040a0, #003087);
    color: white;
    border-radius: 50%;
    font-size: 15px;
    font-weight: bold;
    margin: 4px 3px;
    box-shadow: 0 3px 6px rgba(0, 48, 135, 0.35), 0 1px 2px rgba(0,0,0,0.15);
    border: 2px solid rgba(255,255,255,0.15);
    transition: transform 0.15s;
}}

.info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px 16px;
}}

.info-item {{
    font-size: 12px;
}}

.info-item .label {{
    font-size: 8.5px;
    color: #777;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
    margin-bottom: 2px;
}}

.info-item .value {{
    font-weight: 700;
    color: #1a1a1a;
    font-size: 13px;
    word-break: break-word;
}}

.valor-box {{
    text-align: center;
    background: linear-gradient(135deg, #0a8c2e 0%, #15a33f 50%, #0a8c2e 100%);
    color: white;
    padding: 12px 15px;
    border-radius: 10px;
    margin: 12px 0;
    box-shadow: 0 4px 10px rgba(10, 140, 46, 0.3);
    position: relative;
    overflow: hidden;
}}

.valor-box::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
}}

.valor-box .label {{
    font-size: 10px;
    opacity: 0.9;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-weight: 600;
}}

.valor-box .valor {{
    font-size: 32px;
    font-weight: 900;
    letter-spacing: 1px;
    text-shadow: 0 1px 3px rgba(0,0,0,0.2);
    margin-top: 2px;
}}

.barcode {{
    text-align: center;
    padding: 12px 10px;
    background: #f8f9fa;
    border: 1px solid #e0e4ea;
    border-radius: 6px;
    margin: 12px 0;
}}

.barcode-visual {{
    height: 36px;
    margin: 0 auto 6px;
    max-width: 340px;
    display: flex;
    align-items: stretch;
    justify-content: center;
}}

.barcode-visual .bar {{
    display: inline-block;
    background: #1a1a1a;
    height: 100%;
}}

.barcode-visual .bar.thin {{ width: 1px; margin-right: 1px; }}
.barcode-visual .bar.medium {{ width: 2px; margin-right: 1px; }}
.barcode-visual .bar.thick {{ width: 3px; margin-right: 1px; }}
.barcode-visual .bar.space {{ width: 2px; background: transparent; }}
.barcode-visual .bar.space-thin {{ width: 1px; background: transparent; }}

.barcode-text {{
    font-family: 'Courier New', monospace;
    font-size: 10px;
    color: #333;
    letter-spacing: 2px;
    margin-top: 4px;
    font-weight: 600;
}}

.barcode-label {{
    font-size: 8px;
    color: #999;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.conferir-section {{
    text-align: center;
    margin: 10px 0;
    padding: 10px;
    background: linear-gradient(135deg, #f0f4ff 0%, #e8edf8 100%);
    border: 2px dashed #003087;
    border-radius: 8px;
}}

.conferir-section .title {{
    font-size: 11px;
    font-weight: 700;
    color: #003087;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}}

.conferir-section .url {{
    font-size: 13px;
    color: #1a1a1a;
    font-weight: 700;
    font-family: 'Courier New', monospace;
    background: white;
    padding: 5px 12px;
    border-radius: 4px;
    display: inline-block;
    border: 1px solid #003087;
}}

.footer {{
    text-align: center;
    padding: 10px 15px 12px;
    border-top: 2px solid #003087;
    position: relative;
    z-index: 1;
}}

.footer .comprovante-title {{
    font-size: 10px;
    font-weight: 700;
    color: #003087;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 4px;
}}

.footer p {{
    font-size: 9px;
    color: #555;
    margin: 2px 0;
}}

.footer .aviso {{
    font-size: 8px;
    color: #888;
    margin-top: 6px;
    line-height: 1.4;
    padding-top: 6px;
    border-top: 1px dashed #ddd;
}}

.footer .sistema {{
    font-size: 7.5px;
    color: #aaa;
    margin-top: 8px;
    padding-top: 6px;
    border-top: 1px solid #eee;
    letter-spacing: 0.3px;
}}

.linha-corte {{
    border: none;
    border-top: 1px dashed #999;
    margin: 15px 0;
}}

.btn-print {{
    display: block;
    width: 220px;
    margin: 16px auto 10px;
    padding: 12px 20px;
    background: linear-gradient(135deg, #003087, #0050d4);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    text-align: center;
    letter-spacing: 1px;
    text-transform: uppercase;
    box-shadow: 0 3px 8px rgba(0, 48, 135, 0.3);
    transition: background 0.2s, box-shadow 0.2s;
    position: relative;
    z-index: 1;
}}

.btn-print:hover {{
    background: linear-gradient(135deg, #002266, #003087);
    box-shadow: 0 4px 12px rgba(0, 48, 135, 0.4);
}}

@media print {{
    body {{
        background: white;
        padding: 0;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    .boleto {{
        border: none;
        box-shadow: none;
        width: 100%;
        min-height: auto;
    }}

    .boleto::before {{
        color: rgba(198, 40, 40, 0.07);
    }}

    .btn-print {{
        display: none !important;
    }}

    .header-bar {{
        background: #003087 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    .num {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    .valor-box {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    .barcode-visual .bar {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    .numeros-container {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    .conferir-section {{
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}

    .footer .sistema {{
        font-size: 7px;
        color: #bbb;
    }}
}}
</style>
</head>
<body>
<div class="boleto">
    <div class="header-bar"></div>

    <div class="header">
        <div class="caixa-logo">Controle pessoal &bull; sem vínculo com a Caixa</div>
        <h1>{nome_loteria.upper()}</h1>
        <h2>REGISTRO DE CONTROLE PESSOAL</h2>
        <div class="concurso">Concurso <span>#{aposta.data_sorteio}</span></div>
    </div>

    <div class="aviso-oficial">
        <strong>&#9888; ESTE DOCUMENTO NÃO É UMA APOSTA NEM UM BILHETE DA CAIXA.</strong><br>
        Ele apenas registra, para seu controle, os números escolhidos neste sistema. Não vale como
        jogo, não concorre a prêmios e não pode ser apresentado na lotérica.<br>
        Para concorrer, faça a aposta na lotérica, no app Loterias CAIXA ou em
        www.loteriasonline.caixa.gov.br.
    </div>

    <div class="content">
        <div class="numeros-container">
            <div class="title">Numeros Selecionados ({qtd_num} de 1 a {max_num})</div>
            {numeros_html}
        </div>

        <div class="section">
            <div class="section-title">Dados da Aposta</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="label">Data da Aposta</div>
                    <div class="value">{aposta.data_aposta}</div>
                </div>
                <div class="info-item">
                    <div class="label">Data do Sorteio</div>
                    <div class="value">{aposta.data_sorteio}</div>
                </div>
                <div class="info-item">
                    <div class="label">Tipo de Jogo</div>
                    <div class="value">Simples</div>
                </div>
                <div class="info-item">
                    <div class="label">Qtd. Numeros</div>
                    <div class="value">{len(aposta.numeros)}</div>
                </div>
            </div>
        </div>

        <div class="valor-box">
            <div class="label">Valor da Aposta</div>
            <div class="valor">R$ {aposta.valor:,.2f}</div>
        </div>

        <div class="section">
            <div class="section-title">Dados do Apostador</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="label">Nome</div>
                    <div class="value">{jogador_nome}</div>
                </div>
                <div class="info-item">
                    <div class="label">CPF</div>
                    <div class="value">{jogador_cpf}</div>
                </div>
                <div class="info-item">
                    <div class="label">E-mail</div>
                    <div class="value">{jogador_email}</div>
                </div>
                <div class="info-item">
                    <div class="label">ID da Aposta</div>
                    <div class="value">{aposta.id:06d}</div>
                </div>
            </div>
        </div>

        <div class="barcode">
            <div class="barcode-label">Código interno de controle (não é código de barras oficial)</div>
            <div class="barcode-text">{barcode_code}</div>
        </div>

        <div class="conferir-section">
            <div class="title">Conferir o resultado oficial</div>
            <div class="url">www.loterias.caixa.gov.br</div>
        </div>
    </div>

    <div class="footer">
        <div class="comprovante-title">Registro de controle pessoal &mdash; sem valor como aposta</div>
        <p>Apostador: {jogador_nome} | ID: {aposta.id:06d}</p>
        <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <div class="aviso">
            Este registro NÃO é comprovante de aposta e não tem valor perante a Caixa Econômica Federal.
            <br>Guarde o bilhete oficial emitido pela lotérica ou pelo app/site da Caixa: só ele vale para receber prêmios.
            <br>Verifique os resultados em www.loterias.caixa.gov.br
        </div>
        <div class="sistema">
            Controle de Apostas Lotéricas v1.0 - Desenvolvido por Paulo Sergio dos Santos Fontes
        </div>
    </div>

    <button class="btn-print" onclick="window.print()">Imprimir registro</button>
</div>
</body>
</html>"""

    return html


def salvar_boleto(aposta, jogador=None, diretorio=None) -> str:
    """Salva o boleto como arquivo HTML e retorna o caminho."""
    if diretorio is None:
        diretorio = os.path.join(BASE_DIR, "boletos")

    os.makedirs(diretorio, exist_ok=True)

    nome_loteria = LOTERIAS_NOME.get(aposta.tipo_loteria, aposta.tipo_loteria)
    nome_arquivo = f"boleto_{aposta.tipo_loteria}_{aposta.data_sorteio.replace('/', '-')}_{aposta.id:06d}.html"
    caminho = os.path.join(diretorio, nome_arquivo)

    html = gerar_boleto_html(aposta, jogador)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)

    return caminho


def abrir_boleto(aposta, jogador=None) -> str:
    """Gera e abre o boleto no navegador padrao."""
    caminho = salvar_boleto(aposta, jogador)
    os.startfile(caminho)
    return caminho
