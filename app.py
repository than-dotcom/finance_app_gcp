"""
FinTrack - Aplicativo de Gestão Financeira Pessoal
Desenvolvido com Streamlit + Supabase
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db
import api_client as api

# ============ CONFIGURAÇÃO DA PÁGINA ============
st.set_page_config(
    page_title="FinTrack",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ INICIALIZAÇÃO ============
# Inicializar cliente Supabase (cria tabelas se não existirem)
try:
    db.get_supabase_client()
except Exception as e:
    st.error(f"❌ Erro ao conectar ao Supabase: {str(e)}")
    st.stop()

# Tema dark via CSS customizado
st.markdown("""
    <style>
        :root {
            --primary-color: #3fb950;
            --background-color: #0d1117;
            --surface-color: #161b22;
            --text-color: #c9d1d9;
        }
        
        body {
            background-color: var(--background-color);
            color: var(--text-color);
        }
        
        .stApp {
            background-color: var(--background-color);
        }
        
        .metric-card {
            background-color: var(--surface-color);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--primary-color);
        }
    </style>
""", unsafe_allow_html=True)

# ============ SIDEBAR - NAVEGAÇÃO ============
st.sidebar.title("FinTrack 💰")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navegação",
    ["Dashboard", "Investimentos", "Despesas & Receitas", "Relatórios", "Configurações"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Dica:** Todos os valores são convertidos para BRL automaticamente.")

# ============ ROTEAMENTO DE PÁGINAS ============

if page == "Dashboard":
    from pages.dashboard import render
    render()

elif page == "Investimentos":
    from pages.investimentos import render
    render()

elif page == "Despesas & Receitas":
    from pages.despesas import render
    render()

elif page == "Relatórios":
    from pages.relatorios import render
    render()

elif page == "Configurações":
    from pages.configuracoes import render
    render()

# ============ FOOTER ============
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style='text-align: center; color: #8b949e; font-size: 12px;'>
    FinTrack v1.0 | Desenvolvido com ❤️<br>
    Dados persistidos em Supabase PostgreSQL
    </div>
    """,
    unsafe_allow_html=True
)
