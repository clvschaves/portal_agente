"""Mock aluno service for local database."""
import json
import logging
from pathlib import Path
from typing import Optional, List

from config import settings
from app.models.aluno import AlunoDadosDto, PPessoaDto, AlunoDadosEscolaresDto
from app.models.curso import CursoDto
from app.models.disciplina import DisciplinaDto

logger = logging.getLogger(__name__)


class AlunoMockService:
    """Mock service for aluno data using local JSON database."""
    
    def __init__(self):
        """Initialize the mock service."""
        self.database_file = Path(settings.database_file)
        self._data = None
        self._load_data()
    
    def _load_data(self) -> None:
        """Load data from JSON file."""
        try:
            if self.database_file.exists():
                with open(self.database_file, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                logger.info(f"Loaded mock data from {self.database_file}")
            else:
                logger.warning(f"Database file not found: {self.database_file}")
                self._data = {"alunos": [], "cursos": [], "disciplinas": [], "dados_escolares": []}
        except Exception as e:
            logger.error(f"Error loading database file: {e}")
            self._data = {"alunos": [], "cursos": [], "disciplinas": [], "dados_escolares": []}
    
    async def get_aluno_dados(self, cod_coligada: int, ra: str) -> Optional[AlunoDadosDto]:
        """Get aluno dados cadastrais."""
        try:
            logger.info(f"Getting aluno dados for RA: {ra}, codColigada: {cod_coligada}")
            
            # Find aluno in mock data
            for aluno in self._data.get("alunos", []):
                if aluno["ra"] == ra and aluno["codColigada"] == cod_coligada:
                    # Convert to expected format
                    pessoa_data = aluno["pPessoa"]
                    pessoa = PPessoaDto(**pessoa_data)
                    
                    aluno_dados = AlunoDadosDto(pPessoa=pessoa)
                    logger.info(f"Found aluno dados: {aluno_dados.p_pessoa.nome}")
                    return aluno_dados
            
            logger.warning(f"Aluno not found for RA: {ra}, codColigada: {cod_coligada}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting aluno dados: {e}", exc_info=True)
            return None
    
    async def get_aluno_cursos(self, ra: str) -> List[CursoDto]:
        """Get aluno cursos/habilitações."""
        try:
            logger.info(f"Getting aluno cursos for RA: {ra}")
            
            cursos = []
            for curso in self._data.get("cursos", []):
                if curso["RA"] == ra:
                    curso_dto = CursoDto(**curso)
                    cursos.append(curso_dto)
            
            logger.info(f"Found {len(cursos)} cursos for RA: {ra}")
            return cursos
            
        except Exception as e:
            logger.error(f"Error getting aluno cursos: {e}", exc_info=True)
            return []
    
    async def get_aluno_disciplinas(
        self,
        ra: str,
        id_habilitacao_filial: int,
        cod_coligada: int,
        id_per_let: Optional[int] = None,
        cod_per_let: Optional[str] = None,
        cod_status: Optional[int] = None,
        status: Optional[str] = None,
        retornar_notas_faltas: bool = False,
        id_turma_disc: Optional[int] = None
    ) -> List[DisciplinaDto]:
        """Get aluno disciplinas matriculadas."""
        try:
            logger.info(f"Getting aluno disciplinas for RA: {ra}, idHabilitacaoFilial: {id_habilitacao_filial}")
            
            disciplinas = []
            for disciplina in self._data.get("disciplinas", []):
                # Filter by required parameters
                if (disciplina["RA"] != ra or 
                    disciplina["IDHABILITACAOFILIAL"] != id_habilitacao_filial or
                    disciplina["CODCOLIGADA"] != cod_coligada):
                    continue
                
                # Apply optional filters
                if id_per_let is not None and disciplina.get("IDPERLET") != id_per_let:
                    continue
                
                if cod_per_let is not None and disciplina.get("CODPERLET") != cod_per_let:
                    continue
                
                if cod_status is not None and disciplina.get("CODSTATUS") != cod_status:
                    continue
                
                if status is not None and disciplina.get("NOMESTATUS") != status:
                    continue
                
                if id_turma_disc is not None and disciplina.get("IDTURMADISC") != id_turma_disc:
                    continue
                
                # If retornar_notas_faltas is False, remove detailed grade fields
                if not retornar_notas_faltas:
                    disciplina_copy = disciplina.copy()
                    # Remove detailed fields
                    fields_to_remove = [
                        "NOTAV1", "NOTAV2", "NOTAFINAL", "MEDIAALUNO", "MEDIATURMAV1", "MEDIATURMAV2",
                        "MEDIATURMAFINAL", "MEDIATURMA", "DATAAV1", "DATAAV2", "DATAAVFINAL",
                        "FALTASCOMETIDAS", "MAXIMOFALTASDISCIPLINA", "MEDIAFALTASTURMA",
                        "CHPRATICA", "CHTEORICA", "TIPOTURMA", "CODTURMAUBIQUA", "DATAINICIOAULA",
                        "DATAFIMAULA", "DESCRICAORES", "DATA2CH", "MEDIAGERAL", "MEDIAAV1",
                        "MEDIAAV2", "MEDIAFINAL"
                    ]
                    for field in fields_to_remove:
                        disciplina_copy.pop(field, None)
                    
                    disciplina_dto = DisciplinaDto(**disciplina_copy)
                else:
                    disciplina_dto = DisciplinaDto(**disciplina)
                
                disciplinas.append(disciplina_dto)
            
            logger.info(f"Found {len(disciplinas)} disciplinas for RA: {ra}")
            return disciplinas
            
        except Exception as e:
            logger.error(f"Error getting aluno disciplinas: {e}", exc_info=True)
            return []
    
    async def get_aluno_dados_escolares(self, ra: str) -> Optional[AlunoDadosEscolaresDto]:
        """Get aluno dados escolares."""
        try:
            logger.info(f"Getting aluno dados escolares for RA: {ra}")
            
            # Find dados escolares in mock data
            for dados in self._data.get("dados_escolares", []):
                if dados["ra"] == ra:
                    dados_escolares = AlunoDadosEscolaresDto(**dados)
                    logger.info(f"Found dados escolares for RA: {ra}")
                    return dados_escolares
            
            logger.warning(f"Dados escolares not found for RA: {ra}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting aluno dados escolares: {e}", exc_info=True)
            return None