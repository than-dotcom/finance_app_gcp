"""
Relatórios — FinTrack
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
WHITE="#e6edf3"; MUTED="#8b949e"; CARD="#161b22"; BORDER="#30363d"

st.markdown(f"""<style>
.block-container{{padding-top:1rem!important}}
.panel{{background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1rem}}
.panel-title{{color:{MUTED};font-size:.75rem;text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin-bottom:1rem}}
.badge{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.71rem;font-weight:600}}
</style>""", unsafe_allow_html=True)

settings   = get_settings()
moeda_base = settings.get("moeda_base","BRL")
taxas_brl  = get_taxas_cambio("BRL")
simbolo    = SIMBOLOS_MOEDA.get(moeda_base,"R$")
def fmt(v): return f"{simbolo} {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

st.markdown("## 📊 Relatórios")
st.caption("Visão consolidada: patrimônio, fluxo de caixa e performance.")
st.divider()

with st.spinner("Calculando..."):
    raw = get_investimentos()
    investimentos = [enriquecer_investimento(inv, taxas_brl) for inv in raw]
    transacoes    = get_transacoes()
    for t in transacoes:
        t["valor_brl"] = converter_para_brl(float(t.get("valor",0)),t.get("moeda","BRL"),taxas_brl)
        t["data_dt"]   = datetime.strptime(t.get("data","2000-01-01"),"%Y-%m-%d")

pat   = sum(i["valor_atual_brl"] for i in investimentos)
custo = sum(i["custo_brl"]       for i in investimentos)
ret   = pat - custo
ret_p = (ret/custo*100) if custo else 0.0
total_desp = sum(t["valor_brl"] for t in transacoes if t.get("tipo")=="despesa")
total_rec  = sum(t["valor_brl"] for t in transacoes if t.get("tipo")=="receita")
saldo_hist = total_rec - total_desp

# Ilha KPI 4 células
b_r = "badge-green" if ret>=0 else "badge-red"
s_r = "▲" if ret>=0 else "▼"
b_s = "badge-green" if saldo_hist>=0 else "badge-red"

st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:{BORDER};
            border:1px solid {BORDER};border-radius:12px;overflow:hidden;margin-bottom:1.4rem">
  <div style="background:{CARD};padding:1.1rem 1.3rem">
    <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Patrimônio Investido</div>
    <div style="color:{WHITE};font-size:1.3rem;font-weight:700">{fmt(pat)}</div>
    <span class="badge" style="background:rgba(147,197,253,.15);color:{P_BLUE}">{len(investimentos)} ativos</span>
  </div>
  <div style="background:{CARD};padding:1.1rem 1.3rem">
    <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Retorno Total</div>
    <div style="color:{WHITE};font-size:1.3rem;font-weight:700">{fmt(ret)}</div>
    <span class="badge {'badge-green' if ret>=0 else 'badge-red'}">{s_r} {abs(ret_p):.1f}%</span>
  </div>
  <div style="background:{CARD};padding:1.1rem 1.3rem">
    <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Saldo Histórico</div>
    <div style="color:{WHITE};font-size:1.3rem;font-weight:700">{fmt(saldo_hist)}</div>
    <span class="badge {b_s}">rec − desp</span>
  </div>
  <div style="background:{CARD};padding:1.1rem 1.3rem">
    <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Total Investido</div>
    <div style="color:{WHITE};font-size:1.3rem;font-weight:700">{fmt(custo)}</div>
    <span class="badge" style="background:rgba(196,181,253,.15);color:{P_PURPLE}">custo médio</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Ranking de performance
if investimentos:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Ranking de Performance dos Ativos</div>', unsafe_allow_html=True)
    df_rank = pd.DataFrame([{
        "nome"       : inv.get("nome",inv.get("ticker","—")),
        "retorno_pct": inv["retorno_pct"],
    } for inv in investimentos]).sort_values("retorno_pct", ascending=False)

    cores_bar = [P_GREEN if v>=0 else P_RED for v in df_rank["retorno_pct"]]
    fig_rank = go.Figure(go.Bar(
        x=df_rank["nome"], y=df_rank["retorno_pct"],
        marker_color=cores_bar, opacity=0.85,
        text=[f"{v:+.1f}%" for v in df_rank["retorno_pct"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
    ))
    fig_rank.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font_color=MUTED,height=260,margin=dict(l=0,r=0,t=24,b=0),
        xaxis=dict(showgrid=False,tickangle=-20),
        yaxis=dict(gridcolor="#21262d",ticksuffix="%",zeroline=True,zerolinecolor="#30363d"),
    )
    st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# Fluxo de caixa histórico — eixo X por mês legível
if transacoes:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Fluxo de Caixa Histórico</div>', unsafe_allow_html=True)

    df_t = pd.DataFrame(transacoes)
    # strftime evita timezone/Period issues que geravam timestamps no eixo X
    df_t["mes_key"]   = df_t["data_dt"].dt.strftime("%Y-%m")
    df_t["mes_label"] = df_t["data_dt"].dt.strftime("%b/%Y")

    df_m = (df_t.groupby(["mes_key","mes_label","tipo"])["valor_brl"]
            .sum().reset_index().sort_values("mes_key"))

    df_pivot = df_m.pivot_table(index=["mes_key","mes_label"],
                                columns="tipo", values="valor_brl",
                                aggfunc="sum", fill_value=0).reset_index()
    if "receita" not in df_pivot.columns: df_pivot["receita"] = 0.0
    if "despesa" not in df_pivot.columns: df_pivot["despesa"] = 0.0
    df_pivot["saldo"] = df_pivot["receita"] - df_pivot["despesa"]

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Bar(x=df_pivot["mes_label"], y=df_pivot["receita"],
                            name="Receita", marker_color=P_GREEN, opacity=0.75))
    fig_fc.add_trace(go.Bar(x=df_pivot["mes_label"], y=-df_pivot["despesa"],
                            name="Despesa", marker_color=P_RED, opacity=0.75))
    fig_fc.add_trace(go.Scatter(x=df_pivot["mes_label"], y=df_pivot["saldo"],
                                name="Saldo", mode="lines+markers",
                                line=dict(color=P_YELLOW, width=2.5),
                                marker=dict(color=P_YELLOW, size=7)))
    fig_fc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color=MUTED, height=270, barmode="overlay",
        margin=dict(l=0,r=0,t=0,b=0),
        xaxis=dict(showgrid=False, tickangle=-30, type="category"),
        yaxis=dict(gridcolor="#21262d", zeroline=True, zerolinecolor="#30363d"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_fc, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

# Alocação por moeda + Peso na carteira
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
            labels=df_moeda["moeda"], values=df_moeda["valor"],
            hole=0.52, textinfo="label+percent", textfont_size=10,
            marker_colors=cores_m[:len(df_moeda)],
        ))
        fig_m.update_layout(paper_bgcolor="rgba(0,0,0,0)",font_color=MUTED,
            height=250,margin=dict(l=0,r=0,t=0,b=0),showlegend=False)
        st.plotly_chart(fig_m,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Peso na Carteira</div>', unsafe_allow_html=True)

        # Peso % com 1 casa decimal, Retorno % com 1 casa decimal
        df_peso = pd.DataFrame([{
            "Ativo"    : inv.get("nome",inv.get("ticker","—")),
            "Peso %"   : round((inv["valor_atual_brl"]/pat*100) if pat else 0, 1),
            "Valor"    : fmt(inv["valor_atual_brl"]),
            "Retorno"  : f"{inv['retorno_pct']:+.1f}%",
        } for inv in sorted(investimentos, key=lambda x: -x["valor_atual_brl"])])

        def cor_ret(val):
            if isinstance(val,str) and val.startswith("+"): return f"color:{P_GREEN}"
            if isinstance(val,str) and val.startswith("-"): return f"color:{P_RED}"
            return f"color:{WHITE}"

        st.dataframe(
            df_peso.style
                .map(cor_ret, subset=["Retorno"])
                .format({"Peso %": "{:.1f}%"}),
            use_container_width=True, hide_index=True,
            height=min(320, 50+len(df_peso)*36),
        )
        st.markdown('</div>', unsafe_allow_html=True)
