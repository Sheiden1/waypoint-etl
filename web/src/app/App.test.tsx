import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  PreferencesProvider,
  PreferencesTheme,
} from "../features/preferences";
import {
  type DryRunResult,
  getHealth,
  inspectSource,
  runDryRun,
} from "../lib/api";
import { App } from "./App";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return {
    ...actual,
    getHealth: vi.fn(),
    inspectSource: vi.fn(),
    runDryRun: vi.fn(),
  };
});

const getHealthMock = vi.mocked(getHealth);
const inspectSourceMock = vi.mocked(inspectSource);
const runDryRunMock = vi.mocked(runDryRun);

describe("App", () => {
  beforeEach(() => {
    localStorage.clear();
    getHealthMock.mockReset();
    inspectSourceMock.mockReset();
    runDryRunMock.mockReset();
    getHealthMock.mockResolvedValue({
      status: "ok",
      version: "0.2.0",
      max_upload_mb: 25,
      features: { ocr: false, database: false },
    });
  });

  it("avança da inspeção concluída para o mapeamento", async () => {
    inspectSourceMock.mockResolvedValue({
      source_name: "clientes.csv",
      source_format: "csv",
      is_tabular: true,
      columns: ["Nome Cliente", "CPF_CNPJ"],
      rows: [{ "Nome Cliente": "Ada", CPF_CNPJ: "123" }],
      available_sheets: [],
      ocr_used: false,
      warnings: [],
    });
    runDryRunMock.mockResolvedValue(dryRunResult);
    render(
      <PreferencesProvider>
        <PreferencesTheme>
          <App />
        </PreferencesTheme>
      </PreferencesProvider>,
    );

    const dropzone = screen.getByRole("button", { name: "Arquivo de origem" });
    const input = dropzone.querySelector<HTMLInputElement>('input[type="file"]');
    expect(input).not.toBeNull();
    fireEvent.change(input as HTMLInputElement, {
      target: {
        files: [
          new File(["Nome Cliente,CPF_CNPJ\nAda,123"], "clientes.csv", {
            type: "text/csv",
          }),
        ],
      },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Inspecionar arquivo" }),
    );

    await waitFor(() => {
      expect(inspectSourceMock).toHaveBeenCalledOnce();
    });
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Continuar para mapeamento",
      }),
    );

    expect(
      screen.getByRole("heading", { name: "Associe a origem ao destino" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Mapeamento mínimo completo")).toBeInTheDocument();
    expect(screen.getByText("Mapeamento").closest("li")).toHaveAttribute(
      "aria-current",
      "step",
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Continuar para validação" }),
    );
    expect(
      screen.getByRole("heading", { name: "Execute o pipeline em segurança" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Validação").closest("li")).toHaveAttribute(
      "aria-current",
      "step",
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Executar validação" }),
    );
    expect(await screen.findByText("DRY-RUN CONCLUÍDO")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Continuar para destino" }),
    );

    expect(
      screen.getByRole("heading", {
        name: "Escolha como usar o lote validado",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Baixar audit-report.json" }),
    ).toHaveAttribute("href", expect.stringContaining("audit-report.json"));
    expect(screen.getByText("Destino").closest("li")).toHaveAttribute(
      "aria-current",
      "step",
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Continuar para resultado" }),
    );
    expect(
      screen.getByRole("heading", { name: "Jornada concluída" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Resultado").closest("li")).toHaveAttribute(
      "aria-current",
      "step",
    );

    fireEvent.click(screen.getByRole("button", { name: "Nova jornada" }));
    expect(
      screen.getByRole("heading", { name: "Escolha um arquivo" }),
    ).toBeInTheDocument();
  });
});

const dryRunResult: DryRunResult = {
  run_id: "11111111-1111-4111-8111-111111111111",
  status: "completed",
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
  accepted_rows: [{ full_name: "Ada" }],
  issues: [],
  duplicates: [],
  stages: [],
  transforms_applied: {},
  warnings: [],
  artifacts: [
    {
      name: "accepted.csv",
      media_type: "text/csv",
      download_url:
        "/api/v1/migrations/11111111-1111-4111-8111-111111111111/artifacts/accepted.csv",
    },
    {
      name: "rejected.xlsx",
      media_type:
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      download_url:
        "/api/v1/migrations/11111111-1111-4111-8111-111111111111/artifacts/rejected.xlsx",
    },
    {
      name: "duplicates.csv",
      media_type: "text/csv",
      download_url:
        "/api/v1/migrations/11111111-1111-4111-8111-111111111111/artifacts/duplicates.csv",
    },
    {
      name: "audit-report.json",
      media_type: "application/json",
      download_url:
        "/api/v1/migrations/11111111-1111-4111-8111-111111111111/artifacts/audit-report.json",
    },
  ],
  artifacts_expires_in_seconds: 1800,
};
