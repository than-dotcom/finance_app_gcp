"""
pages/1_💰_Investimentos.py
Gerencia a carteira de investimentos com cotações ao vivo.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime

from utils.data_manager import (
    get_investimentos, salvar_investimento, deletar_investimento,
    get_settings, TIPOS_INVESTIMENTO, MOEDAS, SIMBOLOS_MOEDA,
)
from utils.market_data import (
    get_taxas_cambio, enriquecer_investimento,
    get_cotacao, converter_para_brl, get_historico,
)

st.set_page_config(page_title="Investimentos · FinTrack", page_icon="💰", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 1.2rem !important; }
.chart-panel { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 1.2rem 1.4rem; }
</style>""", unsafe_allow_html=True)

settings   = get_settings()
moeda_base = settings.get("moeda_base", "BRL")
taxas      = get_taxas_cambio(moeda_base)
simbolo    = SIMBOLOS_MOEDA.get(moeda_base, "R$")

def fmt(v): return f"{simbolo} {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

# ─── CABEÇALHO ────────────────────────────────────────────────────────────────
st.markdown("## 💰 Carteira de Investimentos")
st.caption("Gerencie ações, FIIs, ETFs, criptomoedas, renda fixa e muito mais — BR e internacional.")
st.divider()

# ─── ABAS ─────────────────────────────────────────────────────────────────────
aba_cart, aba_add, aba_detalhe = st.tabs(["📋 Minha Carteira", "➕ Adicionar / Editar", "🔍 Detalhe do Ativo"])

# ═══════════════════════════════════════════════════════════════════════════════
# ABA 1 — Carteira
# ═══════════════════════════════════════════════════════════════════════════════
with aba_cart:
    investimentos_raw = get_investimentos()

    if not investimentos_raw:
        st.info("Nenhum investimento cadastrado. Use a aba **Adicionar** para começar.")
        st.stop()

    with st.spinner("Buscando cotações..."):
        investimentos = [enriquecer_investimento(inv, taxas) for inv in investimentos_raw]

    # KPIs da carteira
    pat   = sum(i["valor_atual_brl"] for i in investimentos)
    custo = sum(i["custo_brl"] for i in investimentos)
    ret   = pat - custo
    ret_p = (ret / custo * 100) if custo else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Patrimônio Total", fmt(pat))
    c2.metric("Retorno Total", fmt(ret), f"{ret_p:+.1f}%")
    c3.metric("Total Investido", fmt(custo))

    st.markdown("<br>", unsafe_allow_html=True)

    # Filtro por tipo
    tipos_presentes = list({inv["tipo"] for inv in investimentos})
    tipo_sel = st.multiselect(
        "Filtrar por tipo", options=tipos_presentes,
        default=tipos_presentes,
        format_func=lambda t: TIPOS_INVESTIMENTO.get(t, t),
    )
    inv_filt = [i for i in investimentos if i["tipo"] in tipo_sel]

    # Tabela
    rows = []
    for inv in sorted(inv_filt, key=lambda x: -x["valor_atual_brl"]):
        var = inv.get("variacao_dia", 0.0)
        ret_i = inv.get("retorno_pct", 0.0)
        rows.append({
            "id"          : inv["id"],
            "Nome"        : inv.get("nome", inv.get("ticker", "—")),
            "Ticker"      : inv.get("ticker", "—") or "—",
            "Tipo"        : TIPOS_INVESTIMENTO.get(inv["tipo"], inv["tipo"]),
            "Moeda"       : inv.get("moeda", "BRL"),
            "Qtd."        : inv.get("quantidade", 0),
            "P. Médio"    : inv.get("preco_medio", 0),
            "P. Atual"    : inv.get("preco_atual", 0),
            "Var. Dia %"  : var,
            "Valor BRL"   : inv["valor_atual_brl"],
            "Retorno %"   : ret_i,
            "Retorno BRL" : inv["retorno_brl"],
        })

    df = pd.DataFrame(rows)
    display_df = df.drop(columns=["id"]).copy()

    def cor_num(val):
        if isinstance(val, (int, float)):
            if val > 0: return "color: #3fb950"
            if val < 0: return "color: #f85149"
        return ""

    st.dataframe(
        display_df.style
            .map(cor_num, subset=["Var. Dia %", "Retorno %", "Retorno BRL"])
            .format({
                "Qtd."     : "{:,.4f}",
                "P. Médio" : "{:,.2f}",
                "P. Atual" : "{:,.2f}",
                "Var. Dia %": "{:+.2f}%",
                "Valor BRL": "{:,.2f}",
                "Retorno %" : "{:+.1f}%",
                "Retorno BRL": "{:+,.2f}",
            }),
        use_container_width=True,
        hide_index=True,
        height=min(500, 60 + len(rows) * 38),
    )

    # Excluir
    st.markdown("---")
    st.markdown("**Excluir investimento**")
    nomes_ids = {f"{r['Nome']} ({r['Ticker']})": r["id"] for r in rows}
    sel_del = st.selectbox("Selecione para excluir", ["—"] + list(nomes_ids.keys()))
    if sel_del != "—":
        if st.button("🗑️ Excluir", type="secondary"):
            deletar_investimento(nomes_ids[sel_del])
            st.success("Investimento excluído!")
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ABA 2 — Adicionar / Editar
# ═══════════════════════════════════════════════════════════════════════════════
with aba_add:
    st.markdown("### Novo Investimento")
    st.caption("Preencha os dados do ativo. Para ativos com ticker (ações, ETFs, cripto), o preço atual será buscado automaticamente.")

    with st.form("form_invest", clear_on_submit=True):
        c1, c2 = st.columns(2)

        with c1:
            tipo = st.selectbox("Tipo de ativo", list(TIPOS_INVESTIMENTO.keys()),
                                format_func=lambda k: TIPOS_INVESTIMENTO[k])
            nome = st.text_input("Nome do ativo", placeholder="Ex: Petrobras PN")
            ticker = st.text_input(
                "Ticker (Yahoo Finance)",
                placeholder="Ex: PETR4.SA | AAPL | BTC-USD | HGLG11.SA",
                help="Deixe em branco para Tesouro, CDB, LCI, LCA, etc."
            )

        with c2:
            moeda = st.selectbox("Moeda", list(MOEDAS.keys()),
                                 format_func=lambda k: MOEDAS[k])
            quantidade = st.number_input("Quantidade", min_value=0.0, step=0.001, format="%.4f")
            preco_medio = st.number_input("Preço médio de compra", min_value=0.0, step=0.01, format="%.2f")

        data_compra = st.date_input("Data da primeira compra", value=date.today())
        notas = st.text_area("Notas (opcional)", height=70)

        # Preview do valor
        if quantidade > 0 and preco_medio > 0:
            custo_prev = quantidade * preco_medio
            st.info(f"💡 Valor investido: **{SIMBOLOS_MOEDA.get(moeda,'R$')} {custo_prev:,.2f}**")

        submitted = st.form_submit_button("💾 Salvar Investimento", use_container_width=True)

    if submitted:
        if not nome and not ticker:
            st.error("Preencha ao menos o Nome ou o Ticker.")
        elif quantidade <= 0:
            st.error("Quantidade deve ser maior que zero.")
        else:
            dados = {
                "id": "", "tipo": tipo, "nome": nome or ticker,
                "ticker": ticker.upper().strip(),
                "moeda": moeda, "quantidade": quantidade,
                "preco_medio": preco_medio,
                "data_compra": str(data_compra), "notas": notas,
            }
            salvar_investimento(dados)
            st.success(f"✅ **{nome or ticker}** salvo com sucesso!")
            st.cache_data.clear()

    # Dicas de tickers
    with st.expander("📖 Exemplos de tickers por categoria"):
        st.markdown("""
| Categoria | Exemplos de ticker |
|---|---|
| 🇧🇷 Ações BR | `PETR4.SA` `VALE3.SA` `ITUB4.SA` `WEGE3.SA` `BBAS3.SA` |
| 🇺🇸 Ações EUA | `AAPL` `MSFT` `GOOGL` `AMZN` `NVDA` `TSLA` |
| 🇪🇺 Ações Europa | `SIE.DE` `LVMH.PA` `ENI.MI` `SAP.DE` `ASML.AS` |
| 🇬🇧 Ações UK | `SHEL.L` `HSBA.L` `AZN.L` `BP.L` |
| 🏢 FIIs | `HGLG11.SA` `XPLG11.SA` `KNRI11.SA` `VISC11.SA` |
| 📦 ETFs BR | `BOVA11.SA` `IVVB11.SA` `GOLD11.SA` `NASD11.SA` |
| 📦 ETFs EUA | `SPY` `QQQ` `IWM` `VTI` `GLD` |
| ₿ Cripto | `BTC-USD` `ETH-USD` `SOL-USD` `BNB-USD` |
        """)

# ═══════════════════════════════════════════════════════════════════════════════
# ABA 3 — Detalhe
# ═══════════════════════════════════════════════════════════════════════════════
with aba_detalhe:
    investimentos_raw2 = get_investimentos()
    if not investimentos_raw2:
        st.info("Nenhum ativo cadastrado.")
    else:
        opcoes = {
            f"{inv.get('nome', inv.get('ticker','—'))} ({inv.get('ticker','—')})": inv
            for inv in investimentos_raw2 if inv.get("ticker")
        }
        sel = st.selectbox("Selecione o ativo", list(opcoes.keys()))
        inv_sel = opcoes[sel]
        ticker  = inv_sel.get("ticker", "")

        if ticker:
            col_info, col_chart = st.columns([1, 2])

            with col_info:
                cot = get_cotacao(ticker)
                inv_enr = enriquecer_investimento(inv_sel, taxas)
                st.markdown(f"### {inv_sel.get('nome', ticker)}")
                st.caption(f"`{ticker}`  •  {TIPOS_INVESTIMENTO.get(inv_sel['tipo'], inv_sel['tipo'])}")
                st.metric("Preço Atual", f"{SIMBOLOS_MOEDA.get(cot['moeda'],'$')} {cot['preco']:,.2f}" if cot["preco"] else "N/D",
                          f"{cot['variacao_dia']:+.2f}% hoje")
                st.metric("Preço Médio", f"{SIMBOLOS_MOEDA.get(inv_sel['moeda'],'R$')} {inv_sel['preco_medio']:,.2f}")
                st.metric("Retorno", fmt(inv_enr["retorno_brl"]), f"{inv_enr['retorno_pct']:+.1f}%")
                st.metric("Valor na Carteira", fmt(inv_enr["valor_atual_brl"]))

            with col_chart:
                periodo_map = {"1 mês": "1mo", "3 meses": "3mo", "6 meses": "6mo", "1 ano": "1y", "5 anos": "5y"}
                per_sel = st.radio("Período", list(periodo_map.keys()), horizontal=True, index=3)
                hist = get_historico(ticker, periodo_map[per_sel])

                if not hist.empty:
                    cor = "#3fb950" if hist["preco"].iloc[-1] >= hist["preco"].iloc[0] else "#f85149"
                    fig = go.Figure(go.Scatter(
                        x=hist.index, y=hist["preco"],
                        mode="lines", line=dict(color=cor, width=2),
                        fill="tozeroy",
                        fillcolor=f"{'rgba(63,185,80,' if cor=='#3fb950' else 'rgba(248,81,73,'}0.08)",
                        hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:,.2f}</b><extra></extra>",
                    ))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#c9d1d9", height=280,
                        margin=dict(l=0, r=0, t=10, b=0),
                        xaxis=dict(showgrid=True, gridcolor="#21262d"),
                        yaxis=dict(showgrid=True, gridcolor="#21262d"),
                    )
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
