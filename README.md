# xSwE Agent - GitHub Issues Monitor & Analytics

Sistema Python para monitoramento de issues do GitHub com análise inteligente via Gemini AI e servidor MCP.

## 📊 Funcionalidades

- **Monitoramento de Issues**: Monitora automaticamente o repositório xLabInternet/xRatEcosystem
- **Analytics Avançada**: Gera gráficos de tarefas concluídas vs abertas, tempo médio de implementação
- **Análise de Código IA**: Integração com Gemini 2.5 Flash para análise inteligente de código
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
│   ├── gemini_integration/      # Integração com Gemini AI
│   ├── mcp_server/              # Servidor MCP
│   └── config/                  # Sistema de configuração
├── tests/                       # Testes unitários
├── docs/                        # Documentação
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

### Via MCP Server
O sistema expõe suas funcionalidades via servidor MCP, permitindo integração com clientes compatíveis.

### Via API REST
Acesse as funcionalidades via endpoints REST no servidor MCP.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Faça commit das mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT.