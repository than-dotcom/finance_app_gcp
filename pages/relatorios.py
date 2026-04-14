"""
Página de Relatórios - Análises consolidadas e gráficos
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import database as db
import api_client as api
from datetime import datetime, timedelta

def render():
    st.title("📊 Relatórios")
    
    tab1, tab2, tab3 = st.tabs(["Performance", "Fluxo de Caixa", "Alocação"])
    
    with tab1:
        render_performance()
    
    with tab2:
        render_cashflow()
    
    with tab3:
        render_allocation()

def render_performance():
    """Ranking de performance dos ativos."""
    st.subheader("🏆 Performance dos Ativos")
    
    investments = db.get_investments()
    
    if not investments:
        st.info("📌 Nenhum investimento registrado.")
        return
    
    # Calcular performance
    data = []
    for inv in investments:
        preco_atual = api.get_current_price(inv["ticker"]) or inv["preco_medio"]
        valor_investido = inv["quantidade"] * inv["preco_medio"]
        valor_atual = inv["quantidade"] * preco_atual
        ganho = valor_atual - valor_investido
        rentabilidade = (ganho / valor_investido * 100) if valor_investido > 0 else 0
        
        data.append({
            "Ativo": inv["ticker"],
            "Nome": inv["nome"],
            "Tipo": inv["tipo"],
            "Qtd.": inv["quantidade"],
            "P. Médio": inv["preco_medio"],
            "P. Atual": preco_atual,
            "Valor Investido": valor_investido,
            "Valor Atual": valor_atual,
            "Ganho": ganho,
            "Rentabilidade %": rentabilidade
        })
    
    df = pd.DataFrame(data).sort_values("Rentabilidade %", ascending=False)
    
    # Exibir tabela
    df_display = df.copy()
    df_display["Valor Investido"] = df_display["Valor Investido"].apply(lambda x: api.format_currency(x))
    df_display["Valor Atual"] = df_display["Valor Atual"].apply(lambda x: api.format_currency(x))
    df_display["Ganho"] = df_display["Ganho"].apply(lambda x: api.format_currency(x))
    df_display["Rentabilidade %"] = df_display["Rentabilidade %"].apply(lambda x: f"{x:+.2f}%")
    
    st.dataframe(
        df_display[["Ativo", "Nome", "Qtd.", "P. Médio", "P. Atual", "Valor Investido", "Valor Atual", "Ganho", "Rentabilidade %"]],
        use_container_width=True,
        hide_index=True
    )
    
    # Gráfico de performance
    fig = px.bar(
        df,
        x="Ativo",
        y="Rentabilidade %",
        color="Rentabilidade %",
        color_continuous_scale=["#f85149", "#ffd700", "#3fb950"],
        title="Rentabilidade por Ativo (%)"
    )
    
    fig.update_layout(
        template="plotly_dark",
        height=400,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_cashflow():
    """Fluxo de caixa histórico."""
    st.subheader("💰 Fluxo de Caixa")
    
    transactions = db.get_transactions()
    
    if not transactions:
        st.info("📌 Nenhuma transação registrada.")
        return
    
    df = pd.DataFrame(transactions)
    df["data_transacao"] = pd.to_datetime(df["data_transacao"])
    df["mes"] = df["data_transacao"].dt.to_period("M")
    
    # Agrupar por mês
    df_monthly = df.groupby("mes").apply(
        lambda x: pd.Series({
            "Receitas": x[x["tipo"] == "receita"]["valor_brl"].sum(),
            "Despesas": x[x["tipo"] == "despesa"]["valor_brl"].sum(),
        })
    ).reset_index()
    
    df_monthly["Saldo"] = df_monthly["Receitas"] - df_monthly["Despesas"]
    df_monthly["mes"] = df_monthly["mes"].astype(str)
    
    # Gráfico
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_monthly["mes"],
        y=df_monthly["Receitas"],
        name="Receitas",
        marker_color="#3fb950"
    ))
    
    fig.add_trace(go.Bar(
        x=df_monthly["mes"],
        y=-df_monthly["Despesas"],
        name="Despesas",
        marker_color="#f85149"
    ))
    
    fig.update_layout(
        title="Fluxo de Caixa Mensal",
        xaxis_title="Mês",
        yaxis_title="Valor (BRL)",
        barmode="relative",
        template="plotly_dark",
        height=400,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela mensal
    st.subheader("Resumo Mensal")
    
    df_monthly_display = df_monthly.copy()
    df_monthly_display["Receitas"] = df_monthly_display["Receitas"].apply(lambda x: api.format_currency(x))
    df_monthly_display["Despesas"] = df_monthly_display["Despesas"].apply(lambda x: api.format_currency(x))
    df_monthly_display["Saldo"] = df_monthly_display["Saldo"].apply(lambda x: api.format_currency(x))
    
    st.dataframe(
        df_monthly_display[["mes", "Receitas", "Despesas", "Saldo"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "mes": st.column_config.TextColumn("Mês"),
            "Receitas": st.column_config.TextColumn("Receitas"),
            "Despesas": st.column_config.TextColumn("Despesas"),
            "Saldo": st.column_config.TextColumn("Saldo")
        }
    )

def render_allocation():
    """Alocação por tipo de ativo e moeda."""
    st.subheader("🥧 Alocação do Portfólio")
    
    investments = db.get_investments()
    
    if not investments:
        st.info("📌 Nenhum investimento registrado.")
        return
    
    df = pd.DataFrame(investments)
    df["valor"] = df.apply(
        lambda row: row["quantidade"] * (api.get_current_price(row["ticker"]) or row["preco_medio"]),
        axis=1
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Por tipo
        tipo_allocation = df.groupby("tipo")["valor"].sum()
        
        fig_tipo = go.Figure(data=[go.Pie(
            labels=tipo_allocation.index,
            values=tipo_allocation.values,
            marker=dict(colors=["#3fb950", "#58a6ff", "#79c0ff", "#d29922", "#f85149", "#a371f7", "#bc8ef9"])
        )])
        
        fig_tipo.update_layout(
            title="Alocação por Tipo",
            template="plotly_dark",
            height=400
        )
        
        st.plotly_chart(fig_tipo, use_container_width=True)
    
    with col2:
        # Por moeda
        moeda_allocation = df.groupby("moeda")["valor"].sum()
        
        fig_moeda = go.Figure(data=[go.Pie(
            labels=moeda_allocation.index,
            values=moeda_allocation.values,
            marker=dict(colors=["#3fb950", "#58a6ff", "#79c0ff"])
        )])
        
        fig_moeda.update_layout(
            title="Alocação por Moeda",
            template="plotly_dark",
            height=400
        )
        
        st.plotly_chart(fig_moeda, use_container_width=True)
    
    # Tabela de peso
    st.subheader("Peso de Cada Ativo")
    
    df["percentual"] = (df["valor"] / df["valor"].sum() * 100).round(2)
    df["valor_formatado"] = df["valor"].apply(lambda x: api.format_currency(x))
    
    df_display = df[["ticker", "nome", "tipo", "quantidade", "valor_formatado", "percentual"]].sort_values("valor", ascending=False)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ticker": st.column_config.TextColumn("Ticker"),
            "nome": st.column_config.TextColumn("Nome"),
            "tipo": st.column_config.TextColumn("Tipo"),
            "quantidade": st.column_config.NumberColumn("Qtd."),
            "valor_formatado": st.column_config.TextColumn("Valor"),
            "percentual": st.column_config.NumberColumn("% do Portfólio")
        }
    )
