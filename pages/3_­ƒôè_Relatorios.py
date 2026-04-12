"""
pages/3_📊_Relatorios.py
Relatórios consolidados.
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
    get_taxas_cambio, enriquecer_investimento, converter_para_brl,
)

st.set_page_config(page_title="Relatórios · FinTrack", page_icon="📊", layout="wide")

P_GREEN="#86efac"; P_RED="#fca5a5"; P_BLUE="#93c5fd"
P_YELLOW="#fde68a"; P_PURPLE="#c4b5fd"; P_TEAL="#5eead4"
TEXT_SEC="#8b949e"; TEXT_PRI="#e6edf3"

st.markdown(f"""<style>
.block-container{{padding-top:1rem!important}}
.panel{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1rem}}
.panel-title{{color:{TEXT_SEC};font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;font-weight:600;margin-bottom:1rem}}
</style>""", unsafe_allow_html=True)

settings   = get_settings()
moeda_base = settings.get("moeda_base","BRL")
taxas_brl  = get_taxas_cambio("BRL")
simbolo    = SIMBOLOS_MOEDA.get(moeda_base,"R$")

def fmt(v): return f"{simbolo} {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

st.markdown("## 📊 Relatórios Financeiros")
st.caption("Visão consolidada: patrimônio, fluxo de caixa e performance dos ativos.")
st.divider()

with st.spinner("Calculando..."):
    raw = get_investimentos()
    investimentos = [enriquecer_investimento(inv, taxas_brl) for inv in raw]
    transacoes = get_transacoes()
    for t in transacoes:
        t["valor_brl"] = converter_para_brl(float(t.get("valor",0)), t.get("moeda","BRL"), taxas_brl)
        t["data_dt"]   = datetime.strptime(t.get("data","2000-01-01"),"%Y-%m-%d")

pat   = sum(i["valor_atual_brl"] for i in investimentos)
custo = sum(i["custo_brl"] for i in investimentos)
ret   = pat - custo
ret_p = (ret / custo * 100) if custo else 0
total_desp = sum(t["valor_brl"] for t in transacoes if t.get("tipo")=="despesa")
total_rec  = sum(t["valor_brl"] for t in transacoes if t.get("tipo")=="receita")
saldo_hist = total_rec - total_desp

# Ilha KPI 4 células
cor_r = P_GREEN if ret >= 0 else P_RED
bg_r  = "rgba(134,239,172,.15)" if ret >= 0 else "rgba(252,165,165,.15)"
cor_s = P_GREEN if saldo_hist >= 0 else P_RED
bg_s  = "rgba(134,239,172,.15)" if saldo_hist >= 0 else "rgba(252,165,165,.15)"

st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#30363d;
            border:1px solid #30363d;border-radius:12px;overflow:hidden;margin-bottom:1.4rem">
  <div style="background:#161b22;padding:1.1rem 1.3rem">
    <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Patrimônio Investido</div>
    <div style="color:{TEXT_PRI};font-size:1.3rem;font-weight:700">{fmt(pat)}</div>
    <span style="background:rgba(147,197,253,.12);color:{P_BLUE};padding:2px 8px;border-radius:20px;font-size:.72rem;font-weight:600">{len(investimentos)} ativos</span>
  </div>
  <div style="background:#161b22;padding:1.1rem 1.3rem">
    <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Retorno Total</div>
    <div style="color:{cor_r};font-size:1.3rem;font-weight:700">{fmt(ret)}</div>
    <span style="background:{bg_r};color:{cor_r};padding:2px 8px;border-radius:20px;font-size:.72rem;font-weight:600">{"▲" if ret>=0 else "▼"} {abs(ret_p):.1f}%</span>
  </div>
  <div style="background:#161b22;padding:1.1rem 1.3rem">
    <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Saldo Histórico</div>
    <div style="color:{cor_s};font-size:1.3rem;font-weight:700">{fmt(saldo_hist)}</div>
    <span style="background:{bg_s};color:{cor_s};padding:2px 8px;border-radius:20px;font-size:.72rem;font-weight:600">rec - desp</span>
  </div>
  <div style="background:#161b22;padding:1.1rem 1.3rem">
    <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Total Investido</div>
    <div style="color:{TEXT_PRI};font-size:1.3rem;font-weight:700">{fmt(custo)}</div>
    <span style="background:rgba(196,181,253,.12);color:{P_PURPLE};padding:2px 8px;border-radius:20px;font-size:.72rem;font-weight:600">custo médio</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Ranking
if investimentos:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Ranking de Performance</div>', unsafe_allow_html=True)
    df_rank = pd.DataFrame([{
        "nome"       : inv.get("nome",inv.get("ticker","—")),
        "retorno_pct": inv["retorno_pct"],
        "retorno_brl": inv["retorno_brl"],
    } for inv in investimentos]).sort_values("retorno_pct", ascending=False)

    cores_bar = [P_GREEN if v >= 0 else P_RED for v in df_rank["retorno_pct"]]
    fig_rank = go.Figure(go.Bar(
        x=df_rank["nome"], y=df_rank["retorno_pct"],
        marker_color=cores_bar, opacity=0.85,
        text=[f"{v:+.1f}%" for v in df_rank["retorno_pct"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    ))
    fig_rank.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT_SEC,height=260,margin=dict(l=0,r=0,t=20,b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#21262d",ticksuffix="%",zeroline=True,zerolinecolor="#30363d"),
    )
    st.plotly_chart(fig_rank,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# Fluxo de caixa
if transacoes:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Fluxo de Caixa Histórico</div>', unsafe_allow_html=True)
    df_t = pd.DataFrame(transacoes)
    df_t["mes"] = df_t["data_dt"].dt.to_period("M").astype(str)
    df_m = df_t.groupby(["mes","tipo"])["valor_brl"].sum().unstack(fill_value=0).reset_index()
    if "receita" not in df_m.columns: df_m["receita"] = 0
    if "despesa" not in df_m.columns: df_m["despesa"] = 0
    df_m["saldo"] = df_m["receita"] - df_m["despesa"]

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Bar(x=df_m["mes"],y=df_m["receita"],
                            name="Receita",marker_color=P_GREEN,opacity=0.75))
    fig_fc.add_trace(go.Bar(x=df_m["mes"],y=-df_m["despesa"],
                            name="Despesa",marker_color=P_RED,opacity=0.75))
    fig_fc.add_trace(go.Scatter(x=df_m["mes"],y=df_m["saldo"],
                                name="Saldo",line=dict(color=P_YELLOW,width=2.5),
                                mode="lines+markers",
                                marker=dict(color=P_YELLOW,size=6)))
    fig_fc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font_color=TEXT_SEC,height=260,barmode="overlay",
        margin=dict(l=0,r=0,t=0,b=0),
        xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#21262d"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_fc,use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# Alocação
if investimentos:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Alocação por Moeda</div>', unsafe_allow_html=True)
        df_moeda = (pd.DataFrame([{"moeda":i.get("moeda","BRL"),"valor":i["valor_atual_brl"]}
                                   for i in investimentos])
                    .groupby("moeda")["valor"].sum().reset_index())
        cores_m = [P_BLUE,P_GREEN,P_YELLOW,P_RED,P_PURPLE,P_TEAL]
        fig_m = go.Figure(go.Pie(
            labels=df_moeda["moeda"],values=df_moeda["valor"],
            hole=0.52,textinfo="label+percent",textfont_size=10,
            marker_colors=cores_m[:len(df_moeda)],
        ))
        fig_m.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",font_color=TEXT_SEC,
            height=240,margin=dict(l=0,r=0,t=0,b=0),showlegend=False,
        )
        st.plotly_chart(fig_m,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Peso na Carteira</div>', unsafe_allow_html=True)
        df_peso = pd.DataFrame([{
            "Ativo" : inv.get("nome",inv.get("ticker","—")),
            "Peso %" : round((inv["valor_atual_brl"]/pat*100) if pat else 0,1),
            "Valor"  : fmt(inv["valor_atual_brl"]),
            "Retorno": f"{inv['retorno_pct']:+.1f}%",
        } for inv in sorted(investimentos,key=lambda x:-x["valor_atual_brl"])])

        def cor_ret(val):
            if isinstance(val,str) and "+" in val: return f"color:{P_GREEN}"
            if isinstance(val,str) and "-" in val: return f"color:{P_RED}"
            return f"color:{TEXT_SEC}"

        st.dataframe(
            df_peso.style.map(cor_ret,subset=["Retorno"]),
            use_container_width=True,hide_index=True,
            height=min(300,50+len(df_peso)*35),
        )
        st.markdown('</div>', unsafe_allow_html=True)
