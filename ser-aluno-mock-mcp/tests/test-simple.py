#!/usr/bin/env python3
"""
Script de teste simples para o Ser Aluno Mock MCP
Executa testes básicos para validar o funcionamento do mock
"""
import json
import os
import sys
import time
import requests
from typing import Dict, Any, Optional

# Configuração
KEYCLOAK_URL = "http://localhost:8080"
MOCK_MCP_URL = "http://localhost:8081"
REALM = "sereduc-mcps"
CLIENT_ID = "ser-mcp-client"

# Dados de teste
TEST_RA = "01493115"
TEST_COD_COLIGADA = 1
TEST_ID_HABILITACAO_FILIAL = 18486

def print_header(title: str):
    """Imprime cabeçalho formatado"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step: str):
    """Imprime passo do teste"""
    print(f"\n🔸 {step}")

def print_success(message: str):
    """Imprime mensagem de sucesso"""
    print(f"✅ {message}")

def print_error(message: str):
    """Imprime mensagem de erro"""
    print(f"❌ {message}")

def print_warning(message: str):
    """Imprime mensagem de aviso"""
    print(f"⚠️  {message}")

def wait_for_service(url: str, service_name: str, max_attempts: int = 30) -> bool:
    """Aguarda serviço ficar disponível"""
    print_step(f"Aguardando {service_name} ficar disponível...")
    
    for i in range(max_attempts):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 404]:  # 404 é OK para alguns endpoints
                print_success(f"{service_name} está respondendo")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < max_attempts - 1:
            print(f"   Tentativa {i+1}/{max_attempts}, aguardando...")
            time.sleep(2)
    
    print_error(f"{service_name} não ficou disponível após {max_attempts} tentativas")
    return False

def get_access_token(client_secret: str) -> Optional[str]:
    """Obtém token de acesso do Keycloak"""
    print_step("Obtendo token de acesso do Keycloak...")
    
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": client_secret
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if access_token:
            print_success("Token obtido com sucesso")
            return access_token
        else:
            print_error("Token não encontrado na resposta")
            return None
            
    except requests.exceptions.RequestException as e:
        print_error(f"Erro ao obter token: {e}")
        return None

def test_health_endpoints() -> bool:
    """Testa endpoints de health check"""
    print_step("Testando endpoints de health check...")
    
    # Test Keycloak health
    try:
        response = requests.get(f"{KEYCLOAK_URL}/health/ready", timeout=10)
        if response.status_code == 200:
            print_success("Keycloak health check OK")
        else:
            print_warning(f"Keycloak health check retornou {response.status_code}")
    except:
        print_error("Keycloak health check falhou")
        return False
    
    # Test Mock MCP health
    try:
        response = requests.get(f"{MOCK_MCP_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print_success(f"Mock MCP health check OK - Status: {health_data.get('status')}")
            if health_data.get('mock_mode'):
                print_success("Modo mock confirmado")
        else:
            print_error(f"Mock MCP health check falhou: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Mock MCP health check falhou: {e}")
        return False
    
    return True

def test_mcp_info(token: str) -> bool:
    """Testa endpoint de informações do MCP"""
    print_step("Testando endpoint de informações MCP...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{MOCK_MCP_URL}/mcp/info", headers=headers, timeout=10)
        if response.status_code == 200:
            info_data = response.json()
            print_success(f"MCP Info OK - Versão: {info_data.get('version')}")
            return True
        else:
            print_error(f"MCP Info falhou: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"MCP Info falhou: {e}")
        return False

def test_mcp_resources(token: str) -> bool:
    """Testa resources do MCP"""
    print_step("Testando resources do MCP...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test aluno:dados
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "resources/read",
        "params": {
            "uri": "aluno:dados",
            "arguments": {
                "codColigada": TEST_COD_COLIGADA,
                "ra": TEST_RA
            }
        }
    }
    
    try:
        response = requests.post(f"{MOCK_MCP_URL}/mcp", json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("result"):
                print_success("Resource aluno:dados OK")
                aluno_data = result["result"]["contents"][0]["text"]
                aluno_json = json.loads(aluno_data)
                print_success(f"  Aluno: {aluno_json.get('nome')} (RA: {aluno_json.get('ra')})")
                return True
            else:
                print_error(f"Resource aluno:dados falhou: {result.get('error')}")
                return False
        else:
            print_error(f"Resource aluno:dados falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Resource aluno:dados falhou: {e}")
        return False

def test_mcp_tools(token: str) -> bool:
    """Testa tools do MCP"""
    print_step("Testando tools do MCP...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test get_aluno_summary
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "get_aluno_summary",
            "arguments": {
                "ra": TEST_RA,
                "codColigada": TEST_COD_COLIGADA,
                "idHabilitacaoFilial": TEST_ID_HABILITACAO_FILIAL,
                "includeNotasFaltas": True
            }
        }
    }
    
    try:
        response = requests.post(f"{MOCK_MCP_URL}/mcp", json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("result"):
                print_success("Tool get_aluno_summary OK")
                summary_data = result["result"]["content"][0]["text"]
                print_success(f"  Resumo gerado com {len(summary_data)} caracteres")
                return True
            else:
                print_error(f"Tool get_aluno_summary falhou: {result.get('error')}")
                return False
        else:
            print_error(f"Tool get_aluno_summary falhou: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Tool get_aluno_summary falhou: {e}")
        return False

def main():
    """Função principal"""
    print_header("🧪 Teste do Ser Aluno Mock MCP")
    
    # Verificar se CLIENT_SECRET foi fornecido
    client_secret = os.getenv("CLIENT_SECRET")
    if not client_secret:
        print_warning("CLIENT_SECRET não definido como variável de ambiente")
        client_secret = input("Digite o Client Secret do Keycloak (ou ENTER para pular autenticação): ").strip()
        
        if not client_secret:
            print_warning("Pulando testes que requerem autenticação")
            # Só testa health checks
            if wait_for_service(f"{KEYCLOAK_URL}/health/ready", "Keycloak"):
                if wait_for_service(f"{MOCK_MCP_URL}/health", "Mock MCP"):
                    if test_health_endpoints():
                        print_header("✅ Testes básicos concluídos com sucesso!")
                        print("Para testes completos, configure CLIENT_SECRET e execute novamente.")
                        return 0
            print_header("❌ Testes básicos falharam")
            return 1
    
    # Aguardar serviços
    if not wait_for_service(f"{KEYCLOAK_URL}/health/ready", "Keycloak"):
        return 1
        
    if not wait_for_service(f"{MOCK_MCP_URL}/health", "Mock MCP"):
        return 1
    
    # Executar testes
    all_tests_passed = True
    
    # Health checks
    if not test_health_endpoints():
        all_tests_passed = False
    
    # Obter token
    token = get_access_token(client_secret)
    if not token:
        print_error("Não foi possível obter token de acesso")
        return 1
    
    # Testes com autenticação
    if not test_mcp_info(token):
        all_tests_passed = False
    
    if not test_mcp_resources(token):
        all_tests_passed = False
        
    if not test_mcp_tools(token):
        all_tests_passed = False
    
    # Resultado final
    if all_tests_passed:
        print_header("🎉 Todos os testes passaram!")
        print("\n📋 Dados de teste utilizados:")
        print(f"   RA: {TEST_RA}")
        print(f"   Coligada: {TEST_COD_COLIGADA}")
        print(f"   Habilitação: {TEST_ID_HABILITACAO_FILIAL}")
        print("\n🌐 URLs importantes:")
        print(f"   Keycloak Admin: {KEYCLOAK_URL}/admin")
        print(f"   Mock MCP: {MOCK_MCP_URL}")
        return 0
    else:
        print_header("❌ Alguns testes falharam")
        print("\n💡 Dicas:")
        print("   - Verifique se os serviços estão rodando: make ps")
        print("   - Veja os logs: make logs")
        print("   - Reconfigure o Keycloak: make setup")
        return 1

if __name__ == "__main__":
    sys.exit(main())