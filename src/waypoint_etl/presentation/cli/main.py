"""Entry point da CLI ``waypoint-etl``.

Nesta fundação (Dia 1) apenas o comando ``version`` está implementado. Os
comandos ``inspect`` e ``migrate`` estão declarados, porém explicitamente
marcados como indisponíveis até que o núcleo do pipeline seja construído
(Dias 9). Nenhuma funcionalidade é simulada.
"""

from __future__ import annotations

import typer

from waypoint_etl import __version__

app = typer.Typer(
    help="Waypoint - ERP & CRM Data Migration Toolkit.",
    no_args_is_help=True,
    add_completion=False,
)

_NOT_AVAILABLE = "Comando indisponível nesta versão. Em desenvolvimento."


@app.command()
def version() -> None:
    """Exibe a versão do Waypoint."""
    typer.echo(f"Waypoint {__version__}")


@app.command()
def inspect(path: str) -> None:
    """Inspeciona um arquivo de origem (indisponível nesta versão)."""
    typer.echo(_NOT_AVAILABLE)
    raise typer.Exit(code=1)


@app.command()
def migrate(
    input: str = typer.Option(..., "--input"),
    entity: str = typer.Option(..., "--entity"),
    mapping: str = typer.Option(..., "--mapping"),
    output: str = typer.Option("./exports", "--output"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    load_postgres: bool = typer.Option(False, "--load-postgres"),
) -> None:
    """Executa uma migração (indisponível nesta versão)."""
    typer.echo(_NOT_AVAILABLE)
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
