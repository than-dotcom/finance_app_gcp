"""
Configurações — FinTrack
"""
import streamlit as st
import json
from utils.data_manager import get_settings, salvar_settings, MOEDAS, SIMBOLOS_MOEDA
from utils.market_data import get_taxas_cambio, taxa_brl_por_moeda

st.set_page_config(page_title="Configurações · FinTrack", page_icon="⚙️", layout="wide")
st.markdown("<style>.block-container{padding-top:1rem!important}</style>", unsafe_allow_html=True)

P_BLUE="#93c5fd"; P_GREEN="#86efac"; WHITE="#e6edf3"; MUTED="#8b949e"

st.markdown("## ⚙️ Configurações")
st.divider()

settings = get_settings()
with st.form("settings_form"):
    nome  = st.text_input("Seu nome", value=settings.get("nome_usuario","Investidor"))
    moeda = st.selectbox("Moeda principal", list(MOEDAS.keys()),
                         index=list(MOEDAS.keys()).index(settings.get("moeda_base","BRL")),
                         format_func=lambda k: MOEDAS[k])
    if st.form_submit_button("💾 Salvar", use_container_width=True):
        salvar_settings({"nome_usuario":nome,"moeda_base":moeda})
        st.cache_data.clear()
        st.success("✅ Configurações salvas!")

st.divider()
st.markdown("### 💱 Câmbio ao vivo (base BRL)")
taxas_brl = get_taxas_cambio("BRL")
moedas_ex = ["USD","EUR","GBP","CHF","JPY","CAD","AUD"]
cols = st.columns(len(moedas_ex))
for i, m in enumerate(moedas_ex):
    v = taxa_brl_por_moeda(m, taxas_brl)
    cols[i].metric(f"1 {m}", f"R$ {v:.2f}")

st.divider()
st.markdown("### 📦 Exportar dados")
from utils.data_manager import get_investimentos, get_transacoes
export = {"investimentos":get_investimentos(),"transacoes":get_transacoes(),"settings":settings}
st.download_button("⬇️ Exportar tudo (JSON)",
    data=json.dumps(export,ensure_ascii=False,indent=2,default=str),
    file_name="fintrack_backup.json", mime="application/json",
    use_container_width=True)
