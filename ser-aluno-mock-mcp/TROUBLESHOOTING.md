# Troubleshooting - Ser Aluno Mock MCP

Guia rápido para resolver problemas comuns no ambiente mock.

## 🚨 Problemas Comuns

### 1. "Connection refused" ou serviços não respondem

**Sintomas:**

- `curl: (7) Failed to connect to localhost:8080`
- `Connection refused` nos logs
- `make health` mostra serviços indisponíveis

**Soluções:**

```bash
# Verificar se Docker está rodando
docker --version
docker ps

# Verificar status dos containers
make ps

# Se containers não estão rodando
make up

# Se ainda não funcionar, limpar e tentar novamente
make clean
make up

# Aguardar inicialização (pode levar 2-3 minutos)
make logs-keycloak
```

### 2. Keycloak demora para inicializar

**Sintomas:**

- Keycloak fica "Starting" por muito tempo
- Erro: `Waiting for server startup...`

**Soluções:**

```bash
# Aguardar mais tempo (normal: 2-3 minutos)
make logs-keycloak

# Verificar recursos da máquina (Keycloak precisa de memória)
docker stats

# Se muito lento, reiniciar com mais recursos
make down
# Fechar outros aplicativos
make up
```

### 3. Erro de autenticação "403 Forbidden"

**Sintomas:**

- `{"error":"invalid_client"}`
- `403 Forbidden` ao testar MCP
- Token inválido

**Soluções:**

```bash
# Reconfigurar Keycloak automaticamente
make setup

# Verificar se realm e client foram criados
make open-keycloak
# Navegar para: Realms > sereduc-mcps > Clients > ser-mcp-client

# Obter novo client secret
# No Keycloak Admin > Clients > ser-mcp-client > Credentials
```

### 4. Mock MCP não inicia

**Sintomas:**

- Container `ser-aluno-mock-mcp` com status `Exited`
- Erro no logs do mock

**Soluções:**

```bash
# Ver logs detalhados do mock
make logs-mock

# Verificar se imagem foi construída
make build

# Reiniciar apenas o mock
make restart-mock

# Se problema persistir, reconstruir
docker-compose build ser-aluno-mock-mcp --no-cache
make up
```

### 5. "Database connection failed" (PostgreSQL)

**Sintomas:**

- Keycloak não consegue conectar no banco
- Logs mostram erro de conexão com PostgreSQL

**Soluções:**

```bash
# Verificar se PostgreSQL está rodando
docker-compose logs keycloak-db

# Reiniciar banco
docker-compose restart keycloak-db
docker-compose restart keycloak

# Se problema persistir, limpar dados
make clean
make up
```

### 6. Client Secret não funciona

**Sintomas:**

- `{"error":"unauthorized_client"}`
- Testes falham com erro de autenticação

**Soluções:**

```bash
# 1. Obter client secret correto
make open-keycloak
# Ir para: Realms > sereduc-mcps > Clients > ser-mcp-client > Credentials

# 2. Testar token manualmente
curl -X POST http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=ser-mcp-client&client_secret=SEU_CLIENT_SECRET"

# 3. Se não funcionar, recriar client
make setup
```

### 7. Portas já em uso

**Sintomas:**

- `Port 8080 already in use`
- `Port 8081 already in use`

**Soluções:**

```bash
# Verificar o que está usando as portas
netstat -tulpn | grep :8080
netstat -tulpn | grep :8081

# Para Windows:
netstat -ano | findstr :8080
netstat -ano | findstr :8081

# Parar processos usando as portas ou alterar no docker-compose.yml
make down
# Editar docker-compose.yml para usar portas diferentes
make up
```

## 🔧 Comandos de Diagnóstico

### Verificar status geral

```bash
make health          # Status de todos os serviços
make ps              # Status dos containers
docker system df     # Uso de espaço do Docker
```

### Logs detalhados

```bash
make logs            # Todos os logs
make logs-keycloak   # Só Keycloak
make logs-mock       # Só Mock MCP
docker-compose logs --tail=50 keycloak-db  # PostgreSQL
```

### Testes manuais

```bash
# Health checks básicos
curl http://localhost:8080/health/ready
curl http://localhost:8081/health

# Teste simples interativo
make test-simple

# Info do MCP (sem auth)
curl http://localhost:8081/mcp/info
```

### Verificar configurações

```bash
# Ver variáveis de ambiente dos containers
docker-compose exec keycloak env | grep KEYCLOAK
docker-compose exec ser-aluno-mock-mcp env

# Verificar arquivos de configuração
docker-compose config
```

## 🆘 Reset Completo

Se nada funcionar, reset completo:

```bash
# Parar tudo e limpar
make clean

# Limpar imagens Docker (cuidado!)
docker image prune -f

# Reconstruir tudo
make build
make up

# Aguardar inicialização
sleep 180

# Configurar novamente
make setup

# Testar
make test-simple
```

## 🐛 Debug Avançado

### Entrar nos containers

```bash
make shell-keycloak  # Shell do Keycloak
make shell-mock      # Shell do Mock MCP

# Dentro do container, verificar:
ps aux               # Processos rodando
netstat -tlnp        # Portas abertas
env                  # Variáveis de ambiente
```

### Executar mock em modo desenvolvimento

```bash
# Parar container do mock
docker-compose stop ser-aluno-mock-mcp

# Executar localmente para debug
make dev
```

### Logs de startup do Keycloak

```bash
# Ver todo o processo de inicialização
docker-compose logs keycloak | head -100

# Ver se realm foi criado corretamente
docker-compose exec keycloak /opt/keycloak/bin/kcadm.sh get realms --server http://localhost:8080 --realm master --user admin --password admin
```

## 📞 Ainda tendo problemas?

1. Verifique os requisitos mínimos:
   - Docker 20.10+
   - Docker Compose 2.0+
   - 4GB RAM livres
   - Portas 8080 e 8081 livres

2. Veja a documentação completa:
   - [README.md](README.md)
   - [KEYCLOAK-SETUP.md](KEYCLOAK-SETUP.md)

3. Execute o diagnóstico completo:
   ```bash
   echo "=== Docker Info ===" && docker --version
   echo "=== Containers ===" && make ps
   echo "=== Health ===" && make health
   echo "=== Logs ===" && make logs --tail=20
   ```
