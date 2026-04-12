[README.md](https://github.com/user-attachments/files/26661226/README.md)
# 📈 FinTrack — Controle Financeiro Completo

App de controle financeiro pessoal com suporte a investimentos brasileiros e internacionais, múltiplas moedas e rastreamento de despesas — pronto para Streamlit Cloud e caminho para PWA.

## ✨ Funcionalidades

| Módulo | Funcionalidades |
|---|---|
| 📊 Dashboard | KPIs, evolução do portfólio, composição por tipo |
| 💰 Investimentos | Ações BR/EUA/Europa, FIIs, ETFs, Cripto, Renda Fixa, Tesouro |
| 💸 Despesas | Controle de receitas e despesas, gráficos mensais |
| 📊 Relatórios | Ranking de ativos, fluxo de caixa, alocação por moeda |
| ⚙️ Configurações | Moeda base, exportação de dados |

## 💱 Moedas suportadas
BRL · USD · EUR · GBP · CHF · JPY · CAD · AUD

## 🚀 Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/fintrack.git
cd fintrack

# 2. Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute
streamlit run app.py
```

## ☁️ Deploy no Streamlit Cloud (gratuito)

1. Faça push do projeto para um repositório GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte o repositório
4. Defina `app.py` como entry point
5. Clique em **Deploy** — pronto!

## 📱 Caminho para PWA

Após o deploy no Streamlit Cloud, o app já funciona no celular via browser.
Para transformar em PWA completo (ícone na tela inicial, offline):

```
Opção 1: Streamlit Cloud → adicionar manifest.json + service worker via components
Opção 2: Migrar para FastAPI + React/Vue com a mesma lógica de backend
Opção 3: Wrapper com Capacitor.js (iOS/Android nativo)
```

## 🗂️ Estrutura do projeto

```
fintrack/
├── app.py                        # Dashboard principal
├── requirements.txt
├── .streamlit/
│   └── config.toml               # Tema dark
├── pages/
│   ├── 1_💰_Investimentos.py
│   ├── 2_💸_Despesas.py
│   ├── 3_📊_Relatorios.py
│   └── 4_⚙️_Configuracoes.py
├── utils/
│   ├── data_manager.py           # Persistência JSON
│   └── market_data.py            # yfinance + câmbio
└── data/                         # Gerado automaticamente
    ├── investimentos.json
    ├── despesas.json
    └── settings.json
```

## 📡 Fontes de dados

- **Cotações**: Yahoo Finance via `yfinance` (atualizado a cada 5 min)
- **Câmbio**: exchangerate-api.com (atualizado a cada 30 min)

## ⚠️ Aviso

Este app é uma ferramenta de acompanhamento pessoal. Não constitui recomendação de investimento.
