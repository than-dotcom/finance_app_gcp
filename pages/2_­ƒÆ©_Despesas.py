"""
pages/2_💸_Despesas.py
Controle de despesas e receitas.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime

from utils.data_manager import (
    get_transacoes, salvar_transacao, deletar_transacao,
    get_settings, CATEGORIAS_DESPESA, CATEGORIAS_RECEITA,
    MOEDAS, SIMBOLOS_MOEDA,
)
from utils.market_data import get_taxas_cambio, converter_para_brl

st.set_page_config(page_title="Despesas · FinTrack", page_icon="💸", layout="wide")

P_GREEN="#86efac"; P_RED="#fca5a5"; P_BLUE="#93c5fd"
P_YELLOW="#fde68a"; P_PURPLE="#c4b5fd"
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

st.markdown("## 💸 Despesas & Receitas")
st.caption("Registre e acompanhe todas as entradas e saídas, em qualquer moeda.")
st.divider()

aba_lista, aba_add = st.tabs(["📋 Extrato","➕ Nova Transação"])

# ═══════════════════════════════════════════════════════════════════════════════
with aba_lista:
    transacoes = get_transacoes()
    if not transacoes:
        st.info("Nenhuma transação. Use **Nova Transação** para começar.")
        st.stop()

    for t in transacoes:
        t["valor_brl"] = converter_para_brl(float(t.get("valor",0)), t.get("moeda","BRL"), taxas_brl)
        t["data_dt"]   = datetime.strptime(t.get("data","2000-01-01"),"%Y-%m-%d")

    df_all = pd.DataFrame(transacoes)
    df_all["mes_ano"] = df_all["data_dt"].dt.to_period("M")

    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    meses = sorted(df_all["mes_ano"].unique(), reverse=True)
    mes_sel  = col_f1.selectbox("Mês", ["Todos"]+[str(m) for m in meses])
    tipo_sel = col_f2.selectbox("Tipo", ["Todos","Despesa","Receita"])
    cat_todas = sorted(df_all["categoria"].unique())
    cat_sel  = col_f3.multiselect("Categorias", cat_todas, default=cat_todas)

    df = df_all.copy()
    if mes_sel != "Todos": df = df[df["mes_ano"].astype(str) == mes_sel]
    if tipo_sel != "Todos": df = df[df["tipo"] == tipo_sel.lower()]
    if cat_sel: df = df[df["categoria"].isin(cat_sel)]
    df = df.sort_values("data_dt", ascending=False)

    receitas = df[df["tipo"]=="receita"]["valor_brl"].sum()
    despesas = df[df["tipo"]=="despesa"]["valor_brl"].sum()
    saldo    = receitas - despesas

    # Ilha KPI
    cor_s = P_GREEN if saldo >= 0 else P_RED
    bg_s  = "rgba(134,239,172,.15)" if saldo >= 0 else "rgba(252,165,165,.15)"
    poup_pct = int(saldo/receitas*100) if receitas else 0

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#30363d;
                border:1px solid #30363d;border-radius:12px;overflow:hidden;margin-bottom:1.2rem">
      <div style="background:#161b22;padding:1.1rem 1.3rem">
        <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Receitas</div>
        <div style="color:{P_GREEN};font-size:1.4rem;font-weight:700">{fmt(receitas)}</div>
        <span style="background:rgba(134,239,172,.12);color:{P_GREEN};padding:2px 8px;border-radius:20px;font-size:.72rem;font-weight:600">
            ▲ entradas
        </span>
      </div>
      <div style="background:#161b22;padding:1.1rem 1.3rem">
        <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Despesas</div>
        <div style="color:{P_RED};font-size:1.4rem;font-weight:700">{fmt(despesas)}</div>
        <span style="background:rgba(252,165,165,.12);color:{P_RED};padding:2px 8px;border-radius:20px;font-size:.72rem;font-weight:600">
            ▼ saídas
        </span>
      </div>
      <div style="background:#161b22;padding:1.1rem 1.3rem">
        <div style="color:{TEXT_SEC};font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Saldo</div>
        <div style="color:{cor_s};font-size:1.4rem;font-weight:700">{fmt(saldo)}</div>
        <span style="background:{bg_s};color:{cor_s};padding:2px 8px;border-radius:20px;font-size:.72rem;font-weight:600">
            {poup_pct}% poupado
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Gráficos
    col_bar, col_pie = st.columns([2,1])

    with col_bar:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Receitas vs Despesas por Mês</div>', unsafe_allow_html=True)
        df_mes = (df_all.groupby(["mes_ano","tipo"])["valor_brl"]
                  .sum().reset_index())
        df_mes["mes_str"] = df_mes["mes_ano"].astype(str)
        fig_bar = go.Figure()
        for t_g, cor in [("receita",P_GREEN),("despesa",P_RED)]:
            sub = df_mes[df_mes["tipo"]==t_g]
            fig_bar.add_trace(go.Bar(x=sub["mes_str"],y=sub["valor_brl"],
                                     name=t_g.capitalize(),marker_color=cor,opacity=0.8))
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            font_color=TEXT_SEC,height=240,barmode="group",
            margin=dict(l=0,r=0,t=0,b=0),
            xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#21262d"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_bar,use_container_width=True,config={"displayModeBar":False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_pie:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Desp. por Categoria</div>', unsafe_allow_html=True)
        df_cat = (df[df["tipo"]=="despesa"].groupby("categoria")["valor_brl"]
                  .sum().reset_index().sort_values("valor_brl",ascending=False))
        if not df_cat.empty:
            cores_p = [P_RED,P_YELLOW,P_BLUE,P_PURPLE,P_GREEN,
                       "#f9a8d4","#fdba74","#a5f3fc","#d9f99d","#fde68a"]
            fig_cat = go.Figure(go.Pie(
                labels=df_cat["categoria"],values=df_cat["valor_brl"],
                hole=0.5,textinfo="percent",
                marker_colors=cores_p[:len(df_cat)],textfont_size=10,
            ))
            fig_cat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",font_color=TEXT_SEC,
                height=240,margin=dict(l=0,r=0,t=0,b=0),showlegend=False,
            )
            st.plotly_chart(fig_cat,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Nenhuma despesa no período.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabela extrato — usa .map()
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Extrato Detalhado</div>', unsafe_allow_html=True)

    df_show = df[["data","tipo","categoria","descricao","moeda","valor","valor_brl"]].copy()
    df_show.columns = ["Data","Tipo","Categoria","Descrição","Moeda","Valor",f"BRL"]
    df_show["Data"] = df["data_dt"].dt.strftime("%d/%m/%Y")

    def cor_tipo(val):
        if val == "receita": return f"color:{P_GREEN}"
        if val == "despesa": return f"color:{P_RED}"
        return f"color:{TEXT_SEC}"

    st.dataframe(
        df_show.style.map(cor_tipo, subset=["Tipo"])
               .format({"Valor":"{:,.2f}","BRL":"{:,.2f}"}),
        use_container_width=True, hide_index=True,
        height=min(420,60+len(df_show)*38),
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Excluir
    st.markdown("---")
    ids_desc = {
        f"{t['data']} · {t['categoria']} · {fmt(t['valor_brl'])}": t["id"]
        for t in sorted(transacoes, key=lambda x: x["data"], reverse=True)
    }
    sel_del = st.selectbox("🗑️ Excluir transação", ["—"]+list(ids_desc.keys()))
    if sel_del != "—" and st.button("Excluir", type="secondary"):
        deletar_transacao(ids_desc[sel_del]); st.success("Excluído!"); st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
with aba_add:
    st.markdown("### ➕ Nova Transação")

    with st.form("form_transacao", clear_on_submit=True):
        tipo_t = st.radio("Tipo", ["💸 Despesa","💰 Receita"], horizontal=True)
        is_desp = "Despesa" in tipo_t

        c1, c2 = st.columns(2)
        with c1:
            cats = CATEGORIAS_DESPESA if is_desp else CATEGORIAS_RECEITA
            categoria = st.selectbox("Categoria", cats)
            descricao = st.text_input("Descrição", placeholder="Ex: Supermercado Extra")
        with c2:
            moeda_t = st.selectbox("Moeda", list(MOEDAS.keys()),
                                   format_func=lambda k: MOEDAS[k])
            valor_t = st.number_input("Valor", min_value=0.01, step=0.01, format="%.2f")

        data_t = st.date_input("Data", value=date.today())
        obs    = st.text_input("Observação (opcional)")

        if valor_t > 0:
            em_brl = converter_para_brl(valor_t, moeda_t, taxas_brl)
            st.info(f"💡 {SIMBOLOS_MOEDA.get(moeda_t,'$')} {valor_t:,.2f} = **R$ {em_brl:,.2f}**")

        if st.form_submit_button("💾 Registrar Transação", use_container_width=True):
            salvar_transacao({
                "id":"","tipo":"despesa" if is_desp else "receita",
                "categoria":categoria,"descricao":descricao or categoria,
                "moeda":moeda_t,"valor":valor_t,"data":str(data_t),"obs":obs,
            })
            st.success(f"✅ {'Despesa' if is_desp else 'Receita'} de "
                       f"{SIMBOLOS_MOEDA.get(moeda_t,'R$')} {valor_t:,.2f} registrada!")
            st.cache_data.clear()
