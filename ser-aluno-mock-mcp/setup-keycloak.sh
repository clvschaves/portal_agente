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