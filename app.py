"""
app.py — FinTrack · Dashboard Principal
========================================
Página inicial com KPIs, evolução temporal e composição do portfólio.
Execute com:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="FinTrack",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Imports internos
from utils.data_manager import (
    get_investimentos, get_transacoes, get_settings,
    salvar_settings, seed_dados_exemplo,
    TIPOS_INVESTIMENTO, SIMBOLOS_MOEDA,
)
from utils.market_data import (
    get_taxas_cambio, enriquecer_investimento,
    historico_portfolio, converter_para_brl,
)

# ─── SEED ─────────────────────────────────────────────────────────────────────
seed_dados_exemplo()

# ─── CSS GLOBAL ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Remove padding padrão do Streamlit */
.block-container { padding-top: 1.2rem !important; padding-bottom: 0 !important; }

/* Cards KPI */
.kpi-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    height: 130px;
}
.kpi-label {
    color: #8b949e;
    font-size: 0.82rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: .05em;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.kpi-value {
    color: #e6edf3;
    font-size: 1.55rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
    line-height: 1.2;
}
.kpi-sub   { color: #8b949e; font-size: 0.78rem; }
.kpi-green { color: #3fb950 !important; }
.kpi-red   { color: #f85149 !important; }

/* Título do dashboard */
.dash-title { font-size: 1.6rem; font-weight: 700; color: #e6edf3; }
.dash-sub   { font-size: 0.88rem; color: #8b949e; margin-top: -0.3rem; }

/* Painéis de gráfico */
.chart-panel {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
}
</style>
""", unsafe_allow_html=True)

# ─── SETTINGS + CÂMBIO ────────────────────────────────────────────────────────
settings   = get_settings()
moeda_base = settings.get("moeda_base", "BRL")
nome_user  = settings.get("nome_usuario", "Investidor")
taxas      = get_taxas_cambio(moeda_base)
simbolo    = SIMBOLOS_MOEDA.get(moeda_base, "R$")

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    moeda_sel = st.selectbox(
        "Moeda de exibição",
        list(SIMBOLOS_MOEDA.keys()),
        index=list(SIMBOLOS_MOEDA.keys()).index(moeda_base),
        format_func=lambda x: f"{SIMBOLOS_MOEDA[x]} {x}",
    )
    if moeda_sel != moeda_base:
        settings["moeda_base"] = moeda_sel
        salvar_settings(settings)
        st.cache_data.clear()
        st.rerun()

    nome_input = st.text_input("Seu nome", value=nome_user)
    if nome_input != nome_user:
        settings["nome_usuario"] = nome_input
        salvar_settings(settings)

    st.divider()
    st.markdown("### 🧭 Navegação")
    st.page_link("app.py",                       label="📊 Dashboard",      icon="📊")
    st.page_link("pages/1_💰_Investimentos.py",  label="💰 Investimentos",  icon="💰")
    st.page_link("pages/2_💸_Despesas.py",       label="💸 Despesas",       icon="💸")
    st.page_link("pages/3_📊_Relatorios.py",     label="📊 Relatórios",     icon="📊")
    st.page_link("pages/4_⚙️_Configuracoes.py", label="⚙️ Configurações",  icon="⚙️")

    st.divider()
    st.caption("FinTrack v1.0  •  Dados em tempo real via yfinance")

# ─── CABEÇALHO ────────────────────────────────────────────────────────────────
col_title, col_filter = st.columns([3, 1])
with col_title:
    hora = datetime.now().hour
    saudacao = "Bom dia" if hora < 12 else ("Boa tarde" if hora < 18 else "Boa noite")
    st.markdown(f'<div class="dash-title">Dashboard Financeiro</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="dash-sub">{saudacao}, {nome_user} · Última atualização: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)

with col_filter:
    filtro_periodo = st.selectbox("", ["Este mês", "3 meses", "6 meses", "1 ano", "Tudo"], label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# ─── CARREGAR E ENRIQUECER DADOS ──────────────────────────────────────────────
with st.spinner("Atualizando cotações..."):
    investimentos_raw = get_investimentos()
    investimentos     = [enriquecer_investimento(inv, taxas) for inv in investimentos_raw]

transacoes = get_transacoes()

# ─── KPIs ─────────────────────────────────────────────────────────────────────
patrimonio_total = sum(inv["valor_atual_brl"] for inv in investimentos)
custo_total      = sum(inv["custo_brl"] for inv in investimentos)
retorno_total    = patrimonio_total - custo_total
retorno_pct      = (retorno_total / custo_total * 100) if custo_total else 0.0

# Despesas e receitas do mês atual
mes_atual = datetime.now().month
ano_atual = datetime.now().year
transacoes_mes = [
    t for t in transacoes
    if datetime.strptime(t.get("data", "2000-01-01"), "%Y-%m-%d").month == mes_atual
    and datetime.strptime(t.get("data", "2000-01-01"), "%Y-%m-%d").year == ano_atual
]
despesas_mes = sum(
    converter_para_brl(float(t["valor"]), t.get("moeda", "BRL"), taxas)
    for t in transacoes_mes if t.get("tipo") == "despesa"
)
receitas_mes = sum(
    converter_para_brl(float(t["valor"]), t.get("moeda", "BRL"), taxas)
    for t in transacoes_mes if t.get("tipo") == "receita"
)
saldo_mes = receitas_mes - despesas_mes

def fmt(v): return f"{simbolo} {abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Patrimônio Total <span>💰</span></div>
        <div class="kpi-value">{fmt(patrimonio_total)}</div>
        <div class="kpi-sub">{len(investimentos)} ativos monitorados</div>
    </div>""", unsafe_allow_html=True)

with col2:
    cor = "kpi-green" if retorno_total >= 0 else "kpi-red"
    sinal = "↑" if retorno_total >= 0 else "↓"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Retorno Total <span>📈</span></div>
        <div class="kpi-value {cor}">{fmt(retorno_total)}</div>
        <div class="kpi-sub {cor}">{sinal} {abs(retorno_pct):.1f}% sobre o investido</div>
    </div>""", unsafe_allow_html=True)

with col3:
    cor_saldo = "kpi-green" if saldo_mes >= 0 else "kpi-red"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Saldo do Mês <span>🗓️</span></div>
        <div class="kpi-value">{fmt(saldo_mes)}</div>
        <div class="kpi-sub">Receitas: {fmt(receitas_mes)} · Desp: {fmt(despesas_mes)}</div>
    </div>""", unsafe_allow_html=True)

with col4:
    n_pos = sum(1 for inv in investimentos if inv["retorno_brl"] >= 0)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Ativos no Positivo <span>✅</span></div>
        <div class="kpi-value kpi-green">{n_pos} / {len(investimentos)}</div>
        <div class="kpi-sub">Investido: {fmt(custo_total)}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── GRÁFICOS PRINCIPAIS ──────────────────────────────────────────────────────
col_pie, col_line = st.columns([1, 2])

# ── Composição por tipo ─────────────────────────────────────────────────────
with col_pie:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown("**Composição do Portfólio**")

    if investimentos:
        df_comp = (
            pd.DataFrame(investimentos)
            .groupby("tipo")["valor_atual_brl"]
            .sum()
            .reset_index()
        )
        df_comp["label"] = df_comp["tipo"].map(
            lambda t: TIPOS_INVESTIMENTO.get(t, t)
        )
        df_comp = df_comp[df_comp["valor_atual_brl"] > 0]

        cores = [
            "#388bfd","#3fb950","#e3b341","#f85149",
            "#bc8cff","#79c0ff","#56d364","#ffa657",
            "#ff7b72","#d2a8ff","#a5d6ff","#7ee787",
        ]
        fig_pie = go.Figure(go.Pie(
            labels=df_comp["label"],
            values=df_comp["valor_atual_brl"],
            hole=0.52,
            marker_colors=cores[:len(df_comp)],
            textinfo="percent",
            textfont_size=11,
            hovertemplate="<b>%{label}</b><br>%{customdata}<br>%{percent}<extra></extra>",
            customdata=[fmt(v) for v in df_comp["valor_atual_brl"]],
        ))
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(
                orientation="v", font_size=10,
                bgcolor="rgba(0,0,0,0)", x=1.0,
            ),
            annotations=[dict(
                text=f"<b>{fmt(patrimonio_total)}</b>",
                x=0.5, y=0.5, font_size=11,
                showarrow=False, font_color="#c9d1d9",
            )],
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Nenhum investimento cadastrado.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Evolução temporal ───────────────────────────────────────────────────────
with col_line:
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown("**Evolução do Portfólio**")

    hist = historico_portfolio(investimentos_raw, taxas)

    if not hist.empty:
        # Filtra pelo período selecionado
        mapa_periodo = {
            "Este mês": 30, "3 meses": 90,
            "6 meses": 180, "1 ano": 365, "Tudo": 9999,
        }
        dias = mapa_periodo[filtro_periodo]
        hist_filt = hist.tail(dias)

        retorno_periodo = (
            (hist_filt["total"].iloc[-1] / hist_filt["total"].iloc[0] - 1) * 100
            if len(hist_filt) > 1 else 0
        )
        cor_linha = "#3fb950" if retorno_periodo >= 0 else "#f85149"

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=hist_filt.index,
            y=hist_filt["total"],
            mode="lines",
            line=dict(color=cor_linha, width=2.5),
            fill="tozeroy",
            fillcolor=f"{'rgba(63,185,80,' if retorno_periodo >= 0 else 'rgba(248,81,73,'}0.08)",
            name="Portfólio",
            hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:,.2f}</b><extra></extra>",
        ))
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(
                showgrid=True, gridcolor="#21262d", gridwidth=0.5,
                tickfont_size=10, zeroline=False,
            ),
            yaxis=dict(
                showgrid=True, gridcolor="#21262d", gridwidth=0.5,
                tickfont_size=10, zeroline=False,
                tickprefix=f"{simbolo} ",
            ),
            hovermode="x unified",
            showlegend=False,
        )
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Histórico não disponível (adicione ativos com ticker).")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── TABELA DE ATIVOS ─────────────────────────────────────────────────────────
st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
st.markdown("**Carteira de Investimentos**")

if investimentos:
    rows = []
    for inv in sorted(investimentos, key=lambda x: -x["valor_atual_brl"]):
        var_dia = inv.get("variacao_dia", 0.0)
        ret     = inv.get("retorno_pct", 0.0)
        rows.append({
            "Ativo"         : inv.get("nome", inv.get("ticker", "—")),
            "Tipo"          : TIPOS_INVESTIMENTO.get(inv["tipo"], inv["tipo"]),
            "Qtd."          : inv.get("quantidade", 0),
            "P. Médio"      : f"{SIMBOLOS_MOEDA.get(inv['moeda'],'R$')} {inv.get('preco_medio', 0):,.2f}",
            "P. Atual"      : f"{SIMBOLOS_MOEDA.get(inv.get('moeda','BRL'),'R$')} {inv.get('preco_atual', 0):,.2f}",
            "Var. Dia"      : f"{'▲' if var_dia >= 0 else '▼'} {abs(var_dia):.2f}%",
            "Valor (BRL)"   : fmt(inv["valor_atual_brl"]),
            "Retorno"       : f"{'▲' if ret >= 0 else '▼'} {abs(ret):.1f}%",
        })
    df_tab = pd.DataFrame(rows)

    def colorir_col(val):
        if isinstance(val, str) and ("▲" in val):
            return "color: #3fb950"
        if isinstance(val, str) and ("▼" in val):
            return "color: #f85149"
        return ""

    st.dataframe(
        df_tab.style.applymap(colorir_col, subset=["Var. Dia", "Retorno"]),
        use_container_width=True,
        hide_index=True,
        height=min(400, 60 + len(rows) * 38),
    )
else:
    st.info("Nenhum investimento encontrado. Acesse **Investimentos** para adicionar.")

st.markdown('</div>', unsafe_allow_html=True)

# ─── RODAPÉ ───────────────────────────────────────────────────────────────────
st.markdown("<br>")
st.caption("⚠️ FinTrack é uma ferramenta pessoal de acompanhamento. Cotações via Yahoo Finance. Não constitui recomendação de investimento.")
