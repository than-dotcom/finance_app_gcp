"""
pages/4_⚙️_Configuracoes.py
Configurações gerais do FinTrack.
"""

import streamlit as st
import json
from utils.data_manager import get_settings, salvar_settings, MOEDAS, SIMBOLOS_MOEDA
from utils.market_data import get_taxas_cambio

st.set_page_config(page_title="Configurações · FinTrack", page_icon="⚙️", layout="wide")
st.markdown("<style>.block-container{padding-top:1.2rem!important}</style>", unsafe_allow_html=True)

st.markdown("## ⚙️ Configurações")
st.divider()

settings = get_settings()

with st.form("settings_form"):
    nome = st.text_input("Seu nome", value=settings.get("nome_usuario", "Investidor"))
    moeda = st.selectbox(
        "Moeda principal de exibição",
        list(MOEDAS.keys()),
        index=list(MOEDAS.keys()).index(settings.get("moeda_base", "BRL")),
        format_func=lambda k: MOEDAS[k],
    )
    if st.form_submit_button("💾 Salvar", use_container_width=True):
        salvar_settings({"nome_usuario": nome, "moeda_base": moeda})
        st.cache_data.clear()
        st.success("Configurações salvas!")

st.divider()
st.markdown("### 📦 Exportar / Importar dados")

col1, col2 = st.columns(2)
with col1:
    from utils.data_manager import get_investimentos, get_transacoes
    export = {
        "investimentos": get_investimentos(),
        "transacoes": get_transacoes(),
        "settings": settings,
    }
    st.download_button(
        "⬇️ Exportar todos os dados (JSON)",
        data=json.dumps(export, ensure_ascii=False, indent=2, default=str),
        file_name="fintrack_backup.json",
        mime="application/json",
        use_container_width=True,
    )

with col2:
    st.info("📤 Importação disponível na próxima versão.")

st.divider()
st.markdown("### 💱 Taxas de câmbio atuais")
taxas = get_taxas_cambio("BRL")
moedas_exibir = ["USD","EUR","GBP","CHF","JPY","CAD","AUD"]
cols = st.columns(len(moedas_exibir))
for i, m in enumerate(moedas_exibir):
    taxa = taxas.get(m, 0)
    if taxa:
        cols[i].metric(m, f"{1/taxa:.4f}", "vs BRL")
