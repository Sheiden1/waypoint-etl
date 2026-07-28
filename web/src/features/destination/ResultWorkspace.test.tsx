import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Theme } from "@astryxdesign/core/theme";

import type { DryRunResult } from "../../lib/api";
import { waypointTheme } from "../../theme/waypointTheme";
import { ResultWorkspace } from "./ResultWorkspace";

describe("ResultWorkspace", () => {
  it("resume o dry-run, preserva os downloads e encerra a jornada", () => {
    const onBack = vi.fn();
    const onRestart = vi.fn();
    renderWorkspace({ onBack, onRestart });

    expect(screen.getByText("Jornada concluída")).toBeInTheDocument();
    expect(screen.getByText("Dry-run concluído")).toBeInTheDocument();
    expect(
      screen.getByText("Processamento concluído sem alterar o banco"),
    ).toBeInTheDocument();
    expect(screen.getByText("run-dry")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /^Baixar / })).toHaveLength(4);

    fireEvent.click(
      screen.getByRole("button", { name: "Voltar ao destino" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Nova jornada" }));
    expect(onBack).toHaveBeenCalledOnce();
    expect(onRestart).toHaveBeenCalledOnce();
  });

  it("diferencia uma execução realmente gravada no PostgreSQL", () => {
    renderWorkspace({ loadResult });

    expect(screen.getByText("Importado")).toBeInTheDocument();
    expect(screen.getByText("Registros aprovados gravados")).toBeInTheDocument();
    expect(
      screen.getByText("2 registros gravados no PostgreSQL."),
    ).toBeInTheDocument();
    expect(screen.getByText("run-load")).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL + artefatos")).toBeInTheDocument();
  });
});

const artifacts: NonNullable<DryRunResult["artifacts"]> = [
  {
    name: "accepted.csv",
    media_type: "text/csv",
    download_url: "/api/v1/migrations/run-dry/artifacts/accepted.csv",
  },
  {
    name: "rejected.xlsx",
    media_type:
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    download_url: "/api/v1/migrations/run-dry/artifacts/rejected.xlsx",
  },
  {
    name: "duplicates.csv",
    media_type: "text/csv",
    download_url: "/api/v1/migrations/run-dry/artifacts/duplicates.csv",
  },
  {
    name: "audit-report.json",
    media_type: "application/json",
    download_url: "/api/v1/migrations/run-dry/artifacts/audit-report.json",
  },
];

const dryRunResult: DryRunResult = {
  run_id: "run-dry",
  status: "dry_run",
  entity: "customers",
  source_name: "clientes.csv",
  mapping_name: "Clientes",
  mapping_version: 1,
  dry_run: true,
  summary: {
    total: 3,
    valid: 2,
    rejected: 1,
    duplicates: 0,
    possible_duplicates: 0,
    duration_ms: 18,
  },
  accepted_rows: [],
  issues: [],
  duplicates: [],
  stages: [],
  transforms_applied: {},
  warnings: [],
  artifacts,
  artifacts_expires_in_seconds: 1800,
};

const loadResult: DryRunResult = {
  ...dryRunResult,
  run_id: "run-load",
  status: "completed",
  dry_run: false,
  loaded_records: 2,
  artifacts: artifacts.map((artifact) => ({
    ...artifact,
    download_url: artifact.download_url.replace("run-dry", "run-load"),
  })),
};

function renderWorkspace({
  loadResult = null,
  onBack = vi.fn(),
  onRestart = vi.fn(),
}: {
  loadResult?: DryRunResult | null;
  onBack?: () => void;
  onRestart?: () => void;
} = {}) {
  return render(
    <Theme theme={waypointTheme} mode="light">
      <ResultWorkspace
        validationResult={dryRunResult}
        loadResult={loadResult}
        onBack={onBack}
        onRestart={onRestart}
      />
    </Theme>,
  );
}
