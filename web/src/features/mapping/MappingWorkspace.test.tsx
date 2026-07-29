import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { Theme } from "@astryxdesign/core/theme";

import {
  getMappings,
  previewMapping,
  type MappingTemplate,
  type SourcePreview,
} from "../../lib/api";
import "../../styles/global.css";
import { waypointTheme } from "../../theme/waypointTheme";
import {
  MappingWorkspace,
  type MappingDraft,
} from "./MappingWorkspace";

vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>(
    "../../lib/api",
  );
  return {
    ...actual,
    getMappings: vi.fn(),
    previewMapping: vi.fn(),
  };
});

const getMappingsMock = vi.mocked(getMappings);
const previewMappingMock = vi.mocked(previewMapping);

describe("MappingWorkspace", () => {
  beforeEach(() => {
    getMappingsMock.mockReset();
    previewMappingMock.mockReset();
  });

  it("sugere o De/Para e mantém a navegação de retorno disponível", () => {
    const onBack = vi.fn();
    const onContinue = vi.fn<(draft: MappingDraft) => void>();
    renderWorkspace(
      {
        ...preview,
        columns: ["Nome Cliente", "CPF_CNPJ", "Correio Eletrônico"],
        rows: [
          {
            "Nome Cliente": "Ada Lovelace",
            CPF_CNPJ: "123",
            "Correio Eletrônico": "ada@example.test",
          },
        ],
      },
      onBack,
      onContinue,
    );

    expect(
      screen.getByRole("heading", { name: "Associe a origem ao destino" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Mapeamento mínimo completo")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Baixar template YAML" }),
    ).toBeEnabled();
    expect(
      screen.getByRole("button", { name: "Continuar para validação" }),
    ).toBeEnabled();

    fireEvent.click(
      screen.getByRole("button", { name: "Continuar para validação" }),
    );
    expect(onContinue).toHaveBeenCalledOnce();
    const draft = onContinue.mock.calls[0]?.[0];
    expect(draft).toMatchObject({
      entity: "customers",
      filename: "clientes-mapping.yaml",
    });
    expect(draft?.content).toContain("target: full_name");

    fireEvent.click(screen.getByRole("button", { name: "Voltar para origem" }));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("impede o download enquanto faltam campos obrigatórios", () => {
    renderWorkspace({
      ...preview,
      columns: ["Coluna desconhecida"],
      rows: [{ "Coluna desconhecida": "valor" }],
    });

    expect(
      screen.getByText("Ainda faltam campos obrigatórios"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Baixar template YAML" }),
    ).toHaveAttribute("aria-disabled", "true");
  });

  it("carrega um template compatível do catálogo", async () => {
    const onContinue = vi.fn<(draft: MappingDraft) => void>();
    getMappingsMock.mockResolvedValue({ templates: [catalogTemplate] });
    renderWorkspace(preview, vi.fn(), onContinue);

    fireEvent.click(
      screen.getByRole("radio", { name: "Template pronto" }),
    );

    expect((await screen.findAllByText("ERP CSV")).length).toBeGreaterThan(0);
    fireEvent.click(
      screen.getByRole("button", { name: "Continuar para validação" }),
    );
    expect(onContinue.mock.calls[0]?.[0]).toMatchObject({
      filename: "erp.csv.yaml",
      content: "version: 1\n",
    });
  });

  it("valida um upload YAML antes de liberar a continuação", async () => {
    const onContinue = vi.fn<(draft: MappingDraft) => void>();
    previewMappingMock.mockResolvedValue({
      ...catalogTemplate,
      template_id: "uploaded",
      filename: "meu-template.yaml",
    });
    renderWorkspace(preview, vi.fn(), onContinue);

    fireEvent.click(screen.getByRole("radio", { name: "Enviar YAML" }));
    const dropzone = screen.getByRole("button", { name: "Template De/Para" });
    const input = dropzone.querySelector<HTMLInputElement>('input[type="file"]');
    expect(input).not.toBeNull();
    const yaml = new File(["version: 1"], "meu-template.yaml", {
      type: "application/yaml",
    });
    fireEvent.change(input as HTMLInputElement, {
      target: { files: [yaml] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Validar YAML" }));

    await waitFor(() => {
      expect(previewMappingMock).toHaveBeenCalledWith(
        yaml,
        "customers",
        "csv",
      );
    });
    expect(await screen.findByText("Compatível")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Continuar para validação" }),
    );
    expect(onContinue.mock.calls[0]?.[0].filename).toBe("meu-template.yaml");
  });

  it("tolera coluna opcional ausente e libera a continuação", async () => {
    const onContinue = vi.fn<(draft: MappingDraft) => void>();
    getMappingsMock.mockResolvedValue({
      templates: [
        {
          ...catalogTemplate,
          fields: [
            ...catalogTemplate.fields,
            {
              source: "Correio Eletrônico",
              target: "email",
              required: false,
              transforms: ["email"],
            },
          ],
        },
      ],
    });
    renderWorkspace(preview, vi.fn(), onContinue);

    fireEvent.click(screen.getByRole("radio", { name: "Template pronto" }));

    expect(await screen.findByText("Campos vazios")).toBeInTheDocument();
    expect(
      screen.getByText(/Ficarão vazias: Correio Eletrônico/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Continuar para validação" }),
    ).toBeEnabled();
  });

  it("bloqueia quando falta coluna obrigatória do template", async () => {
    getMappingsMock.mockResolvedValue({
      templates: [
        {
          ...catalogTemplate,
          fields: [
            {
              source: "RAZAO_SOCIAL",
              target: "full_name",
              required: true,
              transforms: [],
            },
            {
              source: "CNPJ",
              target: "document",
              required: true,
              transforms: [],
            },
          ],
        },
      ],
    });
    renderWorkspace(preview);

    fireEvent.click(screen.getByRole("radio", { name: "Template pronto" }));

    expect(await screen.findByText("Incompatível")).toBeInTheDocument();
    expect(
      screen.getByText(/Faltam colunas obrigatórias: RAZAO_SOCIAL, CNPJ/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Continuar para validação" }),
    ).toHaveAttribute("aria-disabled", "true");
  });
});

const preview: SourcePreview = {
  source_name: "clientes.csv",
  source_format: "csv",
  is_tabular: true,
  columns: ["Nome Cliente", "CPF_CNPJ"],
  rows: [{ "Nome Cliente": "Ada", CPF_CNPJ: "123" }],
  available_sheets: [],
  ocr_used: false,
  warnings: [],
};

const catalogTemplate: MappingTemplate = {
  template_id: "erp_csv",
  filename: "erp.csv.yaml",
  name: "ERP CSV",
  version: 1,
  entity: "customers",
  source_format: "csv",
  header_row: 1,
  fields: [
    {
      source: "Nome Cliente",
      target: "full_name",
      required: true,
      transforms: ["clean_text"],
    },
    {
      source: "CPF_CNPJ",
      target: "document",
      required: true,
      transforms: ["digits_only"],
    },
  ],
  ignored_fields: [],
  assignments: {
    "Nome Cliente": "full_name",
    CPF_CNPJ: "document",
  },
  content: "version: 1\n",
};

function renderWorkspace(
  sourcePreview: SourcePreview,
  onBack = vi.fn(),
  onContinue = vi.fn(),
) {
  return render(
    <Theme theme={waypointTheme} mode="light">
      <MappingWorkspace
        file={new File(["dados"], "clientes.csv", { type: "text/csv" })}
        preview={sourcePreview}
        apiAvailable
        onBack={onBack}
        onContinue={onContinue}
      />
    </Theme>,
  );
}
