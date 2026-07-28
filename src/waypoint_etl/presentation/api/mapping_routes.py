"""Catálogo e validação HTTP de templates De/Para."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field

from ...domain.enums.entity_type import EntityType
from ...domain.enums.source_format import SourceFormat
from ...pipeline.mappers.loader import MappingError, load_mapping, parse_mapping
from ...pipeline.mappers.schema import MappingTemplate
from .schemas import ApiError, ApiErrorResponse

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_MAPPINGS_DIR = _PROJECT_ROOT / "mappings"
_MAX_MAPPING_BYTES = 1024 * 1024
_READ_CHUNK_BYTES = 64 * 1024


class MappingFieldResponse(BaseModel):
    """Uma associação origem → destino validada."""

    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    required: bool
    transforms: list[str] = Field(default_factory=list)


class MappingTemplateResponse(BaseModel):
    """Template pronto para seleção ou execução pelo frontend."""

    model_config = ConfigDict(extra="forbid")

    template_id: str
    filename: str
    name: str
    version: int
    entity: str
    source_format: str | None = None
    sheet: str | None = None
    header_row: int = Field(ge=1)
    fields: list[MappingFieldResponse]
    ignored_fields: list[str] = Field(default_factory=list)
    assignments: dict[str, str | None]
    content: str

    @classmethod
    def from_template(
        cls,
        *,
        template_id: str,
        filename: str,
        content: str,
        template: MappingTemplate,
    ) -> Self:
        """Serializa o domínio sem duplicar validações no HTTP."""
        assignments: dict[str, str | None] = {
            field.source: field.target for field in template.fields
        }
        assignments.update(dict.fromkeys(template.ignored_fields))
        return cls(
            template_id=template_id,
            filename=filename,
            name=template.name,
            version=template.version,
            entity=template.entity.value,
            source_format=(
                template.source.type.value if template.source.type is not None else None
            ),
            sheet=template.source.sheet,
            header_row=template.source.header_row,
            fields=[
                MappingFieldResponse(
                    source=field.source,
                    target=field.target,
                    required=field.required,
                    transforms=list(field.transforms),
                )
                for field in template.fields
            ],
            ignored_fields=list(template.ignored_fields),
            assignments=assignments,
            content=content,
        )


class MappingCatalogResponse(BaseModel):
    """Lista de templates versionados disponíveis no repositório."""

    model_config = ConfigDict(extra="forbid")

    templates: list[MappingTemplateResponse] = Field(default_factory=list)


def create_mapping_router(
    mappings_dir: Path = _DEFAULT_MAPPINGS_DIR,
) -> APIRouter:
    """Cria as rotas com diretório injetável para testes."""
    router = APIRouter(prefix="/api/v1/mappings", tags=["mappings"])

    @router.get(
        "",
        response_model=MappingCatalogResponse,
        responses={
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Um template versionado é inválido.",
                "model": ApiErrorResponse,
            }
        },
    )
    def list_mappings(
        entity: EntityType | None = None,
        source_format: SourceFormat | None = None,
    ) -> MappingCatalogResponse:
        templates: list[MappingTemplateResponse] = []
        if not mappings_dir.is_dir():
            return MappingCatalogResponse()

        for path in sorted(mappings_dir.glob("*.yaml")):
            try:
                template = load_mapping(path)
                content = path.read_text(encoding="utf-8")
            except (MappingError, UnicodeDecodeError, OSError) as error:
                raise _mapping_error(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    code="mapping_catalog_invalid",
                    message=f"O catálogo contém um template inválido: {error}",
                ) from error

            if entity is not None and template.entity is not entity:
                continue
            if (
                source_format is not None
                and template.source.type is not None
                and template.source.type is not source_format
            ):
                continue
            templates.append(
                MappingTemplateResponse.from_template(
                    template_id=path.stem,
                    filename=path.name,
                    content=content,
                    template=template,
                )
            )
        return MappingCatalogResponse(templates=templates)

    @router.post(
        "/preview",
        response_model=MappingTemplateResponse,
        responses={
            status.HTTP_413_CONTENT_TOO_LARGE: {
                "description": "Template maior que 1 MB.",
                "model": ApiErrorResponse,
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": "Template inválido ou incompatível.",
                "model": ApiErrorResponse,
            },
        },
    )
    async def preview_mapping(
        mapping: Annotated[UploadFile, File(description="Template YAML De/Para")],
        entity: Annotated[EntityType | None, Form()] = None,
        source_format: Annotated[SourceFormat | None, Form()] = None,
    ) -> MappingTemplateResponse:
        content = await _read_mapping(mapping)
        filename = Path(mapping.filename or "mapping.yaml").name
        try:
            text = content.decode("utf-8")
            template = parse_mapping(text, source_name=filename)
        except (MappingError, UnicodeDecodeError) as error:
            raise _mapping_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="mapping_invalid",
                message=str(error),
            ) from error

        if entity is not None and template.entity is not entity:
            raise _mapping_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="mapping_entity_mismatch",
                message=(
                    f"O template migra '{template.entity.value}', mas "
                    f"'{entity.value}' foi selecionado."
                ),
            )
        if (
            source_format is not None
            and template.source.type is not None
            and template.source.type is not source_format
        ):
            raise _mapping_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="mapping_format_mismatch",
                message=(
                    f"O template declara origem '{template.source.type.value}', "
                    f"mas o arquivo inspecionado é '{source_format.value}'."
                ),
            )

        return MappingTemplateResponse.from_template(
            template_id="uploaded",
            filename=filename,
            content=text,
            template=template,
        )

    return router


async def _read_mapping(upload: UploadFile) -> bytes:
    """Lê o YAML com limite pequeno e fecha o arquivo recebido."""
    content = bytearray()
    try:
        while chunk := await upload.read(_READ_CHUNK_BYTES):
            content.extend(chunk)
            if len(content) > _MAX_MAPPING_BYTES:
                raise _mapping_error(
                    status.HTTP_413_CONTENT_TOO_LARGE,
                    code="mapping_too_large",
                    message="O template De/Para ultrapassa o limite de 1 MB.",
                )
    finally:
        await upload.close()

    if not content:
        raise _mapping_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="empty_mapping",
            message="O template De/Para está vazio.",
        )
    return bytes(content)


def _mapping_error(status_code: int, *, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ApiError(code=code, message=message).model_dump(),
    )


__all__ = [
    "MappingCatalogResponse",
    "MappingFieldResponse",
    "MappingTemplateResponse",
    "create_mapping_router",
]
