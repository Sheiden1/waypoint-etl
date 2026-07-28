import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Theme } from "@astryxdesign/core/theme";

import {
  ApiRequestError,
  runDryRun,
  type DryRunResult,
} from "../../lib/api";
import "../../styles/global.css";
import { waypointTheme } from "../../theme/waypointTheme";
import type { MappingDraft } from "../mapping/MappingWorkspace";
import { ValidationWorkspace } from "./ValidationWorkspace";

vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>(
    "../../lib/api",
  );
  return {
    ...actual,
    runDryRun: vi.fn(),
  };
});

const runDryRunMock = vi.mocked(runDryRun);

describe("ValidationWorkspace", () => {
  beforeEach(() => {
    runDryRunMock.mockReset();
  });

  it("executa o dry-run e apresenta qualidade, issues e run_id", async () => {
    const onResult = vi.fn();
    runDryRunMock.mockResolvedValue(result);
    renderWorkspace({ onResult });

    fireEvent.click(
      screen.getByRole("button", { name: "Executar validação" }),
    );

    await waitFor(() => {
      expect(runDryRunMock).toHaveBeenCalledWith(
        sourceFile,
        mapping.content,
        "customers",
        mapping.filename,
      );
    });
    expect(await screen.findByText("DRY-RUN CONCLUÍDO")).toBeInTheDocument();
    expect(screen.getByText("run-123")).toBeInTheDocument();
    expect(screen.getByText("Documento inválido.")).toBeInTheDocument();
    expect(screen.getByText("Revisão necessária")).toBeInTheDocument();
    expect(onResult).toHaveBeenCalledWith(result);

    fireEvent.click(
      screen.getByRole("combobox", { name: "Filtrar problemas" }),
    );
    fireEvent.click(screen.getByRole("option", { name: "Somente avisos" }));
    expect(screen.queryByText("Documento inválido.")).not.toBeInTheDocument();
    expect(screen.getByText("Nenhum resultado")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Pipeline" }));
    expect(screen.getByText("Duração por etapa")).toBeInTheDocument();
    expect(screen.getByText("Limpeza de texto")).toBeInTheDocument();
  });

  it("mantém erro controlado e permite nova tentativa", async () => {
    runDryRunMock.mockRejectedValue(
      new ApiRequestError(
        "O template está inválido.",
        422,
        "dry_run_failed",
      ),
    );
    renderWorkspace();

    fireEvent.click(
      screen.getByRole("button", { name: "Executar validação" }),
    );

    expect(
      await screen.findByText("O template está inválido."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Executar validação" }),
    ).toBeEnabled();
  });

  it("restaura um resultado e volta ao mapeamento", () => {
    const onBack = vi.fn();
    const onContinue = vi.fn();
    renderWorkspace({ initialResult: result, onBack, onContinue });

    expect(screen.getByText("DRY-RUN CONCLUÍDO")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Continuar para destino" }),
    );
    expect(onContinue).toHaveBeenCalledOnce();
    fireEvent.click(
      screen.getByRole("button", { name: "Voltar ao mapeamento" }),
    );
    expect(onBack).toHaveBeenCalledOnce();
  });
});

const sourceFile = new File(["dados"], "clientes.csv", { type: "text/csv" });

const mapping: MappingDraft = {
  entity: "customers",
  assignments: {
    "Nome Cliente": "full_name",
    CPF_CNPJ: "document",
  },
  filename: "clientes-mapping.yaml",
  content: "version: 1\nentity: customers\n",
};

const result: DryRunResult = {
  run_id: "run-123",
  status: "dry_run",
  entity: "customers",
  source_name: "clientes.csv",
  mapping_name: "Mapeamento web",
  mapping_version: 1,
  dry_run: true,
  summary: {
    total: 2,
    valid: 1,
    rejected: 1,
    duplicates: 0,
    possible_duplicates: 0,
    duration_ms: 18,
  },
  accepted_rows: [
    {
      full_name: "Ada Lovelace",
      document: "***.***.***-12",
    },
  ],
  issues: [
    {
      row_number: 3,
      field: "document",
      code: "invalid_document",
      severity: "error",
      message: "Documento inválido.",
      original_value: "***",
    },
  ],
  duplicates: [],
  stages: [
    { name: "extract", duration_ms: 5 },
    { name: "validate", duration_ms: 2 },
  ],
  transforms_applied: { clean_text: 1, digits_only: 2 },
  warnings: [],
};

function renderWorkspace({
  initialResult = null,
  onBack = vi.fn(),
  onContinue = vi.fn(),
  onResult = vi.fn(),
}: {
  initialResult?: DryRunResult | null;
  onBack?: () => void;
  onContinue?: () => void;
  onResult?: (result: DryRunResult) => void;
} = {}) {
  return render(
    <Theme theme={waypointTheme} mode="light">
      <ValidationWorkspace
        file={sourceFile}
        mapping={mapping}
        apiAvailable
        initialResult={initialResult}
        onBack={onBack}
        onContinue={onContinue}
        onResult={onResult}
      />
    </Theme>,
  );
}
