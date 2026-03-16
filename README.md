# SerEduc MCPs

Sistema de servidores MCP (Model Context Protocol) para integração com dados educacionais do SerEduc.

## 🚀 Serviços

### Produção/Desenvolvimento

- **[ser-aluno-mcp](ser-aluno-mcp/)** - Servidor MCP para dados de alunos (integração real)
- **[ser-utils-mcp](ser-utils-mcp/)** - Servidor MCP para utilidades (CEP, cursos, etc.)
- **[ser-sofia-services](ser-sofia-services/)** - Serviços de chat e orquestração dos MCPs

### Mock/Testes

- **[ser-aluno-mock-mcp](ser-aluno-mock-mcp/)** - 🧪 **Mock** do ser-aluno-mcp com dados simulados e ambiente Docker completo

## 🏃‍♂️ Início Rápido - Mock Environment

Para desenvolvimento e testes, use o ambiente mock completo:

```bash
cd ser-aluno-mock-mcp
make quickstart
```

Isso irá:

1. Subir Keycloak + PostgreSQL + Mock MCP via Docker Compose
2. Configurar automaticamente realm e client no Keycloak
3. Executar testes de validação

**URLs do ambiente mock:**

- Keycloak Admin: http://localhost:8080/admin (admin/admin)
- Mock MCP: http://localhost:8081

## 📚 Documentação

- [**KEYCLOAK-AUTH.md**](KEYCLOAK-AUTH.md) - Documentação completa do processo de autenticação OAuth
- [**SECURITY-AUDIT.md**](SECURITY-AUDIT.md) - Auditoria de segurança dos MCPs
- [**ser-aluno-mock-mcp/KEYCLOAK-SETUP.md**](ser-aluno-mock-mcp/KEYCLOAK-SETUP.md) - Guia de configuração do Keycloak

## 🛠 Tecnologias

- **Python 3.11**
- **FastAPI** - Framework web assíncrono
- **MCP SDK** - SDK oficial do Model Context Protocol
- **Keycloak** - Autenticação OAuth com JWT
- **PostgreSQL** - Banco de dados
- **Docker & Docker Compose** - Containerização

## 📁 Estrutura Completa

```
sereduc-mcps/
├── ser-aluno-mcp/           # 🔗 MCP real para dados de alunos
├── ser-aluno-mock-mcp/      # 🧪 Mock MCP com ambiente Docker
│   ├── docker-compose.yml  # Keycloak + PostgreSQL + Mock MCP
│   ├── setup-keycloak.sh   # Setup automático do Keycloak
│   ├── test-mock.sh        # Testes automatizados
│   ├── Makefile            # Comandos simplificados
│   └── KEYCLOAK-SETUP.md   # Guia detalhado de configuração
├── ser-utils-mcp/          # 🔧 MCP para utilidades gerais
├── ser-sofia-services/     # 🤖 Serviços de chat e orquestração
├── KEYCLOAK-AUTH.md        # 📖 Documentação de autenticação
└── SECURITY-AUDIT.md       # 🔒 Auditoria de segurança
```

## 🎯 Casos de Uso

### Para Desenvolvimento/Testes

Use o **ser-aluno-mock-mcp** que oferece:

- ✅ Ambiente completo via Docker Compose
- ✅ Dados mock realistas (aluno RA 01493115)
- ✅ Setup automático do Keycloak
- ✅ Testes automatizados incluídos
- ✅ Zero dependências externas

### Para Produção/Integração

Use os MCPs reais:

- **ser-aluno-mcp** - Conecta com APIs reais do sistema
- **ser-utils-mcp** - Serviços de utilidade real
- **ser-sofia-services** - Orquestração completa

## 🔐 Autenticação

Todos os MCPs usam **Keycloak OAuth** com:

- **Client Credentials Flow** para autenticação de serviços
- **JWT tokens** com validação via JWKS
- **Bearer Token middleware** no FastAPI

Veja [KEYCLOAK-AUTH.md](KEYCLOAK-AUTH.md) para documentação completa.

## ⚡ Commands Rápidos

```bash
# Mock environment (recomendado para dev/test)
cd ser-aluno-mock-mcp
make quickstart           # Setup completo
make health              # Verificar status
make test                # Executar testes
make down                # Parar ambiente

# MCPs individuais
cd ser-aluno-mcp
python main.py

cd ser-utils-mcp
python main.py

cd ser-sofia-services
python main.py
```
