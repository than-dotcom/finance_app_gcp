"""
utils/market_data.py
Busca cotações de ativos (yfinance) e taxas de câmbio (API gratuita).
Usa cache do Streamlit para evitar requisições repetidas.
"""

import streamlit as st
import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta


# ─── CÂMBIO ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800)  # cache 30 min
def get_taxas_cambio(moeda_base: str = "BRL") -> dict:
    """
    Retorna taxas de câmbio relativas à moeda_base.
    Fonte: exchangerate-api (gratuito, sem chave).
    """
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{moeda_base}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json().get("rates", {})
    except Exception:
        pass

    # Fallback: taxas aproximadas vs BRL
    fallback = {
        "BRL": 1.0, "USD": 0.177, "EUR": 0.163,
        "GBP": 0.140, "CHF": 0.160, "JPY": 26.5,
        "CAD": 0.240, "AUD": 0.274,
    }
    return fallback


def converter_para_brl(valor: float, moeda_origem: str, taxas: dict) -> float:
    """Converte qualquer valor para BRL usando as taxas carregadas."""
    if moeda_origem == "BRL":
        return valor
    taxa_origem_vs_brl = taxas.get(moeda_origem, 1.0)
    if taxa_origem_vs_brl == 0:
        return valor
    # taxas está em "quanto 1 BRL compra de X"
    # então 1 X = 1 / taxa BRL
    return valor / taxa_origem_vs_brl


def converter_valor(valor: float, de: str, para: str, taxas: dict) -> float:
    """Converte entre quaisquer duas moedas via BRL como pivô."""
    if de == para:
        return valor
    em_brl = converter_para_brl(valor, de, taxas)
    if para == "BRL":
        return em_brl
    taxa_para = taxas.get(para, 1.0)
    return em_brl * taxa_para


# ─── COTAÇÕES ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)  # cache 5 min
def get_cotacao(ticker: str) -> dict:
    """
    Busca cotação atual de um ativo via yfinance.
    Retorna dict com preco, variacao_dia, moeda, nome.
    """
    if not ticker or ticker.strip() == "":
        return {"preco": None, "variacao_dia": 0.0, "moeda": "BRL", "nome": ""}
    try:
        t = yf.Ticker(ticker.strip())
        info = t.fast_info
        preco = getattr(info, "last_price", None) or getattr(info, "regularMarketPrice", None)
        prev  = getattr(info, "previous_close", None) or preco
        variacao = ((preco - prev) / prev * 100) if preco and prev and prev != 0 else 0.0
        moeda = getattr(info, "currency", "BRL") or "BRL"
        nome  = ticker
        return {
            "preco"       : round(float(preco), 4) if preco else None,
            "variacao_dia": round(float(variacao), 2),
            "moeda"       : moeda.upper(),
            "nome"        : nome,
        }
    except Exception:
        return {"preco": None, "variacao_dia": 0.0, "moeda": "BRL", "nome": ticker}


@st.cache_data(ttl=3600)  # cache 1h
def get_historico(ticker: str, periodo: str = "1y") -> pd.DataFrame:
    """Retorna histórico de preços de fechamento."""
    if not ticker:
        return pd.DataFrame()
    try:
        df = yf.download(ticker, period=periodo, progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        return df[["Close"]].rename(columns={"Close": "preco"})
    except Exception:
        return pd.DataFrame()


# ─── PREÇO DE CUSTO vs MERCADO ────────────────────────────────────────────────

def enriquecer_investimento(inv: dict, taxas: dict) -> dict:
    """
    Adiciona ao dict de investimento:
    - preco_atual, variacao_dia
    - valor_investido_brl, valor_atual_brl
    - retorno_brl, retorno_pct
    """
    qtd   = float(inv.get("quantidade", 0))
    pm    = float(inv.get("preco_medio", 0))
    moeda = inv.get("moeda", "BRL")

    custo_brl = converter_para_brl(qtd * pm, moeda, taxas)

    ticker = inv.get("ticker", "").strip()
    cot = get_cotacao(ticker) if ticker else {"preco": None, "variacao_dia": 0.0, "moeda": moeda}

    preco_atual = cot["preco"]

    if preco_atual:
        moeda_cot  = cot.get("moeda", moeda)
        valor_brl  = converter_para_brl(qtd * preco_atual, moeda_cot, taxas)
        retorno_brl = valor_brl - custo_brl
        retorno_pct = (retorno_brl / custo_brl * 100) if custo_brl else 0.0
    else:
        # Ativo sem cotação automática (Tesouro, CDB) — usa preço médio como atual
        valor_brl   = custo_brl
        retorno_brl = 0.0
        retorno_pct = 0.0

    return {
        **inv,
        "preco_atual"       : preco_atual or pm,
        "variacao_dia"      : cot.get("variacao_dia", 0.0),
        "custo_brl"         : round(custo_brl, 2),
        "valor_atual_brl"   : round(valor_brl, 2),
        "retorno_brl"       : round(retorno_brl, 2),
        "retorno_pct"       : round(retorno_pct, 2),
    }


# ─── HISTÓRICO DO PORTFÓLIO ───────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def historico_portfolio(investimentos: list, taxas_snap: dict) -> pd.DataFrame:
    """
    Aproxima a evolução histórica do portfólio somando os históricos
    de cada ativo ponderado pela quantidade.
    """
    if not investimentos:
        return pd.DataFrame()

    series_list = []
    for inv in investimentos:
        ticker = inv.get("ticker", "").strip()
        if not ticker:
            continue
        qtd = float(inv.get("quantidade", 0))
        moeda = inv.get("moeda", "BRL")
        hist = get_historico(ticker, "1y")
        if hist.empty:
            continue
        hist = hist.copy()
        hist["valor"] = hist["preco"] * qtd
        # converte para BRL
        if moeda != "BRL":
            hist["valor"] = hist["valor"].apply(
                lambda v: converter_para_brl(v, moeda, taxas_snap)
            )
        series_list.append(hist[["valor"]])

    if not series_list:
        return pd.DataFrame()

    combined = pd.concat(series_list, axis=1)
    combined.columns = range(len(combined.columns))
    combined["total"] = combined.sum(axis=1)
    combined.index = pd.to_datetime(combined.index)
    combined.index = combined.index.tz_localize(None)
    return combined[["total"]].dropna()
