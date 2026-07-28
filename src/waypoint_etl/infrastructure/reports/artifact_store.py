"""Armazenamento efêmero dos relatórios produzidos pela API web.

O upload original nunca entra neste armazenamento. Somente os quatro artefatos
gerados pelo caso de uso são copiados para uma pasta temporária, identificada
pelo ``run_id`` e removida automaticamente após o TTL configurado.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ...domain.errors import WaypointError
from .audit import AUDIT_FILENAME
from .exporters import ACCEPTED_FILENAME, DUPLICATES_FILENAME, REJECTED_FILENAME


@dataclass(frozen=True, slots=True)
class ArtifactSpec:
    """Nome público e tipo de conteúdo de um relatório permitido."""

    name: str
    media_type: str


ARTIFACT_SPECS: tuple[ArtifactSpec, ...] = (
    ArtifactSpec(ACCEPTED_FILENAME, "text/csv"),
    ArtifactSpec(
        REJECTED_FILENAME,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
    ArtifactSpec(DUPLICATES_FILENAME, "text/csv"),
    ArtifactSpec(AUDIT_FILENAME, "application/json"),
)
_ARTIFACT_BY_NAME = {spec.name: spec for spec in ARTIFACT_SPECS}


class ArtifactStoreError(WaypointError):
    """Falha ao publicar os relatórios temporários de uma execução."""


class ArtifactRunNotFoundError(WaypointError):
    """A execução não existe mais no armazenamento efêmero."""


class ArtifactNotFoundError(WaypointError):
    """O nome pedido não pertence ao conjunto seguro de relatórios."""


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    """Arquivo liberado para download após validação de nome e ``run_id``."""

    path: Path
    spec: ArtifactSpec


class TemporaryArtifactStore:
    """Guarda somente relatórios gerados, em disco temporário com TTL.

    O diretório padrão fica no volume efêmero da instância. Isso funciona em
    serviços como o Render sem exigir storage persistente: uma reinicialização
    simplesmente invalida downloads antigos, enquanto o pipeline continua
    stateless em relação aos uploads.
    """

    def __init__(
        self,
        *,
        ttl_seconds: int,
        root: Path | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("O TTL dos artefatos precisa ser maior que zero.")
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._owns_root = root is None
        if root is None:
            root = Path(tempfile.mkdtemp(prefix="waypoint-api-artifacts-"))
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def ttl_seconds(self) -> int:
        """Tempo, em segundos, durante o qual um download fica disponível."""
        return self._ttl_seconds

    @property
    def root(self) -> Path:
        """Raiz temporária; exposta para observabilidade e testes."""
        return self._root

    def publish(self, run_id: str, files: Sequence[Path]) -> tuple[ArtifactSpec, ...]:
        """Publica os quatro relatórios de uma execução de forma atômica."""
        safe_run_id = _validated_run_id(run_id)
        self.cleanup_expired()

        files_by_name = {path.name: path for path in files}
        missing = [
            spec.name for spec in ARTIFACT_SPECS if spec.name not in files_by_name
        ]
        if missing:
            names = ", ".join(missing)
            raise ArtifactStoreError(
                f"A execução não gerou todos os relatórios esperados: {names}."
            )

        destination = self._root / safe_run_id
        staging = self._root / f".{safe_run_id}-{uuid.uuid4().hex}.tmp"
        try:
            staging.mkdir(parents=False)
            for spec in ARTIFACT_SPECS:
                source = files_by_name[spec.name]
                if not source.is_file():
                    raise ArtifactStoreError(
                        f"O relatório '{spec.name}' não foi encontrado após a execução."
                    )
                shutil.copyfile(source, staging / spec.name)

            if destination.exists():
                raise ArtifactStoreError(
                    "Já existem relatórios temporários para esta execução."
                )
            staging.replace(destination)
            created_at = self._clock()
            os.utime(destination, (created_at, created_at))
        except ArtifactStoreError:
            if staging.exists():
                shutil.rmtree(staging)
            raise
        except OSError as error:
            if staging.exists():
                shutil.rmtree(staging)
            raise ArtifactStoreError(
                "Os relatórios temporários não puderam ser publicados."
            ) from error

        return ARTIFACT_SPECS

    def resolve(self, run_id: str, artifact_name: str) -> StoredArtifact:
        """Localiza um relatório sem permitir nomes arbitrários ou traversal."""
        spec = _ARTIFACT_BY_NAME.get(artifact_name)
        if spec is None:
            raise ArtifactNotFoundError(
                "Relatório desconhecido. Escolha accepted.csv, rejected.xlsx, "
                "duplicates.csv ou audit-report.json."
            )

        try:
            safe_run_id = _validated_run_id(run_id)
        except ArtifactRunNotFoundError:
            raise ArtifactRunNotFoundError(
                "Execução não encontrada ou já expirada. Faça uma nova validação."
            ) from None

        self.cleanup_expired()
        run_dir = self._root / safe_run_id
        if not run_dir.is_dir():
            raise ArtifactRunNotFoundError(
                "Execução não encontrada ou já expirada. Faça uma nova validação."
            )

        path = run_dir / spec.name
        if not path.is_file():
            raise ArtifactNotFoundError(
                "O relatório solicitado não está disponível. Execute a validação "
                "novamente."
            )
        return StoredArtifact(path=path, spec=spec)

    def cleanup_expired(self) -> int:
        """Remove execuções cujo TTL terminou e devolve quantas foram limpas."""
        cutoff = self._clock() - self._ttl_seconds
        removed = 0
        if not self._root.is_dir():
            return removed

        try:
            candidates = tuple(self._root.iterdir())
        except OSError as error:
            raise ArtifactStoreError(
                "O armazenamento temporário não pôde ser consultado."
            ) from error

        for candidate in candidates:
            if not candidate.is_dir() or candidate.name.startswith("."):
                continue
            try:
                expired = candidate.stat().st_mtime <= cutoff
            except FileNotFoundError:
                continue
            except OSError as error:
                raise ArtifactStoreError(
                    "A validade dos relatórios temporários não pôde ser verificada."
                ) from error
            if expired:
                try:
                    shutil.rmtree(candidate)
                except FileNotFoundError:
                    continue
                except OSError as error:
                    raise ArtifactStoreError(
                        "Um relatório expirado não pôde ser removido com segurança."
                    ) from error
                removed += 1
        return removed

    def close(self) -> None:
        """Remove a raiz criada pelo próprio armazenamento ao encerrar a API."""
        if self._owns_root and self._root.is_dir():
            shutil.rmtree(self._root)


def _validated_run_id(run_id: str) -> str:
    """Aceita apenas UUID canônico, impedindo nomes de diretório controlados."""
    try:
        parsed = uuid.UUID(run_id)
    except (ValueError, AttributeError) as error:
        raise ArtifactRunNotFoundError(
            "Execução não encontrada ou já expirada. Faça uma nova validação."
        ) from error
    if str(parsed) != run_id.lower():
        raise ArtifactRunNotFoundError(
            "Execução não encontrada ou já expirada. Faça uma nova validação."
        )
    return str(parsed)


__all__ = [
    "ARTIFACT_SPECS",
    "ArtifactNotFoundError",
    "ArtifactRunNotFoundError",
    "ArtifactSpec",
    "ArtifactStoreError",
    "StoredArtifact",
    "TemporaryArtifactStore",
]
