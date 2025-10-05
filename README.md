# xSwE Agent - GitHub Issues Monitor & Analytics

Sistema Python para monitoramento de issues do GitHub com análise inteligente via Gemini AI e servidor MCP.

## 📊 Funcionalidades

- **Monitoramento de Issues**: Monitora automaticamente o repositório xLabInternet/xRatEcosystem
- **Analytics Avançada**: Gera gráficos de tarefas concluídas vs abertas, tempo médio de implementação
- **Chart Generation System**: Sistema completo de visualização com múltiplos backends (Matplotlib + Plotly)
  - 10+ tipos de gráficos (BAR, LINE, PIE, TIME_SERIES, HEATMAP, etc.)
  - Exportação em múltiplos formatos (PNG, SVG, PDF, HTML)
  - Backend interativo com Plotly para visualizações web
  - Infraestrutura de retry, circuit breaker e métricas
- **Análise de Código IA**: Integração com Gemini 2.5 Flash para análise inteligente de código
- **Servidor MCP**: Exposição de funcionalidades via Model Context Protocol
- **Dashboard Web**: Interface visual para acompanhamento das métricas
- **Infrastructure Utilities**: Retry logic, circuit breakers, health checks, performance metrics

## 🏗️ Arquitetura

O projeto utiliza os design patterns:
- **Repository Pattern**: Para abstração do acesso a dados do GitHub
- **Strategy Pattern**: Para diferentes tipos de análises e visualizações
- **Factory Pattern**: Para criação de gráficos com múltiplos backends
- **Circuit Breaker Pattern**: Para proteção contra falhas em cascata
- **Observer Pattern**: Para notificações de mudanças nas issues

## 📁 Estrutura do Projeto

```
xsweAgent/
├── src/
│   ├── github_monitor/          # Módulo de monitoramento GitHub
│   ├── analytics/               # Engine de análise de dados
│   ├── charts/                  # Gerador de gráficos (Matplotlib + Plotly)
│   ├── gemini_integration/      # Integração com Gemini AI
│   ├── mcp_server/              # Servidor MCP
│   ├── utils/                   # Infraestrutura (retry, metrics, health checks)
│   └── config/                  # Sistema de configuração
├── tests/                       # Comprehensive testing framework (5,258 lines)
├── docs/                        # Documentação
│   └── CHART_GENERATION.md      # Documentação do sistema de gráficos
├── examples/                    # Exemplos de uso
├── requirements.txt             # Dependências Python
├── docker-compose.yml           # Setup Docker
├── .env.example                 # Variáveis de ambiente
└── TODO.md                      # Lista de tarefas
```

## � Plano de Desenvolvimento

**Status**: ✅ Pronto para Execução (Janeiro 2025)

### Documentação de Planejamento
- **[Resumo Executivo](docs/EXECUTIVE_SUMMARY.md)** - Visão geral e status atual
- **[Prioridades](docs/PRIORITIES.md)** - Matriz P0-P3 e roadmap de negócio
- **[Workflow de Desenvolvimento](docs/DEVELOPMENT_WORKFLOW.md)** - Branches e processo git
- **[Plano da Equipe](docs/TEAM_PLAN.md)** - Divisão de responsabilidades
- **[Templates de Sincronização](docs/SYNC_TEMPLATES.md)** - Reuniões e processos

### Quick Start para Desenvolvedores
```bash
# 1. Setup do ambiente
git checkout develop
pip install -r requirements.txt

# 2. Escolher feature branch
git checkout feature/analytics-engine  # ou sua especialidade

# 3. Verificar testes
pytest tests/test_examples.py -v

# 4. Começar desenvolvimento
# Ver docs/TEAM_PLAN.md para tarefas específicas
```

## �🚀 Instalação

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

### Via MCP Server
O sistema expõe suas funcionalidades via servidor MCP, permitindo integração com clientes compatíveis.

### Via API REST
Acesse as funcionalidades via endpoints REST no servidor MCP.

## 🧪 Testing Framework

Comprehensive testing framework with **131 tests** and **73.3% pass rate**:

- **Test Utilities**: 3 mock utilities (GitHub, Gemini, TestDataBuilder)
- **Custom Assertions**: 5 specialized classes for validation
- **Integration Tests**: 31 tests covering GitHub, Analytics, and Charts
- **Performance Tests**: 18 benchmarks for scalability validation
- **Test Fixtures**: 20+ reusable fixtures
- **Documentation**: 47 KB of comprehensive guides

### Quick Test Commands

```bash
# Run all tests
pytest

# Run integration tests
pytest -m integration

# Run with coverage
pytest --cov=src --cov-report=html

# GitHub integration tests (all passing)
pytest tests/integration/test_github_integration.py -v
```

### Documentation
- **[tests/README.md](tests/README.md)** - Main testing guide
- **[tests/TEST_EXECUTION_GUIDE.md](tests/TEST_EXECUTION_GUIDE.md)** - Command reference
- **[TESTING_FRAMEWORK_COMPLETE.md](TESTING_FRAMEWORK_COMPLETE.md)** - Complete overview

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.