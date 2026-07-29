"""FastAPI como borda HTTP fina sobre os casos de uso do Waypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from ... import __version__
from ...application.dto.extraction import ExtractionOptions
from ...application.dto.results import MigrationResult
from ...application.use_cases.run_migration import MigrationRequest, run_migration
from ...config import Settings, get_settings
from ...domain.enums.entity_type import EntityType
from ...domain.errors import WaypointError
from ...infrastructure.database.session import (
    DatabaseUnavailableError,
    engine_from_settings,
)
from ...infrastructure.loaders.postgres_loader import LoadError
from ...infrastructure.ocr.tesseract import TesseractEngine
from ...infrastructure.reports.artifact_store import (
    ArtifactNotFoundError,
    ArtifactRunNotFoundError,
    ArtifactSpec,
    ArtifactStoreError,
    TemporaryArtifactStore,
)
from ..uploads import inspect_uploaded_source, materialized_upload, safe_upload_name
from .mapping_routes import create_mapping_router
from .schemas import (
    ApiError,
    ApiErrorResponse,
    ArtifactLinkResponse,
    DatabaseLoadResponse,
    DryRunResponse,
    HealthFeatures,
    HealthResponse,
    SourcePreviewResponse,
)

_READ_CHUNK_BYTES = 1024 * 1024
_MAX_MAPPING_BYTES = 1024 * 1024


def create_app(
    settings: Settings | None = None,
    *,
    artifact_store: TemporaryArtifactStore | None = None,
) -> FastAPI:
    """Cria a aplicação com configuração injetável para testes."""
    resolved_settings = settings if settings is not None else get_settings()
    owns_artifact_store = artifact_store is None
    resolved_artifact_store = artifact_store or TemporaryArtifactStore(
        ttl_seconds=resolved_settings.artifact_ttl_seconds
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            if owns_artifact_store:
                resolved_artifact_store.close()

    application = FastAPI(
        title="Waypoint API",
        summary="API local e open-source para o pipeline Waypoint.",
        version=__version__,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    application.state.artifact_store = resolved_artifact_store

    if resolved_settings.allowed_web_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_settings.allowed_web_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )

    application.include_router(create_mapping_router())

    @application.get("/api/v1/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        ocr_engine = TesseractEngine(settings=resolved_settings)
        return HealthResponse(
            max_upload_mb=resolved_settings.max_upload_mb,
            features=HealthFeatures(
                ocr=ocr_engine.is_available(),
                database=resolved_settings.database_available,
            ),
        )

    @application.post(
        "/api/v1/inspect",
        response_model=SourcePreviewResponse,
        response_model_exclude_none=True,
        responses={
            status.HTTP_413_CONTENT_TOO_LARGE: {
                "description": "Arquivo maior que o limite configurado.",
                "model": ApiErrorResponse,
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": "Arquivo vazio, inválido ou não suportado.",
                "model": ApiErrorResponse,
            },
        },
    )
    async def inspect_upload(
        file: Annotated[UploadFile, File(description="Arquivo de origem")],
        header_row: Annotated[int, Form(ge=1)] = 1,
        sheet: Annotated[str | None, Form()] = None,
        encoding: Annotated[str | None, Form()] = None,
        delimiter: Annotated[str | None, Form()] = None,
    ) -> SourcePreviewResponse:
        content = await _read_upload(
            file,
            max_bytes=resolved_settings.max_upload_mb * 1024 * 1024,
        )
        if not content:
            raise _http_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="empty_upload",
                message="O arquivo está vazio. Escolha uma origem com conteúdo.",
            )

        options = ExtractionOptions(
            sheet=sheet or None,
            header_row=header_row,
            encoding=encoding or None,
            delimiter=delimiter or None,
        )
        ocr_engine = TesseractEngine(settings=resolved_settings)
        try:
            preview = inspect_uploaded_source(
                file.filename or "upload.bin",
                content,
                options=options,
                ocr_engine=ocr_engine,
            )
        except WaypointError as error:
            raise _http_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="inspection_failed",
                message=str(error),
            ) from error

        return SourcePreviewResponse.from_preview(preview)

    @application.post(
        "/api/v1/migrations/dry-run",
        response_model=DryRunResponse,
        responses={
            status.HTTP_413_CONTENT_TOO_LARGE: {
                "description": "Origem ou template maior que o limite.",
                "model": ApiErrorResponse,
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": "Origem, entidade ou template inválido.",
                "model": ApiErrorResponse,
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Relatórios temporários indisponíveis.",
                "model": ApiErrorResponse,
            },
        },
    )
    async def dry_run_upload(
        file: Annotated[UploadFile, File(description="Arquivo de origem")],
        mapping: Annotated[UploadFile, File(description="Template YAML De/Para")],
        entity: Annotated[EntityType, Form(description="Entidade canônica")],
    ) -> DryRunResponse:
        source_content, mapping_content = await _read_migration_uploads(
            file,
            mapping,
            max_upload_bytes=resolved_settings.max_upload_mb * 1024 * 1024,
        )

        try:
            result, specs = _execute_uploaded_migration(
                source_name=file.filename or "upload.bin",
                source_content=source_content,
                mapping_name=mapping.filename or "mapping.yaml",
                mapping_content=mapping_content,
                entity=entity,
                dry_run=True,
                artifact_store=resolved_artifact_store,
            )
        except ArtifactStoreError as error:
            raise _http_error(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="artifact_storage_failed",
                message=(
                    "A validação terminou, mas os relatórios temporários não puderam "
                    "ser preparados. Tente executar o dry-run novamente."
                ),
            ) from error
        except (WaypointError, UnicodeDecodeError, FileNotFoundError, OSError) as error:
            raise _http_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="dry_run_failed",
                message=str(error),
            ) from error

        return DryRunResponse.from_result(
            result,
            artifacts=_artifact_links(result.run_id, specs),
            artifact_ttl_seconds=resolved_artifact_store.ttl_seconds,
        )

    @application.get(
        "/api/v1/migrations/{run_id}/artifacts/{artifact_name}",
        response_class=FileResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {
                "description": "Execução expirada ou relatório desconhecido.",
                "model": ApiErrorResponse,
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Armazenamento temporário indisponível.",
                "model": ApiErrorResponse,
            },
        },
    )
    def download_artifact(run_id: str, artifact_name: str) -> FileResponse:
        try:
            artifact = resolved_artifact_store.resolve(run_id, artifact_name)
        except ArtifactRunNotFoundError as error:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                code="run_not_found",
                message=str(error),
            ) from error
        except ArtifactNotFoundError as error:
            raise _http_error(
                status.HTTP_404_NOT_FOUND,
                code="artifact_not_found",
                message=str(error),
            ) from error
        except ArtifactStoreError as error:
            raise _http_error(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="artifact_storage_failed",
                message=(
                    "Os relatórios temporários não puderam ser consultados. "
                    "Tente executar a validação novamente."
                ),
            ) from error

        return FileResponse(
            artifact.path,
            media_type=artifact.spec.media_type,
            filename=artifact.spec.name,
            headers={
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @application.post(
        "/api/v1/migrations/load-postgres",
        response_model=DatabaseLoadResponse,
        responses={
            status.HTTP_409_CONFLICT: {
                "description": "Carga ainda não confirmada.",
                "model": ApiErrorResponse,
            },
            status.HTTP_413_CONTENT_TOO_LARGE: {
                "description": "Origem ou template maior que o limite.",
                "model": ApiErrorResponse,
            },
            status.HTTP_422_UNPROCESSABLE_CONTENT: {
                "description": "Origem, entidade ou template inválido.",
                "model": ApiErrorResponse,
            },
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "description": (
                    "Banco não configurado, indisponível ou carga revertida."
                ),
                "model": ApiErrorResponse,
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Relatórios temporários indisponíveis.",
                "model": ApiErrorResponse,
            },
        },
    )
    async def load_postgres(
        file: Annotated[UploadFile, File(description="Arquivo de origem")],
        mapping: Annotated[UploadFile, File(description="Template YAML De/Para")],
        entity: Annotated[EntityType, Form(description="Entidade canônica")],
        confirm: Annotated[
            bool,
            Form(description="Confirma explicitamente a escrita no PostgreSQL"),
        ] = False,
    ) -> DatabaseLoadResponse:
        if not confirm:
            await file.close()
            await mapping.close()
            raise _http_error(
                status.HTTP_409_CONFLICT,
                code="confirmation_required",
                message=(
                    "A carga no PostgreSQL altera o banco de destino. Marque a "
                    "confirmação explícita antes de continuar."
                ),
            )
        if not resolved_settings.database_available:
            await file.close()
            await mapping.close()
            raise _http_error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                code="database_unavailable",
                message=(
                    "Nenhum banco está configurado. Defina DATABASE_URL no serviço "
                    "da API e tente novamente; o dry-run continua disponível."
                ),
            )

        source_content, mapping_content = await _read_migration_uploads(
            file,
            mapping,
            max_upload_bytes=resolved_settings.max_upload_mb * 1024 * 1024,
        )

        engine: Engine | None = None
        try:
            engine = engine_from_settings(resolved_settings)
            result, specs = _execute_uploaded_migration(
                source_name=file.filename or "upload.bin",
                source_content=source_content,
                mapping_name=mapping.filename or "mapping.yaml",
                mapping_content=mapping_content,
                entity=entity,
                dry_run=False,
                artifact_store=resolved_artifact_store,
                engine=engine,
            )
        except ArtifactStoreError as error:
            raise _http_error(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                code="artifact_storage_failed",
                message=(
                    "A carga foi concluída, mas os relatórios temporários não puderam "
                    "ser disponibilizados. Consulte o run_id nos logs antes de tentar "
                    "uma nova carga."
                ),
            ) from error
        except (DatabaseUnavailableError, LoadError, SQLAlchemyError) as error:
            raise _http_error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                code="database_load_failed",
                message=(
                    "Não foi possível concluir a carga no PostgreSQL. A transação foi "
                    "revertida; verifique a conexão e tente novamente."
                ),
            ) from error
        except (WaypointError, UnicodeDecodeError, FileNotFoundError, OSError) as error:
            raise _http_error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="database_load_invalid",
                message=str(error),
            ) from error
        finally:
            if engine is not None:
                engine.dispose()

        return DatabaseLoadResponse.from_result(
            result,
            artifacts=_artifact_links(result.run_id, specs),
            artifact_ttl_seconds=resolved_artifact_store.ttl_seconds,
        )

    return application


async def _read_migration_uploads(
    file: UploadFile,
    mapping: UploadFile,
    *,
    max_upload_bytes: int,
) -> tuple[bytes, bytes]:
    """Lê e valida o par origem/template usado nas rotas de migração."""
    source_content = await _read_upload(file, max_bytes=max_upload_bytes)
    if not source_content:
        await mapping.close()
        raise _http_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="empty_upload",
            message="O arquivo de origem está vazio. Escolha outro arquivo.",
        )

    mapping_content = await _read_upload(
        mapping,
        max_bytes=_MAX_MAPPING_BYTES,
        too_large_code="mapping_too_large",
        too_large_message=(
            "O template De/Para ultrapassa 1 MB. Revise o YAML e tente novamente."
        ),
    )
    if not mapping_content:
        raise _http_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="empty_mapping",
            message="O template De/Para está vazio. Configure o mapeamento novamente.",
        )
    return source_content, mapping_content


def _execute_uploaded_migration(
    *,
    source_name: str,
    source_content: bytes,
    mapping_name: str,
    mapping_content: bytes,
    entity: EntityType,
    dry_run: bool,
    artifact_store: TemporaryArtifactStore,
    engine: Engine | None = None,
) -> tuple[MigrationResult, tuple[ArtifactSpec, ...]]:
    """Executa o caso de uso e publica só seus relatórios antes da limpeza."""
    with (
        TemporaryDirectory(prefix="waypoint-api-") as temporary_dir,
        materialized_upload(source_name, source_content) as source_path,
        materialized_upload(
            safe_upload_name(mapping_name, fallback="mapping.yaml"),
            mapping_content,
        ) as mapping_path,
    ):
        result = run_migration(
            MigrationRequest(
                source=source_path,
                mapping=mapping_path,
                output_dir=Path(temporary_dir),
                entity=entity,
                dry_run=dry_run,
            ),
            engine=engine,
        )
        specs = artifact_store.publish(result.run_id, result.exported_files)
    return result, specs


def _artifact_links(
    run_id: str, specs: tuple[ArtifactSpec, ...]
) -> list[ArtifactLinkResponse]:
    """Monta URLs relativas para o frontend usar na mesma API."""
    return [
        ArtifactLinkResponse(
            name=spec.name,
            media_type=spec.media_type,
            download_url=f"/api/v1/migrations/{run_id}/artifacts/{spec.name}",
        )
        for spec in specs
    ]


async def _read_upload(
    upload: UploadFile,
    *,
    max_bytes: int,
    too_large_code: str = "upload_too_large",
    too_large_message: str = (
        "O arquivo ultrapassa o limite configurado. Escolha um arquivo menor."
    ),
) -> bytes:
    """Lê em blocos e interrompe assim que o limite for ultrapassado."""
    content = bytearray()
    try:
        while chunk := await upload.read(_READ_CHUNK_BYTES):
            content.extend(chunk)
            if len(content) > max_bytes:
                raise _http_error(
                    status.HTTP_413_CONTENT_TOO_LARGE,
                    code=too_large_code,
                    message=too_large_message,
                )
    finally:
        await upload.close()
    return bytes(content)


def _http_error(status_code: int, *, code: str, message: str) -> HTTPException:
    """Cria o envelope de erro estável consumido pelo frontend."""
    return HTTPException(
        status_code=status_code,
        detail=ApiError(code=code, message=message).model_dump(),
    )


app = create_app()

__all__ = ["app", "create_app"]
