"""Smoke test reproduzível para um deploy público do Waypoint."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPOSITORY_ROOT / "samples" / "input" / "clientes_legado.csv"
DEFAULT_MAPPING = REPOSITORY_ROOT / "mappings" / "erp_legacy_customers_csv.yaml"
EXPECTED_ARTIFACTS = {
    "accepted.csv",
    "rejected.xlsx",
    "duplicates.csv",
    "audit-report.json",
}


def _normalized_url(value: str) -> str:
    url = value.rstrip("/")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"URL inválida: {value}")
    return url


def _request(
    url: str,
    *,
    timeout: float,
    method: str = "GET",
    headers: Mapping[str, str] | None = None,
    body: bytes | None = None,
) -> tuple[int, Mapping[str, str], bytes]:
    request = Request(
        url,
        data=body,
        headers=dict(headers or {}),
        method=method,
    )
    with urlopen(request, timeout=timeout) as response:
        return response.status, response.headers, response.read()


def _multipart_body(
    *,
    fields: Mapping[str, str],
    files: Sequence[tuple[str, Path, str]],
) -> tuple[bytes, str]:
    boundary = f"waypoint-smoke-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.extend(
            (
                f"--{boundary}\r\n".encode(),
                (f'Content-Disposition: form-data; name="{name}"\r\n\r\n').encode(),
                value.encode(),
                b"\r\n",
            )
        )

    for field_name, path, content_type in files:
        chunks.extend(
            (
                f"--{boundary}\r\n".encode(),
                (
                    "Content-Disposition: form-data; "
                    f'name="{field_name}"; filename="{path.name}"\r\n'
                ).encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                path.read_bytes(),
                b"\r\n",
            )
        )

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _check_frontend(web_url: str, *, timeout: float) -> None:
    status, _, body = _request(web_url, timeout=timeout)
    page = body.decode("utf-8", errors="replace")
    if status != 200 or 'id="root"' not in page or "Waypoint" not in page:
        raise RuntimeError("O frontend não devolveu o HTML esperado.")
    print("[ok] Frontend estático")


def _check_health(api_url: str, *, timeout: float) -> None:
    status, _, body = _request(
        f"{api_url}/api/v1/health",
        timeout=timeout,
        headers={"Accept": "application/json"},
    )
    payload = json.loads(body)
    if status != 200 or payload.get("status") != "ok":
        raise RuntimeError("O health check da API não retornou status=ok.")
    print(f"[ok] API saudável (versão {payload.get('version', 'desconhecida')})")


def _check_cors(web_url: str, api_url: str, *, timeout: float) -> None:
    status, headers, _ = _request(
        f"{api_url}/api/v1/health",
        timeout=timeout,
        method="OPTIONS",
        headers={
            "Origin": web_url,
            "Access-Control-Request-Method": "GET",
        },
    )
    allowed_origin = headers.get("Access-Control-Allow-Origin")
    if status != 200 or allowed_origin != web_url:
        raise RuntimeError(
            f"CORS não autorizou a origem do frontend. Recebido: {allowed_origin!r}."
        )
    print("[ok] CORS autoriza o frontend")


def _check_mapping_catalog(api_url: str, *, timeout: float) -> None:
    status, _, body = _request(
        f"{api_url}/api/v1/mappings?entity=customers&source_format=csv",
        timeout=timeout,
        headers={"Accept": "application/json"},
    )
    payload = json.loads(body)
    templates = payload.get("templates", [])
    if (
        status != 200
        or not isinstance(templates, list)
        or not any(
            template.get("template_id") == "erp_legacy_customers_csv"
            for template in templates
            if isinstance(template, dict)
        )
    ):
        raise RuntimeError("O catálogo não devolveu o template CSV esperado.")
    print("[ok] Catálogo de mapeamentos")


def _check_inspection(api_url: str, source: Path, *, timeout: float) -> None:
    body, content_type = _multipart_body(
        fields={"header_row": "1"},
        files=(("file", source, "text/csv"),),
    )
    status, _, response_body = _request(
        f"{api_url}/api/v1/inspect",
        timeout=timeout,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": content_type,
        },
        body=body,
    )
    payload = json.loads(response_body)
    if status != 200 or payload.get("source_format") != "csv":
        raise RuntimeError("A inspeção do CSV sintético falhou.")
    print("[ok] Upload e inspeção de CSV")


def _check_dry_run(
    api_url: str,
    source: Path,
    mapping: Path,
    *,
    timeout: float,
) -> None:
    body, content_type = _multipart_body(
        fields={"entity": "customers"},
        files=(
            ("file", source, "text/csv"),
            ("mapping", mapping, "application/yaml"),
        ),
    )
    status, _, response_body = _request(
        f"{api_url}/api/v1/migrations/dry-run",
        timeout=timeout,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": content_type,
        },
        body=body,
    )
    payload = json.loads(response_body)
    summary = payload.get("summary", {})
    if (
        status != 200
        or payload.get("dry_run") is not True
        or summary.get("total", 0) < 1
    ):
        raise RuntimeError("O dry-run do CSV sintético falhou.")
    _check_artifacts(api_url, payload, timeout=timeout)
    print(
        "[ok] Pipeline dry-run "
        f"({summary.get('valid', 0)} válidos, "
        f"{summary.get('rejected', 0)} rejeitados)"
    )


def _check_artifacts(
    api_url: str,
    payload: Mapping[str, object],
    *,
    timeout: float,
) -> None:
    artifacts = payload.get("artifacts")
    ttl = payload.get("artifacts_expires_in_seconds")
    if not isinstance(artifacts, list) or not isinstance(ttl, int) or ttl <= 0:
        raise RuntimeError("A API não informou os artefatos temporários e seu TTL.")

    links = {
        artifact.get("name"): artifact.get("download_url")
        for artifact in artifacts
        if isinstance(artifact, dict)
    }
    if set(links) != EXPECTED_ARTIFACTS:
        raise RuntimeError(
            "O dry-run não publicou exatamente os quatro artefatos esperados."
        )

    for name, download_url in links.items():
        if not isinstance(download_url, str):
            raise RuntimeError(f"O artefato {name} não possui uma URL válida.")
        status, headers, body = _request(
            urljoin(f"{api_url}/", download_url),
            timeout=timeout,
        )
        if (
            status != 200
            or not body
            or headers.get("X-Content-Type-Options") != "nosniff"
        ):
            raise RuntimeError(f"O download de {name} falhou.")
    print(f"[ok] Quatro artefatos temporários (TTL de {ttl} s)")


def _existing_file(path: str) -> Path:
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise argparse.ArgumentTypeError(f"Arquivo não encontrado: {resolved}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida frontend, API, CORS, upload e dry-run do Waypoint.",
    )
    parser.add_argument("--web-url", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument(
        "--source",
        type=_existing_file,
        default=DEFAULT_SOURCE,
        help=f"CSV sintético (padrão: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--mapping",
        type=_existing_file,
        default=DEFAULT_MAPPING,
        help=f"Template YAML (padrão: {DEFAULT_MAPPING})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120,
        help="Timeout por requisição; 120 s cobre o cold start do Render Free.",
    )
    args = parser.parse_args()

    try:
        web_url = _normalized_url(args.web_url)
        api_url = _normalized_url(args.api_url)
        _check_frontend(web_url, timeout=args.timeout)
        _check_health(api_url, timeout=args.timeout)
        _check_cors(web_url, api_url, timeout=args.timeout)
        _check_mapping_catalog(api_url, timeout=args.timeout)
        _check_inspection(api_url, args.source, timeout=args.timeout)
        _check_dry_run(
            api_url,
            args.source,
            args.mapping,
            timeout=args.timeout,
        )
    except (
        HTTPError,
        URLError,
        OSError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
    ) as error:
        print(f"[falha] {error}", file=sys.stderr)
        return 1

    print("[ok] Deploy funcional de ponta a ponta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
