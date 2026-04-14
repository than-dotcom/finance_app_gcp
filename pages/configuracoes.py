"""
Página de Configurações - Preferências e gerenciamento de dados
"""

import streamlit as st
import json
import database as db
from datetime import datetime

def render():
    st.title("⚙️ Configurações")
    
    tab1, tab2, tab3 = st.tabs(["Preferências", "Dados", "Sobre"])
    
    with tab1:
        render_preferences()
    
    with tab2:
        render_data_management()
    
    with tab3:
        render_about()

def render_preferences():
    """Configurações de preferências."""
    st.subheader("🎨 Preferências")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Tema**")
        tema = st.radio(
            "Selecione o tema",
            ["Escuro (Padrão)", "Claro"],
            horizontal=True,
            key="tema_config"
        )
        st.info("💡 O tema escuro é otimizado para reduzir fadiga ocular.")
    
    with col2:
        st.write("**Moeda Base**")
        moeda_base = st.selectbox(
            "Moeda padrão para exibição",
            ["BRL", "USD", "EUR"],
            key="moeda_base_config"
        )
        st.info("💡 Todos os valores serão exibidos nesta moeda.")
    
    st.markdown("---")
    
    st.subheader("📊 Cotações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        atualizar_cache = st.button("🔄 Limpar Cache de Preços", use_container_width=True)
        if atualizar_cache:
            db.clear_price_cache()
            st.success("✅ Cache de preços limpo! Os preços serão atualizados na próxima consulta.")
    
    with col2:
        st.write("")
        st.write("")
        st.info("💡 O cache de preços é atualizado a cada 5 minutos automaticamente.")

def render_data_management():
    """Gerenciamento de dados."""
    st.subheader("💾 Gerenciamento de Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Exportar Dados**")
        
        if st.button("📥 Exportar como JSON", use_container_width=True):
            # Preparar dados para exportação
            data = {
                "exportado_em": datetime.now().isoformat(),
                "investimentos": db.get_investments(),
                "transacoes": db.get_transactions(),
                "snapshots": db.get_portfolio_snapshots()
            }
            
            # Converter para JSON serializável
            data_json = json.dumps(data, indent=2, default=str)
            
            st.download_button(
                label="💾 Baixar JSON",
                data=data_json,
                file_name=f"fintrack_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
            
            st.success("✅ Dados prontos para download!")
    
    with col2:
        st.write("**Importar Dados**")
        
        uploaded_file = st.file_uploader(
            "Selecione um arquivo JSON para importar",
            type="json",
            key="import_file"
        )
        
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                
                st.warning("⚠️ Importar dados vai sobrescrever os dados existentes!")
                
                if st.button("📤 Confirmar Importação", type="primary", use_container_width=True):
                    # Aqui você implementaria a lógica de importação
                    st.info("💡 Funcionalidade de importação será implementada em breve.")
                    
            except json.JSONDecodeError:
                st.error("❌ Arquivo JSON inválido!")
    
    st.markdown("---")
    
    st.subheader("🗑️ Dados Perigosos")
    
    if st.button("🗑️ Limpar Todos os Dados", type="secondary", use_container_width=True):
        st.warning("⚠️ Esta ação é irreversível! Todos os dados serão deletados.")
        
        if st.button("🔴 Confirmar Exclusão de Todos os Dados", type="primary", use_container_width=True):
            # Aqui você implementaria a lógica de limpeza
            st.error("❌ Funcionalidade de limpeza será implementada em breve.")

def render_about():
    """Informações sobre o app."""
    st.subheader("ℹ️ Sobre o FinTrack")
    
    st.markdown("""
    ### FinTrack v1.0
    
    **Aplicativo de Gestão Financeira Pessoal**
    
    FinTrack é um aplicativo web desenvolvido com Streamlit que permite rastrear seus investimentos, 
    despesas e receitas em um único lugar.
    
    #### Recursos Principais
    
    - 📈 **Dashboard com Equity Curve**: Acompanhe a evolução do seu patrimônio ao longo do tempo
    - 💼 **Gestão de Investimentos**: Rastreie ações, ETFs, FIIs, criptomoedas e mais
    - 💳 **Despesas e Receitas**: Categorize e acompanhe suas transações
    - 📊 **Relatórios Consolidados**: Análises de performance, fluxo de caixa e alocação
    - 💱 **Conversão Automática**: Todas as transações são convertidas para BRL
    - 🔄 **Cotações em Tempo Real**: Integração com Finnhub API
    - 💾 **Persistência SQLite**: Seus dados são salvos localmente
    
    #### Tecnologias
    
    - **Frontend**: Streamlit
    - **Backend**: Python
    - **Banco de Dados**: SQLite
    - **APIs**: Finnhub, ExchangeRate-API
    
    #### Contato
    
    Para dúvidas ou sugestões, entre em contato através do GitHub.
    """)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Versão", "1.0.0")
    
    with col2:
        st.metric("Banco de Dados", "SQLite")
    
    with col3:
        st.metric("Última Atualização", datetime.now().strftime("%d/%m/%Y"))
