import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Theme } from "@astryxdesign/core/theme";

import { ApiRequestError, inspectSource } from "../../lib/api";
import "../../styles/global.css";
import { waypointTheme } from "../../theme/waypointTheme";
import { InspectionWorkspace } from "./InspectionWorkspace";

vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>(
    "../../lib/api",
  );
  return {
    ...actual,
    inspectSource: vi.fn(),
  };
});

const inspectSourceMock = vi.mocked(inspectSource);

describe("InspectionWorkspace", () => {
  beforeEach(() => {
    inspectSourceMock.mockReset();
  });

  it("mantém a ação indisponível enquanto não há arquivo", () => {
    renderWorkspace();

    const dropzone = screen.getByRole("button", { name: "Arquivo de origem" });
    const boundary = dropzone.closest(".file-input-boundary");
    const field = dropzone.closest(".astryx-field");

    expect(boundary).not.toBeNull();
    expect(field).not.toBeNull();
    expect(getComputedStyle(boundary as Element).maxWidth).toBe("100%");
    expect(
      (field as HTMLElement).style.getPropertyValue("--x-width"),
    ).toBe("100%");
    expect(
      screen.getByRole("button", { name: "Inspecionar arquivo" }),
    ).toBeDisabled();
    expect(
      screen.getByText("Nada é armazenado após a operação."),
    ).toBeInTheDocument();
  });

  it("envia o arquivo e apresenta a prévia tabular", async () => {
    const onContinue = vi.fn();
    inspectSourceMock.mockResolvedValue({
      source_name: "clientes.csv",
      source_format: "csv",
      is_tabular: true,
      columns: ["name", "document"],
      rows: [{ name: "Ada", document: "123" }],
      available_sheets: [],
      ocr_used: false,
      warnings: [],
    });
    renderWorkspace(onContinue);

    const file = new File(["name,document\nAda,123"], "clientes.csv", {
      type: "text/csv",
    });
    fireEvent.change(getFileInput(), {
      target: { files: [file] },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Inspecionar arquivo" }),
    );

    await waitFor(() => {
      expect(inspectSourceMock).toHaveBeenCalledWith(file);
    });
    expect(await screen.findByText("PRÉVIA REAL")).toBeInTheDocument();
    expect(screen.getByText("Ada")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Continuar para mapeamento" }),
    );
    expect(onContinue).toHaveBeenCalledWith(
      file,
      expect.objectContaining({ source_name: "clientes.csv" }),
    );
  });

  it("apresenta a mensagem controlada retornada pela API", async () => {
    inspectSourceMock.mockRejectedValue(
      new ApiRequestError("Formato não suportado.", 422, "inspection_failed"),
    );
    renderWorkspace();

    fireEvent.change(getFileInput(), {
      target: {
        files: [new File(["data"], "clientes.csv", { type: "text/csv" })],
      },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Inspecionar arquivo" }),
    );

    expect(
      await screen.findByText("Formato não suportado."),
    ).toBeInTheDocument();
  });
});

function renderWorkspace(onContinue = vi.fn()) {
  return render(
    <Theme theme={waypointTheme} mode="light">
      <InspectionWorkspace
        maxUploadMb={25}
        ocrAvailable={false}
        apiAvailable
        onContinue={onContinue}
      />
    </Theme>,
  );
}

function getFileInput(): HTMLInputElement {
  const dropzone = screen.getByRole("button", { name: "Arquivo de origem" });
  const input = dropzone.querySelector<HTMLInputElement>('input[type="file"]');
  if (input === null) {
    throw new Error("O FileInput do Astryx não renderizou o input nativo.");
  }
  return input;
}
