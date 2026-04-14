"""
Página de Despesas e Receitas - Rastreamento com conversão automática para BRL
"""

import streamlit as st
import pandas as pd
import database as db
import api_client as api
from datetime import datetime, timedelta

CATEGORIAS_DESPESA = [
    "Alimentação", "Transporte", "Moradia", "Saúde", "Educação",
    "Entretenimento", "Compras", "Assinaturas", "Seguros", "Impostos",
    "Investimentos", "Outro"
]

CATEGORIAS_RECEITA = [
    "Salário", "Freelance", "Investimentos", "Bônus", "Presente",
    "Reembolso", "Outro"
]

MOEDAS = ["BRL", "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"]

def render():
    st.title("💳 Despesas & Receitas")
    
    tab1, tab2 = st.tabs(["Histórico", "Adicionar Nova"])
    
    with tab1:
        render_transactions_history()
    
    with tab2:
        render_add_transaction()

def render_transactions_history():
    """Exibe histórico de transações com filtros."""
    transactions = db.get_transactions()
    
    if not transactions:
        st.info("📌 Nenhuma transação registrada ainda.")
        return
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_filtro = st.selectbox(
            "Tipo",
            ["Todos", "Despesa", "Receita"],
            key="filter_tipo"
        )
    
    with col2:
        categoria_filtro = st.selectbox(
            "Categoria",
            ["Todas"] + CATEGORIAS_DESPESA + CATEGORIAS_RECEITA,
            key="filter_categoria"
        )
    
    with col3:
        periodo = st.selectbox(
            "Período",
            ["Tudo", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias"],
            key="filter_periodo"
        )
    
    # Aplicar filtros
    df = pd.DataFrame(transactions)
    df["data_transacao"] = pd.to_datetime(df["data_transacao"])
    
    if tipo_filtro != "Todos":
        df = df[df["tipo"] == tipo_filtro.lower()]
    
    if categoria_filtro != "Todas":
        df = df[df["categoria"] == categoria_filtro]
    
    if periodo != "Tudo":
        hoje = datetime.now()
        if periodo == "Últimos 7 dias":
            df = df[df["data_transacao"] >= hoje - timedelta(days=7)]
        elif periodo == "Últimos 30 dias":
            df = df[df["data_transacao"] >= hoje - timedelta(days=30)]
        elif periodo == "Últimos 90 dias":
            df = df[df["data_transacao"] >= hoje - timedelta(days=90)]
    
    # Ordenar por data descendente
    df = df.sort_values("data_transacao", ascending=False)
    
    # Exibir resumo
    col1, col2, col3 = st.columns(3)
    
    despesas = df[df["tipo"] == "despesa"]["valor_brl"].sum()
    receitas = df[df["tipo"] == "receita"]["valor_brl"].sum()
    saldo = receitas - despesas
    
    with col1:
        st.metric("💰 Receitas", api.format_currency(receitas))
    
    with col2:
        st.metric("💸 Despesas", api.format_currency(despesas))
    
    with col3:
        st.metric("📊 Saldo", api.format_currency(saldo))
    
    st.markdown("---")
    
    # Tabela de transações
    df["valor_formatado"] = df["valor_brl"].apply(lambda x: api.format_currency(x))
    df["tipo_emoji"] = df["tipo"].apply(lambda x: "📈" if x == "receita" else "📉")
    
    st.dataframe(
        df[["data_transacao", "tipo_emoji", "categoria", "descricao", "valor_formatado"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "data_transacao": st.column_config.DateColumn("Data"),
            "tipo_emoji": st.column_config.TextColumn(""),
            "categoria": st.column_config.TextColumn("Categoria"),
            "descricao": st.column_config.TextColumn("Descrição"),
            "valor_formatado": st.column_config.TextColumn("Valor")
        }
    )
    
    # Ações
    st.markdown("---")
    st.subheader("⚙️ Gerenciar Transações")
    
    if len(df) > 0:
        transaction_to_delete = st.selectbox(
            "Selecione uma transação para deletar",
            df["id"].tolist(),
            format_func=lambda x: f"{df[df['id']==x]['data_transacao'].values[0]} - {df[df['id']==x]['descricao'].values[0]}",
            key="delete_transaction"
        )
        
        if st.button("🗑️ Deletar Transação", type="secondary"):
            db.delete_transaction(transaction_to_delete)
            st.success("✅ Transação deletada com sucesso!")
            st.rerun()

def render_add_transaction():
    """Formulário para adicionar nova transação."""
    st.subheader("Adicionar Nova Transação")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tipo = st.radio(
            "Tipo",
            ["Despesa", "Receita"],
            horizontal=True,
            key="new_tipo"
        ).lower()
    
    with col2:
        categorias = CATEGORIAS_DESPESA if tipo == "despesa" else CATEGORIAS_RECEITA
        categoria = st.selectbox(
            "Categoria",
            categorias,
            key="new_categoria"
        )
    
    descricao = st.text_input(
        "Descrição",
        placeholder="Ex: Compra no supermercado",
        key="new_descricao"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        moeda = st.selectbox(
            "Moeda",
            MOEDAS,
            key="new_moeda"
        )
    
    with col2:
        valor = st.number_input(
            "Valor",
            min_value=0.0,
            value=0.0,
            step=0.01,
            key="new_valor"
        )
    
    with col3:
        data = st.date_input(
            "Data",
            key="new_data"
        )
    
    # Preview de conversão
    if valor > 0 and moeda != "BRL":
        valor_brl, taxa = api.convert_to_brl(valor, moeda)
        st.info(f"💱 {valor} {moeda} = {api.format_currency(valor_brl)} (Taxa: {taxa:.4f})")
    elif valor > 0:
        valor_brl = valor
        st.info(f"✅ Valor: {api.format_currency(valor_brl)}")
    
    notas = st.text_area(
        "Notas",
        placeholder="Adicione observações...",
        key="new_notas"
    )
    
    # Botão de envio
    if st.button("➕ Adicionar Transação", type="primary", use_container_width=True):
        if not descricao:
            st.error("❌ Por favor, insira uma descrição!")
        elif valor <= 0:
            st.error("❌ Valor deve ser maior que 0!")
        else:
            # Converter para BRL
            if moeda == "BRL":
                valor_brl = valor
            else:
                valor_brl, _ = api.convert_to_brl(valor, moeda)
            
            db.add_transaction(
                tipo=tipo,
                categoria=categoria,
                valor_brl=valor_brl,
                data_transacao=str(data),
                descricao=descricao,
                notas=notas
            )
            
            st.success(f"✅ Transação adicionada com sucesso! ({api.format_currency(valor_brl)})")
            st.rerun()
