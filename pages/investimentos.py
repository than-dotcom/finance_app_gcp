"""
Página de Investimentos - CRUD de ativos com cotações em tempo real
"""

import streamlit as st
import pandas as pd
import database as db\nimport api_client as api
from datetime import datetime

# Dados de exemplo para autocomplete
ASSET_TYPES = {
    "acao_br": "🇧🇷 Ação BR (B3)",\n    "acao_us": "🇺🇸 Ação EUA",
    "acao_eu": "🇪🇺 Ação Europa",
    "etf": "📊 ETF",
    "fii": "🏢 FII",
    "cripto": "₿ Criptomoeda",
    "tesouro": "🏛️ Tesouro Direto",
    "outro": "📌 Outro"
}

POPULAR_ASSETS = {
    "PETR3": {"nome": "Petrobras", "tipo": "acao_br"},
    "VALE3": {"nome": "Vale", "tipo": "acao_br"},
    "WEGE3": {"nome": "WEG", "tipo": "acao_br"},
    "ITUB4": {"nome": "Itaú", "tipo": "acao_br"},
    "BBDC4": {"nome": "Bradesco", "tipo": "acao_br"},
    "AAPL": {"nome": "Apple", "tipo": "acao_us"},
    "MSFT": {"nome": "Microsoft", "tipo": "acao_us"},
    "GOOGL": {"nome": "Google", "tipo": "acao_us"},
    "TSLA": {"nome": "Tesla", "tipo": "acao_us"},
    "NVDA": {"nome": "NVIDIA", "tipo": "acao_us"},
    "BTC": {"nome": "Bitcoin", "tipo": "cripto"},
    "ETH": {"nome": "Ethereum", "tipo": "cripto"},
}

def render():
    st.title("📈 Investimentos")
    
    # Abas
    tab1, tab2 = st.tabs(["Meus Ativos", "Adicionar Novo"])
    
    with tab1:
        render_investments_list()
    
    with tab2:
        render_add_investment()

def render_investments_list():
    """Exibe lista de investimentos com cotações e rentabilidade."""
    investments = db.get_investments()
    
    if not investments:
        st.info("📌 Nenhum investimento registrado. Adicione um novo ativo na aba 'Adicionar Novo'!")
        return
    
    # Preparar dados
    data = []
    for inv in investments:
        preco_atual = api.get_current_price(inv["ticker"]) or inv["preco_medio"]
        valor_total = inv["quantidade"] * preco_atual
        rentabilidade = ((preco_atual - inv["preco_medio"]) / inv["preco_medio"] * 100) if inv["preco_medio"] > 0 else 0
        
        data.append({
            "Ativo": inv["ticker"],
            "Nome": inv["nome"],
            "Qtd.": inv["quantidade"],
            "P. Médio (R$)": f"R$ {inv['preco_medio']:.2f}",
            "P. Atual (R$)": f"R$ {preco_atual:.2f}",
            "Rentab. %": f"{rentabilidade:+.2f}%",
            "Valor (R$)": f"R$ {valor_total:,.2f}",
            "Tipo": ASSET_TYPES.get(inv["tipo"], inv["tipo"]),
            "ID": inv["id"]
        })
    
    df = pd.DataFrame(data)
    
    # Exibir tabela
    st.dataframe(
        df.drop("ID", axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ativo": st.column_config.TextColumn("Ativo", width="small"),
            "Nome": st.column_config.TextColumn("Nome"),
            "Qtd.": st.column_config.NumberColumn("Qtd."),
            "P. Médio (R$)": st.column_config.TextColumn("P. Médio"),
            "P. Atual (R$)": st.column_config.TextColumn("P. Atual"),
            "Rentab. %": st.column_config.TextColumn("Rentab. %"),
            "Valor (R$)": st.column_config.TextColumn("Valor Total"),
            "Tipo": st.column_config.TextColumn("Tipo")
        }
    )
    
    # Ações
    st.markdown("---")
    st.subheader("⚙️ Gerenciar Ativos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ticker_to_edit = st.selectbox(
            "Selecione um ativo para editar",
            [inv["ticker"] for inv in investments],
            key="edit_select"
        )
        
        if ticker_to_edit:
            inv = next(i for i in investments if i["ticker"] == ticker_to_edit)
            
            col_a, col_b = st.columns(2)
            with col_a:
                nova_quantidade = st.number_input(
                    "Nova Quantidade",
                    value=inv["quantidade"],
                    min_value=0.0,
                    step=0.01,
                    key="edit_qtd"
                )
            
            with col_b:
                novo_preco = st.number_input(
                    "Novo Preço Médio (R$)",
                    value=inv["preco_medio"],
                    min_value=0.0,
                    step=0.01,
                    key="edit_price"
                )
            
            novas_notas = st.text_area(
                "Notas",
                value=inv["notas"] or "",
                key="edit_notes"
            )
            
            if st.button("✏️ Atualizar", key="btn_update"):
                db.update_investment(ticker_to_edit, nova_quantidade, novo_preco, novas_notas)
                st.success(f"✅ {ticker_to_edit} atualizado com sucesso!")
                st.rerun()
    
    with col2:
        ticker_to_delete = st.selectbox(
            "Selecione um ativo para deletar",
            [inv["ticker"] for inv in investments],
            key="delete_select"
        )
        
        if ticker_to_delete:
            if st.button("🗑️ Deletar", key="btn_delete", type="secondary"):
                db.delete_investment(ticker_to_delete)
                st.success(f"✅ {ticker_to_delete} deletado com sucesso!")
                st.rerun()

def render_add_investment():
    """Formulário para adicionar novo investimento."""
    st.subheader("Adicionar Novo Investimento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Busca de ativo com autocomplete
        ticker = st.text_input(
            "Ticker (ex: PETR3, AAPL, BTC)",
            placeholder="Digite o ticker...",
            key="new_ticker"
        ).upper()
        
        # Mostrar sugestões
        if ticker:
            sugestoes = [t for t in POPULAR_ASSETS.keys() if ticker in t]
            if sugestoes:
                st.caption("Sugestões:")
                for sug in sugestoes[:5]:
                    if st.button(f"{sug} - {POPULAR_ASSETS[sug]['nome']}", key=f"sug_{sug}"):
                        ticker = sug
                        st.session_state.new_ticker = sug
    
    with col2:
        tipo = st.selectbox(
            "Tipo de Ativo",
            list(ASSET_TYPES.keys()),
            format_func=lambda x: ASSET_TYPES[x],
            key="new_tipo"
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        quantidade = st.number_input(
            "Quantidade",
            min_value=0.0,
            value=1.0,
            step=0.01,
            key="new_qtd"
        )
    
    with col2:
        preco_medio = st.number_input(
            "Preço Médio (R$)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            key="new_price"
        )
    
    # Preview de preço atual
    if ticker:
        preco_atual = api.get_current_price(ticker)
        if preco_atual:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Preço Atual", api.format_currency(preco_atual))
            with col2:
                valor_total = quantidade * preco_atual
                st.metric("Valor Total", api.format_currency(valor_total))
            
            # Atualizar preço médio com preço atual
            if st.button("💡 Usar preço atual como preço médio"):
                st.session_state.new_price = preco_atual
                st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        data_compra = st.date_input(
            "Data de Compra",
            key="new_data"
        )
    
    with col2:
        notas = st.text_area(
            "Notas",
            placeholder="Adicione observações sobre este investimento...",
            key="new_notas"
        )
    
    # Botão de envio
    if st.button("➕ Adicionar Investimento", type="primary", use_container_width=True):
        if not ticker:
            st.error("❌ Por favor, insira um ticker!")
        elif quantidade <= 0:
            st.error("❌ Quantidade deve ser maior que 0!")
        else:
            success = db.add_investment(
                ticker=ticker,
                nome=POPULAR_ASSETS.get(ticker, {}).get("nome", ticker),
                tipo=tipo,
                quantidade=quantidade,
                preco_medio=preco_medio,
                data_compra=str(data_compra),
                notas=notas
            )
            
            if success:
                st.success(f"✅ {ticker} adicionado com sucesso!")
                st.rerun()
            else:
                st.error(f"❌ {ticker} já existe no portfólio!")
