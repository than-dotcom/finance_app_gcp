"""
Módulo de integração com APIs externas (Finnhub, ExchangeRate)
Gerencia cotações de ativos e taxas de câmbio com cache
"""

import requests
import streamlit as st
from datetime import datetime
from typing import Optional, Dict
import database as db

# Configurações
FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "")
CACHE_TTL = 300  # 5 minutos


@st.cache_data(ttl=CACHE_TTL)
def get_asset_price_finnhub(ticker: str) -> Optional[float]:
    """
    Busca o preço de um ativo via Finnhub API.
    Usa cache de 5 minutos.
    """
    if not FINNHUB_API_KEY:
        return None
    
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "c" in data and data["c"] > 0:
            return float(data["c"])
    except Exception as e:
        print(f"Erro ao buscar preço de {ticker} no Finnhub: {e}")
    
    return None


@st.cache_data(ttl=CACHE_TTL)
def get_exchange_rate(from_currency: str, to_currency: str = "BRL") -> Optional[float]:
    """
    Busca a taxa de câmbio entre duas moedas.
    Tenta Finnhub primeiro, depois ExchangeRate-API como fallback.
    """
    # Tenta Finnhub
    if FINNHUB_API_KEY:
        try:
            symbol = f"OANDA:{from_currency}{to_currency}"
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if "c" in data and data["c"] > 0:
                return float(data["c"])
        except Exception as e:
            print(f"Erro ao buscar câmbio {from_currency}/{to_currency} no Finnhub: {e}")
    
    # Fallback: ExchangeRate-API
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "rates" in data and to_currency in data["rates"]:
            return float(data["rates"][to_currency])
    except Exception as e:
        print(f"Erro ao buscar câmbio via ExchangeRate-API: {e}")
    
    return None


def convert_to_brl(valor: float, moeda: str) -> tuple[float, Optional[float]]:
    """
    Converte um valor para BRL.
    Retorna (valor_em_brl, taxa_usada)
    """
    if moeda == "BRL":
        return valor, 1.0
    
    # Tenta buscar taxa de câmbio
    taxa = get_exchange_rate(moeda, "BRL")
    
    if taxa is None:
        # Fallback: taxas hardcoded
        taxas_fallback = {
            "USD": 5.15,
            "EUR": 5.60,
            "GBP": 6.50,
            "JPY": 0.035,
            "CHF": 5.90,
            "CAD": 3.80,
            "AUD": 3.40,
        }
        taxa = taxas_fallback.get(moeda, 1.0)
    
    valor_brl = valor * taxa
    return valor_brl, taxa


def get_current_price(ticker: str) -> Optional[float]:
    """
    Obtém o preço atual de um ativo.
    Hierarquia: (1) Cache local → (2) Finnhub → (3) Preço médio cadastrado
    """
    # Tenta cache local
    cached = db.get_cached_price(ticker, ttl_seconds=CACHE_TTL)
    if cached is not None:
        return cached
    
    # Tenta Finnhub
    price = get_asset_price_finnhub(ticker)
    if price is not None:
        db.set_cached_price(ticker, price)
        return price
    
    # Fallback: preço médio cadastrado
    investments = db.get_investments()
    for inv in investments:
        if inv["ticker"] == ticker:
            return inv["preco_medio"]
    
    return None


def format_currency(valor: float, moeda: str = "BRL") -> str:
    """Formata um valor como moeda."""
    if moeda == "BRL":
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif moeda == "USD":
        return f"US$ {valor:,.2f}"
    elif moeda == "EUR":
        return f"€ {valor:,.2f}"
    else:
        return f"{valor:,.2f} {moeda}"
