"""Caso de uso principal: executar uma migração de ponta a ponta.

Este é o núcleo compartilhado pela CLI e pelo Streamlit (seção 5). As duas
interfaces só montam os parâmetros e apresentam o ``MigrationResult``; nenhuma
regra vive na camada de apresentação.

A ordem segue o pipeline da seção 6: extrair, mapear, limpar, validar,
deduplicar, exportar e — apenas fora do ``dry-run`` — carregar.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from sqlalchemy import Engine

from ...domain.enums.entity_type import EntityType
from ...domain.enums.run_status import RunStatus
from ...domain.enums.source_format import SourceFormat
from ...domain.errors import WaypointError
from ...infrastructure.extractors.registry import (
    detect_format,
    get_document_extractor,
    get_tabular_extractor,
    is_tabular,
)
from ...infrastructure.loaders.postgres_loader import load_records
from ...infrastructure.reports.audit import AUDIT_FILENAME, write_audit_report
from ...infrastructure.reports.exporters import (
    ACCEPTED_FILENAME,
    DUPLICATES_FILENAME,
    REJECTED_FILENAME,
    export_accepted,
    export_duplicates,
    export_rejected,
    run_output_dir,
)
from ...logging import get_logger
from ...pipeline.deduplication.detector import annotate_duplicates, find_duplicates
from ...pipeline.documents.records import parse_document_records
from ...pipeline.mappers.loader import load_mapping
from ...pipeline.mappers.mapper import MappedRecord, apply_mapping
from ...pipeline.mappers.schema import MappingTemplate
from ...pipeline.validators.entities import validate_records
from ..dto.extraction import ExtractionResult
from ..dto.migration import MigrationRun, compute_file_hash
from ..dto.results import MigrationResult, StageTimer
from ..ports.ocr import OcrEngine


class UnsupportedSourceError(WaypointError):
    """A origem não pode ser migrada pelo caminho tabular do MVP."""


@dataclass(frozen=True, slots=True)
class MigrationRequest:
    """Parâmetros de uma migração."""

    source: Path
    mapping: Path
    output_dir: Path = Path("exports")
    dry_run: bool = True
    entity: EntityType | None = None
    """Entidade esperada. Quando informada, precisa bater com a do template."""
    ocr_engine: OcrEngine | None = None
    """Motor de OCR para documentos digitalizados. Sem ele, só texto nativo."""


def run_migration(
    request: MigrationRequest, *, engine: Engine | None = None
) -> MigrationResult:
    """Executa a migração descrita em ``request``.

    Levanta erro apenas para problemas de configuração (template inválido,
    arquivo ausente, entidade divergente). Problemas de dado viram registros
    rejeitados, nunca interrupção do lote.
    """
    timer = StageTimer()

    with timer.measure("load_mapping"):
        template = load_mapping(request.mapping)
        _check_entity(template, request.entity)
        _check_source_format(template, request.source)

    run = MigrationRun(
        entity=template.entity,
        source_filename=request.source.name,
        source_hash=compute_file_hash(request.source),
        dry_run=request.dry_run,
        mapping_name=template.name,
        mapping_version=template.version,
    )
    logger = get_logger(__name__, run_id=run.run_id)
    logger.info(
        "Iniciando migração",
        extra={"entity": template.entity.value, "dry_run": request.dry_run},
    )

    with timer.measure("extract"):
        extraction = _extract(request, template)

    with timer.measure("map"):
        mapped = apply_mapping(extraction, template)

    with timer.measure("validate"):
        validated = validate_records(mapped.records, template.entity)

    with timer.measure("deduplicate"):
        duplicates = find_duplicates(validated)
        records = annotate_duplicates(validated, duplicates)

    accepted = [record for record in records if record.is_valid]
    counted = run.with_counters(
        total=len(records),
        valid=len(accepted),
        rejected=len(records) - len(accepted),
        duplicates=len(duplicates.exact),
        ocr_used=extraction.ocr_used,
    )
    status = RunStatus.DRY_RUN if request.dry_run else RunStatus.COMPLETED

    loaded = 0
    if not request.dry_run:
        if engine is None:
            raise UnsupportedSourceError(
                "A carga no banco foi solicitada, mas nenhuma conexão está "
                "configurada. Defina DATABASE_URL no .env ou use --dry-run."
            )
        with timer.measure("load"):
            loaded = load_records(engine, records, counted).loaded_records
        logger.info("Carga concluída", extra={"loaded_records": loaded})

    result = MigrationResult(
        run=counted.finish(status),
        entity=template.entity,
        records=records,
        duplicates=duplicates,
        stages=timer.stages,
        warnings=extraction.warnings + mapped.warnings,
        transforms_applied=_count_transforms(mapped.records),
        loaded_records=loaded,
    )

    with timer.measure("export"):
        output_dir, files = _export(result, request.output_dir)

    # O relatório é escrito depois que o estágio "export" fecha, para que ele
    # possa registrar a própria duração da exportação.
    result = replace(result, stages=timer.stages, output_dir=output_dir)
    audit_file = write_audit_report(output_dir / AUDIT_FILENAME, result)
    files = (*files, audit_file)

    logger.info(
        "Migração concluída",
        extra={
            "total": result.total_records,
            "valid": len(result.accepted),
            "rejected": len(result.rejected),
            "duplicates": result.duplicate_count,
        },
    )

    return replace(result, exported_files=files)


def _check_entity(template: MappingTemplate, expected: EntityType | None) -> None:
    """Impede rodar um template de clientes pedindo cobranças, por exemplo."""
    if expected is not None and template.entity is not expected:
        raise UnsupportedSourceError(
            f"O template '{template.name}' migra '{template.entity.value}', mas "
            f"'{expected.value}' foi solicitado. Escolha o template correto."
        )


def _extract(
    request: MigrationRequest, template: MappingTemplate
) -> ExtractionResult:
    """Lê a origem, tabular ou documento, no mesmo contrato de extração.

    Planilha já vem em linhas e colunas. Documento passa antes por uma etapa de
    estruturação que reconhece pares ``Rótulo: valor``, de modo que o restante
    do pipeline não precisa saber a diferença.
    """
    if is_tabular(request.source):
        extractor = get_tabular_extractor(request.source)
        return extractor.extract(
            request.source, template.source.to_extraction_options()
        )

    document_extractor = get_document_extractor(
        request.source, ocr_engine=request.ocr_engine
    )
    if (
        request.ocr_engine is not None
        and detect_format(request.source) is SourceFormat.PDF
    ):
        from ...infrastructure.ocr.fallback import DocumentExtractorWithOcr

        document_extractor = DocumentExtractorWithOcr(
            document_extractor, request.ocr_engine
        )

    document = document_extractor.extract_text(
        request.source, template.source.to_extraction_options()
    )
    return parse_document_records(document, template.source)


def _check_source_format(template: MappingTemplate, source: Path) -> None:
    """Impede aplicar um template de Excel a um CSV, e vice-versa.

    Sem esta checagem o erro apareceria lá na frente como "coluna não
    encontrada", porque o ``header_row`` de uma planilha desalinha a leitura de
    um CSV — uma mensagem que não aponta a causa real.
    """
    declared = template.source.type
    if declared is None:
        return

    detected = detect_format(source)
    if detected is not declared:
        raise UnsupportedSourceError(
            f"O template '{template.name}' declara origem '{declared.value}', "
            f"mas '{source.name}' é '{detected.value}'. Use o template "
            "correspondente ao formato do arquivo."
        )


def _count_transforms(records: Sequence[MappedRecord]) -> dict[str, int]:
    """Conta quantas vezes cada transformação alterou algum valor."""
    counter: Counter[str] = Counter()
    for record in records:
        counter.update(record.applied_transforms)
    return dict(counter)


def _export(result: MigrationResult, base_dir: Path) -> tuple[Path, tuple[Path, ...]]:
    """Escreve os arquivos de dados da execução (seção 16).

    O ``audit-report.json`` é escrito por quem chama, já fora da medição, para
    poder registrar a duração desta própria exportação.
    """
    output_dir = run_output_dir(base_dir, result.run_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = (
        export_accepted(output_dir / ACCEPTED_FILENAME, result.accepted, result.entity),
        export_rejected(output_dir / REJECTED_FILENAME, result.rejected),
        export_duplicates(output_dir / DUPLICATES_FILENAME, result.duplicates),
    )
    return output_dir, files


__all__ = ["MigrationRequest", "UnsupportedSourceError", "run_migration"]
