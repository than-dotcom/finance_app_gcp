"""
utils/data_manager.py
Gerencia toda a persistência de dados em JSON.
Futuramente pode ser trocado por SQLite ou PostgreSQL sem alterar o restante do app.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, date
from typing import Optional
import streamlit as st

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

INVEST_FILE   = DATA_DIR / "investimentos.json"
EXPENSE_FILE  = DATA_DIR / "despesas.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


# ─── helpers ──────────────────────────────────────────────────────────────────

def _load(path: Path) -> list:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []

def _save(path: Path, data: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


# ─── INVESTIMENTOS ─────────────────────────────────────────────────────────────

TIPOS_INVESTIMENTO = {
    "acao_br"    : "🇧🇷 Ação BR (B3)",
    "acao_us"    : "🇺🇸 Ação EUA",
    "acao_eu"    : "🇪🇺 Ação Europa",
    "acao_uk"    : "🇬🇧 Ação UK",
    "fii"        : "🏢 FII",
    "etf_br"     : "📦 ETF BR",
    "etf_us"     : "📦 ETF EUA",
    "cripto"     : "₿ Criptomoeda",
    "tesouro"    : "🏛️ Tesouro Direto",
    "cdb_lci_lca": "🏦 CDB / LCI / LCA",
    "poupanca"   : "💳 Poupança",
    "fundo"      : "📊 Fundo de Investimento",
    "outro"      : "📁 Outro",
}

MOEDAS = {
    "BRL": "R$ — Real Brasileiro",
    "USD": "$ — Dólar Americano",
    "EUR": "€ — Euro",
    "GBP": "£ — Libra Esterlina",
    "CHF": "Fr — Franco Suíço",
    "JPY": "¥ — Iene Japonês",
    "CAD": "C$ — Dólar Canadense",
    "AUD": "A$ — Dólar Australiano",
    "BTC": "₿ — Bitcoin",
}

SIMBOLOS_MOEDA = {
    "BRL": "R$", "USD": "$", "EUR": "€",
    "GBP": "£",  "CHF": "Fr", "JPY": "¥",
    "CAD": "C$", "AUD": "A$", "BTC": "₿",
}

def get_investimentos() -> list:
    return _load(INVEST_FILE)

def salvar_investimento(dados: dict) -> str:
    items = get_investimentos()
    if "id" not in dados or not dados["id"]:
        dados["id"] = str(uuid.uuid4())
    dados["criado_em"] = dados.get("criado_em", datetime.now().isoformat())
    dados["atualizado_em"] = datetime.now().isoformat()
    # update or insert
    idx = next((i for i, x in enumerate(items) if x["id"] == dados["id"]), None)
    if idx is not None:
        items[idx] = dados
    else:
        items.append(dados)
    _save(INVEST_FILE, items)
    return dados["id"]

def deletar_investimento(inv_id: str):
    items = [x for x in get_investimentos() if x["id"] != inv_id]
    _save(INVEST_FILE, items)


# ─── DESPESAS / RECEITAS ───────────────────────────────────────────────────────

CATEGORIAS_DESPESA = [
    "🍔 Alimentação", "🚗 Transporte", "🏠 Moradia",
    "💊 Saúde", "🎓 Educação", "👕 Vestuário",
    "📱 Tecnologia", "🎬 Lazer", "✈️ Viagem",
    "💡 Contas & Utilidades", "💰 Investimento", "📦 Outros",
]

CATEGORIAS_RECEITA = [
    "💼 Salário", "🔧 Freelance", "📈 Rendimentos",
    "🏠 Aluguel Recebido", "🎁 Presente / Doação",
    "💹 Dividendos", "📦 Outros",
]

def get_transacoes() -> list:
    return _load(EXPENSE_FILE)

def salvar_transacao(dados: dict) -> str:
    items = get_transacoes()
    if "id" not in dados or not dados["id"]:
        dados["id"] = str(uuid.uuid4())
    dados["criado_em"] = dados.get("criado_em", datetime.now().isoformat())
    idx = next((i for i, x in enumerate(items) if x["id"] == dados["id"]), None)
    if idx is not None:
        items[idx] = dados
    else:
        items.append(dados)
    _save(EXPENSE_FILE, items)
    return dados["id"]

def deletar_transacao(tid: str):
    items = [x for x in get_transacoes() if x["id"] != tid]
    _save(EXPENSE_FILE, items)


# ─── SETTINGS ─────────────────────────────────────────────────────────────────

def get_settings() -> dict:
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"moeda_base": "BRL", "nome_usuario": "Investidor"}

def salvar_settings(dados: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


# ─── DADOS DE EXEMPLO (seed inicial) ──────────────────────────────────────────

def seed_dados_exemplo():
    """Popula o app com dados de exemplo na primeira execução."""
    if get_investimentos():
        return  # já tem dados

    exemplos_invest = [
        {"tipo": "acao_br",  "ticker": "PETR4.SA", "nome": "Petrobras PN",        "moeda": "BRL", "quantidade": 200,  "preco_medio": 38.50,  "data_compra": "2023-06-01"},
        {"tipo": "acao_br",  "ticker": "VALE3.SA", "nome": "Vale ON",             "moeda": "BRL", "quantidade": 100,  "preco_medio": 68.00,  "data_compra": "2023-08-15"},
        {"tipo": "fii",      "ticker": "HGLG11.SA","nome": "CSHG Logística",      "moeda": "BRL", "quantidade": 50,   "preco_medio": 162.00, "data_compra": "2023-09-01"},
        {"tipo": "acao_us",  "ticker": "AAPL",     "nome": "Apple Inc.",          "moeda": "USD", "quantidade": 10,   "preco_medio": 175.00, "data_compra": "2023-07-10"},
        {"tipo": "acao_us",  "ticker": "MSFT",     "nome": "Microsoft Corp.",     "moeda": "USD", "quantidade": 5,    "preco_medio": 320.00, "data_compra": "2023-10-01"},
        {"tipo": "cripto",   "ticker": "BTC-USD",  "nome": "Bitcoin",             "moeda": "USD", "quantidade": 0.05, "preco_medio": 42000,  "data_compra": "2024-01-01"},
        {"tipo": "tesouro",  "ticker": "",         "nome": "Tesouro IPCA+ 2029",  "moeda": "BRL", "quantidade": 1,    "preco_medio": 5000.00,"data_compra": "2023-05-01"},
        {"tipo": "cdb_lci_lca","ticker":"",        "nome": "CDB Banco XP 120%CDI","moeda": "BRL", "quantidade": 1,    "preco_medio":10000.00,"data_compra": "2023-11-01"},
    ]
    for inv in exemplos_invest:
        inv["id"] = ""
        salvar_investimento(inv)

    exemplos_desp = [
        {"tipo": "despesa",  "categoria": "🍔 Alimentação",      "descricao": "Supermercado",      "valor": 850.00,  "moeda": "BRL", "data": "2025-03-05"},
        {"tipo": "despesa",  "categoria": "🚗 Transporte",        "descricao": "Combustível",       "valor": 320.00,  "moeda": "BRL", "data": "2025-03-08"},
        {"tipo": "despesa",  "categoria": "🏠 Moradia",           "descricao": "Aluguel",           "valor": 2200.00, "moeda": "BRL", "data": "2025-03-01"},
        {"tipo": "despesa",  "categoria": "💡 Contas & Utilidades","descricao": "Energia + Internet","valor": 380.00,  "moeda": "BRL", "data": "2025-03-10"},
        {"tipo": "despesa",  "categoria": "🎬 Lazer",             "descricao": "Streaming + Cinema","valor": 180.00,  "moeda": "BRL", "data": "2025-03-15"},
        {"tipo": "receita",  "categoria": "💼 Salário",           "descricao": "Salário Março",     "valor": 8500.00, "moeda": "BRL", "data": "2025-03-05"},
        {"tipo": "receita",  "categoria": "💹 Dividendos",        "descricao": "Dividendos PETR4",  "valor": 420.00,  "moeda": "BRL", "data": "2025-03-20"},
    ]
    for d in exemplos_desp:
        d["id"] = ""
        salvar_transacao(d)
