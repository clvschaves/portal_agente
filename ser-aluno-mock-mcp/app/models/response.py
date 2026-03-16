"""Response models for ser-aluno-services."""
from typing import Generic, TypeVar, Optional

from pydantic import BaseModel

T = TypeVar('T')


class SerAlunoServicesResponse(BaseModel, Generic[T]):
    """Generic response wrapper from ser-aluno-services."""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None