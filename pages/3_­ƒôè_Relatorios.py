"""
pages/3_📊_Relatorios.py
Relatórios consolidados: patrimônio líquido, fluxo de caixa, ranking de ativos.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from utils.data_manager import (
    get_investimentos, get_transacoes, get_settings,
    TIPOS_INVESTIMENTO, SIMBOLOS_MOEDA,
)
from utils.market_data import (
    get_taxas_cambio, enriquecer_investimento,
    converter_para_brl,
)

st.set_page_config(page_title="Relatórios · FinTrack", page_icon="📊", layout="wide")
st.markdown("""
<style>
.block-container { padding-top: 1.2rem !important; }
.chart-panel { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 1.2rem 1.4rem; margin-bottom: 1rem; }
</style>""", unsafe_allow_html=True)

settings   = get_settings()
moeda_base = settings.get("moeda_base", "BRL")
taxas      = get_taxas_cambio(moeda_base)
simbolo    = SIMBOLOS_MOEDA.get(moeda_base, "R$")

def fmt(v): return f"{simbolo} {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

st.markdown("## 📊 Relatórios Financeiros")
st.caption("Visão consolidada do seu patrimônio, fluxo de caixa e performance dos ativos.")
st.divider()

with st.spinner("Calculando..."):
    investimentos_raw = get_investimentos()
    investimentos = [enriquecer_investimento(inv, taxas) for inv in investimentos_raw]
    transacoes = get_transacoes()
    for t in transacoes:
        t["valor_brl"] = converter_para_brl(float(t.get("valor", 0)), t.get("moeda", "BRL"), taxas)
        t["data_dt"]   = datetime.strptime(t.get("data", "2000-01-01"), "%Y-%m-%d")

# ─── KPIs GERAIS ──────────────────────────────────────────────────────────────
pat   = sum(i["valor_atual_brl"] for i in investimentos)
custo = sum(i["custo_brl"] for i in investimentos)
ret   = pat - custo
ret_p = (ret / custo * 100) if custo else 0

total_desp = sum(t["valor_brl"] for t in transacoes if t.get("tipo") == "despesa")
total_rec  = sum(t["valor_brl"] for t in transacoes if t.get("tipo") == "receita")
patrim_liq = pat + (total_rec - total_desp)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Patrimônio Investido", fmt(pat), f"{ret_p:+.1f}%")
c2.metric("Retorno Total", fmt(ret))
c3.metric("Saldo Histórico (receitas - desp)", fmt(total_rec - total_desp))
c4.metric("Total Investido (custo)", fmt(custo))

st.markdown("<br>", unsafe_allow_html=True)

# ─── RANKING DE ATIVOS ────────────────────────────────────────────────────────
st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
st.markdown("**Ranking de Performance dos Ativos**")

if investimentos:
    df_rank = pd.DataFrame([{
        "nome"        : inv.get("nome", inv.get("ticker","—")),
        "tipo"        : TIPOS_INVESTIMENTO.get(inv["tipo"], inv["tipo"]),
        "valor_atual" : inv["valor_atual_brl"],
        "retorno_brl" : inv["retorno_brl"],
        "retorno_pct" : inv["retorno_pct"],
        "peso_pct"    : (inv["valor_atual_brl"] / pat * 100) if pat else 0,
    } for inv in investimentos]).sort_values("retorno_pct", ascending=False)

    cores_bar = ["#3fb950" if v >= 0 else "#f85149" for v in df_rank["retorno_pct"]]
    fig_rank = go.Figure(go.Bar(
        x=df_rank["nome"],
        y=df_rank["retorno_pct"],
        marker_color=cores_bar,
        text=[f"{v:+.1f}%" for v in df_rank["retorno_pct"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Retorno: %{y:.1f}%<extra></extra>",
    ))
    fig_rank.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9", height=280,
        margin=dict(l=0,r=0,t=20,b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#21262d", ticksuffix="%", zeroline=True, zerolinecolor="#30363d"),
    )
    st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ─── FLUXO DE CAIXA MENSAL ────────────────────────────────────────────────────
if transacoes:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown("**Fluxo de Caixa Histórico**")

    df_t = pd.DataFrame(transacoes)
    df_t["mes"] = df_t["data_dt"].dt.to_period("M").astype(str)
    df_mes = df_t.groupby(["mes","tipo"])["valor_brl"].sum().unstack(fill_value=0).reset_index()
    if "receita" not in df_mes.columns: df_mes["receita"] = 0
    if "despesa" not in df_mes.columns: df_mes["despesa"] = 0
    df_mes["saldo"] = df_mes["receita"] - df_mes["despesa"]

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Bar(x=df_mes["mes"], y=df_mes["receita"],
                            name="Receita", marker_color="#3fb950", opacity=0.8))
    fig_fc.add_trace(go.Bar(x=df_mes["mes"], y=-df_mes["despesa"],
                            name="Despesa", marker_color="#f85149", opacity=0.8))
    fig_fc.add_trace(go.Scatter(x=df_mes["mes"], y=df_mes["saldo"],
                                name="Saldo", line=dict(color="#e3b341", width=2.5),
                                mode="lines+markers"))
    fig_fc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9", height=280, barmode="overlay",
        margin=dict(l=0,r=0,t=10,b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#21262d"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_fc, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

# ─── ALOCAÇÃO DETALHADA ───────────────────────────────────────────────────────
if investimentos:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.markdown("**Alocação por Moeda**")
        df_moeda = (
            pd.DataFrame([{"moeda": i.get("moeda","BRL"), "valor": i["valor_atual_brl"]}
                          for i in investimentos])
            .groupby("moeda")["valor"].sum().reset_index()
        )
        fig_m = go.Figure(go.Pie(
            labels=df_moeda["moeda"], values=df_moeda["valor"],
            hole=0.5, textinfo="label+percent",
            marker_colors=["#388bfd","#3fb950","#e3b341","#f85149","#bc8cff"],
        ))
        fig_m.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_color="#c9d1d9",
            height=250, margin=dict(l=0,r=0,t=10,b=0), showlegend=False,
        )
        st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.markdown("**Peso na Carteira (%)**")
        df_peso = pd.DataFrame([{
            "Ativo" : inv.get("nome", inv.get("ticker","—")),
            "Peso %": round((inv["valor_atual_brl"] / pat * 100) if pat else 0, 1),
            "Valor" : fmt(inv["valor_atual_brl"]),
        } for inv in sorted(investimentos, key=lambda x: -x["valor_atual_brl"])])

        st.dataframe(df_peso, use_container_width=True, hide_index=True,
                     height=min(300, 50 + len(df_peso)*35))
        st.markdown('</div>', unsafe_allow_html=True)
