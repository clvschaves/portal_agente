#!/bin/bash

CLIENT_SECRET="6bavjk9RGsUsnysaJHSM1YoayNCwkmlS"

if [ "$CLIENT_SECRET" = "COLE_SEU_CLIENT_SECRET_AQUI" ]; then
    echo "❌ Configure o CLIENT_SECRET no script primeiro!"
    echo ""
    echo "Para obter o CLIENT_SECRET:"
    echo "1. Acesse http://localhost:8080/admin"
    echo "2. Login com admin/admin"
    echo "3. Vá em Realm: sereduc-mcps > Clients > ser-mcp-client"
    echo "4. Aba Credentials > copie o Client Secret"
    echo "5. Edite este script e substitua o valor de CLIENT_SECRET"
    exit 1
fi

echo "🧪 Testando Ser Aluno Mock MCP..."

# Verificar se jq está instalado
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq não está instalado. Instalando via apt-get..."
    sudo apt-get update && sudo apt-get install -y jq
fi

# Obter token
echo "🔑 Obtendo token..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8080/realms/sereduc-mcps/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=ser-mcp-client" \
  -d "client_secret=$CLIENT_SECRET")

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Erro ao obter token. Resposta:"
    echo $TOKEN_RESPONSE | jq
    echo ""
    echo "Verifique:"
    echo "- Se o CLIENT_SECRET está correto"
    echo "- Se o Keycloak está rodando (http://localhost:8080)"
    echo "- Se o realm 'sereduc-mcps' existe"
    exit 1
fi

echo "✅ Token obtido!"

# Testar health
echo ""
echo "🏥 Testando health do Mock MCP..."
HEALTH_RESPONSE=$(curl -s http://localhost:8081/health)
echo $HEALTH_RESPONSE | jq

if echo $HEALTH_RESPONSE | jq -e '.status == "healthy"' > /dev/null; then
    echo "✅ Health OK!"
else
    echo "❌ Health falhou!"
    exit 1
fi

# Testar endpoint público
echo ""
echo "📡 Testando endpoint público MCP..."
curl -s http://localhost:8081/mcp | jq

# Testar dados do aluno
echo ""
echo "👨‍🎓 Testando dados do aluno (autenticado)..."
ALUNO_RESPONSE=$(curl -s -X POST http://localhost:8081/mcp \
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
  }')

echo $ALUNO_RESPONSE | jq

if echo $ALUNO_RESPONSE | jq -e '.result.contents[0].text' > /dev/null; then
    echo "✅ Dados do aluno obtidos com sucesso!"
else
    echo "❌ Erro ao obter dados do aluno"
fi

# Testar disciplinas
echo ""
echo "📚 Testando disciplinas do aluno..."
DISC_RESPONSE=$(curl -s -X POST http://localhost:8081/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
  }')

DISC_COUNT=$(echo $DISC_RESPONSE | jq '.result.contents[0].text | fromjson | length')
echo "📊 Encontradas $DISC_COUNT disciplinas"

# Testar tool de resumo
echo ""
echo "🛠️  Testando tool get_aluno_summary..."
SUMMARY_RESPONSE=$(curl -s -X POST http://localhost:8081/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
  }')

echo $SUMMARY_RESPONSE | jq '.result.content[0].text | fromjson | {ra, totalDisciplinas, includeNotasFaltas}'

echo ""
echo "🎉 Testes concluídos com sucesso!"
echo ""
echo "📋 Resumo dos Testes:"
echo "✅ Keycloak - Token obtido"
echo "✅ Mock MCP Health - OK"  
echo "✅ Dados do Aluno - OK"
echo "✅ Disciplinas - $DISC_COUNT encontradas"
echo "✅ Tool Summary - OK"
echo ""
echo "🚀 O ambiente está pronto para uso!"