# Makefile para Ser Aluno Mock MCP

.PHONY: help up down logs setup test clean build health

help: ## Mostrar ajuda
	@echo "🚀 Ser Aluno Mock MCP - Comandos Disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Subir todos os serviços (Keycloak + Mock MCP)
	@echo "🚀 Subindo ambiente..."
	docker-compose up -d
	@echo "⏳ Aguardando serviços ficarem prontos..."
	@echo "📋 Use 'make logs' para acompanhar o progresso"

build: ## Fazer build da imagem do Mock MCP
	@echo "🔨 Building Mock MCP..."
	docker-compose build ser-aluno-mock-mcp

down: ## Parar todos os serviços
	@echo "⬇️ Parando ambiente..."
	docker-compose down

clean: ## Parar e remover todos os dados (CUIDADO!)
	@echo "🧹 Limpando ambiente completamente..."
	docker-compose down -v --remove-orphans
	docker system prune -f

logs: ## Mostrar logs dos serviços
	docker-compose logs -f

logs-keycloak: ## Mostrar logs apenas do Keycloak
	docker-compose logs -f keycloak

logs-mock: ## Mostrar logs apenas do Mock MCP
	docker-compose logs -f ser-aluno-mock-mcp

health: ## Verificar status dos serviços
	@echo "🏥 Verificando health dos serviços..."
	@echo ""
	@echo "🔐 Keycloak:"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:8080/health/ready || echo "❌ Keycloak não está acessível"
	@echo ""
	@echo "🤖 Mock MCP:"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:8081/health || echo "❌ Mock MCP não está acessível"
	@echo ""

setup: ## Configurar automaticamente o Keycloak
	@echo "⚙️ Executando setup automático do Keycloak..."
	@chmod +x setup-keycloak.sh
	@./setup-keycloak.sh

test: ## Executar testes completos (requer CLIENT_SECRET configurado)
	@echo "🧪 Executando testes..."
	@chmod +x test-mock.sh
	@./test-mock.sh

test-simple: ## Executar teste simples em Python (interativo para client secret)
	@echo "🐍 Executando teste simples..."
	python test-simple.py

test-py: test-simple ## Alias para test-simple

ps: ## Mostrar status dos containers
	docker-compose ps

restart: ## Reiniciar todos os serviços
	@echo "🔄 Reiniciando ambiente..."
	docker-compose restart

restart-mock: ## Reiniciar apenas o Mock MCP
	@echo "🔄 Reiniciando Mock MCP..."
	docker-compose restart ser-aluno-mock-mcp

dev: ## Executar Mock MCP em modo desenvolvimento (local)
	@echo "💻 Iniciando em modo desenvolvimento..."
	@echo "⚠️  Certifique-se que o Keycloak está rodando (make up-keycloak)"
	python main.py

up-keycloak: ## Subir apenas Keycloak e banco
	@echo "🔐 Subindo apenas Keycloak..."
	docker-compose up -d keycloak-db keycloak

shell-mock: ## Acessar shell do container Mock MCP
	docker-compose exec ser-aluno-mock-mcp /bin/bash

shell-keycloak: ## Acessar shell do container Keycloak
	docker-compose exec keycloak /bin/bash

# Comandos de desenvolvimento
install: ## Instalar dependências Python localmente
	pip install -r requirements.txt

format: ## Formatar código com black
	@echo "🎨 Formatando código..."
	black app/ main.py config.py || echo "⚠️ black não está instalado (pip install black)"

lint: ## Verificar código com flake8
	@echo "🔍 Verificando código..."
	flake8 app/ main.py config.py || echo "⚠️ flake8 não está instalado (pip install flake8)"

# Utilitários
open-keycloak: ## Abrir Keycloak Admin no navegador
	@echo "🌐 Abrindo Keycloak Admin..."
	@command -v xdg-open >/dev/null && xdg-open http://localhost:8080/admin || \
	 command -v open >/dev/null && open http://localhost:8080/admin || \
	 echo "📋 Acesse: http://localhost:8080/admin (admin/admin)"

open-mock: ## Abrir Mock MCP info no navegador
	@echo "🌐 Abrindo Mock MCP..."
	@command -v xdg-open >/dev/null && xdg-open http://localhost:8081/mcp/info || \
	 command -v open >/dev/null && open http://localhost:8081/mcp/info || \
	 echo "📋 Acesse: http://localhost:8081/mcp/info"

urls: ## Mostrar URLs importantes
	@echo "📋 URLs Importantes:"
	@echo ""
	@echo "🔐 Keycloak Admin: http://localhost:8080/admin"
	@echo "   Login: admin / admin"
	@echo ""
	@echo "🤖 Mock MCP Health: http://localhost:8081/health"
	@echo "🤖 Mock MCP Info: http://localhost:8081/mcp/info"
	@echo "🤖 Mock MCP Endpoint: http://localhost:8081/mcp"
	@echo ""
	@echo "🔑 Token Endpoint: http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token"

backup: ## Fazer backup dos dados do Keycloak
	@echo "💾 Fazendo backup do Keycloak..."
	docker-compose exec keycloak-db pg_dump -U keycloak -d keycloak > keycloak-backup-$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup salvo em keycloak-backup-*.sql"

# Quick start completo
quickstart: up setup ## Subir ambiente e configurar automaticamente
	@echo ""
	@echo "🎉 Ambiente pronto!"
	@echo ""
	@echo "📋 Próximos passos:"
	@echo "1. Acesse http://localhost:8080/admin (admin/admin)"  
	@echo "2. Copie o Client Secret de ser-mcp-client"
	@echo "3. Execute 'make test' (após configurar CLIENT_SECRET no teste)"
	@echo ""
	@echo "📚 Veja KEYCLOAK-SETUP.md para mais detalhes"

# Default
.DEFAULT_GOAL := help