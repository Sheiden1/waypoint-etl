"""Entry point da CLI ``waypoint-etl``.

Esta camada só monta parâmetros e apresenta resultados: toda a regra vive nos
casos de uso, que o Streamlit consome igualmente (seção 5).

As mensagens de erro sugerem uma ação e nunca expõem stack trace (seção 17);
o rastreamento completo fica nos logs quando ``--verbose`` está ativo.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

import typer
from sqlalchemy import Engine

from waypoint_etl import __version__
from waypoint_etl.application.dto.results import MigrationResult, SourcePreview
from waypoint_etl.application.use_cases.inspect_source import inspect_source
from waypoint_etl.application.use_cases.run_migration import (
    MigrationRequest,
    run_migration,
)
from waypoint_etl.config import get_settings
from waypoint_etl.domain.enums.entity_type import EntityType
from waypoint_etl.domain.errors import WaypointError
from waypoint_etl.logging import configure_logging

app = typer.Typer(
    help="Waypoint - ERP & CRM Data Migration Toolkit.",
    no_args_is_help=True,
    add_completion=False,
)

# Quantas linhas da prévia aparecem no terminal.
_PREVIEW_LIMIT = 5


@app.command()
def version() -> None:
    """Exibe a versão do Waypoint."""
    typer.echo(f"Waypoint {__version__}")


@app.command()
def inspect(
    path: Annotated[Path, typer.Argument(help="Arquivo de origem a inspecionar.")],
    sheet: Annotated[
        str | None, typer.Option("--sheet", help="Aba da planilha a ler.")
    ] = None,
    header_row: Annotated[
        int, typer.Option("--header-row", help="Linha do cabeçalho (1-based).")
    ] = 1,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Exibe logs detalhados.")
    ] = False,
) -> None:
    """Mostra formato, colunas e uma prévia do conteúdo de um arquivo."""
    _configure(verbose)
    from waypoint_etl.application.dto.extraction import ExtractionOptions

    with _handled():
        preview = inspect_source(
            path, options=ExtractionOptions(sheet=sheet, header_row=header_row)
        )
    _render_preview(preview)


@app.command()
def migrate(
    input: Annotated[
        Path, typer.Option("--input", "-i", help="Arquivo de origem.")
    ],
    mapping: Annotated[
        Path, typer.Option("--mapping", "-m", help="Template De/Para em YAML.")
    ],
    entity: Annotated[
        EntityType | None,
        typer.Option("--entity", "-e", help="Entidade esperada pelo template."),
    ] = None,
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Diretório das exportações.")
    ] = Path("exports"),
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run/--no-dry-run",
            help="Em dry-run nada é gravado no banco (padrão).",
        ),
    ] = True,
    load_postgres: Annotated[
        bool,
        typer.Option("--load-postgres", help="Carrega os válidos no PostgreSQL."),
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Exibe logs detalhados.")
    ] = False,
) -> None:
    """Executa uma migração e gera os relatórios da execução."""
    _configure(verbose)

    if load_postgres and dry_run:
        typer.secho(
            "Erro: --load-postgres exige --no-dry-run. Em dry-run nada é gravado.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    request = MigrationRequest(
        source=input,
        mapping=mapping,
        output_dir=output,
        dry_run=dry_run,
        entity=entity,
    )

    # A criação da engine fica dentro do bloco tratado: a ausência de
    # DATABASE_URL é um erro de configuração e merece mensagem, não stack trace.
    with _handled():
        result = run_migration(request, engine=_engine_for(load_postgres))

    _render_result(result)
    if result.rejected:
        # Saída não-zero permite usar o comando em pipelines de verificação.
        raise typer.Exit(code=1)


def _configure(verbose: bool) -> None:
    """Configura o logging conforme o nível pedido."""
    settings = get_settings()
    configure_logging("DEBUG" if verbose else settings.log_level)


def _engine_for(load_postgres: bool) -> Engine | None:
    """Cria a engine apenas quando a carga real foi solicitada."""
    if not load_postgres:
        return None
    from waypoint_etl.infrastructure.database.session import engine_from_settings

    return engine_from_settings()


@contextmanager
def _handled() -> Iterator[None]:
    """Converte erros conhecidos em mensagens acionáveis, sem stack trace.

    O ``from None`` corta o encadeamento: o usuário da CLI recebe a orientação,
    e o rastreamento completo fica nos logs (seção 17).
    """
    try:
        yield
    except WaypointError as error:
        typer.secho(f"Erro: {error}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from None
    except FileNotFoundError as error:
        typer.secho(
            f"Erro: arquivo não encontrado: {error}", fg=typer.colors.RED, err=True
        )
        raise typer.Exit(code=2) from None


def _render_preview(preview: SourcePreview) -> None:
    """Imprime a prévia de um arquivo inspecionado."""
    typer.echo(f"Arquivo:  {preview.source_name}")
    typer.echo(f"Formato:  {preview.source_format.value}")

    if preview.available_sheets:
        typer.echo(f"Abas:     {', '.join(preview.available_sheets)}")

    if preview.is_tabular:
        typer.echo(f"Colunas:  {len(preview.columns)}")
        for column in preview.columns:
            typer.echo(f"  - {column}")
        typer.echo(f"\nPrévia ({min(len(preview.rows), _PREVIEW_LIMIT)} linhas):")
        for row in preview.rows[:_PREVIEW_LIMIT]:
            rendered = ", ".join(f"{key}={value!r}" for key, value in row.items())
            typer.echo(f"  {rendered}")
    else:
        typer.echo(f"Páginas:  {preview.page_count}")
        typer.echo(f"OCR:      {'sim' if preview.ocr_used else 'não'}")
        typer.echo("\nTrecho do texto:")
        typer.echo(preview.text_preview or "(sem texto)")

    _render_warnings(preview.warnings)


def _render_result(result: MigrationResult) -> None:
    """Imprime o resumo de uma migração."""
    typer.echo(f"run_id:      {result.run_id}")
    typer.echo(f"Entidade:    {result.entity.value}")
    typer.echo(f"Modo:        {'dry-run' if result.run.dry_run else 'carga real'}")
    typer.echo("")
    typer.echo(f"Total:       {result.total_records}")
    typer.secho(f"Válidos:     {len(result.accepted)}", fg=typer.colors.GREEN)

    rejected_color = typer.colors.RED if result.rejected else None
    typer.secho(f"Rejeitados:  {len(result.rejected)}", fg=rejected_color)
    typer.echo(f"Duplicatas:  {result.duplicate_count}")
    typer.echo(f"Suspeitas:   {result.possible_duplicate_count}")

    if result.loaded_records:
        typer.secho(
            f"Carregados:  {result.loaded_records}", fg=typer.colors.GREEN
        )

    if result.stages:
        total_ms = sum(stage.duration_ms for stage in result.stages)
        typer.echo(f"\nDuração:     {total_ms} ms")
        for stage in result.stages:
            typer.echo(f"  {stage.name:<14} {stage.duration_ms:>6} ms")

    if result.output_dir is not None:
        typer.echo(f"\nExportações em {result.output_dir}:")
        for file in result.exported_files:
            typer.echo(f"  - {file.name}")

    _render_warnings(result.warnings)


def _render_warnings(warnings: tuple[str, ...]) -> None:
    """Imprime os avisos acumulados, se houver."""
    if not warnings:
        return
    typer.echo("")
    for warning in warnings:
        typer.secho(f"Aviso: {warning}", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()
