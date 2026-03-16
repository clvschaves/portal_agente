"""MCP Tool handlers."""
import logging
from typing import Dict, Any, Optional
from app.services.aluno_mock_service import AlunoMockService

logger = logging.getLogger(__name__)


class ToolHandler:
    """Handler for MCP tools."""
    
    def __init__(self, aluno_service: AlunoMockService):
        """Initialize tool handler."""
        self.aluno_service = aluno_service
    
    def list_tools(self) -> list[Dict[str, Any]]:
        """List available tools."""
        return [
            {
                "name": "get_aluno_summary",
                "description": "Obtém um resumo completo dos dados do aluno (dados pessoais, cursos e disciplinas)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ra": {
                            "type": "string",
                            "description": "RA (Registro Acadêmico) do aluno"
                        },
                        "codColigada": {
                            "type": "integer",
                            "description": "Código da coligada"
                        },
                        "idHabilitacaoFilial": {
                            "type": "integer",
                            "description": "ID da habilitação filial"
                        },
                        "includeNotasFaltas": {
                            "type": "boolean",
                            "description": "Se true, inclui notas e faltas detalhadas",
                            "default": False
                        }
                    },
                    "required": ["ra", "codColigada", "idHabilitacaoFilial"]
                }
            }
        ]
    
    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool."""
        if name == "get_aluno_summary":
            return await self._get_aluno_summary(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    async def _get_aluno_summary(self, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get aluno summary with all data."""
        if not arguments:
            raise ValueError("ra, codColigada and idHabilitacaoFilial are required")
        
        ra = arguments.get("ra")
        cod_coligada = arguments.get("codColigada")
        id_habilitacao_filial = arguments.get("idHabilitacaoFilial")
        include_notas_faltas = arguments.get("includeNotasFaltas", False)
        
        if not ra or cod_coligada is None or id_habilitacao_filial is None:
            raise ValueError("ra, codColigada and idHabilitacaoFilial are required")
        
        try:
            # Get all data
            dados = await self.aluno_service.get_aluno_dados(cod_coligada, ra)
            cursos = await self.aluno_service.get_aluno_cursos(ra)
            disciplinas = await self.aluno_service.get_aluno_disciplinas(
                ra=ra,
                id_habilitacao_filial=id_habilitacao_filial,
                cod_coligada=cod_coligada,
                retornar_notas_faltas=include_notas_faltas
            )
            dados_escolares = await self.aluno_service.get_aluno_dados_escolares(ra)
            
            # Build summary
            summary = {
                "ra": ra,
                "codColigada": cod_coligada,
                "idHabilitacaoFilial": id_habilitacao_filial,
                "dadosPessoais": dados.model_dump(mode="json", by_alias=True, exclude_none=True) if dados else None,
                "cursos": [curso.model_dump(mode="json", by_alias=True, exclude_none=True) for curso in cursos],
                "disciplinas": [disc.model_dump(mode="json", by_alias=True, exclude_none=True) for disc in disciplinas],
                "dadosEscolares": dados_escolares.model_dump(mode="json", by_alias=True, exclude_none=True) if dados_escolares else None,
                "includeNotasFaltas": include_notas_faltas,
                "totalDisciplinas": len(disciplinas)
            }
            
            logger.info(f"Summary gerado para RA {ra}: {len(disciplinas)} disciplinas, includeNotasFaltas={include_notas_faltas}")
            return summary
            
        except Exception as e:
            logger.error(f"Error getting aluno summary: {e}", exc_info=True)
            raise