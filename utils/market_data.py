"""
utils/market_data.py
Busca cotações (yfinance) e taxas de câmbio.
"""

import streamlit as st
import yfinance as yf
import requests
import pandas as pd


@st.cache_data(ttl=1800)
def get_taxas_cambio(moeda_base: str = "BRL") -> dict:
    """
    Retorna taxas onde rates[X] = quanto de X equivale a 1 moeda_base.
    Ex: base=BRL → rates["USD"]=0.177 significa 1 BRL = 0.177 USD.
    Portanto 1 USD = 1/0.177 ≈ 5.65 BRL.
    """
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{moeda_base}"
        r = requests.get(url, timeout=6)
        if r.status_code == 200:
            return r.json().get("rates", {})
    except Exception:
        pass
    # Fallback: 1 BRL = X moeda
    fb = {"BRL":1.0,"USD":0.177,"EUR":0.163,"GBP":0.140,
          "CHF":0.160,"JPY":26.5,"CAD":0.240,"AUD":0.274,"BTC":0.0000030}
    if moeda_base == "BRL":
        return fb
    base_rate = fb.get(moeda_base, 1.0)
    return {k: v / base_rate for k, v in fb.items()}


def taxa_brl_por_moeda(moeda: str, taxas_brl: dict) -> float:
    """Quantos BRL valem 1 unidade de `moeda`. taxas_brl = get_taxas_cambio('BRL')."""
    if moeda == "BRL":
        return 1.0
    t = taxas_brl.get(moeda, 1.0)
    return (1.0 / t) if t else 1.0


def converter_para_brl(valor: float, moeda: str, taxas_brl: dict) -> float:
    return valor * taxa_brl_por_moeda(moeda, taxas_brl)


def converter_valor(valor: float, de: str, para: str, taxas_brl: dict) -> float:
    if de == para:
        return valor
    em_brl = converter_para_brl(valor, de, taxas_brl)
    if para == "BRL":
        return em_brl
    t = taxas_brl.get(para, 1.0)
    return em_brl * t


@st.cache_data(ttl=300)
def get_cotacao(ticker: str) -> dict:
    if not ticker or not ticker.strip():
        return {"preco": None, "variacao_dia": 0.0, "moeda": "BRL"}
    try:
        t = yf.Ticker(ticker.strip())
        info = t.fast_info
        preco = getattr(info, "last_price", None)
        prev  = getattr(info, "previous_close", None) or preco
        variacao = ((preco - prev) / prev * 100) if preco and prev and prev != 0 else 0.0
        moeda = (getattr(info, "currency", "BRL") or "BRL").upper()
        return {"preco": round(float(preco), 4) if preco else None,
                "variacao_dia": round(float(variacao), 2), "moeda": moeda}
    except Exception:
        return {"preco": None, "variacao_dia": 0.0, "moeda": "BRL"}


@st.cache_data(ttl=3600)
def get_historico(ticker: str, periodo: str = "1y") -> pd.DataFrame:
    if not ticker:
        return pd.DataFrame()
    try:
        df = yf.download(ticker, period=periodo, progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        close = df["Close"]
        if hasattr(close, "squeeze"):
            close = close.squeeze()
        return close.rename("preco").to_frame()
    except Exception:
        return pd.DataFrame()


def enriquecer_investimento(inv: dict, taxas_brl: dict) -> dict:
    qtd   = float(inv.get("quantidade", 0))
    pm    = float(inv.get("preco_medio", 0))
    moeda = inv.get("moeda", "BRL")
    custo_brl = converter_para_brl(qtd * pm, moeda, taxas_brl)

    ticker = inv.get("ticker", "").strip()
    cot = get_cotacao(ticker) if ticker else {"preco": None, "variacao_dia": 0.0, "moeda": moeda}
    preco_atual = cot.get("preco")
    moeda_cot   = cot.get("moeda", moeda)

    if preco_atual:
        valor_brl   = converter_para_brl(qtd * preco_atual, moeda_cot, taxas_brl)
        retorno_brl = valor_brl - custo_brl
        retorno_pct = (retorno_brl / custo_brl * 100) if custo_brl else 0.0
    else:
        valor_brl   = custo_brl
        retorno_brl = 0.0
        retorno_pct = 0.0

    return {**inv,
            "preco_atual":     preco_atual or pm,
            "variacao_dia":    cot.get("variacao_dia", 0.0),
            "custo_brl":       round(custo_brl, 2),
            "valor_atual_brl": round(valor_brl, 2),
            "retorno_brl":     round(retorno_brl, 2),
            "retorno_pct":     round(retorno_pct, 2)}


@st.cache_data(ttl=3600)
def historico_portfolio(investimentos: list, taxas_brl: dict) -> pd.DataFrame:
    if not investimentos:
        return pd.DataFrame()
    series_list = []
    for inv in investimentos:
        ticker = inv.get("ticker", "").strip()
        if not ticker:
            continue
        qtd   = float(inv.get("quantidade", 0))
        moeda = inv.get("moeda", "BRL")
        hist  = get_historico(ticker, "1y")
        if hist.empty:
            continue
        h = hist.copy()
        h["valor"] = h["preco"] * qtd
        h["valor"] = h["valor"].apply(lambda v: converter_para_brl(v, moeda, taxas_brl))
        series_list.append(h[["valor"]])
    if not series_list:
        return pd.DataFrame()
    combined = pd.concat(series_list, axis=1)
    combined.columns = range(len(combined.columns))
    combined["total"] = combined.sum(axis=1)
    combined.index = pd.to_datetime(combined.index).tz_localize(None)
    return combined[["total"]].dropna()
