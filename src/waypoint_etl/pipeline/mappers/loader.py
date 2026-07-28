"""Carregamento e validação do template De/Para em YAML.

A seção 10 lista os erros que precisam falhar com mensagem clara. Todos são
detectados aqui, antes de qualquer registro ser processado: um template errado
é problema de configuração, não de dado, e não deve virar 500 registros
rejeitados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ...domain.enums.entity_type import EntityType
from ...domain.enums.source_format import SourceFormat
from ...domain.errors import WaypointError
from ...domain.services.canonical_schema import field_names, required_field_names
from .schema import (
    SUPPORTED_TEMPLATE_VERSION,
    FieldMapping,
    MappingTemplate,
    SourceSpec,
)
from .transforms import available_transforms, is_known_transform


class MappingError(WaypointError):
    """Template De/Para inválido."""


def load_mapping(path: Path) -> MappingTemplate:
    """Carrega e valida um template a partir de um arquivo YAML."""
    if not path.is_file():
        raise MappingError(
            f"Template de mapeamento não encontrado: {path}. "
            "Verifique o caminho informado em --mapping."
        )
    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise MappingError(
            f"O template '{path.name}' não está em UTF-8. Salve o arquivo "
            "nessa codificação e tente novamente."
        ) from error
    return parse_mapping(raw_text, source_name=path.name)


def parse_mapping(raw_text: str, *, source_name: str = "<template>") -> MappingTemplate:
    """Interpreta o YAML de um template e devolve o modelo validado."""
    data = _parse_yaml(raw_text, source_name)
    _check_version(data, source_name)

    name = _require_text(data, "name", source_name)
    entity = _parse_entity(data, source_name)
    source = _parse_source(data, source_name)
    fields = _parse_fields(data, entity, source_name)
    _check_duplicated_targets(fields, source_name)
    _check_required_targets(fields, entity, source_name)

    return MappingTemplate(
        name=name,
        entity=entity,
        fields=fields,
        version=int(data.get("version", SUPPORTED_TEMPLATE_VERSION)),
        source=source,
        ignored_fields=_parse_ignored(data, source_name),
    )


def _parse_yaml(raw_text: str, source_name: str) -> dict[str, Any]:
    """Converte o texto em dicionário, com erro claro para YAML inválido."""
    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as error:
        detail = getattr(error, "problem", None) or "estrutura inválida"
        mark = getattr(error, "problem_mark", None)
        position = f" (linha {mark.line + 1})" if mark is not None else ""
        raise MappingError(
            f"O template '{source_name}' não é um YAML válido{position}: {detail}."
        ) from error

    if data is None:
        raise MappingError(f"O template '{source_name}' está vazio.")
    if not isinstance(data, dict):
        raise MappingError(
            f"O template '{source_name}' deve começar com um mapeamento de "
            "chaves (name, entity, fields), e não com uma lista ou valor solto."
        )
    return data


def _check_version(data: dict[str, Any], source_name: str) -> None:
    """Rejeita versões de schema que este código não sabe interpretar."""
    version = data.get("version", SUPPORTED_TEMPLATE_VERSION)
    if not isinstance(version, int) or isinstance(version, bool):
        raise MappingError(
            f"O campo 'version' do template '{source_name}' deve ser um número "
            f"inteiro (esperado: {SUPPORTED_TEMPLATE_VERSION})."
        )
    if version != SUPPORTED_TEMPLATE_VERSION:
        raise MappingError(
            f"Versão de template não suportada em '{source_name}': {version}. "
            f"Esta versão do Waypoint entende a versão {SUPPORTED_TEMPLATE_VERSION}."
        )


def _require_text(data: dict[str, Any], key: str, source_name: str) -> str:
    """Lê uma chave obrigatória de texto."""
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MappingError(
            f"O template '{source_name}' precisa de um campo '{key}' preenchido."
        )
    return value.strip()


def _parse_entity(data: dict[str, Any], source_name: str) -> EntityType:
    """Converte ``entity`` no enum, listando as opções válidas em caso de erro."""
    raw = _require_text(data, "entity", source_name)
    try:
        return EntityType(raw.lower())
    except ValueError as error:
        options = ", ".join(entity.value for entity in EntityType)
        raise MappingError(
            f"Entidade desconhecida em '{source_name}': '{raw}'. "
            f"Valores aceitos: {options}."
        ) from error


def _parse_source(data: dict[str, Any], source_name: str) -> SourceSpec:
    """Interpreta o bloco ``source`` (opcional)."""
    raw = data.get("source")
    if raw is None:
        return SourceSpec()
    if not isinstance(raw, dict):
        raise MappingError(
            f"O bloco 'source' do template '{source_name}' deve ser um "
            "mapeamento de chaves (type, sheet, header_row)."
        )

    header_row = raw.get("header_row", 1)
    is_positive_int = (
        isinstance(header_row, int)
        and not isinstance(header_row, bool)
        and header_row >= 1
    )
    if not is_positive_int:
        raise MappingError(
            f"'source.header_row' em '{source_name}' deve ser um inteiro maior "
            f"ou igual a 1 (recebido: {header_row!r})."
        )

    return SourceSpec(
        type=_parse_source_type(raw.get("type"), source_name),
        sheet=_optional_text(raw.get("sheet")),
        header_row=header_row,
        encoding=_optional_text(raw.get("encoding")),
        delimiter=_optional_text(raw.get("delimiter")),
    )


def _parse_source_type(raw: object, source_name: str) -> SourceFormat | None:
    """Converte ``source.type`` no enum de formato."""
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise MappingError(
            f"'source.type' em '{source_name}' deve ser texto (ex.: excel, csv)."
        )
    try:
        return SourceFormat(raw.strip().lower())
    except ValueError as error:
        options = ", ".join(fmt.value for fmt in SourceFormat)
        raise MappingError(
            f"Formato de origem desconhecido em '{source_name}': '{raw}'. "
            f"Valores aceitos: {options}."
        ) from error


def _optional_text(raw: object) -> str | None:
    """Normaliza um campo textual opcional."""
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _parse_fields(
    data: dict[str, Any], entity: EntityType, source_name: str
) -> tuple[FieldMapping, ...]:
    """Interpreta o bloco ``fields``, validando alvos e transformações."""
    raw = data.get("fields")
    if not isinstance(raw, dict) or not raw:
        raise MappingError(
            f"O template '{source_name}' precisa de um bloco 'fields' com ao "
            "menos uma coluna de origem."
        )

    valid_targets = field_names(entity)
    mappings: list[FieldMapping] = []

    for column, definition in raw.items():
        source_column = str(column).strip()
        if not source_column:
            raise MappingError(
                f"O template '{source_name}' tem uma coluna de origem sem nome."
            )
        if not isinstance(definition, dict):
            raise MappingError(
                f"A coluna '{source_column}' em '{source_name}' deve declarar ao "
                "menos 'target'. Exemplo: 'target: full_name'."
            )

        target = definition.get("target")
        if not isinstance(target, str) or not target.strip():
            raise MappingError(
                f"A coluna '{source_column}' em '{source_name}' está sem 'target'."
            )
        target = target.strip()
        if target not in valid_targets:
            options = ", ".join(valid_targets)
            raise MappingError(
                f"A coluna '{source_column}' em '{source_name}' aponta para o "
                f"campo '{target}', que não existe no schema de "
                f"'{entity.value}'. Campos disponíveis: {options}."
            )

        mappings.append(
            FieldMapping(
                source=source_column,
                target=target,
                required=bool(definition.get("required", False)),
                transforms=_parse_transforms(definition, source_column, source_name),
                default=_optional_text(definition.get("default")),
            )
        )

    return tuple(mappings)


def _parse_transforms(
    definition: dict[str, Any], column: str, source_name: str
) -> tuple[str, ...]:
    """Valida a lista de transformações declaradas para uma coluna."""
    raw = definition.get("transforms")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise MappingError(
            f"'transforms' da coluna '{column}' em '{source_name}' deve ser uma "
            "lista de nomes."
        )

    names: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise MappingError(
                f"'transforms' da coluna '{column}' em '{source_name}' contém um "
                "item que não é um nome de transformação."
            )
        name = item.strip()
        if not is_known_transform(name):
            options = ", ".join(available_transforms())
            raise MappingError(
                f"Transformação desconhecida na coluna '{column}' de "
                f"'{source_name}': '{name}'. Transformações disponíveis: {options}."
            )
        names.append(name)

    return tuple(names)


def _parse_ignored(data: dict[str, Any], source_name: str) -> tuple[str, ...]:
    """Interpreta ``ignored_fields`` (colunas de origem descartadas de propósito)."""
    raw = data.get("ignored_fields")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise MappingError(
            f"'ignored_fields' em '{source_name}' deve ser uma lista de nomes de "
            "colunas."
        )
    return tuple(str(item).strip() for item in raw if str(item).strip())


def _check_duplicated_targets(
    fields: tuple[FieldMapping, ...], source_name: str
) -> None:
    """Dois campos de origem para o mesmo destino, sem estratégia de merge."""
    seen: dict[str, str] = {}
    for mapping in fields:
        previous = seen.get(mapping.target)
        if previous is not None:
            raise MappingError(
                f"Em '{source_name}', as colunas '{previous}' e '{mapping.source}' "
                f"apontam para o mesmo campo '{mapping.target}'. Remova uma delas: "
                "o MVP não define estratégia de merge entre colunas."
            )
        seen[mapping.target] = mapping.source


def _check_required_targets(
    fields: tuple[FieldMapping, ...], entity: EntityType, source_name: str
) -> None:
    """Todo campo obrigatório do schema precisa ter uma origem."""
    mapped = {mapping.target for mapping in fields}
    missing = [name for name in required_field_names(entity) if name not in mapped]
    if missing:
        listed = ", ".join(missing)
        raise MappingError(
            f"O template '{source_name}' não informa origem para "
            f"campo(s) obrigatório(s) de '{entity.value}': {listed}."
        )


__all__ = ["MappingError", "load_mapping", "parse_mapping"]
