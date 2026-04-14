"""
Página Dashboard - Visão geral financeira com Equity Curve
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import database as db
import api_client as api

def render():
    st.title("📊 Dashboard")
    
    # Obter dados
    investments = db.get_investments()
    transactions = db.get_transactions()
    snapshots = db.get_portfolio_snapshots()
    
    # ============ SALVAR SNAPSHOT DIÁRIO ============
    if investments:
        valor_total = sum(inv["quantidade"] * api.get_current_price(inv["ticker"]) or inv["preco_medio"] 
                         for inv in investments)
        db.save_daily_snapshot(valor_total)
    
    # ============ KPIs ============
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_investido = sum(inv["quantidade"] * inv["preco_medio"] for inv in investments)
        st.metric(
            "💼 Total Investido",
            api.format_currency(total_investido),
            delta=None
        )
    
    with col2:
        valor_atual = sum(inv["quantidade"] * (api.get_current_price(inv["ticker"]) or inv["preco_medio"]) 
                         for inv in investments)
        st.metric(
            "📈 Valor Atual",
            api.format_currency(valor_atual),
            delta=api.format_currency(valor_atual - total_investido)
        )
    
    with col3:
        receitas = sum(t["valor_brl"] for t in transactions if t["tipo"] == "receita")
        despesas = sum(t["valor_brl"] for t in transactions if t["tipo"] == "despesa")
        saldo = receitas - despesas
        st.metric(
            "💰 Saldo Mês",
            api.format_currency(saldo),
            delta=None
        )
    
    with col4:
        if snapshots and len(snapshots) >= 2:
            valor_hoje = snapshots[-1]["valor_total_brl"]
            valor_ontem = snapshots[-2]["valor_total_brl"]
            variacao = valor_hoje - valor_ontem
            st.metric(
                "📊 Variação Dia",
                api.format_currency(variacao),
                delta=f"{(variacao/valor_ontem*100):.2f}%" if valor_ontem > 0 else "0%"
            )
        else:
            st.metric("📊 Variação Dia", "N/A", delta=None)
    
    st.markdown("---")
    
    # ============ EQUITY CURVE ============
    st.subheader("📈 Evolução do Portfólio")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        periodo = st.selectbox(
            "Período",
            ["7 dias", "30 dias", "90 dias", "1 ano", "Tudo"],
            key="equity_curve_period"
        )
    
    with col1:
        if snapshots:
            df_snapshots = pd.DataFrame(snapshots)
            df_snapshots["data"] = pd.to_datetime(df_snapshots["data"])
            
            # Filtrar por período
            hoje = datetime.now()
            if periodo == "7 dias":
                df_snapshots = df_snapshots[df_snapshots["data"] >= hoje - timedelta(days=7)]
            elif periodo == "30 dias":
                df_snapshots = df_snapshots[df_snapshots["data"] >= hoje - timedelta(days=30)]
            elif periodo == "90 dias":
                df_snapshots = df_snapshots[df_snapshots["data"] >= hoje - timedelta(days=90)]
            elif periodo == "1 ano":
                df_snapshots = df_snapshots[df_snapshots["data"] >= hoje - timedelta(days=365)]
            
            # Gráfico
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_snapshots["data"],
                y=df_snapshots["valor_total_brl"],
                mode="lines+markers",
                name="Valor do Portfólio",
                line=dict(color="#3fb950", width=3),
                fill="tozeroy",
                fillcolor="rgba(63, 185, 80, 0.1)"
            ))
            
            fig.update_layout(
                title="Evolução do Patrimônio",
                xaxis_title="Data",
                yaxis_title="Valor (BRL)",
                hovermode="x unified",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📌 Nenhum snapshot de portfólio disponível ainda. Adicione investimentos para começar!")
    
    st.markdown("---")
    
    # ============ RESUMO DE TRANSAÇÕES RECENTES ============
    st.subheader("💳 Transações Recentes")
    
    if transactions:
        # Últimas 5 transações
        df_transactions = pd.DataFrame(transactions[-5:]).iloc[::-1]
        df_transactions["data_transacao"] = pd.to_datetime(df_transactions["data_transacao"])
        df_transactions["valor_formatado"] = df_transactions["valor_brl"].apply(lambda x: api.format_currency(x))
        
        st.dataframe(
            df_transactions[["data_transacao", "tipo", "categoria", "descricao", "valor_formatado"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "data_transacao": st.column_config.DateColumn("Data"),
                "tipo": st.column_config.TextColumn("Tipo"),
                "categoria": st.column_config.TextColumn("Categoria"),
                "descricao": st.column_config.TextColumn("Descrição"),
                "valor_formatado": st.column_config.TextColumn("Valor")
            }
        )
    else:
        st.info("📌 Nenhuma transação registrada ainda.")
    
    # ============ COMPOSIÇÃO DO PORTFÓLIO ============
    st.markdown("---")
    st.subheader("🥧 Composição do Portfólio")
    
    if investments:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza por tipo
            df_inv = pd.DataFrame(investments)
            df_inv["valor"] = df_inv.apply(
                lambda row: row["quantidade"] * (api.get_current_price(row["ticker"]) or row["preco_medio"]),
                axis=1
            )
            
            tipo_counts = df_inv.groupby("tipo")["valor"].sum()
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=tipo_counts.index,
                values=tipo_counts.values,
                marker=dict(colors=["#3fb950", "#58a6ff", "#79c0ff", "#d29922", "#f85149", "#a371f7", "#bc8ef9"])
            )])
            
            fig_pie.update_layout(
                title="Por Tipo de Ativo",
                template="plotly_dark",
                height=400
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Tabela de top 5 ativos
            st.write("**Top 5 Ativos**")
            df_top = df_inv.nlargest(5, "valor")[["ticker", "nome", "quantidade", "valor"]]
            df_top["valor_formatado"] = df_top["valor"].apply(lambda x: api.format_currency(x))
            df_top["percentual"] = (df_top["valor"] / df_top["valor"].sum() * 100).round(2).astype(str) + "%"
            
            st.dataframe(
                df_top[["ticker", "nome", "quantidade", "valor_formatado", "percentual"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ticker": st.column_config.TextColumn("Ticker"),
                    "nome": st.column_config.TextColumn("Nome"),
                    "quantidade": st.column_config.NumberColumn("Qtd."),
                    "valor_formatado": st.column_config.TextColumn("Valor"),
                    "percentual": st.column_config.TextColumn("%")
                }
            )
    else:
        st.info("📌 Nenhum investimento registrado ainda.")
