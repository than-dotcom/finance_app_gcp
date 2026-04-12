"""
app.py — FinTrack · Dashboard Principal
Execute: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="FinTrack",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.data_manager import (
    get_investimentos, get_transacoes, get_settings,
    salvar_settings, seed_dados_exemplo,
    TIPOS_INVESTIMENTO, SIMBOLOS_MOEDA,
)
from utils.market_data import (
    get_taxas_cambio, enriquecer_investimento,
    historico_portfolio, converter_para_brl, taxa_brl_por_moeda,
)

seed_dados_exemplo()

# ── PALETA PASTEL ──────────────────────────────────────────────────────────────
P_GREEN  = "#86efac"   # verde pastel
P_RED    = "#fca5a5"   # vermelho pastel
P_BLUE   = "#93c5fd"   # azul pastel
P_YELLOW = "#fde68a"   # amarelo pastel
P_PURPLE = "#c4b5fd"   # roxo pastel
P_TEAL   = "#5eead4"   # teal pastel
CARD_BG  = "#161b22"
BORDER   = "#30363d"
TEXT_PRI = "#e6edf3"
TEXT_SEC = "#8b949e"
BG_MAIN  = "#0d1117"

st.markdown(f"""
<style>
.block-container {{ padding-top: 1rem !important; padding-bottom: 0 !important; }}

/* ── Ilha de KPIs ── */
.kpi-island {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 1.4rem;
}}
.kpi-cell {{
    background: {CARD_BG};
    padding: 1.3rem 1.5rem;
}}
.kpi-cell:first-child {{ border-radius: 13px 0 0 13px; }}
.kpi-cell:last-child  {{ border-radius: 0 13px 13px 0; }}

.kpi-icon-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.8rem;
}}
.kpi-label {{
    color: {TEXT_SEC};
    font-size: 0.80rem;
    font-weight: 500;
    letter-spacing: .05em;
    text-transform: uppercase;
}}
.kpi-icon {{
    width: 32px; height: 32px;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px;
}}
.kpi-value {{
    color: {TEXT_PRI};
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 0.35rem;
}}
.kpi-sub  {{ color: {TEXT_SEC}; font-size: 0.78rem; }}
.kpi-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-top: 0.3rem;
}}
.badge-green  {{ background: rgba(134,239,172,.15); color: {P_GREEN};  }}
.badge-red    {{ background: rgba(252,165,165,.15); color: {P_RED};    }}
.badge-blue   {{ background: rgba(147,197,253,.15); color: {P_BLUE};   }}
.badge-yellow {{ background: rgba(253,230,138,.15); color: {P_YELLOW}; }}

/* ── Painéis ── */
.panel {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}}
.panel-title {{
    color: {TEXT_SEC};
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: .06em;
    font-weight: 600;
    margin-bottom: 1rem;
}}

/* ── Topo ── */
.dash-title {{ font-size: 1.55rem; font-weight: 700; color: {TEXT_PRI}; margin-bottom: 2px; }}
.dash-sub   {{ font-size: 0.86rem; color: {TEXT_SEC}; }}
</style>
""", unsafe_allow_html=True)

# ── SETTINGS ──────────────────────────────────────────────────────────────────
settings   = get_settings()
moeda_base = settings.get("moeda_base", "BRL")
nome_user  = settings.get("nome_usuario", "Investidor")
taxas_brl  = get_taxas_cambio("BRL")   # sempre base BRL internamente
simbolo    = SIMBOLOS_MOEDA.get(moeda_base, "R$")

def fmt(v):
    return f"{simbolo} {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## FinTrack")
    moeda_sel = st.selectbox(
        "💱 Moeda de exibição",
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
        st.rerun()

    st.divider()
    st.caption("📊 Dashboard · 💰 Investimentos · 💸 Despesas\n📈 Relatórios · ⚙️ Configurações")
    st.caption("Use o menu acima para navegar entre páginas.")
    st.divider()

    # Câmbio ao vivo
    st.markdown("**💱 Câmbio vs BRL**")
    pares = [("USD","$"),("EUR","€"),("GBP","£"),("CHF","Fr")]
    for m, s in pares:
        val = taxa_brl_por_moeda(m, taxas_brl)
        st.caption(f"1 {s} = R$ {val:.2f}")

    st.divider()
    st.caption("FinTrack v1.1  •  yfinance + exchangerate-api")

# ── CABEÇALHO ─────────────────────────────────────────────────────────────────
hora = datetime.now().hour
saudacao = "Bom dia" if hora < 12 else ("Boa tarde" if hora < 18 else "Boa noite")

col_h, col_f = st.columns([3, 1])
with col_h:
    st.markdown(f'<div class="dash-title">Dashboard Financeiro</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="dash-sub">{saudacao}, {nome_user} · {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)
with col_f:
    filtro = st.selectbox("", ["Este mês","3 meses","6 meses","1 ano","Tudo"],
                          label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# ── DADOS ─────────────────────────────────────────────────────────────────────
with st.spinner("Atualizando cotações..."):
    investimentos = [enriquecer_investimento(inv, taxas_brl) for inv in get_investimentos()]

transacoes = get_transacoes()

# KPI valores
patrimonio  = sum(i["valor_atual_brl"] for i in investimentos)
custo_total = sum(i["custo_brl"] for i in investimentos)
retorno     = patrimonio - custo_total
retorno_pct = (retorno / custo_total * 100) if custo_total else 0.0

mes_atual = datetime.now().month
ano_atual = datetime.now().year
t_mes = [t for t in transacoes
         if datetime.strptime(t.get("data","2000-01-01"),"%Y-%m-%d").month == mes_atual
         and datetime.strptime(t.get("data","2000-01-01"),"%Y-%m-%d").year == ano_atual]
desp_mes = sum(converter_para_brl(float(t["valor"]),t.get("moeda","BRL"),taxas_brl)
               for t in t_mes if t.get("tipo")=="despesa")
rec_mes  = sum(converter_para_brl(float(t["valor"]),t.get("moeda","BRL"),taxas_brl)
               for t in t_mes if t.get("tipo")=="receita")
saldo_mes = rec_mes - desp_mes
n_pos = sum(1 for i in investimentos if i["retorno_brl"] >= 0)

# ── ILHA DE KPIs ──────────────────────────────────────────────────────────────
ret_badge  = "badge-green" if retorno >= 0 else "badge-red"
ret_sinal  = "▲" if retorno >= 0 else "▼"
saldo_badge = "badge-green" if saldo_mes >= 0 else "badge-red"

st.markdown(f"""
<div class="kpi-island">
  <div class="kpi-cell">
    <div class="kpi-icon-row">
      <span class="kpi-label">Patrimônio Total</span>
      <span class="kpi-icon" style="background:rgba(147,197,253,.12)">💰</span>
    </div>
    <div class="kpi-value">{fmt(patrimonio)}</div>
    <div class="kpi-sub">{len(investimentos)} ativos monitorados</div>
    <span class="kpi-badge badge-blue">{len(investimentos)} ativos</span>
  </div>
  <div class="kpi-cell">
    <div class="kpi-icon-row">
      <span class="kpi-label">Retorno Total</span>
      <span class="kpi-icon" style="background:rgba(134,239,172,.12)">📈</span>
    </div>
    <div class="kpi-value">{fmt(retorno)}</div>
    <div class="kpi-sub">Sobre {fmt(custo_total)} investidos</div>
    <span class="kpi-badge {ret_badge}">{ret_sinal} {abs(retorno_pct):.1f}%</span>
  </div>
  <div class="kpi-cell">
    <div class="kpi-icon-row">
      <span class="kpi-label">Saldo do Mês</span>
      <span class="kpi-icon" style="background:rgba(253,230,138,.12)">🗓️</span>
    </div>
    <div class="kpi-value">{fmt(saldo_mes)}</div>
    <div class="kpi-sub">Receitas: {fmt(rec_mes)}</div>
    <span class="kpi-badge {saldo_badge}">Desp: {fmt(desp_mes)}</span>
  </div>
  <div class="kpi-cell">
    <div class="kpi-icon-row">
      <span class="kpi-label">No Positivo</span>
      <span class="kpi-icon" style="background:rgba(196,181,253,.12)">✅</span>
    </div>
    <div class="kpi-value">{n_pos} / {len(investimentos)}</div>
    <div class="kpi-sub">ativos com retorno positivo</div>
    <span class="kpi-badge badge-purple" style="background:rgba(196,181,253,.15);color:{P_PURPLE}">
        {int(n_pos/len(investimentos)*100) if investimentos else 0}% da carteira
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── GRÁFICOS ──────────────────────────────────────────────────────────────────
col_pie, col_line = st.columns([1, 2])

with col_pie:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Composição do Portfólio</div>', unsafe_allow_html=True)

    if investimentos:
        df_comp = (pd.DataFrame(investimentos)
                   .groupby("tipo")["valor_atual_brl"].sum().reset_index())
        df_comp["label"] = df_comp["tipo"].map(lambda t: TIPOS_INVESTIMENTO.get(t, t))
        df_comp = df_comp[df_comp["valor_atual_brl"] > 0]

        cores_pastel = [P_BLUE,P_GREEN,P_YELLOW,P_RED,P_PURPLE,P_TEAL,
                        "#f9a8d4","#fdba74","#a5f3fc","#d9f99d"]
        fig_pie = go.Figure(go.Pie(
            labels=df_comp["label"], values=df_comp["valor_atual_brl"],
            hole=0.55, marker_colors=cores_pastel[:len(df_comp)],
            textinfo="percent", textfont_size=10,
            hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        ))
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color=TEXT_SEC, height=280, margin=dict(l=0,r=0,t=0,b=0),
            legend=dict(orientation="v", font_size=9, bgcolor="rgba(0,0,0,0)"),
            annotations=[dict(text=f"<b>{fmt(patrimonio)}</b>",
                              x=0.5,y=0.5,font_size=10,showarrow=False,font_color=TEXT_PRI)],
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

with col_line:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Evolução do Portfólio</div>', unsafe_allow_html=True)

    hist = historico_portfolio(get_investimentos(), taxas_brl)
    if not hist.empty:
        mapa = {"Este mês":30,"3 meses":90,"6 meses":180,"1 ano":365,"Tudo":9999}
        hf = hist.tail(mapa[filtro])
        ret_p = ((hf["total"].iloc[-1]/hf["total"].iloc[0]-1)*100) if len(hf)>1 else 0
        cor = P_GREEN if ret_p >= 0 else P_RED
        fill_cor = "rgba(134,239,172,0.08)" if ret_p >= 0 else "rgba(252,165,165,0.08)"

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=hf.index, y=hf["total"], mode="lines",
            line=dict(color=cor, width=2.5),
            fill="tozeroy", fillcolor=fill_cor,
            hovertemplate="%{x|%d/%m/%Y}<br><b>R$ %{y:,.0f}</b><extra></extra>",
        ))
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color=TEXT_SEC, height=280, margin=dict(l=0,r=0,t=0,b=0),
            xaxis=dict(showgrid=True, gridcolor="#21262d", tickfont_size=10, zeroline=False),
            yaxis=dict(showgrid=True, gridcolor="#21262d", tickfont_size=10, zeroline=False,
                       tickprefix="R$ "),
            hovermode="x unified", showlegend=False,
        )
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Histórico disponível após adicionar ativos com ticker.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── TABELA ────────────────────────────────────────────────────────────────────
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-title">Carteira de Investimentos</div>', unsafe_allow_html=True)

if investimentos:
    rows = []
    for inv in sorted(investimentos, key=lambda x: -x["valor_atual_brl"]):
        var = inv.get("variacao_dia", 0.0)
        ret = inv.get("retorno_pct", 0.0)
        rows.append({
            "Ativo"       : inv.get("nome", inv.get("ticker","—")),
            "Tipo"        : TIPOS_INVESTIMENTO.get(inv["tipo"], inv["tipo"]),
            "Qtd."        : inv.get("quantidade", 0),
            "P. Médio"    : f"{SIMBOLOS_MOEDA.get(inv['moeda'],'R$')} {inv.get('preco_medio',0):,.2f}",
            "P. Atual"    : f"{SIMBOLOS_MOEDA.get(inv.get('moeda','BRL'),'R$')} {inv.get('preco_atual',0):,.2f}",
            "Var. Dia"    : var,
            "Valor (BRL)" : inv["valor_atual_brl"],
            "Retorno %"   : ret,
        })
    df_tab = pd.DataFrame(rows)

    def cor_num(val):
        if isinstance(val, (int, float)):
            if val > 0: return f"color: {P_GREEN}"
            if val < 0: return f"color: {P_RED}"
        return f"color: {TEXT_SEC}"

    st.dataframe(
        df_tab.style.map(cor_num, subset=["Var. Dia","Retorno %"])
              .format({"Qtd.":"{:,.4f}","Var. Dia":"{:+.2f}%",
                       "Valor (BRL)":"{:,.2f}","Retorno %":"{:+.1f}%"}),
        use_container_width=True, hide_index=True,
        height=min(420, 60+len(rows)*38),
    )
else:
    st.info("Nenhum investimento. Acesse **Investimentos** no menu.")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<br>")
st.caption("⚠️ FinTrack é uma ferramenta de acompanhamento pessoal. Não constitui recomendação de investimento.")
