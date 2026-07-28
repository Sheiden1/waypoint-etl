"""Schemas públicos da API web."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field

from ... import __version__
from ...application.dto.results import MigrationResult, SourcePreview
from ...domain.value_objects.document import mask_document


class HealthFeatures(BaseModel):
    """Recursos opcionais disponíveis no processo atual."""

    model_config = ConfigDict(extra="forbid")

    ocr: bool
    database: bool


class HealthResponse(BaseModel):
    """Estado básico da API."""

    model_config = ConfigDict(extra="forbid")

    status: str = "ok"
    version: str = __version__
    max_upload_mb: int = Field(ge=1)
    features: HealthFeatures


class SourcePreviewResponse(BaseModel):
    """Prévia serializável de uma origem enviada."""

    model_config = ConfigDict(extra="forbid")

    source_name: str
    source_format: str
    is_tabular: bool
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, str | None]] = Field(default_factory=list)
    available_sheets: list[str] = Field(default_factory=list)
    text_preview: str | None = None
    page_count: int | None = None
    ocr_used: bool = False
    warnings: list[str] = Field(default_factory=list)

    @classmethod
    def from_preview(cls, preview: SourcePreview) -> Self:
        """Converte o DTO compartilhado sem expor detalhes internos."""
        return cls(
            source_name=preview.source_name,
            source_format=preview.source_format.value,
            is_tabular=preview.is_tabular,
            columns=list(preview.columns),
            rows=[dict(row) for row in preview.rows],
            available_sheets=list(preview.available_sheets),
            text_preview=preview.text_preview,
            page_count=preview.page_count,
            ocr_used=preview.ocr_used,
            warnings=list(preview.warnings),
        )


class DryRunSummary(BaseModel):
    """Totais de qualidade produzidos pelo pipeline."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0)
    valid: int = Field(ge=0)
    rejected: int = Field(ge=0)
    duplicates: int = Field(ge=0)
    possible_duplicates: int = Field(ge=0)
    duration_ms: int = Field(ge=0)


class ValidationIssueResponse(BaseModel):
    """Problema de uma linha, com valores sensíveis já mascarados."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(ge=1)
    sheet: str | None = None
    field: str | None = None
    code: str
    severity: str
    message: str
    original_value: str | None = None
    normalized_value: str | None = None


class DuplicateResponse(BaseModel):
    """Correspondência exata ou possível encontrada no lote."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(ge=1)
    matched_row_number: int = Field(ge=1)
    kind: str
    key: str
    value: str
    similarity: float = Field(ge=0, le=1)


class StageDurationResponse(BaseModel):
    """Tempo gasto por um estágio do pipeline."""

    model_config = ConfigDict(extra="forbid")

    name: str
    duration_ms: int = Field(ge=0)


class ArtifactLinkResponse(BaseModel):
    """Link temporário para um dos quatro relatórios da execução."""

    model_config = ConfigDict(extra="forbid")

    name: str
    media_type: str
    download_url: str


class DryRunResponse(BaseModel):
    """Resultado completo e seguro de uma validação em dry-run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: str
    entity: str
    source_name: str
    mapping_name: str
    mapping_version: int
    dry_run: bool
    summary: DryRunSummary
    accepted_rows: list[dict[str, Any]] = Field(default_factory=list)
    issues: list[ValidationIssueResponse] = Field(default_factory=list)
    duplicates: list[DuplicateResponse] = Field(default_factory=list)
    stages: list[StageDurationResponse] = Field(default_factory=list)
    transforms_applied: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    artifacts: list[ArtifactLinkResponse] = Field(default_factory=list)
    artifacts_expires_in_seconds: int = Field(ge=1)

    @classmethod
    def from_result(
        cls,
        result: MigrationResult,
        *,
        artifacts: list[ArtifactLinkResponse],
        artifact_ttl_seconds: int,
    ) -> Self:
        """Converte o resultado compartilhado sem expor documentos completos."""
        duration = result.run.duration_ms
        if duration is None:
            duration = sum(stage.duration_ms for stage in result.stages)

        accepted_rows: list[dict[str, Any]] = []
        for record in result.accepted:
            if record.entity is None:
                continue
            row = asdict(record.entity)
            for field in ("document", "customer_document"):
                value = row.get(field)
                if value is not None:
                    row[field] = mask_document(str(value))
            accepted_rows.append(row)

        issues = [
            ValidationIssueResponse(
                row_number=record.row_number,
                sheet=record.sheet,
                field=issue.field,
                code=issue.code,
                severity=issue.severity.value,
                message=issue.message,
                original_value=issue.original_value,
                normalized_value=issue.normalized_value,
            )
            for record in result.records
            for issue in record.issues_for_display()
        ]

        sensitive_keys = {"document", "customer_document"}
        duplicates = [
            DuplicateResponse(
                row_number=match.row_number,
                matched_row_number=match.matched_row_number,
                kind="exact" if match.exact else "possible",
                key=match.key,
                value=(
                    mask_document(match.value)
                    if match.key in sensitive_keys
                    else match.value
                ),
                similarity=match.similarity,
            )
            for match in (*result.duplicates.exact, *result.duplicates.possible)
        ]

        return cls(
            run_id=result.run_id,
            status=result.run.status.value,
            entity=result.entity.value,
            source_name=result.run.source_filename,
            mapping_name=result.run.mapping_name or "Template sem nome",
            mapping_version=result.run.mapping_version or 1,
            dry_run=result.run.dry_run,
            summary=DryRunSummary(
                total=result.total_records,
                valid=len(result.accepted),
                rejected=len(result.rejected),
                duplicates=result.duplicate_count,
                possible_duplicates=result.possible_duplicate_count,
                duration_ms=duration,
            ),
            accepted_rows=accepted_rows,
            issues=issues,
            duplicates=duplicates,
            stages=[
                StageDurationResponse(
                    name=stage.name,
                    duration_ms=stage.duration_ms,
                )
                for stage in result.stages
            ],
            transforms_applied=dict(result.transforms_applied),
            warnings=list(result.warnings),
            artifacts=artifacts,
            artifacts_expires_in_seconds=artifact_ttl_seconds,
        )


class DatabaseLoadResponse(DryRunResponse):
    """Resultado de uma carga PostgreSQL confirmada pelo usuário."""

    loaded_records: int = Field(ge=0)

    @classmethod
    def from_result(
        cls,
        result: MigrationResult,
        *,
        artifacts: list[ArtifactLinkResponse],
        artifact_ttl_seconds: int,
    ) -> Self:
        """Converte o resultado efetivado e acrescenta a contagem persistida."""
        base = DryRunResponse.from_result(
            result,
            artifacts=artifacts,
            artifact_ttl_seconds=artifact_ttl_seconds,
        )
        return cls(**base.model_dump(), loaded_records=result.loaded_records)


class ApiError(BaseModel):
    """Erro controlado e acionável."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class ApiErrorResponse(BaseModel):
    """Envelope estável para erros da plataforma."""

    model_config = ConfigDict(extra="forbid")

    detail: ApiError


__all__ = [
    "ApiError",
    "ApiErrorResponse",
    "ArtifactLinkResponse",
    "DatabaseLoadResponse",
    "DryRunResponse",
    "DryRunSummary",
    "DuplicateResponse",
    "HealthFeatures",
    "HealthResponse",
    "SourcePreviewResponse",
    "StageDurationResponse",
    "ValidationIssueResponse",
]
