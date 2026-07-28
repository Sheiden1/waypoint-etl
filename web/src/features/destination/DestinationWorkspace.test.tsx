import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Theme } from "@astryxdesign/core/theme";

import {
  ApiRequestError,
  loadPostgres,
  type DryRunResult,
} from "../../lib/api";
import { waypointTheme } from "../../theme/waypointTheme";
import type { MappingDraft } from "../mapping/MappingWorkspace";
import { DestinationWorkspace } from "./DestinationWorkspace";

vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>(
    "../../lib/api",
  );
  return {
    ...actual,
    loadPostgres: vi.fn(),
  };
});

const loadPostgresMock = vi.mocked(loadPostgres);

describe("DestinationWorkspace", () => {
  beforeEach(() => {
    loadPostgresMock.mockReset();
  });

  it("oferece os quatro downloads reais e mantém o PostgreSQL opcional", () => {
    const onBack = vi.fn();
    const onContinue = vi.fn();
    renderWorkspace({ databaseAvailable: false, onBack, onContinue });

    const downloadLinks = screen.getAllByRole("link", { name: /^Baixar / });
    expect(downloadLinks).toHaveLength(4);
    expect(downloadLinks[0]).toHaveAttribute(
      "href",
      "/api/v1/migrations/run-dry/artifacts/accepted.csv",
    );
    expect(
      screen.getByText(
        "Os downloads ficam disponíveis por 30 minutos após a execução.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL indisponível")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Importar para PostgreSQL" }),
    ).toHaveAttribute("aria-disabled", "true");

    fireEvent.click(
      screen.getByRole("button", { name: "Continuar para resultado" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Voltar à validação" }),
    );
    expect(onContinue).toHaveBeenCalledOnce();
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("só grava no PostgreSQL após confirmação explícita", async () => {
    const onLoadResult = vi.fn();
    loadPostgresMock.mockResolvedValue(loadResult);
    renderWorkspace({ onLoadResult });

    const loadButton = screen.getByRole("button", {
      name: "Importar para PostgreSQL",
    });
    expect(loadButton).toHaveAttribute("aria-disabled", "true");

    fireEvent.click(
      screen.getByRole("checkbox", {
        name: /Confirmo a gravação de 2 registros válidos no PostgreSQL/,
      }),
    );
    expect(loadButton).not.toHaveAttribute("aria-disabled");
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(loadPostgresMock).toHaveBeenCalledWith(
        sourceFile,
        mapping.content,
        mapping.entity,
        mapping.filename,
      );
    });
    expect(onLoadResult).toHaveBeenCalledWith(loadResult);
    expect(await screen.findByText("Importação concluída")).toBeInTheDocument();
    expect(
      screen.getByText(/2 registros gravados no PostgreSQL/),
    ).toBeInTheDocument();
  });

  it("apresenta o erro controlado e permite tentar novamente", async () => {
    loadPostgresMock.mockRejectedValue(
      new ApiRequestError(
        "A conexão com o banco falhou.",
        503,
        "database_unavailable",
      ),
    );
    renderWorkspace();

    fireEvent.click(
      screen.getByRole("checkbox", {
        name: /Confirmo a gravação de 2 registros válidos no PostgreSQL/,
      }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Importar para PostgreSQL" }),
    );

    expect(
      await screen.findByText("A conexão com o banco falhou."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Importar para PostgreSQL" }),
    ).toBeEnabled();
  });

  it("explica quando os artefatos não estão mais disponíveis", () => {
    renderWorkspace({
      validationResult: {
        ...dryRunResult,
        artifacts: [],
        artifacts_expires_in_seconds: undefined,
      },
    });

    expect(screen.getByText("Downloads não disponíveis")).toBeInTheDocument();
    expect(screen.queryAllByRole("link", { name: /^Baixar / })).toHaveLength(0);
  });
});

const sourceFile = new File(["dados"], "clientes.csv", { type: "text/csv" });

const mapping: MappingDraft = {
  entity: "customers",
  assignments: { Nome: "full_name" },
  filename: "clientes-mapping.yaml",
  content: "version: 1\nentity: customers\n",
};

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
  validationResult = dryRunResult,
  databaseAvailable = true,
  apiAvailable = true,
  initialLoadResult = null,
  onBack = vi.fn(),
  onContinue = vi.fn(),
  onLoadResult = vi.fn(),
}: {
  validationResult?: DryRunResult;
  databaseAvailable?: boolean;
  apiAvailable?: boolean;
  initialLoadResult?: DryRunResult | null;
  onBack?: () => void;
  onContinue?: () => void;
  onLoadResult?: (result: DryRunResult) => void;
} = {}) {
  return render(
    <Theme theme={waypointTheme} mode="light">
      <DestinationWorkspace
        file={sourceFile}
        mapping={mapping}
        validationResult={validationResult}
        apiAvailable={apiAvailable}
        databaseAvailable={databaseAvailable}
        initialLoadResult={initialLoadResult}
        onBack={onBack}
        onContinue={onContinue}
        onLoadResult={onLoadResult}
      />
    </Theme>,
  );
}
