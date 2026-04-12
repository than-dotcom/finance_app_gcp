"""
Despesas & Receitas — FinTrack
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime

from utils.data_manager import (
    get_transacoes, salvar_transacao, deletar_transacao,
    get_settings, CATEGORIAS_DESPESA, CATEGORIAS_RECEITA,
    MOEDAS, SIMBOLOS_MOEDA,
)
from utils.market_data import get_taxas_cambio, converter_para_brl

st.set_page_config(page_title="Despesas · FinTrack", page_icon="💸", layout="wide")

P_GREEN="#86efac"; P_RED="#fca5a5"; P_BLUE="#93c5fd"
P_YELLOW="#fde68a"; P_PURPLE="#c4b5fd"; P_TEAL="#5eead4"
P_PINK="#f9a8d4"; P_ORANGE="#fdba74"; P_CYAN="#a5f3fc"; P_LIME="#d9f99d"
WHITE="#e6edf3"; MUTED="#8b949e"; CARD="#161b22"; BORDER="#30363d"

# Cores pastéis por categoria (índice fixo para consistência)
CORES_CAT = [P_BLUE,P_GREEN,P_YELLOW,P_RED,P_PURPLE,P_TEAL,
             P_PINK,P_ORANGE,P_CYAN,P_LIME,"#c4b5fd","#fde68a"]

st.markdown(f"""<style>
.block-container{{padding-top:1rem!important}}
.panel{{background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1rem}}
.panel-title{{color:{MUTED};font-size:.75rem;text-transform:uppercase;letter-spacing:.07em;font-weight:600;margin-bottom:1rem}}
.badge{{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.71rem;font-weight:600}}
.badge-green{{background:rgba(134,239,172,.15);color:{P_GREEN}}}
.badge-red{{background:rgba(252,165,165,.15);color:{P_RED}}}
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

# ── Extrato ───────────────────────────────────────────────────────────────────
with aba_lista:
    transacoes = get_transacoes()
    if not transacoes:
        st.info("Nenhuma transação. Use **Nova Transação** para começar.")
        st.stop()

    for t in transacoes:
        t["valor_brl"] = converter_para_brl(float(t.get("valor",0)),t.get("moeda","BRL"),taxas_brl)
        t["data_dt"]   = datetime.strptime(t.get("data","2000-01-01"),"%Y-%m-%d")

    df_all = pd.DataFrame(transacoes)
    # Usa strftime para evitar timezone issues no Period
    df_all["mes_key"] = df_all["data_dt"].dt.strftime("%Y-%m")
    df_all["mes_label"] = df_all["data_dt"].dt.strftime("%b/%Y")

    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    meses_uniq = (df_all[["mes_key","mes_label"]]
                  .drop_duplicates().sort_values("mes_key",ascending=False))
    meses_opts = ["Todos"] + meses_uniq["mes_label"].tolist()
    mes_sel  = col_f1.selectbox("Mês", meses_opts)
    tipo_sel = col_f2.selectbox("Tipo", ["Todos","Despesa","Receita"])
    cat_todas = sorted(df_all["categoria"].unique())
    cat_sel  = col_f3.multiselect("Categorias", cat_todas, default=cat_todas)

    df = df_all.copy()
    if mes_sel != "Todos":
        df = df[df["mes_label"] == mes_sel]
    if tipo_sel != "Todos":
        df = df[df["tipo"] == tipo_sel.lower()]
    if cat_sel:
        df = df[df["categoria"].isin(cat_sel)]
    df = df.sort_values("data_dt", ascending=False)

    receitas = df[df["tipo"]=="receita"]["valor_brl"].sum()
    despesas = df[df["tipo"]=="despesa"]["valor_brl"].sum()
    saldo    = receitas - despesas
    poup     = int(saldo/receitas*100) if receitas else 0

    b_s = "badge-green" if saldo>=0 else "badge-red"
    s_s = "▲" if saldo>=0 else "▼"

    # Ilha KPI
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:{BORDER};
                border:1px solid {BORDER};border-radius:12px;overflow:hidden;margin-bottom:1.2rem">
      <div style="background:{CARD};padding:1.1rem 1.3rem">
        <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Receitas</div>
        <div style="color:{WHITE};font-size:1.4rem;font-weight:700">{fmt(receitas)}</div>
        <span class="badge badge-green">▲ entradas</span>
      </div>
      <div style="background:{CARD};padding:1.1rem 1.3rem">
        <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Despesas</div>
        <div style="color:{WHITE};font-size:1.4rem;font-weight:700">{fmt(despesas)}</div>
        <span class="badge badge-red">▼ saídas</span>
      </div>
      <div style="background:{CARD};padding:1.1rem 1.3rem">
        <div style="color:{MUTED};font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;margin-bottom:.5rem">Saldo</div>
        <div style="color:{WHITE};font-size:1.4rem;font-weight:700">{fmt(saldo)}</div>
        <span class="badge {b_s}">{poup}% poupado</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Gráficos
    col_bar, col_pie = st.columns([2,1])
    with col_bar:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Receitas vs Despesas por Mês</div>', unsafe_allow_html=True)

        # Agrega por mês com label legível — sem Period/timezone issues
        df_mes = (df_all.groupby(["mes_key","mes_label","tipo"])["valor_brl"]
                  .sum().reset_index().sort_values("mes_key"))
        fig_bar = go.Figure()
        for t_g, cor in [("receita",P_GREEN),("despesa",P_RED)]:
            sub = df_mes[df_mes["tipo"]==t_g]
            fig_bar.add_trace(go.Bar(x=sub["mes_label"],y=sub["valor_brl"],
                                     name=t_g.capitalize(),marker_color=cor,opacity=0.8))
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
            font_color=MUTED,height=240,barmode="group",
            margin=dict(l=0,r=0,t=0,b=0),
            xaxis=dict(showgrid=False,tickangle=-30),
            yaxis=dict(gridcolor="#21262d"),
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
            fig_cat = go.Figure(go.Pie(
                labels=df_cat["categoria"], values=df_cat["valor_brl"],
                hole=0.5, textinfo="percent", textfont_size=10,
                marker_colors=CORES_CAT[:len(df_cat)],
            ))
            fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)",font_color=MUTED,
                height=240,margin=dict(l=0,r=0,t=0,b=0),showlegend=False)
            st.plotly_chart(fig_cat,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Nenhuma despesa no período.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Tabela extrato
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Extrato Detalhado</div>', unsafe_allow_html=True)
    df_show = df[["data","tipo","categoria","descricao","moeda","valor","valor_brl"]].copy()
    df_show.columns = ["Data","Tipo","Categoria","Descrição","Moeda","Valor","BRL"]
    df_show["Data"] = df["data_dt"].dt.strftime("%d/%m/%Y")
    def cor_tipo(val):
        if val=="receita": return f"color:{P_GREEN}"
        if val=="despesa": return f"color:{P_RED}"
        return f"color:{WHITE}"
    st.dataframe(
        df_show.style.map(cor_tipo, subset=["Tipo"])
               .format({"Valor":"{:,.2f}","BRL":"{:,.2f}"}),
        use_container_width=True, hide_index=True, height=min(420,60+len(df_show)*38),
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    ids_desc = {f"{t['data']} · {t['categoria']} · {fmt(t['valor_brl'])}": t["id"]
                for t in sorted(transacoes,key=lambda x:x["data"],reverse=True)}
    sel_del = st.selectbox("🗑️ Excluir transação",["—"]+list(ids_desc.keys()))
    if sel_del != "—" and st.button("Confirmar exclusão",type="secondary"):
        deletar_transacao(ids_desc[sel_del]); st.success("Excluído!"); st.rerun()

# ── Nova Transação ────────────────────────────────────────────────────────────
with aba_add:
    st.markdown("### ➕ Nova Transação")
    with st.form("form_transacao", clear_on_submit=True):
        tipo_t  = st.radio("Tipo",["💸 Despesa","💰 Receita"],horizontal=True)
        is_desp = "Despesa" in tipo_t
        c1, c2  = st.columns(2)
        with c1:
            cats     = CATEGORIAS_DESPESA if is_desp else CATEGORIAS_RECEITA
            categoria = st.selectbox("Categoria", cats)
            descricao = st.text_input("Descrição", placeholder="Ex: Supermercado Extra")
        with c2:
            moeda_t = st.selectbox("Moeda", list(MOEDAS.keys()), format_func=lambda k: MOEDAS[k])
            valor_t = st.number_input("Valor", min_value=0.01, step=0.01, format="%.2f")
        data_t = st.date_input("Data", value=date.today())
        obs    = st.text_input("Observação (opcional)")

        if valor_t > 0:
            brl = converter_para_brl(valor_t, moeda_t, taxas_brl)
            st.info(f"💡 {SIMBOLOS_MOEDA.get(moeda_t,'$')} {valor_t:,.2f} = R$ {brl:,.2f}")

        if st.form_submit_button("💾 Registrar", use_container_width=True):
            salvar_transacao({"id":"","tipo":"despesa" if is_desp else "receita",
                "categoria":categoria,"descricao":descricao or categoria,
                "moeda":moeda_t,"valor":valor_t,"data":str(data_t),"obs":obs})
            st.success(f"✅ {'Despesa' if is_desp else 'Receita'} registrada!")
            st.cache_data.clear()
