"""MCP Resource handlers."""
import logging
from typing import Dict, Any, Optional, List
from app.services.aluno_mock_service import AlunoMockService

logger = logging.getLogger(__name__)


class ResourceHandler:
    """Handler for MCP resources."""
    
    def __init__(self, aluno_service: AlunoMockService):
        """Initialize resource handler."""
        self.aluno_service = aluno_service
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
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
                "name": "Disciplinas Matriculadas / Notas e Faltas",
                "description": "Retorna as disciplinas matriculadas do aluno. Quando retornarNotasFaltas=true, busca todas as notas e faltas disponíveis e faz merge com as disciplinas filtradas.",
                "mimeType": "application/json",
                "inputSchema": {
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
                            "description": "ID do período letivo (opcional - filtra por período específico)"
                        },
                        "codPerLet": {
                            "type": "string",
                            "description": "Código do período letivo (opcional - filtra por período específico)"
                        },
                        "codStatus": {
                            "type": "integer",
                            "description": "Código do status da matrícula (opcional - filtra por status específico)"
                        },
                        "status": {
                            "type": "string",
                            "description": "Status da matrícula por descrição (opcional - filtra por status específico)"
                        },
                        "retornarNotasFaltas": {
                            "type": "boolean",
                            "description": "Se true, retorna notas e faltas detalhadas. Quando true, busca todas as notas/faltas disponíveis e faz merge com as disciplinas filtradas pelos outros parâmetros."
                        },
                        "idTurmaDisc": {
                            "type": "integer",
                            "description": "ID da turma disciplina (opcional - filtra por turma específica). Nota: quando retornarNotasFaltas=true, este filtro aplica-se apenas às matrículas, mas as notas/faltas são buscadas de todas as turmas para fazer o merge."
                        }
                    },
                    "required": ["ra", "idHabilitacaoFilial", "codColigada"]
                }
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
    
    async def read_resource(self, uri: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Read a resource."""
        uri_parts = uri.split(":")
        if len(uri_parts) != 2:
            raise ValueError(f"Invalid resource URI: {uri}")
        
        resource_type = uri_parts[1]
        
        if resource_type == "dados":
            return await self._read_aluno_dados(arguments)
        elif resource_type == "cursos":
            return await self._read_cursos(arguments)
        elif resource_type == "disciplinas":
            return await self._read_disciplinas(arguments)
        elif resource_type == "dados-escolares":
            return await self._read_dados_escolares(arguments)
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")
    
    async def _read_aluno_dados(self, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Read aluno dados."""
        if not arguments:
            raise ValueError("codColigada and ra are required")
        
        cod_coligada = arguments.get("codColigada")
        ra = arguments.get("ra")
        
        if cod_coligada is None or not ra:
            raise ValueError("codColigada and ra are required")
        
        dados = await self.aluno_service.get_aluno_dados(cod_coligada, ra)
        
        if not dados:
            logger.warning(f"Aluno não encontrado: RA {ra}, codColigada {cod_coligada}")
            raise KeyError("Aluno não encontrado")
        
        # Convert Pydantic model to dict with camelCase
        result_final = dados.model_dump(mode="json", by_alias=True, exclude_none=True)
        logger.info(f"model_dump result: {result_final}, keys: {list(result_final.keys())}")
        
        # Verificar se o resultado está vazio ou se pPessoa está None/vazio
        if not result_final:
            logger.warning(f"Aluno dados retornou dict vazio para RA {ra}, codColigada {cod_coligada}")
            raise KeyError("Dados do aluno não disponíveis")
        
        # Se pPessoa estiver None ou vazio, também considerar como erro
        p_pessoa = result_final.get("pPessoa")
        if not p_pessoa or (isinstance(p_pessoa, dict) and not p_pessoa):
            logger.warning(f"Aluno dados sem pPessoa válido para RA {ra}, codColigada {cod_coligada}")
            logger.warning(f"Resultado completo: {result_final}")
            raise KeyError("Dados da pessoa não disponíveis")
        
        logger.info(f"Aluno dados retornado com sucesso para RA {ra}: {list(result_final.keys())}, pPessoa keys: {list(p_pessoa.keys()) if isinstance(p_pessoa, dict) else 'not a dict'}")
        return result_final
    
    async def _read_cursos(self, arguments: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Read cursos."""
        if not arguments:
            raise ValueError("ra is required")
        
        ra = arguments.get("ra")
        if not ra:
            raise ValueError("ra is required")
        
        cursos = await self.aluno_service.get_aluno_cursos(ra)
        return [curso.model_dump(mode="json", by_alias=True, exclude_none=True) for curso in cursos]
    
    async def _read_disciplinas(self, arguments: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Read disciplinas."""
        if not arguments:
            raise ValueError("ra, idHabilitacaoFilial and codColigada are required")
        
        ra = arguments.get("ra")
        id_habilitacao_filial = arguments.get("idHabilitacaoFilial")
        cod_coligada = arguments.get("codColigada")
        
        if not ra or id_habilitacao_filial is None or cod_coligada is None:
            raise ValueError("ra, idHabilitacaoFilial and codColigada are required")
        
        retornar_notas_faltas = arguments.get("retornarNotasFaltas", False)
        logger.info(
            f"Buscando disciplinas para RA {ra}, idHabilitacaoFilial {id_habilitacao_filial}, "
            f"codColigada {cod_coligada}, retornarNotasFaltas={retornar_notas_faltas}"
        )
        
        disciplinas = await self.aluno_service.get_aluno_disciplinas(
            ra=ra,
            id_habilitacao_filial=id_habilitacao_filial,
            cod_coligada=cod_coligada,
            id_per_let=arguments.get("idPerLet"),
            cod_per_let=arguments.get("codPerLet"),
            cod_status=arguments.get("codStatus"),
            status=arguments.get("status"),
            retornar_notas_faltas=retornar_notas_faltas,
            id_turma_disc=arguments.get("idTurmaDisc")
        )
        
        logger.info(f"Recebidas {len(disciplinas)} disciplinas do serviço")
        
        # Campos de nota e falta que devem retornar "N/E" quando ausentes
        nota_falta_fields = {
            'nota', 'notaV1', 'notaV2', 'notaFinal', 'mediaAluno',
            'mediaTurmaV1', 'mediaTurmaV2', 'mediaTurmaFinal', 'mediaTurma',
            'mediaGeral', 'mediaAv1', 'mediaAv2', 'mediaFinal',
            'faltas', 'faltasCometidas', 'maximoFaltasDisciplina', 'mediaFaltasTurma'
        }
        
        result = []
        for disc in disciplinas:
            try:
                # Primeiro fazer dump sem excluir None para ter acesso a todos os campos
                disc_dict = disc.model_dump(mode="json", by_alias=True, exclude_none=False)
                # Substituir None por "N/E" nos campos de nota e falta
                for field in nota_falta_fields:
                    if field in disc_dict and disc_dict[field] is None:
                        disc_dict[field] = "N/E"
                # Agora remover outros campos None (mantendo apenas os de nota/falta com "N/E")
                disc_dict = {k: v for k, v in disc_dict.items() if v is not None or k in nota_falta_fields}
                logger.debug(f"Disciplina serializada: {disc_dict}")
                result.append(disc_dict)
            except Exception as e:
                logger.error(f"Erro ao serializar disciplina: {disc}, erro: {e}", exc_info=True)
                # Continuar processando outras disciplinas mesmo se uma falhar
                continue
        
        logger.info(f"Retornando {len(result)} disciplinas serializadas")
        return result
    
    async def _read_dados_escolares(self, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Read dados escolares."""
        if not arguments:
            raise ValueError("ra is required")
        
        ra = arguments.get("ra")
        if not ra:
            raise ValueError("ra is required")
        
        dados_escolares = await self.aluno_service.get_aluno_dados_escolares(ra)
        
        if not dados_escolares:
            logger.warning(f"Dados escolares não encontrados para RA {ra}")
            # Retornar objeto vazio em vez de erro, pois pode não ter dados cadastrados
            return {}
        
        # Convert Pydantic model to dict with camelCase
        result = dados_escolares.model_dump(mode="json", by_alias=True, exclude_none=True)
        logger.info(f"Dados escolares retornados com sucesso para RA {ra}: {list(result.keys())}")
        return result