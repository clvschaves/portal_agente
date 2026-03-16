# Guia de Configuração do Keycloak para Ser Aluno Mock MCP

Este guia mostra como configurar o Keycloak para usar com o ser-aluno-mock-mcp.

## 🚀 Início Rápido

### 1. Subir o Ambiente

```bash
# No diretório ser-aluno-mock-mcp
docker-compose up -d

# Verificar status
docker-compose ps
```

### 2. Aguardar Serviços

```bash
# Aguardar Keycloak ficar pronto (pode levar alguns minutos)
docker-compose logs -f keycloak

# Quando ver "Keycloak ... started", está pronto
```

### 3. Acessar o Keycloak

- **URL**: http://localhost:8080
- **Admin**: `admin`
- **Senha**: `admin`

## 🔧 Configuração Passo a Passo

### 1. Criar Realm `sereduc-mcps`

1. **Acesse** http://localhost:8080/admin
2. **Login** com admin/admin
3. No menu superior esquerdo, clique em **"master"**
4. Clique em **"Create Realm"**
5. Configure:
   - **Realm name**: `sereduc-mcps`
   - **Enabled**: ✅ On
6. Clique em **"Create"**

### 2. Criar Client `ser-mcp-client`

1. No realm `sereduc-mcps`, vá em **Clients** no menu lateral
2. Clique em **"Create client"**
3. **General Settings**:
   - **Client type**: `OpenID Connect`
   - **Client ID**: `ser-mcp-client`
   - **Name**: `Ser MCP Client`
   - Clique em **"Next"**

4. **Capability config**:
   - **Client authentication**: ✅ On (para client credentials)
   - **Service accounts**: ✅ On
   - **Standard flow**: ✅ On (para testes via browser)
   - **Direct access grants**: ✅ On (para username/password)
   - Clique em **"Next"**

5. **Login settings** (deixar padrão):
   - Clique em **"Save"**

### 3. Configurar Client Settings

1. **Acessar o client** `ser-mcp-client`
2. Na aba **"Settings"**:
   - **Access Type**: `confidential`
   - **Service Accounts Enabled**: ✅ On
   - **Authorization Enabled**: ❌ Off (não necessário para nosso caso)

3. Na aba **"Credentials"**:
   - **Copie o Client Secret** (necessário para testes)

4. Na aba **"Service Account Roles"** (opcional):
   - Adicione roles se necessário para seu ambiente

## 🧪 Testes

### Método 1: Client Credentials Flow

```bash
# Obter token usando client credentials
curl -X POST http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=ser-mcp-client" \
  -d "client_secret=SEU_CLIENT_SECRET_AQUI"
```

### Método 2: Criar Usuário para Testes

#### 2.1 Criar Usuário

1. No realm `sereduc-mcps`, vá em **Users**
2. Clique em **"Add user"**
3. Configure:
   - **Username**: `testuser`
   - **Email**: `test@example.com`
   - **First name**: `Test`
   - **Last name**: `User`
   - **Email verified**: ✅ On
   - **Enabled**: ✅ On
4. Clique em **"Create"**

#### 2.2 Definir Senha

1. **Acessar o usuário** criado
2. Aba **"Credentials"**
3. Clique em **"Set password"**
4. Configure:
   - **Password**: `testpass123`
   - **Temporary**: ❌ Off
5. Clique em **"Set password"**

#### 2.3 Obter Token com Username/Password

```bash
curl -X POST http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=ser-mcp-client" \
  -d "client_secret=SEU_CLIENT_SECRET_AQUI" \
  -d "username=testuser" \
  -d "password=testpass123"
```

## ✅ Testando o Mock MCP

### 1. Verificar Health

```bash
curl http://localhost:8081/health
```

### 2. Testar sem Autenticação

```bash
# Endpoint público
curl http://localhost:8081/mcp
```

### 3. Testar com Autenticação

```bash
# Primeiro, obter token
TOKEN=$(curl -s -X POST http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=ser-mcp-client" \
  -d "client_secret=SEU_CLIENT_SECRET" \
  | jq -r '.access_token')

# Usar token para acessar dados do aluno
curl -X POST http://localhost:8081/mcp \
  -H "Authorization: Bearer $TOKEN" \
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

## 📋 Scripts Úteis

### Script de Setup Completo

Crie um arquivo `setup-keycloak.sh`:

```bash
#!/bin/bash

echo "🚀 Configurando Keycloak para Ser Aluno Mock MCP..."

# Aguardar Keycloak ficar pronto
echo "⏳ Aguardando Keycloak..."
until curl -s http://localhost:8080/health/ready > /dev/null; do
    echo "Aguardando Keycloak iniciar..."
    sleep 5
done

echo "✅ Keycloak pronto!"

# Obter admin token
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" \
  | jq -r '.access_token')

echo "🔑 Token admin obtido"

# Criar realm sereduc-mcps
curl -s -X POST http://localhost:8080/admin/realms \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "realm": "sereduc-mcps",
    "enabled": true,
    "displayName": "SerEduc MCPs"
  }'

echo "🌐 Realm sereduc-mcps criado"

# Criar client ser-mcp-client
curl -s -X POST http://localhost:8080/admin/realms/sereduc-mcps/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "ser-mcp-client",
    "name": "Ser MCP Client",
    "enabled": true,
    "clientAuthenticatorType": "client-secret",
    "serviceAccountsEnabled": true,
    "standardFlowEnabled": true,
    "directAccessGrantsEnabled": true,
    "protocol": "openid-connect"
  }'

echo "🔌 Client ser-mcp-client criado"

# Criar usuário de teste
curl -s -X POST http://localhost:8080/admin/realms/sereduc-mcps/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "firstName": "Test",
    "lastName": "User",
    "enabled": true,
    "emailVerified": true,
    "credentials": [{
      "type": "password",
      "value": "testpass123",
      "temporary": false
    }]
  }'

echo "👤 Usuário testuser criado"

echo ""
echo "🎉 Setup completo!"
echo ""
echo "📝 Próximos passos:"
echo "1. Acesse http://localhost:8080/admin (admin/admin)"
echo "2. Vá no client 'ser-mcp-client' > Credentials"
echo "3. Copie o Client Secret"
echo "4. Use para obter tokens!"
echo ""
echo "🧪 Teste rápido:"
echo "curl http://localhost:8081/health"
```

### Script de Teste

Crie um arquivo `test-mock.sh`:

```bash
#!/bin/bash

CLIENT_SECRET="COLE_SEU_CLIENT_SECRET_AQUI"

if [ "$CLIENT_SECRET" = "COLE_SEU_CLIENT_SECRET_AQUI" ]; then
    echo "❌ Configure o CLIENT_SECRET no script primeiro!"
    exit 1
fi

echo "🧪 Testando Ser Aluno Mock MCP..."

# Obter token
echo "🔑 Obtendo token..."
TOKEN=$(curl -s -X POST http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=ser-mcp-client" \
  -d "client_secret=$CLIENT_SECRET" \
  | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Erro ao obter token. Verifique o CLIENT_SECRET."
    exit 1
fi

echo "✅ Token obtido!"

# Testar health
echo "🏥 Testando health..."
curl -s http://localhost:8081/health | jq

# Testar dados do aluno
echo "👨‍🎓 Testando dados do aluno..."
curl -s -X POST http://localhost:8081/mcp \
  -H "Authorization: Bearer $TOKEN" \
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
  }' | jq

echo "🎉 Testes concluídos!"
```

## 🔧 Troubleshooting

### Problema: Keycloak não inicia

```bash
# Verificar logs
docker-compose logs keycloak

# Limpar dados (cuidado: apaga tudo)
docker-compose down -v
docker-compose up -d
```

### Problema: Token inválido

1. Verificar se o client secret está correto
2. Verificar se o realm name está correto (`sereduc-mcps`)
3. Verificar se o client está habilitado

### Problema: Mock MCP não conecta no Keycloak

```bash
# Verificar conectividade
docker exec ser-aluno-mock-mcp curl http://keycloak:8080/health/ready
```

## 🎯 Resumo URLs

- **Keycloak Admin**: http://localhost:8080/admin
- **Mock MCP Health**: http://localhost:8081/health
- **Mock MCP Info**: http://localhost:8081/mcp/info
- **Token Endpoint**: http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token

## ⚠️ Uso em Produção

Este setup é para **desenvolvimento/testes**. Para produção:

1. Altere senhas padrão
2. Configure HTTPS
3. Use volumes persistentes
4. Configure backup do banco
5. Ajuste configurações de segurança do Keycloak
