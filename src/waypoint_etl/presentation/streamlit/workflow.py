"""Adaptadores puros do assistente Streamlit.

O módulo não importa Streamlit. Ele materializa uploads apenas durante a chamada
dos casos de uso e converte os resultados em linhas seguras para apresentação.
Assim, a interface continua fina e toda regra do pipeline permanece em
``application``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml
from sqlalchemy import Engine

from ...application.dto.results import MigrationResult
from ...application.use_cases.run_migration import MigrationRequest, run_migration
from ...domain.enums.entity_type import EntityType
from ...domain.enums.source_format import SourceFormat
from ...domain.services.canonical_schema import fields_for
from ...domain.value_objects.document import mask_document
from ...pipeline.mappers.loader import load_mapping, parse_mapping
from ...pipeline.mappers.schema import MappingTemplate
from ...pipeline.validators.result import ValidatedRecord
from ..uploads import (
    SUPPORTED_UPLOAD_EXTENSIONS,
    inspect_uploaded_source,
    materialized_upload,
    safe_upload_name,
    upload_digest,
)

ENTITY_LABELS: Mapping[EntityType, str] = {
    EntityType.CUSTOMERS: "Clientes",
    EntityType.CONTACTS: "Contatos",
    EntityType.INVOICES: "Cobranças",
}

_SENSITIVE_TARGETS = frozenset({"document", "customer_document"})

_SUGGESTED_TRANSFORMS: Mapping[str, tuple[str, ...]] = {
    "external_id": ("clean_text",),
    "full_name": ("clean_text", "title_case"),
    "name": ("clean_text", "title_case"),
    "role": ("clean_text", "title_case"),
    "document": ("digits_only",),
    "customer_document": ("digits_only",),
    "email": ("email",),
    "phone": ("brazilian_phone",),
    "postal_code": ("postal_code",),
    "city": ("clean_text", "title_case"),
    "state": ("uf",),
    "created_at": ("clean_text", "brazilian_date"),
    "description": ("clean_text",),
    "issued_at": ("clean_text", "brazilian_date"),
    "due_at": ("clean_text", "brazilian_date"),
    "amount": ("clean_text", "brazilian_money"),
    "status": ("clean_text", "lowercase"),
}


@dataclass(frozen=True, slots=True)
class MappingSource:
    """Template escolhido na interface, em disco ou recebido como upload."""

    name: str
    path: Path | None = None
    content: bytes | None = None

    def __post_init__(self) -> None:
        if (self.path is None) == (self.content is None):
            raise ValueError("Informe exatamente um entre path e content.")

    @property
    def digest(self) -> str:
        """Identificador estável para invalidar resultados antigos da tela."""
        content = self.path.read_bytes() if self.path is not None else self.content
        assert content is not None
        return hashlib.sha256(content).hexdigest()


def run_uploaded_migration(
    *,
    source_name: str,
    source_content: bytes,
    mapping: MappingSource,
    output_dir: Path,
    entity: EntityType,
    dry_run: bool = True,
    engine: Engine | None = None,
) -> MigrationResult:
    """Executa o mesmo caso de uso da CLI sobre arquivos enviados pela tela."""
    with materialized_upload(source_name, source_content) as source:
        if mapping.path is not None:
            return run_migration(
                MigrationRequest(
                    source=source,
                    mapping=mapping.path,
                    output_dir=output_dir,
                    dry_run=dry_run,
                    entity=entity,
                ),
                engine=engine,
            )

        assert mapping.content is not None
        with materialized_upload(
            safe_upload_name(mapping.name, fallback="mapping.yaml"),
            mapping.content,
        ) as mapping_path:
            return run_migration(
                MigrationRequest(
                    source=source,
                    mapping=mapping_path,
                    output_dir=output_dir,
                    dry_run=dry_run,
                    entity=entity,
                ),
                engine=engine,
            )


def discover_mapping_templates(
    directory: Path,
) -> tuple[tuple[Path, MappingTemplate], ...]:
    """Carrega os templates válidos encontrados no diretório do projeto."""
    if not directory.is_dir():
        return ()
    return tuple(
        (path, load_mapping(path))
        for path in sorted(directory.glob("*.yaml"))
        if path.is_file()
    )


def parse_mapping_source(mapping: MappingSource) -> MappingTemplate:
    """Lê a escolha da tela para apresentar seu conteúdo antes de executar."""
    if mapping.path is not None:
        return load_mapping(mapping.path)
    assert mapping.content is not None
    return parse_mapping(
        mapping.content.decode("utf-8"),
        source_name=safe_upload_name(mapping.name, fallback="mapping.yaml"),
    )


def build_mapping_yaml(
    *,
    name: str,
    entity: EntityType,
    source_format: SourceFormat,
    assignments: Mapping[str, str | None],
    sheet: str | None = None,
    header_row: int = 1,
) -> bytes:
    """Cria e valida um template a partir das associações feitas na tela."""
    required = {field.name for field in fields_for(entity) if field.required}
    mapped_fields: dict[str, object] = {}
    ignored_fields: list[str] = []

    for source, target in assignments.items():
        if target is None:
            ignored_fields.append(source)
            continue
        mapped_fields[source] = {
            "target": target,
            "required": target in required,
            "transforms": list(_SUGGESTED_TRANSFORMS.get(target, ("clean_text",))),
        }

    source_spec: dict[str, object] = {
        "type": source_format.value,
        "header_row": header_row,
    }
    if source_format is SourceFormat.EXCEL and sheet:
        source_spec["sheet"] = sheet

    data = {
        "version": 1,
        "name": name.strip() or "Template criado na interface",
        "entity": entity.value,
        "source": source_spec,
        "fields": mapped_fields,
        "ignored_fields": ignored_fields,
    }
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    parse_mapping(text, source_name="template-criado-na-interface.yaml")
    return text.encode("utf-8")


def mapping_rows(template: MappingTemplate) -> list[dict[str, object]]:
    """Linhas do De/Para para a tabela da etapa de mapeamento."""
    return [
        {
            "Origem": field.source,
            "Destino": field.target,
            "Obrigatório": "Sim" if field.required else "Não",
            "Transformações": " → ".join(field.transforms) or "Nenhuma",
        }
        for field in template.fields
    ]


def accepted_rows(records: tuple[ValidatedRecord, ...]) -> list[dict[str, object]]:
    """Entidades aceitas prontas para prévia, com documentos mascarados."""
    rows: list[dict[str, object]] = []
    for record in records:
        if record.entity is None:
            continue
        row = asdict(record.entity)
        for field in _SENSITIVE_TARGETS:
            value = row.get(field)
            if value is not None:
                row[field] = mask_document(str(value))
        rows.append(row)
    return rows


def rejected_issue_rows(
    records: tuple[ValidatedRecord, ...],
) -> list[dict[str, object]]:
    """Problemas rejeitados em formato tabular e seguro para a interface."""
    rows: list[dict[str, object]] = []
    for record in records:
        for issue in record.issues_for_display():
            rows.append(
                {
                    "Linha": record.row_number,
                    "Aba": record.sheet or "",
                    "Campo": issue.field or "",
                    "Código": issue.code,
                    "Severidade": issue.severity.value,
                    "Mensagem": issue.message,
                    "Original": issue.original_value,
                    "Normalizado": issue.normalized_value,
                }
            )
    return rows


def duplicate_rows(result: MigrationResult) -> list[dict[str, object]]:
    """Duplicidades exatas e possíveis, com documentos mascarados."""
    rows: list[dict[str, object]] = []
    for match in (*result.duplicates.exact, *result.duplicates.possible):
        value = match.value
        if match.key in _SENSITIVE_TARGETS:
            value = mask_document(value)
        rows.append(
            {
                "Linha": match.row_number,
                "Linha correspondente": match.matched_row_number,
                "Tipo": "Exata" if match.exact else "Possível",
                "Chave": match.key,
                "Valor": value,
                "Similaridade": match.similarity,
            }
        )
    return rows


__all__ = [
    "ENTITY_LABELS",
    "SUPPORTED_UPLOAD_EXTENSIONS",
    "MappingSource",
    "accepted_rows",
    "build_mapping_yaml",
    "discover_mapping_templates",
    "duplicate_rows",
    "inspect_uploaded_source",
    "mapping_rows",
    "parse_mapping_source",
    "rejected_issue_rows",
    "run_uploaded_migration",
    "safe_upload_name",
    "upload_digest",
]
