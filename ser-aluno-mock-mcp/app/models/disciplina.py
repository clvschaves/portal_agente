"""Disciplina data models."""
from typing import Optional, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class DisciplinaDto(BaseModel):
    """Disciplina matriculada data model."""
    model_config = ConfigDict(populate_by_name=True)
    
    # Campos obrigatórios (podem vir como None em alguns casos)
    cod_coligada: Optional[int] = Field(default=None, alias="CODCOLIGADA", serialization_alias="codColigada")
    id_turma_disc: Optional[int] = Field(default=None, alias="IDTURMADISC", serialization_alias="idTurmaDisc")
    ra: Optional[str] = Field(default=None, alias="RA")
    cod_status: Optional[int] = Field(default=None, alias="CODSTATUS", serialization_alias="codStatus")
    
    # Campos opcionais
    cod_status_res: Optional[int] = Field(default=None, alias="CODSTATUSRES", serialization_alias="codStatusRes")
    cod_sub_turma: Optional[str] = Field(default=None, alias="CODSUBTURMA", serialization_alias="codSubTurma")
    id_per_let: Optional[int] = Field(default=None, alias="IDPERLET", serialization_alias="idPerLet")
    id_habilitacao_filial: Optional[int] = Field(default=None, alias="IDHABILITACAOFILIAL", serialization_alias="idHabilitacaoFilial")
    num_diario: Optional[int] = Field(default=None, alias="NUMDIARIO", serialization_alias="numDiario")
    dt_matricula: Optional[str] = Field(default=None, alias="DTMATRICULA", serialization_alias="dtMatricula")
    obs_historico: Optional[str] = Field(default=None, alias="OBSHISTORICO", serialization_alias="obsHistorico")
    tipo_mat: Optional[str] = Field(default=None, alias="TIPOMAT", serialization_alias="tipoMat")
    cod_disc: Optional[str] = Field(default=None, alias="CODDISC", serialization_alias="codDisc")
    # Suporta tanto NOMEDISC quanto NOME (quando há notas/faltas)
    # O model_validator normaliza NOME para NOMEDISC antes da validação
    nome_disc: Optional[str] = Field(default=None, alias="NOMEDISC", serialization_alias="nomeDisc")
    usuario: Optional[str] = Field(default=None, alias="USUARIO", serialization_alias="usuario")
    cod_motivo: Optional[int] = Field(default=None, alias="CODMOTIVO", serialization_alias="codMotivo")
    dt_alteracao: Optional[str] = Field(default=None, alias="DTALTERACAO", serialization_alias="dtAlteracao")
    dt_alteracao_sist: Optional[str] = Field(default=None, alias="DTALTERACAOSIST", serialization_alias="dtAlteracaoSist")
    num_creditos_cob: Optional[Decimal] = Field(default=None, alias="NUMCREDITOSCOB", serialization_alias="numCreditosCob")
    tipo_disciplina: Optional[str] = Field(default=None, alias="TIPODISCIPLINA", serialization_alias="tipoDisciplina")
    num_creditos: Optional[Decimal] = Field(default=None, alias="NUMCREDITOS", serialization_alias="numCreditos")
    nome_aluno: Optional[str] = Field(default=None, alias="NOMEALUNO", serialization_alias="nomeAluno")
    nota: Optional[Decimal] = Field(default=None, alias="NOTA")
    falta: Optional[Decimal] = Field(default=None, alias="FALTA", serialization_alias="faltas")
    cod_conceito: Optional[str] = Field(default=None, alias="CODCONCEITO", serialization_alias="codConceito")
    cod_per_let: Optional[str] = Field(default=None, alias="CODPERLET", serialization_alias="codPerLet")
    id_turma_disc_origem: Optional[int] = Field(default=None, alias="IDTURMADISCORIGEM", serialization_alias="idTurmaDiscOrigem")
    cob_posterior_matric: Optional[str] = Field(default=None, alias="COBPOSTERIORMATRIC", serialization_alias="cobPosteriorMatric")
    id_turma_disc_subst: Optional[int] = Field(default=None, alias="IDTURMADISCSUBST", serialization_alias="idTurmaDiscSubst")
    filial: Optional[str] = Field(default=None, alias="FILIAL", exclude=True)
    conceito_ects: Optional[str] = Field(default=None, alias="CONCEITOECTS", serialization_alias="conceitoEcts")
    cod_filial: Optional[int] = Field(default=None, alias="CODFILIAL", serialization_alias="codFilial")
    cod_tipo_curso: Optional[int] = Field(default=None, alias="CODTIPOCURSO", serialization_alias="codTipoCurso")
    cod_turma: Optional[str] = Field(default=None, alias="CODTURMA", serialization_alias="codTurma")
    nome_status: Optional[str] = Field(default=None, alias="NOMESTATUS", serialization_alias="status")
    nome_nivel_ensino: Optional[str] = Field(default=None, alias="NOMENIVELENSINO", serialization_alias="nomeNivelEnsino")
    cod_filial_turma_disc: Optional[int] = Field(default=None, alias="CODFILIALTURMADISC", serialization_alias="codFilialTurmaDisc")
    cod_tipo_curso_turma_disc: Optional[int] = Field(default=None, alias="CODTIPOCURSOTURMADISC", serialization_alias="codTipoCursoTurmaDisc")
    rec_created_by: Optional[str] = Field(default=None, alias="RECCREATEDBY", serialization_alias="recCreatedBy")
    rec_created_on: Optional[str] = Field(default=None, alias="RECCREATEDON", serialization_alias="recCreatedOn")
    rec_modified_by: Optional[str] = Field(default=None, alias="RECMODIFIEDBY", serialization_alias="recModifiedBy")
    rec_modified_on: Optional[str] = Field(default=None, alias="RECMODIFIEDON", serialization_alias="recModifiedOn")
    matricula_isolada: Optional[str] = Field(default=None, alias="MATRICULAISOLADA", serialization_alias="matriculaIsolada")
    
    # Campos adicionais quando retornarNotasFaltas=true (de DisciplinaMatriculaComNotasFaltas)
    nota_v1: Optional[Decimal] = Field(default=None, alias="NOTAV1", serialization_alias="notaV1")
    nota_v2: Optional[Decimal] = Field(default=None, alias="NOTAV2", serialization_alias="notaV2")
    nota_final: Optional[Decimal] = Field(default=None, alias="NOTAFINAL", serialization_alias="notaFinal")
    media_aluno: Optional[Decimal] = Field(default=None, alias="MEDIAALUNO", serialization_alias="mediaAluno")
    media_turma_v1: Optional[Decimal] = Field(default=None, alias="MEDIATURMAV1", serialization_alias="mediaTurmaV1")
    media_turma_v2: Optional[Decimal] = Field(default=None, alias="MEDIATURMAV2", serialization_alias="mediaTurmaV2")
    media_turma_final: Optional[Decimal] = Field(default=None, alias="MEDIATURMAFINAL", serialization_alias="mediaTurmaFinal")
    media_turma: Optional[Decimal] = Field(default=None, alias="MEDIATURMA", serialization_alias="mediaTurma")
    data_av1: Optional[str] = Field(default=None, alias="DATAAV1", serialization_alias="dataAv1")
    data_av2: Optional[str] = Field(default=None, alias="DATAAV2", serialization_alias="dataAv2")
    data_av_final: Optional[str] = Field(default=None, alias="DATAAVFINAL", serialization_alias="dataAvFinal")
    # Suporta tanto FALTAS quanto FALTASCOMETIDAS
    faltas_cometidas: Optional[int] = Field(default=None, alias="FALTASCOMETIDAS", serialization_alias="faltasCometidas")
    maximo_faltas_disciplina: Optional[int] = Field(default=None, alias="MAXIMOFALTASDISCIPLINA", serialization_alias="maximoFaltasDisciplina")
    media_faltas_turma: Optional[Decimal] = Field(default=None, alias="MEDIAFALTASTURMA", serialization_alias="mediaFaltasTurma")
    ch_pratica: Optional[int] = Field(default=None, alias="CHPRATICA", serialization_alias="chPratica")
    ch_teorica: Optional[int] = Field(default=None, alias="CHTEORICA", serialization_alias="chTeorica")
    tipo_turma: Optional[str] = Field(default=None, alias="TIPOTURMA", serialization_alias="tipoTurma")
    cod_turma_ubiqua: Optional[str] = Field(default=None, alias="CODTURMAUBIQUA", serialization_alias="codTurmaUbiqua")
    data_inicio_aula: Optional[str] = Field(default=None, alias="DATAINICIOAULA", serialization_alias="dataInicioAula")
    data_fim_aula: Optional[str] = Field(default=None, alias="DATAFIMAULA", serialization_alias="dataFimAula")
    descricao_res: Optional[str] = Field(default=None, alias="DESCRICAORES", serialization_alias="descricaoRes")
    data_2ch: Optional[str] = Field(default=None, alias="DATA2CH", serialization_alias="data2Ch")
    media_geral: Optional[Decimal] = Field(default=None, alias="MEDIAGERAL", serialization_alias="mediaGeral")
    media_av1: Optional[Decimal] = Field(default=None, alias="MEDIAAV1", serialization_alias="mediaAv1")
    media_av2: Optional[Decimal] = Field(default=None, alias="MEDIAAV2", serialization_alias="mediaAv2")
    media_final: Optional[Decimal] = Field(default=None, alias="MEDIAFINAL", serialization_alias="mediaFinal")
    
    @model_validator(mode='before')
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        """Normalize field names and values."""
        if isinstance(data, dict):
            # Se tem NOME mas não tem NOMEDISC, usar NOME como NOMEDISC
            if "NOME" in data and "NOMEDISC" not in data:
                data["NOMEDISC"] = data["NOME"]
            
            # Se tem FALTA mas não tem FALTASCOMETIDAS, usar FALTA como FALTASCOMETIDAS
            if "FALTA" in data and "FALTASCOMETIDAS" not in data:
                falta_value = data["FALTA"]
                # Converter Decimal para int se necessário
                if isinstance(falta_value, (int, float, Decimal)):
                    data["FALTASCOMETIDAS"] = int(falta_value)
                elif isinstance(falta_value, str) and falta_value.strip():
                    try:
                        data["FALTASCOMETIDAS"] = int(float(falta_value))
                    except (ValueError, TypeError):
                        pass
            
            # Normalizar strings vazias para None em campos inteiros e decimais
            int_fields = [
                'CODCOLIGADA', 'IDTURMADISC', 'CODSTATUS', 'CODSTATUSRES', 
                'IDPERLET', 'IDHABILITACAOFILIAL', 'NUMDIARIO', 'CODMOTIVO',
                'IDTURMADISCORIGEM', 'IDTURMADISCSUBST', 'CODFILIAL', 
                'CODTIPOCURSO', 'CODFILIALTURMADISC', 'CODTIPOCURSOTURMADISC',
                'FALTASCOMETIDAS', 'MAXIMOFALTASDISCIPLINA', 'CHPRATICA', 'CHTEORICA'
            ]
            for field in int_fields:
                if field in data and data[field] == '':
                    data[field] = None
        
        return data
    
    @field_validator(
        'cod_coligada', 'id_turma_disc', 'cod_status', 'cod_status_res',
        'id_per_let', 'id_habilitacao_filial', 'num_diario', 'cod_motivo',
        'id_turma_disc_origem', 'id_turma_disc_subst', 'cod_filial',
        'cod_tipo_curso', 'cod_filial_turma_disc', 'cod_tipo_curso_turma_disc',
        'faltas_cometidas', 'maximo_faltas_disciplina', 'ch_pratica', 'ch_teorica',
        mode='before'
    )
    @classmethod
    def parse_int_or_none(cls, v: Any) -> Optional[int]:
        """Parse integer or return None if empty string or None."""
        if v is None or v == '':
            return None
        if isinstance(v, (Decimal, float)):
            return int(v)
        if isinstance(v, str):
            try:
                return int(float(v)) if v.strip() else None
            except (ValueError, TypeError):
                return None
        return int(v) if v is not None else None
    
    @field_validator('falta', mode='before')
    @classmethod
    def parse_decimal_or_none(cls, v: Any) -> Optional[Decimal]:
        """Parse Decimal or return None if empty string or None."""
        if v is None or v == '':
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            try:
                return Decimal(v) if v.strip() else None
            except (ValueError, TypeError):
                return None
        return None