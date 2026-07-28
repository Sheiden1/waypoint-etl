"""Interface Streamlit do Waypoint.

Execute com:

    streamlit run src/waypoint_etl/presentation/streamlit/app.py
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

import streamlit as st

from waypoint_etl.application.dto.extraction import ExtractionOptions
from waypoint_etl.application.dto.results import MigrationResult, SourcePreview
from waypoint_etl.config import get_settings
from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.domain.errors import WaypointError
from waypoint_etl.domain.services.canonical_schema import fields_for
from waypoint_etl.infrastructure.database.session import engine_from_settings
from waypoint_etl.infrastructure.ocr.tesseract import TesseractEngine
from waypoint_etl.logging import configure_logging
from waypoint_etl.pipeline.mappers.loader import MappingError
from waypoint_etl.presentation.streamlit.workflow import (
    ENTITY_LABELS,
    SUPPORTED_UPLOAD_EXTENSIONS,
    MappingSource,
    accepted_rows,
    build_mapping_yaml,
    discover_mapping_templates,
    duplicate_rows,
    inspect_uploaded_source,
    mapping_rows,
    parse_mapping_source,
    rejected_issue_rows,
    run_uploaded_migration,
    upload_digest,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_MAPPINGS_DIR = _PROJECT_ROOT / "mappings"
_DOWNLOAD_MIME = {
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".json": "application/json",
}

settings = get_settings()
configure_logging(settings.log_level)

st.set_page_config(
    page_title="Waypoint — Migração de dados",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 Waypoint")
st.caption("ERP & CRM Data Migration · projeto open-source educacional")
st.info(
    "Os uploads são processados em diretório temporário e removidos ao final. "
    "Use apenas dados sintéticos nesta demonstração."
)


def _clear_result() -> None:
    """Remove resultados de um contexto anterior da sessão."""
    st.session_state.pop("migration_result", None)
    st.session_state.pop("result_context", None)


def _inspect(
    *,
    source_name: str,
    source_content: bytes,
    sheet: str | None,
    header_row: int,
) -> None:
    """Executa a inspeção com erro controlado."""
    try:
        preview = inspect_uploaded_source(
            source_name,
            source_content,
            options=ExtractionOptions(sheet=sheet, header_row=header_row),
            ocr_engine=TesseractEngine(settings=settings),
        )
    except (WaypointError, FileNotFoundError, OSError) as error:
        st.error(f"Não foi possível inspecionar o arquivo: {error}")
        return
    st.session_state["source_preview"] = preview
    _clear_result()


def _execute(
    *,
    source_name: str,
    source_content: bytes,
    mapping: MappingSource,
    entity: EntityType,
    context: str,
    dry_run: bool,
) -> None:
    """Executa validação ou carga real e mantém o resultado na sessão."""
    try:
        engine = None if dry_run else engine_from_settings(settings)
        with st.spinner(
            "Validando registros..."
            if dry_run
            else "Carregando registros no PostgreSQL..."
        ):
            result = run_uploaded_migration(
                source_name=source_name,
                source_content=source_content,
                mapping=mapping,
                output_dir=settings.export_dir,
                entity=entity,
                dry_run=dry_run,
                engine=engine,
            )
    except (WaypointError, FileNotFoundError, OSError) as error:
        st.error(f"A execução não foi concluída: {error}")
        return

    st.session_state["migration_result"] = result
    st.session_state["result_context"] = context
    if dry_run:
        st.success("Validação concluída. Nenhum registro foi gravado no banco.")
    else:
        st.success(f"Carga concluída: {result.loaded_records} registro(s) gravado(s).")


def _render_preview(preview: SourcePreview) -> None:
    """Apresenta a prévia devolvida pelo caso de uso."""
    left, middle, right = st.columns(3)
    left.metric("Formato", preview.source_format.value.upper())
    middle.metric("Tipo", "Tabular" if preview.is_tabular else "Documento")
    right.metric("OCR", "Usado" if preview.ocr_used else "Não usado")

    if preview.is_tabular:
        st.dataframe(list(preview.rows), use_container_width=True, hide_index=True)
        st.caption(f"{len(preview.columns)} coluna(s) encontrada(s).")
    else:
        st.text_area(
            "Texto extraído",
            preview.text_preview or "(nenhum texto encontrado)",
            height=220,
            disabled=True,
        )

    for warning in preview.warnings:
        st.warning(warning)


def _render_result(result: MigrationResult) -> None:
    """Apresenta totais e tabelas da execução."""
    st.subheader("5. Resultado")
    total, valid, rejected, duplicates = st.columns(4)
    total.metric("Processados", result.total_records)
    valid.metric("Válidos", len(result.accepted))
    rejected.metric("Rejeitados", len(result.rejected))
    duplicates.metric(
        "Duplicidades",
        result.duplicate_count,
        help=f"{result.possible_duplicate_count} suspeita(s) adicional(is)",
    )

    st.code(result.run_id, language=None)
    mode = "dry-run" if result.run.dry_run else "carga PostgreSQL"
    duration = result.run.duration_ms or sum(
        stage.duration_ms for stage in result.stages
    )
    st.caption(f"Modo: {mode} · duração: {duration} ms")

    accepted_tab, rejected_tab, duplicates_tab, stages_tab = st.tabs(
        ["Válidos", "Rejeitados", "Duplicidades", "Etapas"]
    )
    with accepted_tab:
        rows = accepted_rows(result.accepted)
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro válido nesta execução.")
    with rejected_tab:
        rows = rejected_issue_rows(result.rejected)
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.success("Nenhum registro rejeitado.")
    with duplicates_tab:
        rows = duplicate_rows(result)
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.success("Nenhuma duplicidade encontrada.")
    with stages_tab:
        st.dataframe(
            [
                {"Etapa": stage.name, "Duração (ms)": stage.duration_ms}
                for stage in result.stages
            ],
            use_container_width=True,
            hide_index=True,
        )

    for warning in result.warnings:
        st.warning(warning)


def _render_downloads(result: MigrationResult) -> None:
    """Cria downloads reais para os quatro artefatos gerados."""
    st.subheader("4. Destino")
    st.write("Baixe os artefatos gerados nesta execução:")
    columns = st.columns(4)
    for column, file in zip(columns, result.exported_files, strict=False):
        if not file.is_file():
            column.warning(f"{file.name} não está mais disponível.")
            continue
        column.download_button(
            label=f"Baixar {file.name}",
            data=file.read_bytes(),
            file_name=file.name,
            mime=_DOWNLOAD_MIME.get(file.suffix, "application/octet-stream"),
            use_container_width=True,
            key=f"download-{result.run_id}-{file.name}",
        )


st.subheader("1. Origem")
entity = cast(
    EntityType,
    st.selectbox(
        "Tipo de dado",
        options=list(EntityType),
        format_func=lambda item: ENTITY_LABELS[item],
    ),
)
uploaded = st.file_uploader(
    "Arquivo de origem",
    type=list(SUPPORTED_UPLOAD_EXTENSIONS),
    help=f"Limite configurado: {settings.max_upload_mb} MB.",
)

if uploaded is None:
    st.info("Envie um arquivo para iniciar o assistente.")
    st.stop()

source_content = uploaded.getvalue()
source_name = uploaded.name
max_bytes = settings.max_upload_mb * 1024 * 1024
if len(source_content) > max_bytes:
    st.error(
        f"O arquivo excede o limite de {settings.max_upload_mb} MB. "
        "Escolha um arquivo menor."
    )
    st.stop()

source_digest = upload_digest(source_name, source_content)
if st.session_state.get("source_digest") != source_digest:
    st.session_state["source_digest"] = source_digest
    st.session_state.pop("source_preview", None)
    _clear_result()

options_left, options_right = st.columns(2)
header_row = int(
    options_left.number_input(
        "Linha do cabeçalho",
        min_value=1,
        value=1,
        help="Usada somente em CSV e Excel.",
    )
)
sheet_value = options_right.text_input(
    "Aba da planilha (opcional)",
    help="Deixe em branco para usar a aba ativa.",
)
sheet = sheet_value.strip() or None
inspection_context = f"{source_digest}:{sheet or ''}:{header_row}"
if st.session_state.get("inspection_context") not in (None, inspection_context):
    st.session_state.pop("source_preview", None)
    _clear_result()

if st.button("Inspecionar arquivo", type="primary"):
    _inspect(
        source_name=source_name,
        source_content=source_content,
        sheet=sheet,
        header_row=header_row,
    )
    if "source_preview" in st.session_state:
        st.session_state["inspection_context"] = inspection_context

preview = st.session_state.get("source_preview")
if not isinstance(preview, SourcePreview):
    st.caption("A inspeção confirma o formato e mostra uma amostra antes de migrar.")
    st.stop()

_render_preview(preview)

if not preview.is_tabular:
    st.warning(
        "Documentos podem ser inspecionados e usar OCR, mas o mapeamento "
        "estruturado do MVP aceita somente CSV e Excel."
    )
    st.stop()

st.subheader("2. Mapeamento")
mapping_mode = st.radio(
    "Como deseja definir o De/Para?",
    ("Template pronto", "Criar pela interface", "Enviar YAML"),
    horizontal=True,
)

mapping_source: MappingSource | None = None
if mapping_mode == "Template pronto":
    try:
        catalog = discover_mapping_templates(_MAPPINGS_DIR)
    except MappingError as error:
        st.error(f"Um template do catálogo é inválido: {error}")
        st.stop()

    compatible = [
        (path, template)
        for path, template in catalog
        if template.entity is entity
        and (
            template.source.type is None
            or template.source.type is preview.source_format
        )
    ]
    if not compatible:
        st.warning("Não há template pronto compatível com a entidade e o formato.")
    else:
        selected_index = st.selectbox(
            "Template",
            range(len(compatible)),
            format_func=lambda index: compatible[index][1].name,
        )
        selected_path, selected_template = compatible[selected_index]
        mapping_source = MappingSource(name=selected_path.name, path=selected_path)
        st.dataframe(
            mapping_rows(selected_template),
            use_container_width=True,
            hide_index=True,
        )

elif mapping_mode == "Enviar YAML":
    mapping_upload = st.file_uploader(
        "Template De/Para",
        type=["yaml", "yml"],
        key="mapping-upload",
    )
    if mapping_upload is not None:
        mapping_source = MappingSource(
            name=mapping_upload.name,
            content=mapping_upload.getvalue(),
        )
        try:
            uploaded_template = parse_mapping_source(mapping_source)
        except (MappingError, UnicodeDecodeError) as error:
            st.error(f"Template inválido: {error}")
            mapping_source = None
        else:
            st.dataframe(
                mapping_rows(uploaded_template),
                use_container_width=True,
                hide_index=True,
            )

else:
    target_fields = fields_for(entity)
    target_names = [field.name for field in target_fields]
    descriptions = {field.name: field.description for field in target_fields}
    assignments: dict[str, str | None] = {}
    st.caption(
        "Associe cada coluna encontrada a um campo canônico. Campos ignorados "
        "não entram no pipeline."
    )
    for index, source_column in enumerate(preview.columns):
        source_col, target_col = st.columns((2, 3))
        source_col.text_input(
            "Coluna de origem",
            value=source_column,
            disabled=True,
            key=f"source-{source_digest}-{index}",
        )
        target_options: list[str] = ["Ignorar", *target_names]
        choice = target_col.selectbox(
            "Campo de destino",
            target_options,
            format_func=lambda value: (
                value if value == "Ignorar" else f"{value} — {descriptions[value]}"
            ),
            key=f"target-{source_digest}-{entity.value}-{index}",
        )
        assignments[source_column] = None if choice == "Ignorar" else choice

    mapping_name = st.text_input(
        "Nome do template",
        value=f"Mapeamento {source_name}",
    )
    try:
        generated = build_mapping_yaml(
            name=mapping_name,
            entity=entity,
            source_format=preview.source_format,
            assignments=assignments,
            sheet=sheet,
            header_row=header_row,
        )
    except MappingError as error:
        st.warning(f"Complete o De/Para para continuar: {error}")
    else:
        mapping_source = MappingSource(
            name="mapping-interface.yaml",
            content=generated,
        )
        st.download_button(
            "Baixar template YAML",
            data=generated,
            file_name="waypoint-mapping.yaml",
            mime="application/yaml",
        )

if mapping_source is None:
    st.stop()

context = f"{source_digest}:{mapping_source.digest}:{entity.value}"
if st.session_state.get("result_context") not in (None, context):
    _clear_result()

st.subheader("3. Validação")
st.write(
    "Execute o pipeline completo em **dry-run**. Os relatórios são gerados, "
    "mas nenhuma tabela de destino é alterada."
)
if st.button("Executar validação", type="primary"):
    _execute(
        source_name=source_name,
        source_content=source_content,
        mapping=mapping_source,
        entity=entity,
        context=context,
        dry_run=True,
    )

result = st.session_state.get("migration_result")
if (
    not isinstance(result, MigrationResult)
    or st.session_state.get("result_context") != context
):
    st.stop()

_render_downloads(result)

if settings.database_available:
    confirm_load = st.checkbox(
        "Confirmo que desejo gravar os registros válidos no PostgreSQL."
    )
    if st.button(
        "Importar aprovados para PostgreSQL",
        disabled=not confirm_load,
    ):
        _execute(
            source_name=source_name,
            source_content=source_content,
            mapping=mapping_source,
            entity=entity,
            context=context,
            dry_run=False,
        )
        loaded_result = st.session_state.get("migration_result")
        if isinstance(loaded_result, MigrationResult):
            result = loaded_result
else:
    st.caption(
        "Carga PostgreSQL indisponível: defina DATABASE_URL no .env. "
        "O dry-run e os downloads continuam funcionando."
    )

_render_result(result)
