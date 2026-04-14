"""
Módulo de banco de dados SQLite para FinTrack
Gerencia persistência de investimentos, transações e snapshots de portfólio
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import json

DB_PATH = "fintrack.db"


def init_db():
    """
    Inicializa o banco de dados SQLite com as tabelas necessárias.
    Idempotente - cria as tabelas apenas se não existirem.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela de investimentos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL UNIQUE,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL,
            moeda TEXT DEFAULT 'BRL',
            quantidade REAL NOT NULL,
            preco_medio REAL NOT NULL,
            data_compra DATE,
            notas TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de transações (despesas/receitas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            descricao TEXT,
            valor_brl REAL NOT NULL,
            data_transacao DATE NOT NULL,
            notas TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de snapshots de portfólio (equity curve)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE UNIQUE NOT NULL,
            valor_total_brl REAL NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de cache de cotações
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preco_cache (
            ticker TEXT PRIMARY KEY,
            preco REAL NOT NULL,
            moeda TEXT DEFAULT 'BRL',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============ INVESTIMENTOS ============

def add_investment(ticker: str, nome: str, tipo: str, quantidade: float, preco_medio: float, data_compra: str = None, notas: str = ""):
    """Adiciona um novo investimento."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO investimentos (ticker, nome, tipo, quantidade, preco_medio, data_compra, notas)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ticker, nome, tipo, quantidade, preco_medio, data_compra, notas))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_investments() -> List[Dict]:
    """Retorna todos os investimentos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM investimentos ORDER BY ticker")
    investments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return investments


def update_investment(ticker: str, quantidade: float, preco_medio: float, notas: str = ""):
    """Atualiza um investimento existente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE investimentos 
        SET quantidade = ?, preco_medio = ?, notas = ?, atualizado_em = CURRENT_TIMESTAMP
        WHERE ticker = ?
    """, (quantidade, preco_medio, notas, ticker))
    conn.commit()
    conn.close()


def delete_investment(ticker: str):
    """Deleta um investimento."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM investimentos WHERE ticker = ?", (ticker,))
    conn.commit()
    conn.close()


# ============ TRANSAÇÕES ============

def add_transaction(tipo: str, categoria: str, valor_brl: float, data_transacao: str, descricao: str = "", notas: str = ""):
    """Adiciona uma nova transação (despesa ou receita)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transacoes (tipo, categoria, descricao, valor_brl, data_transacao, notas)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tipo, categoria, descricao, valor_brl, data_transacao, notas))
    conn.commit()
    conn.close()


def get_transactions() -> List[Dict]:
    """Retorna todas as transações."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transacoes ORDER BY data_transacao DESC")
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transactions


def get_transactions_by_period(start_date: str, end_date: str) -> List[Dict]:
    """Retorna transações em um período específico."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transacoes 
        WHERE data_transacao BETWEEN ? AND ?
        ORDER BY data_transacao DESC
    """, (start_date, end_date))
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transactions


def update_transaction(transaction_id: int, tipo: str, categoria: str, valor_brl: float, data_transacao: str, descricao: str = "", notas: str = ""):
    """Atualiza uma transação existente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE transacoes 
        SET tipo = ?, categoria = ?, descricao = ?, valor_brl = ?, data_transacao = ?, notas = ?, atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (tipo, categoria, descricao, valor_brl, data_transacao, notas, transaction_id))
    conn.commit()
    conn.close()


def delete_transaction(transaction_id: int):
    """Deleta uma transação."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transacoes WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


# ============ PORTFOLIO SNAPSHOTS ============

def save_daily_snapshot(valor_total_brl: float, data: str = None):
    """
    Salva um snapshot diário do valor total da carteira.
    Se já existe um snapshot para hoje, não sobrescreve.
    """
    if data is None:
        data = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO portfolio_snapshots (data, valor_total_brl)
            VALUES (?, ?)
        """, (data, valor_total_brl))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Snapshot já existe para este dia
        return False
    finally:
        conn.close()


def get_portfolio_snapshots(days: Optional[int] = None) -> List[Dict]:
    """
    Retorna snapshots do portfólio.
    Se days é None, retorna todos; caso contrário, retorna dos últimos N dias.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if days is None:
        cursor.execute("SELECT * FROM portfolio_snapshots ORDER BY data ASC")
    else:
        cursor.execute(f"""
            SELECT * FROM portfolio_snapshots 
            WHERE data >= date('now', '-{days} days')
            ORDER BY data ASC
        """)
    
    snapshots = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return snapshots


# ============ CACHE DE PREÇOS ============

def get_cached_price(ticker: str, ttl_seconds: int = 300) -> Optional[float]:
    """
    Retorna o preço em cache se ainda estiver válido (dentro do TTL).
    TTL padrão: 300 segundos (5 minutos).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT preco FROM preco_cache 
        WHERE ticker = ? AND datetime(timestamp, '+' || ? || ' seconds') > datetime('now')
    """, (ticker, ttl_seconds))
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else None


def set_cached_price(ticker: str, preco: float, moeda: str = "BRL"):
    """Armazena um preço em cache."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO preco_cache (ticker, preco, moeda, timestamp)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (ticker, preco, moeda))
    conn.commit()
    conn.close()


def clear_price_cache():
    """Limpa todo o cache de preços."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM preco_cache")
    conn.commit()
    conn.close()
