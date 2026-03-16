"""Curso data models."""
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class CursoDto(BaseModel):
    """Curso/Habilitação data model."""
    model_config = ConfigDict(populate_by_name=True)
    
    cod_coligada: int = Field(alias="CODCOLIGADA", serialization_alias="codColigada")
    id_habilitacao_filial: int = Field(alias="IDHABILITACAOFILIAL", serialization_alias="idHabilitacaoFilial")
    ra: Optional[str] = Field(default=None, alias="RA")
    cod_curso: Optional[str] = Field(default=None, alias="CODCURSO", serialization_alias="codCurso")
    cod_habilitacao: Optional[str] = Field(default=None, alias="CODHABILITACAO", serialization_alias="codHabilitacao")
    cod_status: Optional[str] = Field(default=None, alias="CODSTATUS", serialization_alias="codStatus")
    cod_grade: Optional[str] = Field(default=None, alias="CODGRADE", serialization_alias="codGrade")
    cod_filial: Optional[int] = Field(default=None, alias="CODFILIAL", serialization_alias="codFilial")
    cod_turno: Optional[int] = Field(default=None, alias="CODTURNO", serialization_alias="codTurno")
    nome_curso: Optional[str] = Field(default=None, alias="NOMECURSO", serialization_alias="nomeCurso")
    data_matricula: Optional[str] = Field(default=None, alias="DATAMATRICULA", serialization_alias="dataMatricula")
    data_conclusao: Optional[str] = Field(default=None, alias="DATACONCLUSAO", serialization_alias="dataConclusao")
    
    @model_validator(mode='before')
    @classmethod
    def normalize_empty_strings(cls, data: Any) -> Any:
        """Convert empty strings to None for optional integer fields."""
        if isinstance(data, dict):
            # Campos opcionais que são inteiros
            int_fields = ['CODTURNO', 'CODFILIAL']
            for field in int_fields:
                if field in data and data[field] == '':
                    data[field] = None
        return data
    
    @field_validator('cod_turno', 'cod_filial', mode='before')
    @classmethod
    def parse_int_or_none(cls, v: Any) -> Optional[int]:
        """Parse integer or return None if empty string or None."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            try:
                return int(v) if v.strip() else None
            except ValueError:
                return None
        return int(v) if v is not None else None