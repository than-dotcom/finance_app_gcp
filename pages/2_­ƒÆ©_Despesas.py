"""
pages/2_💸_Despesas.py
Controle de despesas e receitas com gráficos mensais.
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

st.markdown("## 💸 Despesas & Receitas")
st.caption("Registre e acompanhe todas as suas entradas e saídas, em qualquer moeda.")
st.divider()

aba_lista, aba_add = st.tabs(["📋 Extrato", "➕ Nova Transação"])

# ═══════════════════════════════════════════════════════════════════════════════
# ABA 1 — Extrato
# ═══════════════════════════════════════════════════════════════════════════════
with aba_lista:
    transacoes = get_transacoes()

    if not transacoes:
        st.info("Nenhuma transação registrada. Use a aba **Nova Transação** para começar.")
        st.stop()

    # Enriquece com BRL
    for t in transacoes:
        t["valor_brl"] = converter_para_brl(float(t.get("valor", 0)), t.get("moeda", "BRL"), taxas)
        t["data_dt"]   = datetime.strptime(t.get("data", "2000-01-01"), "%Y-%m-%d")

    df_all = pd.DataFrame(transacoes)
    df_all["mes_ano"] = df_all["data_dt"].dt.to_period("M")

    # ── Filtros ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns(3)
    meses_disp = sorted(df_all["mes_ano"].unique(), reverse=True)
    mes_sel = col_f1.selectbox(
        "Mês", ["Todos"] + [str(m) for m in meses_disp]
    )
    tipo_sel = col_f2.selectbox("Tipo", ["Todos", "Despesa", "Receita"])
    cat_todas = sorted(df_all["categoria"].unique())
    cat_sel = col_f3.multiselect("Categorias", cat_todas, default=cat_todas)

    df_filt = df_all.copy()
    if mes_sel != "Todos":
        df_filt = df_filt[df_filt["mes_ano"].astype(str) == mes_sel]
    if tipo_sel != "Todos":
        df_filt = df_filt[df_filt["tipo"] == tipo_sel.lower()]
    if cat_sel:
        df_filt = df_filt[df_filt["categoria"].isin(cat_sel)]

    df_filt = df_filt.sort_values("data_dt", ascending=False)

    # ── KPIs do filtro ────────────────────────────────────────────────────────
    receitas  = df_filt[df_filt["tipo"] == "receita"]["valor_brl"].sum()
    despesas  = df_filt[df_filt["tipo"] == "despesa"]["valor_brl"].sum()
    saldo     = receitas - despesas

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas", fmt(receitas))
    c2.metric("Despesas", fmt(despesas))
    c3.metric("Saldo", fmt(saldo), delta=f"{(saldo/receitas*100):.0f}% poupado" if receitas else None)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráficos ──────────────────────────────────────────────────────────────
    col_bar, col_pie2 = st.columns([2, 1])

    with col_bar:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.markdown("**Receitas vs Despesas por Mês**")
        df_mes = (
            df_all.groupby(["mes_ano", "tipo"])["valor_brl"]
            .sum().reset_index()
        )
        df_mes["mes_str"] = df_mes["mes_ano"].astype(str)
        fig_bar = go.Figure()
        for tipo_g, cor in [("receita","#3fb950"), ("despesa","#f85149")]:
            sub = df_mes[df_mes["tipo"] == tipo_g]
            fig_bar.add_trace(go.Bar(
                x=sub["mes_str"], y=sub["valor_brl"],
                name=tipo_g.capitalize(), marker_color=cor, opacity=0.85,
            ))
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9", height=250, barmode="group",
            margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#21262d"),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_pie2:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.markdown("**Despesas por Categoria**")
        df_cat = (
            df_filt[df_filt["tipo"] == "despesa"]
            .groupby("categoria")["valor_brl"].sum()
            .reset_index().sort_values("valor_brl", ascending=False)
        )
        if not df_cat.empty:
            fig_cat = go.Figure(go.Pie(
                labels=df_cat["categoria"],
                values=df_cat["valor_brl"],
                hole=0.48, textinfo="percent",
                marker_colors=px.colors.qualitative.Dark24,
            ))
            fig_cat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="#c9d1d9",
                height=250, margin=dict(l=0,r=0,t=10,b=0),
                showlegend=False,
            )
            st.plotly_chart(fig_cat, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Nenhuma despesa no período.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabela ────────────────────────────────────────────────────────────────
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown("**Extrato Detalhado**")

    cols_show = ["data", "tipo", "categoria", "descricao", "moeda", "valor", "valor_brl"]
    df_show = df_filt[cols_show].copy()
    df_show.columns = ["Data", "Tipo", "Categoria", "Descrição", "Moeda", "Valor", f"Valor ({moeda_base})"]
    df_show["Data"] = df_filt["data_dt"].dt.strftime("%d/%m/%Y")

    def cor_tipo(val):
        if val == "receita": return "color: #3fb950"
        if val == "despesa": return "color: #f85149"
        return ""

    st.dataframe(
        df_show.style.applymap(cor_tipo, subset=["Tipo"])
            .format({"Valor": "{:,.2f}", f"Valor ({moeda_base})": "{:,.2f}"}),
        use_container_width=True, hide_index=True,
        height=min(450, 60 + len(df_show) * 38),
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Excluir
    st.markdown("---")
    ids_desc = {
        f"{t['data']} · {t['categoria']} · {fmt(t['valor_brl'])}": t["id"]
        for t in sorted(transacoes, key=lambda x: x["data"], reverse=True)
    }
    sel_del = st.selectbox("Excluir transação", ["—"] + list(ids_desc.keys()))
    if sel_del != "—" and st.button("🗑️ Excluir", type="secondary"):
        deletar_transacao(ids_desc[sel_del])
        st.success("Transação excluída!")
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# ABA 2 — Nova Transação
# ═══════════════════════════════════════════════════════════════════════════════
with aba_add:
    st.markdown("### Nova Transação")

    with st.form("form_transacao", clear_on_submit=True):
        tipo_t = st.radio("Tipo", ["💸 Despesa", "💰 Receita"], horizontal=True)
        is_desp = "Despesa" in tipo_t

        c1, c2 = st.columns(2)
        with c1:
            categorias = CATEGORIAS_DESPESA if is_desp else CATEGORIAS_RECEITA
            categoria  = st.selectbox("Categoria", categorias)
            descricao  = st.text_input("Descrição", placeholder="Ex: Supermercado Extra")
        with c2:
            moeda_t = st.selectbox("Moeda", list(MOEDAS.keys()),
                                   format_func=lambda k: MOEDAS[k])
            valor_t = st.number_input("Valor", min_value=0.01, step=0.01, format="%.2f")

        data_t = st.date_input("Data", value=date.today())
        obs    = st.text_input("Observação (opcional)")

        submitted_t = st.form_submit_button("💾 Registrar Transação", use_container_width=True)

    if submitted_t:
        salvar_transacao({
            "id": "", "tipo": "despesa" if is_desp else "receita",
            "categoria": categoria, "descricao": descricao or categoria,
            "moeda": moeda_t, "valor": valor_t,
            "data": str(data_t), "obs": obs,
        })
        st.success(f"✅ {'Despesa' if is_desp else 'Receita'} de {SIMBOLOS_MOEDA.get(moeda_t,'R$')} {valor_t:,.2f} registrada!")
        st.cache_data.clear()
