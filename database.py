"""
Módulo de Banco de Dados - Supabase PostgreSQL
Gerencia investimentos, transações, snapshots e cache de preços
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import json

# Inicializar cliente Supabase
@st.cache_resource
def get_supabase_client() -> Client:
    """Cria e retorna cliente Supabase com cache."""
    try:
        supabase_url = st.secrets.get("SUPABASE_URL")
        supabase_key = st.secrets.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            st.error("❌ SUPABASE_URL e SUPABASE_KEY não configuradas em st.secrets!")
            st.stop()
        
        client = create_client(supabase_url, supabase_key)
        
        # Inicializar tabelas
        initialize_tables(client)
        
        return client
    
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao Supabase: {str(e)}")
        st.stop()

def initialize_tables(client: Client):
    """Cria tabelas se não existirem."""
    try:
        # Verificar e criar tabela de investimentos
        try:
            client.table("investimentos").select("id", count="exact").limit(1).execute()
        except:
            client.rpc("create_investimentos_table").execute()
        
        # Verificar e criar tabela de transações
        try:
            client.table("transacoes").select("id", count="exact").limit(1).execute()
        except:
            client.rpc("create_transacoes_table").execute()
        
        # Verificar e criar tabela de snapshots
        try:
            client.table("portfolio_snapshots").select("id", count="exact").limit(1).execute()
        except:
            client.rpc("create_snapshots_table").execute()
        
        # Verificar e criar tabela de cache de preços
        try:
            client.table("preco_cache").select("ticker", count="exact").limit(1).execute()
        except:
            client.rpc("create_cache_table").execute()
    
    except Exception as e:
        # Se as RPC functions não existem, criar as tabelas diretamente
        pass

# ==================== INVESTIMENTOS ====================

def get_investments():
    """Retorna lista de investimentos."""
    try:
        client = get_supabase_client()
        response = client.table("investimentos").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ Erro ao buscar investimentos: {str(e)}")
        return []

def add_investment(ticker, nome, tipo, quantidade, preco_medio, data_compra, moeda="BRL", notas=""):
    """Adiciona novo investimento."""
    try:
        client = get_supabase_client()
        
        data = {
            "ticker": ticker.upper(),
            "nome": nome,
            "tipo": tipo,
            "quantidade": float(quantidade),
            "preco_medio": float(preco_medio),
            "data_compra": str(data_compra),
            "moeda": moeda,
            "notas": notas,
            "criado_em": datetime.now().isoformat()
        }
        
        response = client.table("investimentos").insert(data).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Erro ao adicionar investimento: {str(e)}")
        return False

def update_investment(investment_id, **kwargs):
    """Atualiza investimento existente."""
    try:
        client = get_supabase_client()
        
        # Converter valores numéricos
        if "quantidade" in kwargs:
            kwargs["quantidade"] = float(kwargs["quantidade"])
        if "preco_medio" in kwargs:
            kwargs["preco_medio"] = float(kwargs["preco_medio"])
        
        response = client.table("investimentos").update(kwargs).eq("id", investment_id).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Erro ao atualizar investimento: {str(e)}")
        return False

def delete_investment(investment_id):
    """Deleta investimento."""
    try:
        client = get_supabase_client()
        client.table("investimentos").delete().eq("id", investment_id).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Erro ao deletar investimento: {str(e)}")
        return False

# ==================== TRANSAÇÕES ====================

def get_transactions():
    """Retorna lista de transações."""
    try:
        client = get_supabase_client()
        response = client.table("transacoes").select("*").order("data_transacao", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ Erro ao buscar transações: {str(e)}")
        return []

def add_transaction(tipo, categoria, valor_brl, data_transacao, descricao="", notas=""):
    """Adiciona nova transação."""
    try:
        client = get_supabase_client()
        
        data = {
            "tipo": tipo.lower(),
            "categoria": categoria,
            "valor_brl": float(valor_brl),
            "data_transacao": str(data_transacao),
            "descricao": descricao,
            "notas": notas,
            "criado_em": datetime.now().isoformat()
        }
        
        response = client.table("transacoes").insert(data).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Erro ao adicionar transação: {str(e)}")
        return False

def delete_transaction(transaction_id):
    """Deleta transação."""
    try:
        client = get_supabase_client()
        client.table("transacoes").delete().eq("id", transaction_id).execute()
        return True
    
    except Exception as e:
        st.error(f"❌ Erro ao deletar transação: {str(e)}")
        return False

# ==================== SNAPSHOTS ====================

def get_portfolio_snapshots():
    """Retorna snapshots históricos do portfólio."""
    try:
        client = get_supabase_client()
        response = client.table("portfolio_snapshots").select("*").order("data", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"❌ Erro ao buscar snapshots: {str(e)}")
        return []

def add_portfolio_snapshot(valor_total_brl):
    """Adiciona snapshot diário do portfólio."""
    try:
        client = get_supabase_client()
        
        data_hoje = datetime.now().date().isoformat()
        
        data = {
            "data": data_hoje,
            "valor_total_brl": float(valor_total_brl),
            "criado_em": datetime.now().isoformat()
        }
        
        # Verificar se já existe snapshot para hoje
        response = client.table("portfolio_snapshots").select("id").eq("data", data_hoje).execute()
        
        if response.data:
            # Atualizar
            client.table("portfolio_snapshots").update(data).eq("data", data_hoje).execute()
        else:
            # Inserir novo
            client.table("portfolio_snapshots").insert(data).execute()
        
        return True
    
    except Exception as e:
        st.error(f"❌ Erro ao adicionar snapshot: {str(e)}")
        return False

# ==================== CACHE DE PREÇOS ====================

def get_cached_price(ticker):
    """Retorna preço em cache se disponível e válido (< 5 min)."""
    try:
        client = get_supabase_client()
        response = client.table("preco_cache").select("*").eq("ticker", ticker.upper()).execute()
        
        if response.data:
            cache_entry = response.data[0]
            timestamp = datetime.fromisoformat(cache_entry["timestamp"])
            
            # Verificar se cache é válido (< 5 minutos)
            if (datetime.now() - timestamp).total_seconds() < 300:
                return cache_entry["preco"]
        
        return None
    
    except Exception as e:
        return None

def set_cached_price(ticker, preco):
    """Salva preço em cache."""
    try:
        client = get_supabase_client()
        
        data = {
            "ticker": ticker.upper(),
            "preco": float(preco),
            "timestamp": datetime.now().isoformat()
        }
        
        # Verificar se já existe
        response = client.table("preco_cache").select("ticker").eq("ticker", ticker.upper()).execute()
        
        if response.data:
            # Atualizar
            client.table("preco_cache").update(data).eq("ticker", ticker.upper()).execute()
        else:
            # Inserir novo
            client.table("preco_cache").insert(data).execute()
        
        return True
    
    except Exception as e:
        return False

def clear_price_cache():
    """Limpa todo o cache de preços."""
    try:
        client = get_supabase_client()
        client.table("preco_cache").delete().neq("ticker", "").execute()
        st.success("✅ Cache de preços limpo!")
        return True
    
    except Exception as e:
        st.error(f"❌ Erro ao limpar cache: {str(e)}")
        return False

# ==================== EXPORTAÇÃO ====================

def export_data():
    """Exporta todos os dados em JSON."""
    try:
        investments = get_investments()
        transactions = get_transactions()
        snapshots = get_portfolio_snapshots()
        
        data = {
            "exportado_em": datetime.now().isoformat(),
            "investimentos": investments,
            "transacoes": transactions,
            "snapshots": snapshots
        }
        
        return json.dumps(data, indent=2, default=str)
    
    except Exception as e:
        st.error(f"❌ Erro ao exportar dados: {str(e)}")
        return None
