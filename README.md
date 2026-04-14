# FinTrack - Aplicativo de Gestão Financeira Pessoal

Um aplicativo web moderno para rastrear investimentos, despesas e receitas com persistência em SQLite e cotações em tempo real via Finnhub API.

## 🚀 Recursos Principais

- **Dashboard com Equity Curve**: Acompanhe a evolução do seu patrimônio ao longo do tempo
- **Gestão de Investimentos**: Rastreie ações BR/US/EU, ETFs, FIIs, criptomoedas, Tesouro Direto e mais
- **Despesas e Receitas**: Categorize e acompanhe suas transações com conversão automática para BRL
- **Relatórios Consolidados**: Análises de performance, fluxo de caixa mensal e alocação do portfólio
- **Cotações em Tempo Real**: Integração com Finnhub API com cache de 5 minutos
- **Conversão Automática**: Todas as transações em moeda estrangeira são convertidas para BRL
- **Persistência SQLite**: Seus dados são salvos localmente em `fintrack.db`
- **Tema Dark**: Interface otimizada para reduzir fadiga ocular

## 📋 Requisitos

- Python 3.8+
- pip ou conda

## 🔧 Instalação Local

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/fintrack.git
cd fintrack
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure a API Key do Finnhub:
   - Acesse https://finnhub.io e crie uma conta gratuita
   - Copie sua API Key
   - Crie um arquivo `.streamlit/secrets.toml` com:
   ```toml
   FINNHUB_API_KEY = "sua-chave-aqui"
   ```

5. Execute o aplicativo:
```bash
streamlit run app.py
```

O app será aberto em `http://localhost:8501`

## 🌐 Deploy no Streamlit Cloud

1. Faça push do repositório para GitHub
2. Acesse https://share.streamlit.io
3. Clique em "New app"
4. Selecione seu repositório, branch e arquivo `app.py`
5. Clique em "Deploy"
6. Após o deploy, vá em "Settings" → "Secrets" e adicione:
   ```toml
   FINNHUB_API_KEY = "sua-chave-aqui"
   ```

**Nota**: No Streamlit Cloud, o banco de dados SQLite é efêmero (resetado a cada deploy). Para persistência permanente, use Supabase (veja a seção abaixo).

## 🗄️ Persistência em Ambiente Efêmero (Supabase)

Se você quer persistência permanente no Streamlit Cloud, siga estas etapas:

1. Crie uma conta em https://supabase.com
2. Crie um novo projeto
3. Copie a URL e a chave do projeto
4. Adicione ao `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "https://seu-projeto.supabase.co"
   SUPABASE_KEY = "sua-chave-supabase"
   ```

5. Descomente as linhas de Supabase em `database.py` e `app.py`

## 📁 Estrutura do Projeto

```
fintrack/
├── app.py                 # Arquivo principal
├── database.py            # Módulo de banco de dados SQLite
├── api_client.py          # Integração com APIs externas
├── requirements.txt       # Dependências Python
├── README.md              # Este arquivo
├── .streamlit/
│   └── secrets.toml       # Configuração de secrets (não commitar)
└── pages/
    ├── __init__.py
    ├── dashboard.py       # Dashboard com Equity Curve
    ├── investimentos.py   # Gestão de investimentos
    ├── despesas.py        # Despesas e receitas
    ├── relatorios.py      # Relatórios consolidados
    └── configuracoes.py   # Configurações
```

## 🔄 Fluxo de Dados

### Investimentos
1. Usuário adiciona um ativo (ticker, quantidade, preço médio)
2. App busca preço atual via Finnhub API
3. Preço é armazenado em cache por 5 minutos
4. Dashboard calcula valor total = quantidade × preço atual
5. Snapshot diário é salvo em `portfolio_snapshots`

### Despesas/Receitas
1. Usuário insere valor em qualquer moeda
2. App busca taxa de câmbio via Finnhub (fallback: ExchangeRate-API)
3. Valor é convertido para BRL e salvo no banco
4. Relatórios mostram fluxo de caixa em BRL

## 📊 Banco de Dados

### Tabelas

**investimentos**
- `id`: Identificador único
- `ticker`: Símbolo do ativo (ex: PETR3, AAPL, BTC)
- `nome`: Nome do ativo
- `tipo`: Tipo de ativo (acao_br, acao_us, etf, fii, cripto, tesouro, outro)
- `quantidade`: Quantidade de cotas/ações
- `preco_medio`: Preço médio de compra em BRL
- `data_compra`: Data da compra
- `notas`: Observações

**transacoes**
- `id`: Identificador único
- `tipo`: Tipo (despesa ou receita)
- `categoria`: Categoria da transação
- `valor_brl`: Valor em BRL (convertido automaticamente)
- `data_transacao`: Data da transação
- `descricao`: Descrição
- `notas`: Observações

**portfolio_snapshots**
- `id`: Identificador único
- `data`: Data do snapshot (UNIQUE)
- `valor_total_brl`: Valor total do portfólio em BRL

**preco_cache**
- `ticker`: Símbolo do ativo (PRIMARY KEY)
- `preco`: Preço em cache
- `timestamp`: Timestamp do cache

## 🛠️ Troubleshooting

### "ImportError: No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### "FINNHUB_API_KEY not found"
Certifique-se de que `.streamlit/secrets.toml` existe e contém a chave.

### Preços não atualizam
- Verifique se a API Key do Finnhub é válida
- Aguarde 5 minutos (TTL do cache)
- Limpe o cache em Configurações → Dados

### Banco de dados resetado no Streamlit Cloud
Isso é esperado. Use Supabase para persistência permanente.

## 📝 Categorias Padrão

### Despesas
- Alimentação
- Transporte
- Moradia
- Saúde
- Educação
- Entretenimento
- Compras
- Assinaturas
- Seguros
- Impostos
- Investimentos
- Outro

### Receitas
- Salário
- Freelance
- Investimentos
- Bônus
- Presente
- Reembolso
- Outro

## 🔐 Segurança

- **Nunca commite `.streamlit/secrets.toml`** para o repositório
- Use variáveis de ambiente no Streamlit Cloud
- O banco de dados SQLite é local e não é sincronizado automaticamente
- Para dados sensíveis, use Supabase com criptografia

## 📄 Licença

Este projeto está sob a licença MIT.

## 🤝 Contribuições

Contribuições são bem-vindas! Abra uma issue ou pull request.

## 📧 Contato

Para dúvidas ou sugestões, entre em contato através do GitHub.

---

**Desenvolvido com ❤️ usando Streamlit**
