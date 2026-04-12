"""
pages/1_💰_Investimentos.py
Carteira de investimentos com cotações ao vivo.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from utils.data_manager import (
    get_investimentos, salvar_investimento, deletar_investimento,
    get_settings, TIPOS_INVESTIMENTO, MOEDAS, SIMBOLOS_MOEDA,
)
from utils.market_data import (
    get_taxas_cambio, enriquecer_investimento,
    get_cotacao, converter_para_brl, get_historico, taxa_brl_por_moeda,
)

st.set_page_config(page_title="Investimentos · FinTrack", page_icon="💰", layout="wide")

P_GREEN="#86efac"; P_RED="#fca5a5"; P_BLUE="#93c5fd"
P_YELLOW="#fde68a"; P_PURPLE="#c4b5fd"
TEXT_SEC="#8b949e"; TEXT_PRI="#e6edf3"

st.markdown(f"""<style>
.block-container{{padding-top:1rem!important}}
.panel{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1rem}}
.panel-title{{color:{TEXT_SEC};font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;font-weight:600;margin-bottom:1rem}}
</style>""", unsafe_allow_html=True)

settings  = get_settings()
taxas_brl = get_taxas_cambio("BRL")
moeda_base = settings.get("moeda_base","BRL")
simbolo   = SIMBOLOS_MOEDA.get(moeda_base,"R$")

def fmt(v): return f"{simbolo} {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

st.markdown("## 💰 Carteira de Investimentos")
st.caption("Ações BR/EUA/Europa, FIIs, ETFs, Cripto, Renda Fixa — com cotações ao vivo.")
st.divider()

aba_cart, aba_add, aba_detalhe = st.tabs(["📋 Minha Carteira","➕ Adicionar Ativo","🔍 Detalhe do Ativo"])

# ═══════════════════════════════════════════════════════════════════════════════
with aba_cart:
    raw = get_investimentos()
    if not raw:
        st.info("Nenhum ativo cadastrado. Use a aba **Adicionar Ativo** para começar.")
        st.stop()

    with st.spinner("Buscando cotações..."):
        investimentos = [enriquecer_investimento(inv, taxas_brl) for inv in raw]

    pat   = sum(i["valor_atual_brl"] for i in investimentos)
    custo = sum(i["custo_brl"] for i in investimentos)
    ret   = pat - custo
    ret_p = (ret / custo * 100) if custo else 0.0

    # Ilha KPI inline
    badge_ret = "rgba(134,239,172,.15)" if ret >= 0 else "rgba(252,165,165,.15)"
    cor_ret   = P_GREEN if ret >= 0 else P_RED
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#30363d;
                border:1px solid #30363d;border-radius:12px;overflow:hidden;margin-bottom:1.2rem">
      <div style="background:#161b22;padding:1.1rem 1.3rem">
        <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Patrimônio Total</div>
        <div style="color:{TEXT_PRI};font-size:1.4rem;font-weight:700">{fmt(pat)}</div>
        <div style="color:{TEXT_SEC};font-size:.75rem">{len(investimentos)} ativos</div>
      </div>
      <div style="background:#161b22;padding:1.1rem 1.3rem">
        <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Retorno Total</div>
        <div style="color:{cor_ret};font-size:1.4rem;font-weight:700">{fmt(ret)}</div>
        <span style="background:{badge_ret};color:{cor_ret};padding:2px 8px;border-radius:20px;font-size:.72rem;font-weight:600">
            {"▲" if ret >= 0 else "▼"} {abs(ret_p):.1f}%
        </span>
      </div>
      <div style="background:#161b22;padding:1.1rem 1.3rem">
        <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Total Investido</div>
        <div style="color:{TEXT_PRI};font-size:1.4rem;font-weight:700">{fmt(custo)}</div>
        <div style="color:{TEXT_SEC};font-size:.75rem">preço médio ponderado</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Filtro
    tipos_pres = list({inv["tipo"] for inv in investimentos})
    tipo_sel = st.multiselect("Filtrar por tipo", tipos_pres, default=tipos_pres,
                               format_func=lambda t: TIPOS_INVESTIMENTO.get(t, t))
    inv_filt = [i for i in investimentos if i["tipo"] in tipo_sel]

    # Tabela — usa .map() em vez de .applymap()
    rows = []
    for inv in sorted(inv_filt, key=lambda x: -x["valor_atual_brl"]):
        rows.append({
            "id"         : inv["id"],
            "Nome"       : inv.get("nome", inv.get("ticker","—")),
            "Ticker"     : inv.get("ticker","—") or "—",
            "Tipo"       : TIPOS_INVESTIMENTO.get(inv["tipo"], inv["tipo"]),
            "Moeda"      : inv.get("moeda","BRL"),
            "Qtd."       : inv.get("quantidade",0),
            "P. Médio"   : inv.get("preco_medio",0),
            "P. Atual"   : inv.get("preco_atual",0),
            "Var. Dia %"  : inv.get("variacao_dia",0.0),
            "Valor BRL"  : inv["valor_atual_brl"],
            "Retorno %"  : inv.get("retorno_pct",0.0),
            "Retorno BRL": inv.get("retorno_brl",0.0),
        })

    if rows:
        df = pd.DataFrame(rows)
        disp = df.drop(columns=["id"]).copy()

        def cor_num(val):
            if isinstance(val,(int,float)):
                if val > 0: return f"color:{P_GREEN}"
                if val < 0: return f"color:{P_RED}"
            return f"color:{TEXT_SEC}"

        st.dataframe(
            disp.style
                .map(cor_num, subset=["Var. Dia %","Retorno %","Retorno BRL"])
                .format({"Qtd.":"{:,.4f}","P. Médio":"{:,.2f}","P. Atual":"{:,.2f}",
                         "Var. Dia %":"{:+.2f}%","Valor BRL":"{:,.2f}",
                         "Retorno %":"{:+.1f}%","Retorno BRL":"{:+,.2f}"}),
            use_container_width=True, hide_index=True,
            height=min(500,60+len(rows)*38),
        )

    st.markdown("---")
    st.markdown("**🗑️ Excluir investimento**")
    nomes_ids = {f"{r['Nome']} ({r['Ticker']})": r["id"] for r in rows}
    sel_del = st.selectbox("Selecione para excluir", ["—"]+list(nomes_ids.keys()))
    if sel_del != "—" and st.button("Excluir", type="secondary"):
        deletar_investimento(nomes_ids[sel_del])
        st.success("Excluído!"); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
with aba_add:
    st.markdown("### ➕ Novo Investimento")
    st.caption("Para ações, ETFs e cripto, preencha o ticker para busca automática de cotação.")

    with st.form("form_invest", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            tipo = st.selectbox("Tipo de ativo", list(TIPOS_INVESTIMENTO.keys()),
                                format_func=lambda k: TIPOS_INVESTIMENTO[k])
            nome = st.text_input("Nome do ativo", placeholder="Ex: Petrobras PN")
            ticker = st.text_input("Ticker Yahoo Finance",
                                   placeholder="PETR4.SA | AAPL | BTC-USD | HGLG11.SA",
                                   help="Deixe em branco para Tesouro, CDB, Poupança, etc.")
        with c2:
            moeda = st.selectbox("Moeda", list(MOEDAS.keys()),
                                 format_func=lambda k: MOEDAS[k])
            quantidade = st.number_input("Quantidade", min_value=0.0, step=0.001, format="%.4f")
            preco_medio = st.number_input("Preço médio de compra", min_value=0.0,
                                          step=0.01, format="%.2f")
        data_compra = st.date_input("Data da primeira compra", value=date.today())
        notas = st.text_area("Notas (opcional)", height=60)

        if quantidade > 0 and preco_medio > 0:
            v = quantidade * preco_medio
            em_brl = converter_para_brl(v, moeda, taxas_brl)
            st.info(f"💡 Valor investido: **{SIMBOLOS_MOEDA.get(moeda,'R$')} {v:,.2f}** "
                    f"≈ **R$ {em_brl:,.2f}**")

        if st.form_submit_button("💾 Salvar Investimento", use_container_width=True):
            if not nome and not ticker:
                st.error("Preencha ao menos o Nome ou o Ticker.")
            elif quantidade <= 0:
                st.error("Quantidade deve ser maior que zero.")
            else:
                salvar_investimento({
                    "id":"","tipo":tipo,"nome":nome or ticker,
                    "ticker":ticker.upper().strip(),
                    "moeda":moeda,"quantidade":quantidade,
                    "preco_medio":preco_medio,"data_compra":str(data_compra),"notas":notas,
                })
                st.success(f"✅ **{nome or ticker}** salvo!")
                st.cache_data.clear()

    with st.expander("📖 Exemplos de tickers"):
        st.markdown("""
| Mercado | Exemplos |
|---|---|
| 🇧🇷 Ações BR | `PETR4.SA` `VALE3.SA` `ITUB4.SA` `WEGE3.SA` `BBAS3.SA` |
| 🇺🇸 Ações EUA | `AAPL` `MSFT` `GOOGL` `NVDA` `TSLA` `AMZN` |
| 🇪🇺 Europa | `SIE.DE` `LVMH.PA` `ENI.MI` `SAP.DE` `ASML.AS` |
| 🇬🇧 UK | `SHEL.L` `HSBA.L` `AZN.L` `BP.L` |
| 🏢 FIIs | `HGLG11.SA` `XPLG11.SA` `KNRI11.SA` `VISC11.SA` |
| 📦 ETFs BR | `BOVA11.SA` `IVVB11.SA` `GOLD11.SA` `NASD11.SA` |
| 📦 ETFs EUA | `SPY` `QQQ` `IWM` `VTI` `GLD` |
| ₿ Cripto | `BTC-USD` `ETH-USD` `SOL-USD` `BNB-USD` |
        """)

# ═══════════════════════════════════════════════════════════════════════════════
with aba_detalhe:
    raw2 = get_investimentos()
    opcoes_ticker = {
        f"{inv.get('nome',inv.get('ticker','—'))} ({inv.get('ticker','—')})": inv
        for inv in raw2 if inv.get("ticker","").strip()
    }
    if not opcoes_ticker:
        st.info("Nenhum ativo com ticker cadastrado.")
    else:
        sel = st.selectbox("Selecione o ativo", list(opcoes_ticker.keys()))
        inv_sel = opcoes_ticker[sel]
        ticker  = inv_sel.get("ticker","")

        col_i, col_c = st.columns([1,2])
        with col_i:
            cot     = get_cotacao(ticker)
            inv_enr = enriquecer_investimento(inv_sel, taxas_brl)
            st.markdown(f"### {inv_sel.get('nome',ticker)}")
            st.caption(f"`{ticker}` · {TIPOS_INVESTIMENTO.get(inv_sel['tipo'],inv_sel['tipo'])}")
            preco_str = (f"{SIMBOLOS_MOEDA.get(cot['moeda'],'$')} {cot['preco']:,.2f}"
                         if cot["preco"] else "N/D")
            st.metric("Preço Atual", preco_str,
                      f"{cot['variacao_dia']:+.2f}% hoje" if cot["preco"] else None)
            st.metric("Preço Médio",
                      f"{SIMBOLOS_MOEDA.get(inv_sel['moeda'],'R$')} {inv_sel['preco_medio']:,.2f}")
            st.metric("Retorno", fmt(inv_enr["retorno_brl"]),
                      f"{inv_enr['retorno_pct']:+.1f}%")
            st.metric("Valor na Carteira", fmt(inv_enr["valor_atual_brl"]))

        with col_c:
            pm = {"1 mês":"1mo","3 meses":"3mo","6 meses":"6mo","1 ano":"1y","5 anos":"5y"}
            per_sel = st.radio("Período", list(pm.keys()), horizontal=True, index=3)
            hist = get_historico(ticker, pm[per_sel])
            if not hist.empty:
                s = hist["preco"].squeeze()
                cor = P_GREEN if s.iloc[-1] >= s.iloc[0] else P_RED
                fc  = "rgba(134,239,172,0.08)" if cor==P_GREEN else "rgba(252,165,165,0.08)"
                fig = go.Figure(go.Scatter(
                    x=hist.index, y=s, mode="lines",
                    line=dict(color=cor,width=2), fill="tozeroy", fillcolor=fc,
                    hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:,.2f}</b><extra></extra>",
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color=TEXT_SEC, height=270, margin=dict(l=0,r=0,t=0,b=0),
                    xaxis=dict(showgrid=True,gridcolor="#21262d"),
                    yaxis=dict(showgrid=True,gridcolor="#21262d"),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
            else:
                st.warning("Histórico indisponível para este ticker.")
