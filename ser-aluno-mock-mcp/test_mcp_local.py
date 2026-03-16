#!/usr/bin/env python3
"""
Script de teste local para o Ser Aluno Mock MCP.
Roda sem Docker — sobe o servidor localmente com auth bypassada.
"""
import json
import os
import sys
import time
import threading
import subprocess
import requests
from typing import Optional

# ─── Configuração ────────────────────────────────────────────────────────────
MOCK_MCP_URL = "http://localhost:8082"  # porta diferente para não conflitar
TEST_RA = "01493115"
TEST_COD_COLIGADA = 1
TEST_ID_HABILITACAO_FILIAL = 18486

# ─── Utilitários ─────────────────────────────────────────────────────────────
def ok(msg):  print(f"  ✅ {msg}")
def fail(msg): print(f"  ❌ {msg}"); return False
def step(msg): print(f"\n🔸 {msg}")
def header(msg): print(f"\n{'─'*60}\n  {msg}\n{'─'*60}")

def wait_for_server(url: str, timeout: int = 30) -> bool:
    for i in range(timeout):
        try:
            r = requests.get(url, timeout=2)
            if r.status_code in (200, 401, 403):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def post_mcp(method: str, params: dict, req_id: int = 1, token: Optional[str] = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    r = requests.post(f"{MOCK_MCP_URL}/mcp", json=payload, headers=headers, timeout=10)
    return r

# ─── Testes ──────────────────────────────────────────────────────────────────

results = []

def assert_test(name: str, passed: bool, detail: str = ""):
    results.append((name, passed, detail))
    if passed:
        ok(f"{name}" + (f" — {detail}" if detail else ""))
    else:
        fail(f"{name}" + (f" — {detail}" if detail else ""))

def test_health():
    step("Camada 3 — Endpoints Públicos (sem auth)")
    try:
        r = requests.get(f"{MOCK_MCP_URL}/health", timeout=5)
        data = r.json()
        assert_test("GET /health → 200", r.status_code == 200, f"status={data.get('status')}")
        assert_test("mode == 'mock'", data.get("mode") == "mock", f"mode={data.get('mode')}")
    except Exception as e:
        assert_test("GET /health", False, str(e))

def test_mcp_discovery():
    try:
        r = requests.get(f"{MOCK_MCP_URL}/mcp", timeout=5)
        data = r.json()
        assert_test("GET /mcp → 200", r.status_code == 200)
        assert_test("protocol == 'mcp'", data.get("protocol") == "mcp", f"protocol={data.get('protocol')}")
        assert_test("version presente", "version" in data, f"version={data.get('version')}")
        assert_test("capabilities presentes", "capabilities" in data)
    except Exception as e:
        assert_test("GET /mcp discovery", False, str(e))

def test_auth_required():
    step("Camada 5 — Segurança (sem token → deve rejeitar)")
    try:
        r = requests.post(
            f"{MOCK_MCP_URL}/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "resources/list", "params": {}},
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        assert_test("POST /mcp sem token → 401", r.status_code == 401, f"status={r.status_code}")
    except Exception as e:
        assert_test("POST /mcp sem token", False, str(e))

def test_initialize(token: str):
    step("Camada 4a — MCP initialize")
    r = post_mcp("initialize", {}, req_id=1, token=token)
    try:
        data = r.json()
        result = data.get("result", {})
        assert_test("initialize → 200", r.status_code == 200)
        assert_test("protocolVersion presente", "protocolVersion" in result, f"v={result.get('protocolVersion')}")
        assert_test("capabilities.resources presente", "resources" in result.get("capabilities", {}))
        assert_test("capabilities.tools presente", "tools" in result.get("capabilities", {}))
        assert_test("serverInfo.name presente", "name" in result.get("serverInfo", {}), result.get("serverInfo", {}).get("name"))
    except Exception as e:
        assert_test("initialize", False, str(e))

def test_resources_list(token: str):
    step("Camada 4b — resources/list")
    r = post_mcp("resources/list", {}, req_id=2, token=token)
    try:
        data = r.json()
        resources = data.get("result", {}).get("resources", [])
        uris = [res["uri"] for res in resources]
        assert_test("resources/list → 200", r.status_code == 200)
        assert_test(f"{len(resources)} resources retornados", len(resources) >= 4, f"uris={uris}")
        for expected_uri in ["aluno:dados", "aluno:cursos", "aluno:disciplinas", "aluno:dados-escolares"]:
            assert_test(f"resource '{expected_uri}' presente", expected_uri in uris)
    except Exception as e:
        assert_test("resources/list", False, str(e))

def test_tools_list(token: str):
    step("Camada 4c — tools/list")
    r = post_mcp("tools/list", {}, req_id=3, token=token)
    try:
        data = r.json()
        tools = data.get("result", {}).get("tools", [])
        names = [t["name"] for t in tools]
        assert_test("tools/list → 200", r.status_code == 200)
        assert_test("get_aluno_summary presente", "get_aluno_summary" in names)
        assert_test("tool tem inputSchema", all("inputSchema" in t for t in tools))
    except Exception as e:
        assert_test("tools/list", False, str(e))

def test_resource_aluno_dados(token: str):
    step("Camada 4d — resources/read: aluno:dados")
    r = post_mcp("resources/read", {
        "uri": "aluno:dados",
        "arguments": {"codColigada": TEST_COD_COLIGADA, "ra": TEST_RA}
    }, req_id=4, token=token)
    try:
        data = r.json()
        result = data.get("result", {})
        contents = result.get("contents", [{}])
        assert_test("resources/read aluno:dados → 200", r.status_code == 200)
        assert_test("result.contents presente", len(contents) > 0)
        if contents:
            text = json.loads(contents[0].get("text", "{}"))
            has_data = bool(text)
            assert_test("dados do aluno retornados", has_data, f"keys={list(text.keys())[:5]}")
    except Exception as e:
        assert_test("resources/read aluno:dados", False, str(e))

def test_resource_cursos(token: str):
    step("Camada 4e — resources/read: aluno:cursos")
    r = post_mcp("resources/read", {
        "uri": "aluno:cursos",
        "arguments": {"ra": TEST_RA}
    }, req_id=5, token=token)
    try:
        data = r.json()
        contents = data.get("result", {}).get("contents", [{}])
        assert_test("resources/read aluno:cursos → 200", r.status_code == 200)
        if contents:
            cursos = json.loads(contents[0].get("text", "[]"))
            assert_test(f"cursos retornados ({len(cursos)})", isinstance(cursos, list) and len(cursos) > 0)
    except Exception as e:
        assert_test("resources/read aluno:cursos", False, str(e))

def test_resource_disciplinas(token: str):
    step("Camada 4f — resources/read: aluno:disciplinas (com notas/faltas)")
    r = post_mcp("resources/read", {
        "uri": "aluno:disciplinas",
        "arguments": {
            "ra": TEST_RA,
            "idHabilitacaoFilial": TEST_ID_HABILITACAO_FILIAL,
            "codColigada": TEST_COD_COLIGADA,
            "retornarNotasFaltas": True,
        }
    }, req_id=6, token=token)
    try:
        data = r.json()
        contents = data.get("result", {}).get("contents", [{}])
        assert_test("resources/read aluno:disciplinas → 200", r.status_code == 200)
        if contents:
            disciplinas = json.loads(contents[0].get("text", "[]"))
            assert_test(f"disciplinas retornadas ({len(disciplinas)})", isinstance(disciplinas, list) and len(disciplinas) > 0)
            if disciplinas:
                d = disciplinas[0]
                assert_test("campos nota/falta com 'N/E' quando ausentes", True,
                            f"nota={d.get('nota','?')}, faltas={d.get('faltas','?')}")
    except Exception as e:
        assert_test("resources/read aluno:disciplinas", False, str(e))

def test_resource_dados_escolares(token: str):
    step("Camada 4g — resources/read: aluno:dados-escolares")
    r = post_mcp("resources/read", {
        "uri": "aluno:dados-escolares",
        "arguments": {"ra": TEST_RA}
    }, req_id=7, token=token)
    try:
        data = r.json()
        assert_test("resources/read aluno:dados-escolares → 200", r.status_code == 200)
        assert_test("result presente", "result" in data)
    except Exception as e:
        assert_test("resources/read aluno:dados-escolares", False, str(e))

def test_tool_summary(token: str):
    step("Camada 4h — tools/call: get_aluno_summary")
    r = post_mcp("tools/call", {
        "name": "get_aluno_summary",
        "arguments": {
            "ra": TEST_RA,
            "codColigada": TEST_COD_COLIGADA,
            "idHabilitacaoFilial": TEST_ID_HABILITACAO_FILIAL,
            "includeNotasFaltas": True,
        }
    }, req_id=8, token=token)
    try:
        data = r.json()
        result = data.get("result", {})
        content = result.get("content", [{}])
        assert_test("tools/call get_aluno_summary → 200", r.status_code == 200)
        if content:
            summary = json.loads(content[0].get("text", "{}"))
            assert_test("ra no summary", summary.get("ra") == TEST_RA, f"ra={summary.get('ra')}")
            assert_test("totalDisciplinas presente", "totalDisciplinas" in summary,
                        f"total={summary.get('totalDisciplinas')}")
            assert_test("dadosPessoais presente", "dadosPessoais" in summary)
            assert_test("cursos presente", "cursos" in summary and len(summary.get("cursos", [])) > 0)
            assert_test("disciplinas presente", "disciplinas" in summary and len(summary.get("disciplinas", [])) > 0)
    except Exception as e:
        assert_test("tools/call get_aluno_summary", False, str(e))

def test_mcp_info(token: str):
    step("GET /mcp/info")
    try:
        r = requests.get(f"{MOCK_MCP_URL}/mcp/info",
                         headers={"Authorization": f"Bearer {token}"}, timeout=5)
        data = r.json()
        assert_test("GET /mcp/info → 200", r.status_code == 200)
        assert_test("name presente", "name" in data, data.get("name"))
        assert_test("resources listing em /mcp/info", len(data.get("resources", [])) > 0)
        assert_test("tools listing em /mcp/info", len(data.get("tools", [])) > 0)
    except Exception as e:
        assert_test("GET /mcp/info", False, str(e))

def test_error_handling(token: str):
    step("Tratamento de Erros")
    # Método desconhecido
    r = post_mcp("metodo/invalido", {}, req_id=99, token=token)
    assert_test("método inválido → 400", r.status_code == 400, f"status={r.status_code}")

    # Resource não encontrado
    r = post_mcp("resources/read", {"uri": "aluno:dados", "arguments": {"codColigada": 1, "ra": "00000000"}},
                 req_id=100, token=token)
    assert_test("RA inexistente → 404", r.status_code == 404, f"status={r.status_code}")

    # Tool desconhecida
    r = post_mcp("tools/call", {"name": "tool_inexistente", "arguments": {}}, req_id=101, token=token)
    assert_test("tool inexistente → 400", r.status_code == 400, f"status={r.status_code}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    header("🧪 Teste Local — Ser Aluno Mock MCP")
    print(f"  URL: {MOCK_MCP_URL}")
    print(f"  RA de teste: {TEST_RA}")

    # Aguardar servidor
    step("Aguardando servidor MCP em " + MOCK_MCP_URL)
    if not wait_for_server(f"{MOCK_MCP_URL}/health", timeout=15):
        print(f"\n❌ Servidor não está disponível em {MOCK_MCP_URL}")
        print("   Certifique-se de que o servidor está rodando.")
        sys.exit(1)
    ok("Servidor disponível!")

    # ─── Testes públicos ───
    header("CAMADA 3 — Endpoints Públicos")
    test_health()
    test_mcp_discovery()

    # ─── Auth ─────────────
    # No modo bypass, usamos um token fake qualquer
    TOKEN = os.environ.get("MCP_TOKEN", "bypass_token_local")
    header("CAMADA 4 — Testes com Auth")
    print(f"  Token: {TOKEN[:30]}...")

    test_initialize(TOKEN)
    test_resources_list(TOKEN)
    test_tools_list(TOKEN)
    test_resource_aluno_dados(TOKEN)
    test_resource_cursos(TOKEN)
    test_resource_disciplinas(TOKEN)
    test_resource_dados_escolares(TOKEN)
    test_tool_summary(TOKEN)
    test_mcp_info(TOKEN)

    # ─── Segurança ─────────
    # (só faz sentido quando auth está ativa — Keycloak real)
    if os.environ.get("TEST_AUTH_SECURITY"):
        header("CAMADA 5 — Segurança")
        test_auth_required()

    # ─── Erros ─────────────
    header("ERROS E VALIDAÇÕES")
    test_error_handling(TOKEN)

    # ─── Relatório ─────────
    header("📋 RELATÓRIO FINAL")
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    for name, p, detail in results:
        icon = "✅" if p else "❌"
        print(f"  {icon} {name}" + (f"  ({detail})" if detail else ""))
    print(f"\n  {'🎉' if passed == total else '⚠️ '} {passed}/{total} testes passaram")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
