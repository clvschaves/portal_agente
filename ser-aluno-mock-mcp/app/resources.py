"""MCP Resource handlers — alinhado com o contrato real do AWS MCP server."""
import logging
from typing import Dict, Any, Optional, List
from app.services.aluno_mock_service import AlunoMockService

logger = logging.getLogger(__name__)

# Schema base reutilizado pelas três rotas de disciplinas
_DISC_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "ra": {
            "type": "string",
            "description": "RA (Registro Acadêmico) do aluno"
        },
        "idHabilitacaoFilial": {
            "type": "integer",
            "description": "ID da habilitação filial"
        },
        "codColigada": {
            "type": "integer",
            "description": "Código da coligada"
        },
        "idPerLet": {
            "type": "integer",
            "description": (
                "ID do período letivo no banco (chave numérica que relaciona com codPerLet). "
                "Obrigatório preencher idPerLet ou codPerLet."
            )
        },
        "codPerLet": {
            "type": "string",
            "description": (
                "Código do período letivo (ex.: 20251 ou 2025.1 para 2025/1º semestre; "
                "pontos são removidos automaticamente). "
                "Obrigatório preencher idPerLet ou codPerLet."
            )
        },
        "codStatus": {
            "type": "integer",
            "description": "Código do status da matrícula (opcional)"
        },
        "status": {
            "type": "string",
            "description": "Status da matrícula por descrição (opcional)"
        },
        "idTurmaDisc": {
            "type": "integer",
            "description": "ID da turma disciplina (opcional)"
        }
    },
    "required": ["ra", "idHabilitacaoFilial", "codColigada"],
    "allOf": [
        {
            "anyOf": [
                {"required": ["idPerLet"]},
                {"required": ["codPerLet"]}
            ]
        }
    ]
}


class ResourceHandler:
    """Handler for MCP resources — espelho fiel do AWS MCP server."""

    def __init__(self, aluno_service: AlunoMockService):
        self.aluno_service = aluno_service

    def list_resources(self) -> List[Dict[str, Any]]:
        """Lista todos os recursos disponíveis, idêntico ao AWS MCP."""
        return [
            {
                "uri": "aluno:dados",
                "name": "Dados do Aluno",
                "description": "Retorna os dados cadastrais do aluno incluindo telefones, emails, endereço e informações pessoais",
                "mimeType": "application/json",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "codColigada": {
                            "type": "integer",
                            "description": "Código da coligada"
                        },
                        "ra": {
                            "type": "string",
                            "description": "RA (Registro Acadêmico) do aluno"
                        }
                    },
                    "required": ["codColigada", "ra"]
                }
            },
            {
                "uri": "aluno:cursos",
                "name": "Cursos do Aluno",
                "description": "Retorna os cursos/habilitações do aluno",
                "mimeType": "application/json",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ra": {
                            "type": "string",
                            "description": "RA (Registro Acadêmico) do aluno"
                        }
                    },
                    "required": ["ra"]
                }
            },
            {
                "uri": "aluno:disciplinas",
                "name": "Disciplinas matriculadas",
                "description": "Apenas dados de matrícula nas disciplinas (sem bloco de notas nem de faltas detalhadas).",
                "mimeType": "application/json",
                "inputSchema": _DISC_INPUT_SCHEMA
            },
            {
                "uri": "aluno:disciplinas-notas",
                "name": "Disciplinas + notas",
                "description": "Disciplinas matriculadas com campos de notas e médias.",
                "mimeType": "application/json",
                "inputSchema": _DISC_INPUT_SCHEMA
            },
            {
                "uri": "aluno:disciplinas-faltas",
                "name": "Disciplinas + faltas",
                "description": "Disciplinas matriculadas com campos de faltas.",
                "mimeType": "application/json",
                "inputSchema": _DISC_INPUT_SCHEMA
            },
            {
                "uri": "aluno:dados-escolares",
                "name": "Dados Escolares do Aluno",
                "description": "Retorna os dados escolares do aluno incluindo instituição de ensino do ensino médio",
                "mimeType": "application/json",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ra": {
                            "type": "string",
                            "description": "RA (Registro Acadêmico) do aluno"
                        }
                    },
                    "required": ["ra"]
                }
            }
        ]

    async def read_resource(self, uri: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """Rota principal — despacha para o handler correto baseado na URI."""
        uri_parts = uri.split(":")
        if len(uri_parts) != 2:
            raise ValueError(f"URI inválida: {uri}")

        resource_type = uri_parts[1]

        if resource_type == "dados":
            return await self._read_aluno_dados(arguments)
        elif resource_type == "cursos":
            return await self._read_cursos(arguments)
        elif resource_type == "disciplinas":
            return await self._read_disciplinas(arguments, mode="matricula")
        elif resource_type == "disciplinas-notas":
            return await self._read_disciplinas(arguments, mode="notas")
        elif resource_type == "disciplinas-faltas":
            return await self._read_disciplinas(arguments, mode="faltas")
        elif resource_type == "dados-escolares":
            return await self._read_dados_escolares(arguments)
        else:
            raise ValueError(f"Recurso desconhecido: {resource_type}")

    # ── helpers internos ─────────────────────────────────────────────────────

    @staticmethod
    def _normalize_cod_per_let(raw: str) -> str:
        """Remove pontos, espaços e hífens do período letivo (ex: '2025.1' → '20251')."""
        return str(raw).replace(".", "").replace(" ", "").replace("-", "")

    def _validate_disc_args(self, arguments: Optional[Dict]) -> Dict:
        """Valida e retorna os argumentos das rotas de disciplinas."""
        if not arguments:
            raise ValueError("ra, idHabilitacaoFilial e codColigada são obrigatórios")

        ra = arguments.get("ra")
        id_hab = arguments.get("idHabilitacaoFilial")
        cod_col = arguments.get("codColigada")
        id_per_let = arguments.get("idPerLet")
        cod_per_let = arguments.get("codPerLet")

        if not ra or id_hab is None or cod_col is None:
            raise ValueError("ra, idHabilitacaoFilial e codColigada são obrigatórios")

        if id_per_let is None and not cod_per_let:
            raise ValueError(
                "Informe idPerLet (ID numérico do período letivo no banco, relacionado a codPerLet) "
                "ou codPerLet (ex.: 20251 ou 2025.1; pontos são normalizados)."
            )

        if cod_per_let:
            cod_per_let = self._normalize_cod_per_let(cod_per_let)

        return {
            "ra": ra,
            "id_habilitacao_filial": int(id_hab),
            "cod_coligada": int(cod_col),
            "id_per_let": int(id_per_let) if id_per_let is not None else None,
            "cod_per_let": cod_per_let,
            "cod_status": arguments.get("codStatus"),
            "status": arguments.get("status"),
            "id_turma_disc": arguments.get("idTurmaDisc"),
        }

    # Campos de notas (presentes em aluno:disciplinas-notas)
    _NOTA_FIELDS = {
        "notaV1", "notaV2", "notaFinal", "mediaAluno",
        "mediaTurmaV1", "mediaTurmaV2", "mediaTurmaFinal", "mediaTurma",
        "dataAv1", "dataAv2", "dataAvFinal", "codConceito", "conceitoEcts",
        "mediaGeral", "mediaAv1", "mediaAv2", "mediaFinal",
    }
    # Campos de nota numérico (para incluir o campo 'nota' legado)
    _NOTA_FIELDS_ALL = _NOTA_FIELDS | {"nota"}

    # Campos de faltas (presentes em aluno:disciplinas-faltas)
    _FALTA_FIELDS = {
        "faltas", "faltasCometidas", "maximoFaltasDisciplina", "mediaFaltasTurma",
    }

    # Campos retornados em aluno:disciplinas (matrícula pura)
    _MATRICULA_KEEP = {
        "codDisc", "nomeDisc", "status", "codPerLet", "idPerLet",
        "codColigada", "idHabilitacaoFilial", "idTurmaDisc",
        "dtMatricula", "tipoMat", "codStatus",
    }

    async def _read_aluno_dados(self, arguments: Optional[Dict]) -> Dict:
        if not arguments:
            raise ValueError("codColigada e ra são obrigatórios")
        cod_coligada = arguments.get("codColigada")
        ra = arguments.get("ra")
        if cod_coligada is None or not ra:
            raise ValueError("codColigada e ra são obrigatórios")

        dados = await self.aluno_service.get_aluno_dados(cod_coligada, ra)
        if not dados:
            raise KeyError(f"Aluno não encontrado: RA {ra}")

        result = dados.model_dump(mode="json", by_alias=True, exclude_none=True)
        if not result or not result.get("pPessoa"):
            raise KeyError("Dados da pessoa não disponíveis")
        return result

    async def _read_cursos(self, arguments: Optional[Dict]) -> List[Dict]:
        if not arguments or not arguments.get("ra"):
            raise ValueError("ra é obrigatório")
        cursos = await self.aluno_service.get_aluno_cursos(arguments["ra"])
        return [c.model_dump(mode="json", by_alias=True, exclude_none=True) for c in cursos]

    async def _read_disciplinas(
        self, arguments: Optional[Dict], mode: str
    ) -> List[Dict]:
        """
        mode='matricula' → aluno:disciplinas (sem notas/faltas)
        mode='notas'     → aluno:disciplinas-notas
        mode='faltas'    → aluno:disciplinas-faltas
        """
        args = self._validate_disc_args(arguments)

        disciplinas = await self.aluno_service.get_aluno_disciplinas_full(**args)

        # Conjunto de campos de nota/falta p/ substituir None por "N/E"
        if mode == "notas":
            ne_fields = self._NOTA_FIELDS_ALL
        elif mode == "faltas":
            ne_fields = self._FALTA_FIELDS
        else:
            ne_fields = set()

        result = []
        for disc in disciplinas:
            try:
                raw = disc.model_dump(mode="json", by_alias=True, exclude_none=False)

                if mode == "matricula":
                    # Retorna apenas campos de matrícula — sem notas e sem faltas
                    filtered = {k: v for k, v in raw.items()
                                if k in self._MATRICULA_KEEP and v is not None}
                elif mode == "notas":
                    # Mantém matrícula + bloco de notas; substitui None por "N/E"
                    filtered = {k: v for k, v in raw.items()
                                if k not in self._FALTA_FIELDS}
                    filtered = {k: ("N/E" if v is None and k in ne_fields else v)
                                for k, v in filtered.items() if v is not None or k in ne_fields}
                else:  # mode == "faltas"
                    # Mantém campos mínimos + bloco de faltas; substitui None por "N/E"
                    base_keys = {"codDisc", "nomeDisc", "status"}
                    filtered = {k: v for k, v in raw.items()
                                if k not in self._NOTA_FIELDS_ALL or k in base_keys}
                    filtered = {k: ("N/E" if v is None and k in ne_fields else v)
                                for k, v in filtered.items() if v is not None or k in ne_fields}

                result.append(filtered)
            except Exception as e:
                logger.error(f"Erro ao serializar disciplina: {disc}, erro: {e}", exc_info=True)
                continue

        logger.info(f"Retornando {len(result)} disciplinas (mode={mode})")
        return result

    async def _read_dados_escolares(self, arguments: Optional[Dict]) -> Dict:
        if not arguments or not arguments.get("ra"):
            raise ValueError("ra é obrigatório")
        dados = await self.aluno_service.get_aluno_dados_escolares(arguments["ra"])
        if not dados:
            return {}
        return dados.model_dump(mode="json", by_alias=True, exclude_none=True)