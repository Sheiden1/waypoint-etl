import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiRequestError,
  getHealth,
  getMappings,
  inspectSource,
  loadPostgres,
  previewMapping,
  resolveApiUrl,
  runDryRun,
} from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Waypoint API client", () => {
  it("reads the health contract", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          status: "ok",
          version: "0.1.0",
          max_upload_mb: 25,
          features: { ocr: false, database: false },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(getHealth()).resolves.toMatchObject({
      status: "ok",
      max_upload_mb: 25,
    });
  });

  it("sends uploads as multipart data", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          source_name: "clientes.csv",
          source_format: "csv",
          is_tabular: true,
          columns: ["Nome"],
          rows: [{ Nome: "Ada" }],
          available_sheets: [],
          ocr_used: false,
          warnings: [],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["Nome\nAda"], "clientes.csv", { type: "text/csv" });

    await inspectSource(file);

    const request = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(request[0]).toContain("/api/v1/inspect");
    expect(request[1].method).toBe("POST");
    expect(request[1].body).toBeInstanceOf(FormData);
  });

  it("turns the controlled error envelope into an Error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: {
              code: "inspection_failed",
              message: "Formato não suportado.",
            },
          }),
          { status: 422, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    const promise = inspectSource(
      new File(["x"], "arquivo.exe", { type: "application/octet-stream" }),
    );

    await expect(promise).rejects.toEqual(
      new ApiRequestError("Formato não suportado.", 422, "inspection_failed"),
    );
  });

  it("sends the source and generated mapping to dry-run", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          run_id: "run-123",
          status: "dry_run",
          entity: "customers",
          source_name: "clientes.csv",
          mapping_name: "Mapeamento web",
          mapping_version: 1,
          dry_run: true,
          summary: {
            total: 1,
            valid: 1,
            rejected: 0,
            duplicates: 0,
            possible_duplicates: 0,
            duration_ms: 12,
          },
          accepted_rows: [],
          issues: [],
          duplicates: [],
          stages: [],
          transforms_applied: {},
          warnings: [],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await runDryRun(
      new File(["Nome\nAda"], "clientes.csv", { type: "text/csv" }),
      "version: 1\n",
      "customers",
    );

    const request = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(request[0]).toContain("/api/v1/migrations/dry-run");
    expect(request[1].method).toBe("POST");
    const body = request[1].body as FormData;
    expect(body.get("file")).toBeInstanceOf(File);
    expect(body.get("mapping")).toBeInstanceOf(File);
    expect(body.get("entity")).toBe("customers");
  });

  it("filters the versioned mapping catalog", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ templates: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getMappings("customers", "csv");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/v1/mappings?entity=customers&source_format=csv",
      ),
    );
  });

  it("uploads YAML for server-side validation", async () => {
    const response = {
      template_id: "uploaded",
      filename: "mapping.yaml",
      name: "Meu template",
      version: 1,
      entity: "customers",
      source_format: "csv",
      header_row: 1,
      fields: [],
      ignored_fields: [],
      assignments: {},
      content: "version: 1",
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(response), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await previewMapping(
      new File(["version: 1"], "mapping.yaml", {
        type: "application/yaml",
      }),
      "customers",
      "csv",
    );

    const request = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(request[0]).toContain("/api/v1/mappings/preview");
    const body = request[1].body as FormData;
    expect(body.get("mapping")).toBeInstanceOf(File);
    expect(body.get("entity")).toBe("customers");
  });

  it("requires an explicit confirmed PostgreSQL load", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          run_id: "run-load-123",
          status: "completed",
          entity: "customers",
          source_name: "clientes.csv",
          mapping_name: "Mapeamento web",
          mapping_version: 1,
          dry_run: false,
          summary: {
            total: 1,
            valid: 1,
            rejected: 0,
            duplicates: 0,
            possible_duplicates: 0,
            duration_ms: 12,
          },
          accepted_rows: [],
          issues: [],
          duplicates: [],
          stages: [],
          transforms_applied: {},
          warnings: [],
          artifacts: [],
          artifacts_expires_in_seconds: 1800,
          loaded_records: 1,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await loadPostgres(
      new File(["Nome\nAda"], "clientes.csv", { type: "text/csv" }),
      "version: 1\n",
      "customers",
    );

    const request = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(request[0]).toContain("/api/v1/migrations/load-postgres");
    expect(request[1].method).toBe("POST");
    const body = request[1].body as FormData;
    expect(body.get("file")).toBeInstanceOf(File);
    expect(body.get("mapping")).toBeInstanceOf(File);
    expect(body.get("entity")).toBe("customers");
    expect(body.get("confirm")).toBe("true");
  });

  it("resolves artifact links against the configured API", () => {
    expect(
      resolveApiUrl(
        "/api/v1/migrations/run-123/artifacts/audit-report.json",
      ),
    ).toMatch(/\/api\/v1\/migrations\/run-123\/artifacts\/audit-report\.json$/);
    expect(resolveApiUrl("https://example.test/report.json")).toBe(
      "https://example.test/report.json",
    );
  });
});
