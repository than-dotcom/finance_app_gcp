"""
Investimentos — FinTrack
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
P_YELLOW="#fde68a"; P_PURPLE="#c4b5fd"; P_TEAL="#5eead4"
WHITE="#e6edf3"; MUTED="#8b949e"; CARD="#161b22"; BORDER="#30363d"

st.markdown(f"""<style>
.block-container{{padding-top:1rem!important}}
.panel{{background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1rem}}
.panel-title{{color:{MUTED};font-size:.75rem;text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin-bottom:1rem}}
.badge{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.71rem;font-weight:600}}
.badge-green{{background:rgba(134,239,172,.15);color:{P_GREEN}}}
.badge-red{{background:rgba(252,165,165,.15);color:{P_RED}}}
.badge-blue{{background:rgba(147,197,253,.15);color:{P_BLUE}}}
</style>""", unsafe_allow_html=True)

settings   = get_settings()
taxas_brl  = get_taxas_cambio("BRL")
moeda_base = settings.get("moeda_base","BRL")
simbolo    = SIMBOLOS_MOEDA.get(moeda_base,"R$")
def fmt(v): return f"{simbolo} {abs(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")

st.markdown("## 💰 Investimentos")
st.caption("Ações BR/EUA/Europa, FIIs, ETFs, Cripto, Renda Fixa — cotações ao vivo.")
st.divider()

aba_cart, aba_add, aba_det = st.tabs(["📋 Minha Carteira","➕ Adicionar Ativo","🔍 Detalhe"])

# ── Carteira ──────────────────────────────────────────────────────────────────
with aba_cart:
    raw = get_investimentos()
    if not raw:
        st.info("Nenhum ativo. Use **Adicionar Ativo** para começar.")
        st.stop()

    with st.spinner("Buscando cotações..."):
        investimentos = [enriquecer_investimento(inv, taxas_brl) for inv in raw]

    pat   = sum(i["valor_atual_brl"] for i in investimentos)
    custo = sum(i["custo_brl"]       for i in investimentos)
    ret   = pat - custo
    ret_p = (ret/custo*100) if custo else 0.0

    b_r = "badge-green" if ret>=0 else "badge-red"
    cor_r = P_GREEN if ret>=0 else P_RED
    s_r   = "▲" if ret>=0 else "▼"

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:{BORDER};
                border:1px solid {BORDER};border-radius:12px;overflow:hidden;margin-bottom:1.2rem">
      <div style="background:{CARD};padding:1.1rem 1.3rem">
        <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Patrimônio</div>
        <div style="color:{WHITE};font-size:1.4rem;font-weight:700">{fmt(pat)}</div>
        <span class="badge badge-blue">{len(investimentos)} ativos</span>
      </div>
      <div style="background:{CARD};padding:1.1rem 1.3rem">
        <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Retorno Total</div>
        <div style="color:{WHITE};font-size:1.4rem;font-weight:700">{fmt(ret)}</div>
        <span class="badge {b_r}">{s_r} {abs(ret_p):.1f}%</span>
      </div>
      <div style="background:{CARD};padding:1.1rem 1.3rem">
        <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Total Investido</div>
        <div style="color:{WHITE};font-size:1.4rem;font-weight:700">{fmt(custo)}</div>
        <span class="badge badge-blue">custo médio</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    tipos_pres = list({inv["tipo"] for inv in investimentos})
    tipo_sel = st.multiselect("Filtrar por tipo", tipos_pres, default=tipos_pres,
                               format_func=lambda t: TIPOS_INVESTIMENTO.get(t,t))
    inv_filt = [i for i in investimentos if i["tipo"] in tipo_sel]

    rows = []
    for inv in sorted(inv_filt, key=lambda x: -x["valor_atual_brl"]):
        rows.append({
            "id"          : inv["id"],
            "Nome"        : inv.get("nome",inv.get("ticker","—")),
            "Ticker"      : inv.get("ticker","—") or "—",
            "Tipo"        : TIPOS_INVESTIMENTO.get(inv["tipo"],inv["tipo"]),
            "Moeda"       : inv.get("moeda","BRL"),
            "Qtd."        : inv.get("quantidade",0),
            "P. Médio"    : inv.get("preco_medio",0),
            "P. Atual"    : inv.get("preco_atual",0),
            "Var. Dia %"  : inv.get("variacao_dia",0.0),
            "Valor BRL"   : inv["valor_atual_brl"],
            "Retorno %"   : inv.get("retorno_pct",0.0),
            "Retorno BRL" : inv.get("retorno_brl",0.0),
        })

    if rows:
        df = pd.DataFrame(rows)
        disp = df.drop(columns=["id"]).copy()
        def cor_num(val):
            if isinstance(val,(int,float)):
                if val>0: return f"color:{P_GREEN}"
                if val<0: return f"color:{P_RED}"
            return f"color:{WHITE}"
        st.dataframe(
            disp.style.map(cor_num, subset=["Var. Dia %","Retorno %","Retorno BRL"])
                .format({"Qtd.":"{:,.4f}","P. Médio":"{:,.2f}","P. Atual":"{:,.2f}",
                         "Var. Dia %":"{:+.2f}%","Valor BRL":"{:,.2f}",
                         "Retorno %":"{:+.1f}%","Retorno BRL":"{:+,.2f}"}),
            use_container_width=True, hide_index=True, height=min(500,60+len(rows)*38),
        )

    st.markdown("---")
    nomes_ids = {f"{r['Nome']} ({r['Ticker']})": r["id"] for r in rows}
    sel_del   = st.selectbox("🗑️ Excluir ativo", ["—"]+list(nomes_ids.keys()))
    if sel_del != "—" and st.button("Confirmar exclusão", type="secondary"):
        deletar_investimento(nomes_ids[sel_del]); st.success("Excluído!"); st.rerun()

# ── Adicionar ─────────────────────────────────────────────────────────────────
with aba_add:
    st.markdown("### ➕ Novo Investimento")
    with st.form("form_invest", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            tipo   = st.selectbox("Tipo", list(TIPOS_INVESTIMENTO.keys()),
                                  format_func=lambda k: TIPOS_INVESTIMENTO[k])
            nome   = st.text_input("Nome", placeholder="Ex: Petrobras PN")
            ticker = st.text_input("Ticker Yahoo Finance",
                                   placeholder="PETR4.SA | AAPL | BTC-USD | HGLG11.SA")
        with c2:
            moeda      = st.selectbox("Moeda", list(MOEDAS.keys()), format_func=lambda k: MOEDAS[k])
            quantidade = st.number_input("Quantidade", min_value=0.0, step=0.001, format="%.4f")
            preco_med  = st.number_input("Preço médio de compra", min_value=0.0, step=0.01, format="%.2f")
        data_c = st.date_input("Data da compra", value=date.today())
        notas  = st.text_area("Notas", height=60)

        if quantidade > 0 and preco_med > 0:
            brl_v = converter_para_brl(quantidade*preco_med, moeda, taxas_brl)
            st.info(f"💡 {SIMBOLOS_MOEDA.get(moeda,'R$')} {quantidade*preco_med:,.2f} ≈ R$ {brl_v:,.2f}")

        if st.form_submit_button("💾 Salvar", use_container_width=True):
            if not nome and not ticker:
                st.error("Preencha Nome ou Ticker.")
            elif quantidade <= 0:
                st.error("Quantidade deve ser maior que zero.")
            else:
                salvar_investimento({"id":"","tipo":tipo,"nome":nome or ticker,
                    "ticker":ticker.upper().strip(),"moeda":moeda,
                    "quantidade":quantidade,"preco_medio":preco_med,
                    "data_compra":str(data_c),"notas":notas})
                st.success(f"✅ {nome or ticker} salvo!"); st.cache_data.clear()

    with st.expander("📖 Exemplos de tickers"):
        st.markdown("""
| Mercado | Tickers |
|---|---|
| 🇧🇷 Ações BR | `PETR4.SA` `VALE3.SA` `ITUB4.SA` `WEGE3.SA` `BBAS3.SA` |
| 🇺🇸 EUA | `AAPL` `MSFT` `GOOGL` `NVDA` `TSLA` |
| 🇪🇺 Europa | `SIE.DE` `LVMH.PA` `ENI.MI` `SAP.DE` |
| 🇬🇧 UK | `SHEL.L` `HSBA.L` `AZN.L` |
| 🏢 FIIs | `HGLG11.SA` `XPLG11.SA` `KNRI11.SA` |
| 📦 ETFs | `BOVA11.SA` `IVVB11.SA` `SPY` `QQQ` |
| ₿ Cripto | `BTC-USD` `ETH-USD` `SOL-USD` |
        """)

# ── Detalhe ───────────────────────────────────────────────────────────────────
with aba_det:
    raw2 = get_investimentos()
    opcoes = {f"{inv.get('nome',inv.get('ticker','—'))} ({inv.get('ticker','—')})": inv
              for inv in raw2 if inv.get("ticker","").strip()}
    if not opcoes:
        st.info("Nenhum ativo com ticker cadastrado.")
    else:
        sel = st.selectbox("Ativo", list(opcoes.keys()))
        inv_sel = opcoes[sel]
        ticker  = inv_sel.get("ticker","")
        col_i, col_c = st.columns([1,2])
        with col_i:
            cot     = get_cotacao(ticker)
            inv_enr = enriquecer_investimento(inv_sel, taxas_brl)
            st.markdown(f"### {inv_sel.get('nome',ticker)}")
            st.caption(f"`{ticker}` · {TIPOS_INVESTIMENTO.get(inv_sel['tipo'],inv_sel['tipo'])}")
            ps = f"{SIMBOLOS_MOEDA.get(cot['moeda'],'$')} {cot['preco']:,.2f}" if cot["preco"] else "N/D"
            st.metric("Preço Atual", ps, f"{cot['variacao_dia']:+.2f}% hoje" if cot["preco"] else None)
            st.metric("Preço Médio", f"{SIMBOLOS_MOEDA.get(inv_sel['moeda'],'R$')} {inv_sel['preco_medio']:,.2f}")
            st.metric("Retorno", fmt(inv_enr["retorno_brl"]), f"{inv_enr['retorno_pct']:+.1f}%")
            st.metric("Valor na Carteira", fmt(inv_enr["valor_atual_brl"]))
        with col_c:
            pm = {"1 mês":"1mo","3 meses":"3mo","6 meses":"6mo","1 ano":"1y","5 anos":"5y"}
            per = st.radio("Período", list(pm.keys()), horizontal=True, index=3)
            hist = get_historico(ticker, pm[per])
            if not hist.empty:
                s   = hist["preco"].squeeze()
                cor = P_GREEN if s.iloc[-1]>=s.iloc[0] else P_RED
                fc  = "rgba(134,239,172,0.08)" if cor==P_GREEN else "rgba(252,165,165,0.08)"
                fig = go.Figure(go.Scatter(x=hist.index,y=s,mode="lines",
                    line=dict(color=cor,width=2),fill="tozeroy",fillcolor=fc,
                    hovertemplate="%{x|%d/%m/%Y}<br><b>%{y:,.2f}</b><extra></extra>"))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                    font_color=MUTED,height=270,margin=dict(l=0,r=0,t=0,b=0),
                    xaxis=dict(showgrid=True,gridcolor="#21262d"),
                    yaxis=dict(showgrid=True,gridcolor="#21262d"))
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            else:
                st.warning("Histórico indisponível para este ticker.")
