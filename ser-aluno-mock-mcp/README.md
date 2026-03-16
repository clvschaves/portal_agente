# Ser Aluno Mock MCP

Servidor MCP (Model Context Protocol) **mock** em Python para testes e desenvolvimento com dados simulados do sistema SerEduc.

## 🚀 Quick Start

```bash
# Clone e acesse o diretório
cd ser-aluno-mock-mcp

# Subir ambiente completo (Keycloak + Mock MCP)
make quickstart

# OU manualmente:
make up          # Subir serviços
make setup       # Configurar Keycloak automaticamente
make test        # Testar funcionamento completo
```

**Pronto!** O ambiente estará rodando em:

- **Keycloak Admin**: http://localhost:8080/admin (admin/admin)
- **Mock MCP**: http://localhost:8081

## ✨ Características

- **🗂️ Dados Locais**: Uses arquivo JSON local (`database.json`) ao invés de APIs externas
- **🔄 Compatível**: Mantém mesma interface do `ser-aluno-mcp` original
- **🧪 Para Testes**: Ideal para desenvolvimento e testes sem dependências externas
- **👤 Dados Realistas**: Inclui dados completos do aluno RA `01493115`
- **🐳 Docker Ready**: Ambiente completo com Docker Compose
- **⚙️ Setup Automático**: Scripts para configuração automática do Keycloak
- **📋 Makefile**: Comandos simplificados para todas as operações

## 🛠 Tecnologias

- **Python 3.11**
- **FastAPI** - Framework web assíncrono
- **MCP SDK** - SDK oficial do Model Context Protocol
- **Keycloak** - Autenticação OAuth (apenas para validação de tokens)
- **Docker & Docker Compose** - Containerização
- **PostgreSQL** - Banco do Keycloak

## 📁 Estrutura do Projeto

```
ser-aluno-mock-mcp/
├── app/
│   ├── models/              # Modelos Pydantic (DTOs)
│   ├── services/            # Serviços (OAuth, Mock Service)
│   ├── middleware/          # Middleware de autenticação
│   ├── resources.py         # Handlers de resources MCP
│   └── tools.py             # Handlers de tools MCP
├── main.py                  # Aplicação FastAPI principal
├── config.py                # Configurações
├── database.json            # Base de dados mock
├── requirements.txt         # Dependências Python
├── Dockerfile               # Container da aplicação
├── docker-compose.yml       # Orquestração dos serviços
├── setup-keycloak.sh        # Setup automático do Keycloak
├── test-mock.sh            # Testes automatizados
├── Makefile                 # Comandos simplificados
├── KEYCLOAK-SETUP.md       # Guia de configuração do Keycloak
└── README.md               # Este arquivo
```

## 🗂️ Dados Mock Incluídos

O arquivo `database.json` contém:

- **👤 Aluno**: João Silva Santos (RA: 01493115)
- **🎓 Curso**: Comunicação Social - Publicidade e Propaganda (ID: 18486)
- **📚 5 Disciplinas** com notas, faltas e dados completos
- **📋 Dados Escolares** completos com status de matrícula

## 📚 Recursos MCP (Resources)

1. **aluno:dados** - Retorna os dados cadastrais do aluno
   - Parâmetros obrigatórios: `codColigada` (int), `ra` (string)

2. **aluno:cursos** - Retorna os cursos/habilitações do aluno
   - Parâmetros: `ra` (string)

3. **aluno:disciplinas** - Retorna as disciplinas matriculadas do aluno
   - Parâmetros obrigatórios: `ra` (string), `idHabilitacaoFilial` (int), `codColigada` (int)
   - Parâmetros opcionais: filtros por período, status, notas/faltas, etc.

4. **aluno:dados-escolares** - Retorna os dados escolares do aluno
   - Parâmetros obrigatórios: `ra` (string)

## 🔧 Ferramentas MCP (Tools)

1. **get_aluno_summary** - Obtém resumo completo dos dados do aluno
   - Parâmetros: `ra`, `codColigada`, `idHabilitacaoFilial`, `includeNotasFaltas`

## 🔐 Autenticação

⚠️ **IMPORTANTE**: Este mock requer autenticação Keycloak para manter compatibilidade com o sistema original.

- **OAuth Bearer Token** via Keycloak
- **Client Credentials Flow** para autenticação de serviços
- **Configuração automática** via scripts incluídos
- **Desabilitação opcional** para desenvolvimento (veja seção "Desenvolvimento")

## 🌐 Endpoints HTTP

- `GET /health` - Health check (inclui indicador de modo mock)
- `GET /mcp` - Descoberta do servidor MCP (indica modo mock)
- `GET /mcp/info` - Informações detalhadas do servidor
- `POST /mcp` - Processa requisições JSON-RPC 2.0 do protocolo MCP

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Server
HOST=0.0.0.0
PORT=8081  # Porta diferente para evitar conflitos

# Keycloak OAuth (para validação de tokens)
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=sereduc-mcps
KEYCLOAK_CLIENT_ID=ser-mcp-client

# Database mock
DATABASE_FILE=database.json
```

### Configuração do .env (opcional)

```bash
cp .env.example .env
# Edite as variáveis conforme necessário
```

## 🚀 Formas de Execução

### 1. Docker Compose (Recomendado)

```bash
# Subir ambiente completo
make up

# Configurar Keycloak automaticamente
make setup

# Testar tudo
make test

# Ver status
make health
```

### 2. Ambiente Local de Desenvolvimento

```bash
# Subir apenas Keycloak
make up-keycloak

# Executar Mock MCP localmente
make dev
```

### 3. Docker Manual

```bash
# Build da imagem
docker build -t ser-aluno-mock-mcp .

# Executar container
docker run -p 8081:8081 \
  -e KEYCLOAK_URL=http://host.docker.internal:8080 \
  ser-aluno-mock-mcp
```

## 📋 Comandos do Makefile

Execute `make help` para ver todos os comandos disponíveis:

```bash
make help           # Mostrar ajuda
make up             # Subir todos os serviços
make down           # Parar todos os serviços
make setup          # Configurar Keycloak automaticamente
make test           # Executar testes completos
make health         # Verificar status dos serviços
make logs           # Mostrar logs dos serviços
make clean          # Limpeza completa (remove dados)
make quickstart     # Setup completo em um comando
```

## 🧪 Testando o Mock

### Teste Automático Completo

```bash
# Executa bateria completa de testes
make test
```

### Testes Manuais

#### 1. Health Check

```bash
curl http://localhost:8081/health
```

#### 2. Info do MCP

```bash
curl http://localhost:8081/mcp/info
```

#### 3. Obter Token de Acesso

```bash
# Substitua CLIENT_SECRET pelo valor obtido no Keycloak
curl -X POST http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=ser-mcp-client&client_secret=YOUR_CLIENT_SECRET"
```

#### 4. Consultar Dados do Aluno

```bash
curl -X POST http://localhost:8081/mcp \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "resources/read",
    "params": {
      "uri": "aluno:dados",
      "arguments": {
        "codColigada": 1,
        "ra": "01493115"
      }
    }
  }'
```

## 📖 Exemplos de Uso MCP

### Consultar dados do aluno

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/read",
  "params": {
    "uri": "aluno:dados",
    "arguments": {
      "codColigada": 1,
      "ra": "01493115"
    }
  }
}
```

### Consultar disciplinas com notas

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/read",
  "params": {
    "uri": "aluno:disciplinas",
    "arguments": {
      "ra": "01493115",
      "idHabilitacaoFilial": 18486,
      "codColigada": 1,
      "retornarNotasFaltas": true
    }
  }
}
```

### Usar ferramenta de resumo

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_aluno_summary",
    "arguments": {
      "ra": "01493115",
      "codColigada": 1,
      "idHabilitacaoFilial": 18486,
      "includeNotasFaltas": true
    }
  }
}
```

## ⚖️ Diferenças do Ser Aluno MCP Original

| Aspecto               | Original             | Mock                  |
| --------------------- | -------------------- | --------------------- |
| **🗂️ Fonte de Dados** | APIs externas        | JSON local            |
| **🔐 Autenticação**   | Keycloak + Services  | Apenas Keycloak OAuth |
| **📊 Dados**          | Dinâmicos/Reais      | Estáticos/Mock        |
| **🌐 Porta Padrão**   | 8080                 | 8081                  |
| **🔧 Dependências**   | Múltiplos serviços   | Apenas Keycloak       |
| **⚡ Ferramentas**    | Atualização de dados | Apenas leitura        |
| **🚀 Deploy**         | Complexo             | Docker Compose        |

## 💻 Desenvolvimento

### Desabilitar Autenticação

Para usar o mock sem autenticação Keycloak, comente esta linha do `main.py`:

```python
# Comentar para desabilitar autenticação:
# app.add_middleware(BearerTokenMiddleware, keycloak_oauth_service=keycloak_oauth_service)
```

### Executar Localmente

```bash
# Instalar dependências
make install

# Executar em modo dev (com hot reload)
make dev

# Formatar código
make format

# Verificar código
make lint
```

### Modificar Dados Mock

Edite o arquivo `database.json` para modificar:

- Dados do aluno
- Curso e habilitações
- Disciplinas e notas
- Informações escolares

## 📋 Dados de Teste

O aluno mock tem os seguintes dados:

- **👤 Nome**: João Silva Santos
- **🎓 RA**: 01493115
- **📚 Curso**: Comunicação Social - Publicidade e Propaganda (ID: 18486)
- **📅 Período**: 5º período (2026/1)
- **📌 Status**: Pré-matrícula Web
- **📊 Disciplinas**: 5 disciplinas com notas variadas (6.8 a 9.2)

⚠️ **Importante**: Apenas o RA `01493115` retorna dados. Outros RAs retornarão dados vazios ou erro.

## 🔧 Troubleshooting

### Serviços não sobem

```bash
# Verificar logs
make logs

# Verificar status
make ps

# Limpar e tentar novamente
make clean
make up
```

### Keycloak não responde

```bash
# Verificar se está pronto
make health

# Aguardar inicialização (pode levar 2-3 minutos)
make logs-keycloak
```

### Erro de autenticação no Mock

```bash
# Verificar client secret no Keycloak
make open-keycloak

# Reconfigurar automaticamente
make setup
```

## 📚 Documentação Adicional

- [KEYCLOAK-SETUP.md](KEYCLOAK-SETUP.md) - Guia detalhado de configuração do Keycloak
- [../KEYCLOAK-AUTH.md](../KEYCLOAK-AUTH.md) - Documentação sobre autenticação OAuth para MCPs
- [../SECURITY-AUDIT.md](../SECURITY-AUDIT.md) - Auditoria de segurança

## 🎯 Guidelines

- Use Python 3.11+ features
- Compatível com o MCP protocol 2024-11-05
- Mantém compatibilidade com ser-aluno-mcp original
- Segue padrões de segurança OAuth
- Dados sempre retornam para RA `01493115`

## 🌐 URLs Importantes

Execute `make urls` para ver todas as URLs, ou acesse:

- **🔐 Keycloak Admin**: http://localhost:8080/admin (admin/admin)
- **🤖 Mock MCP Health**: http://localhost:8081/health
- **🤖 Mock MCP Info**: http://localhost:8081/mcp/info
- **🔑 Token Endpoint**: http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token
