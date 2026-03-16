"""Aluno data models."""
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class PPessoaDto(BaseModel):
    """Pessoa data model."""
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=lambda field_name: field_name.upper()
    )
    
    codigo: int = Field(alias="CODIGO")
    nome: Optional[str] = Field(default=None, alias="NOME")
    dtnascimento: Optional[str] = Field(default=None, alias="DTNASCIMENTO")
    sexo: Optional[str] = Field(default=None, alias="SEXO")
    email: Optional[str] = Field(default=None, alias="EMAIL")
    email_pessoal: Optional[str] = Field(default=None, alias="EMAILPESSOAL", serialization_alias="emailPessoal")
    telefone1: Optional[str] = Field(default=None, alias="TELEFONE1")
    telefone2: Optional[str] = Field(default=None, alias="TELEFONE2")
    telefone3: Optional[str] = Field(default=None, alias="TELEFONE3")
    rua: Optional[str] = Field(default=None, alias="RUA")
    numero: Optional[str] = Field(default=None, alias="NUMERO")
    complemento: Optional[str] = Field(default=None, alias="COMPLEMENTO")
    bairro: Optional[str] = Field(default=None, alias="BAIRRO")
    estado: Optional[str] = Field(default=None, alias="ESTADO")
    cidade: Optional[str] = Field(default=None, alias="CIDADE")
    cep: Optional[str] = Field(default=None, alias="CEP")
    pais: Optional[str] = Field(default=None, alias="PAIS")


class AlunoDadosDto(BaseModel):
    """Aluno dados model."""
    model_config = ConfigDict(populate_by_name=True)
    
    p_pessoa: Optional[PPessoaDto] = Field(default=None, alias="pPessoa")


class AlunoDadosEscolaresDto(BaseModel):
    """Aluno dados escolares model."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: Optional[str] = None
    ra: str
    escola_anterior: Optional[str] = Field(default=None, serialization_alias="escolaAnterior")
    cidade_escola_anterior: Optional[str] = Field(default=None, serialization_alias="cidadeEscolaAnterior")
    estado_escola_anterior: Optional[str] = Field(default=None, serialization_alias="estadoEscolaAnterior")
    ano_conclusao_ensino_medio: Optional[int] = Field(default=None, serialization_alias="anoConclusaoEnsinoMedio")
    tipo_ensino_medio: Optional[str] = Field(default=None, serialization_alias="tipoEnsinoMedio")
    tipo_escola_ensino_medio: Optional[str] = Field(default=None, serialization_alias="tipoEscolaEnsinoMedio")
    created_at: Optional[str] = Field(default=None, serialization_alias="createdAt")
    updated_at: Optional[str] = Field(default=None, serialization_alias="updatedAt")
    
    @model_validator(mode='before')
    @classmethod
    def normalize_empty_strings(cls, data: Any) -> Any:
        """Convert empty strings to None for optional integer fields."""
        if isinstance(data, dict):
            # Campos opcionais que são inteiros (verificar tanto camelCase quanto snake_case)
            int_fields = ['anoConclusaoEnsinoMedio', 'ano_conclusao_ensino_medio', 'ANOCONCLUSAOENSINOMEDIO']
            for field in int_fields:
                if field in data and data[field] == '':
                    data[field] = None
        return data
    
    @field_validator('ano_conclusao_ensino_medio', mode='before')
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