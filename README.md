# xSwE Agent - GitHub Issues Monitor & Analytics

Sistema Python para monitoramento de issues do GitHub com análise inteligente via Gemini AI e servidor MCP.

## 📊 Funcionalidades

- **Monitoramento de Issues**: Monitora automaticamente o repositório xLabInternet/xRatEcosystem
- **Analytics Avançada**: Gera gráficos de tarefas concluídas vs abertas, tempo médio de implementação
- **🤖 Enhanced AI Integration**: Gemini 2.5 Flash com múltiplos tipos de análise
  - 💻 **Code Analysis**: Análise de qualidade e complexidade do código
  - 🎯 **Issue Intelligence**: Categorização e insights automáticos
  - 📊 **Trend Prediction**: Previsão de tendências e planejamento
  - 😊 **Sentiment Analysis**: Detecção de sentimento em textos
  - ⚡ **Priority Analysis**: Priorização inteligente de issues
  - 👥 **Collaboration Insights**: Análise de saúde da equipe
- **🛡️ Production-Ready Infrastructure**
  - ♻️ Retry logic com exponential backoff
  - 🔌 Circuit breaker para proteção de falhas
  - 💚 Health checks e monitoramento contínuo
  - 📈 Metrics tracking e cost monitoring
- **Servidor MCP**: Exposição de funcionalidades via Model Context Protocol
- **Dashboard Web**: Interface visual para acompanhamento das métricas

## 🏗️ Arquitetura

O projeto utiliza os design patterns:
- **Repository Pattern**: Para abstração do acesso a dados do GitHub
- **Strategy Pattern**: Para diferentes tipos de análises e visualizações
- **Observer Pattern**: Para notificações de mudanças nas issues

## 📁 Estrutura do Projeto

```
xsweAgent/
├── src/
│   ├── github_monitor/          # Módulo de monitoramento GitHub
│   ├── analytics/               # Engine de análise de dados
│   ├── charts/                  # Gerador de gráficos
│   ├── gemini_integration/      # 🤖 Enhanced Gemini AI (6 analysis types)
│   ├── utils/                   # 🛡️ Infrastructure (retry, circuit breaker, metrics)
│   ├── mcp_server/              # Servidor MCP
│   └── config/                  # Sistema de configuração
├── tests/                       # Testes unitários (35 passing)
├── docs/                        # Documentação
│   └── GEMINI_AI_INTEGRATION.md # 📖 AI Integration Guide
├── examples/                    # Exemplos e demos
│   └── gemini_ai_enhanced_demo.py
├── requirements.txt             # Dependências Python
├── docker-compose.yml           # Setup Docker
├── .env.example                 # Variáveis de ambiente
└── TODO.md                      # Lista de tarefas
```

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone <repo-url>
cd xsweAgent
```

2. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite .env com suas chaves de API
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute o sistema:
```bash
python src/main.py
```

## ⚙️ Configuração

Configure as seguintes variáveis de ambiente no arquivo `.env`:

- `GITHUB_TOKEN`: Token de acesso do GitHub
- `GEMINI_API_KEY`: Chave da API do Google Gemini
- `REPO_OWNER`: xLabInternet
- `REPO_NAME`: xRatEcosystem
- `MCP_SERVER_PORT`: Porta do servidor MCP (padrão: 8000)

## 📈 Uso

### 🤖 Enhanced AI Features

```python
from src.gemini_integration import GeminiAnalyzer, CodeSnippet

# Inicializar analyzer
analyzer = GeminiAnalyzer()

# Análise de código
snippet = CodeSnippet(content="def hello(): return 'world'", language="python")
result = await analyzer.analyze_code(snippet)

# Análise de issue
insights = await analyzer.issue_analysis(issue)

# Análise de sentimento
sentiment = await analyzer.sentiment_analysis(text)

# Priorização inteligente
priority = await analyzer.priority_analysis(issue)

# Previsão de tendências
forecast = await analyzer.trend_prediction(historical_data)

# Insights de colaboração
team_health = await analyzer.collaboration_analysis(team_data)
```

**Documentação completa**: `docs/GEMINI_AI_INTEGRATION.md`  
**Demo funcionando**: `python examples/gemini_ai_enhanced_demo.py`

### Via MCP Server
O sistema expõe suas funcionalidades via servidor MCP, permitindo integração com clientes compatíveis.

### Via API REST
Acesse as funcionalidades via endpoints REST no servidor MCP.

## 🧪 Testes

Execute os testes:
```bash
# Todos os testes
pytest tests/

# Testes específicos
pytest tests/test_enhanced_gemini.py -v
pytest tests/test_utils_infrastructure.py -v
```

**Status atual**: ✅ 35/35 testes passando (100%)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.