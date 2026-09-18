# 🎰 Sistema de Controle de Apostas e Resultados - Loterias da Caixa

Sistema de gestão de apostas e resultados das Loterias da Caixa com interface gráfica em Python.

**Desenvolvido por:** Paulo Sérgio dos Santos Fontes  
**Telefone:** (79) 98805 6632

## 📋 Funcionalidades

### Tela Inicial (Dashboard)
- Cards de indicadores, alertas automáticos e últimos resultados
- Frases motivacionais aleatórias

### Resultados
- Filtro por loteria, prêmio acumulado, ganhadores e arrecadação
- Detalhes do resultado com as apostas que usaram esses números
- **Sincronização com a Caixa** manual e **automática** (ao abrir o app e a cada 6 h), com retry e aviso de falha

### Apostas
- Geração aleatória de números, validada pelas regras de cada loteria
- Cards de status, estatísticas e exclusão
- **Importação de CSV** (Configurações → Importar Apostas) com colunas `tipo_loteria;numeros;valor;data_sorteio`
- Cada aposta fica vinculada ao jogador cadastrado
- **Bolão:** informe o nº de cotas e o prêmio é dividido entre elas
- **Teimosinha:** repete a aposta nos próximos 1 a 24 concursos (exige resultados sincronizados)

### Conferência
- Confere **apenas apostas da mesma loteria e do mesmo concurso** do resultado
- Prêmio calculado pelo **rateio real** do concurso, por faixa de acertos de cada loteria
- **Conferência automática** após cada sincronização (novas apostas conferidas, apostas antigas recalculadas)

### Estatísticas (com gráficos)
- Frequência de cada número por loteria (destaque para acima/abaixo da média)
- Atraso de cada número (concursos desde a última vez que saiu)
- Apostas por quantidade de acertos
- Investido × prêmios por mês
- Números quentes/frios e distribuição por período
- Gráficos desenhados em `tkinter.Canvas` (sem dependências extras), com dica ao passar o mouse e suporte a tema claro/escuro

### Histórico e Relatório
- Conferências realizadas com números apostados × sorteados
- Resumo geral, financeiro (ROI), por loteria e por período
- Exportação para TXT/CSV e cópia para a área de transferência

### Cadastro
- Nome, **CPF validado** e e-mail validado; CPF exibido mascarado (`***.123.456-**`)

### Extras
- Busca global, tema escuro/claro, relógio/status, notificações (toast), backup e restauração do banco

## 🛠️ Instalação

```bash
pip install -r requirements.txt
python main.py
```

Para rodar os testes:

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

## 📁 Estrutura do Projeto

```
BR_Loterias_Caixa/
├── main.py                    # Janela principal e navegação
├── controllers.py             # Controlador central (validação, conferência, importação)
├── cores.py                   # Paleta de cores
├── models/                    # aposta, resultado, jogador, conferencia
├── services/
│   ├── api_service.py         # Busca de resultados na API da Caixa (retry + log)
│   ├── database_service.py    # Persistência SQLite (com migrações automáticas)
│   ├── regras.py              # Regras por loteria: validação, faixas, prêmio, CPF
│   └── estatisticas.py        # Cálculos estatísticos puros (testáveis)
├── views/                     # Telas
│   ├── *_view.py              # resultados, apostas, conferência, estatísticas, ...
│   ├── graficos.py            # Gráfico de barras em Canvas
│   └── *_mixin.py             # Partes do App: busca, nova aposta, sistema
├── utils/                     # helpers, export (CSV), importacao (CSV), boleto
├── tests/                     # Testes (pytest)
└── data/                      # loterias.db (SQLite), backups
```

## 🎯 Loterias Suportadas

| Loteria | Aposta simples | Números | Acertos que premiam |
|---------|---------------|---------|---------------------|
| Mega-Sena | 6 (até 20) | 1-60 | 4, 5, 6 |
| Quina | 5 (até 15) | 1-80 | 2 a 5 |
| Lotofácil | 15 (até 20) | 1-25 | 11 a 15 |
| Lotomania | 50 | 0-99 | 0 e 16 a 20 |
| Timemania | 10 | 1-80 | 3 a 7 |
| Dupla Sena | 6 (até 15) | 1-50 | 3 a 6 |
| Dia de Sorte | 7 (até 15) | 1-31 | 4 a 7 |

## 🚀 Tecnologias

Python 3.14+, CustomTkinter, SQLite3, Requests, Dataclasses, pytest.

## 📦 Executável (Windows)

```powershell
pip install -r requirements-dev.txt
./build.ps1
```

O app salva `data/`, `boletos/` e `exports/` ao lado do `.exe`.

## 📊 Banco de Dados

Tabelas SQLite: `resultados` (inclui `premiacao` por faixa), `apostas` (inclui `id_jogador` e `cotas`), `jogadores` e `conferencias`.
Colunas novas são adicionadas automaticamente em bancos existentes.

## ⚠️ Observações

- O prêmio só é calculado quando o resultado tem o rateio por faixa; resultados sincronizados antes dessa versão ficam com prêmio 0 até serem buscados novamente.
- Aposta com mais números que o mínimo (desdobramento) é conferida pelos acertos totais, sem calcular as combinações premiadas.
- O executável (`build.ps1`) não foi testado neste ambiente.

## 📝 Licença

Uso educacional e pessoal.
