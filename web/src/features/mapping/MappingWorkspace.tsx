import { useEffect, useMemo, useState } from "react";

import { Badge } from "@astryxdesign/core/Badge";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { FileInput } from "@astryxdesign/core/FileInput";
import { Heading } from "@astryxdesign/core/Heading";
import { Section } from "@astryxdesign/core/Section";
import {
  SegmentedControl,
  SegmentedControlItem,
} from "@astryxdesign/core/SegmentedControl";
import { Selector } from "@astryxdesign/core/Selector";
import { Text } from "@astryxdesign/core/Text";

import {
  ApiRequestError,
  getMappings,
  previewMapping,
  type MappingTemplate,
  type MigrationEntity,
  type SourcePreview,
} from "../../lib/api";

type Assignments = Record<string, string | null>;

interface CanonicalField {
  name: string;
  label: string;
  required: boolean;
}

interface EntityDefinition {
  label: string;
  fields: CanonicalField[];
}

export interface MappingDraft {
  entity: MigrationEntity;
  assignments: Assignments;
  filename: string;
  content: string;
}

interface MappingWorkspaceProps {
  file: File;
  preview: SourcePreview;
  apiAvailable: boolean;
  initialDraft?: MappingDraft | null;
  onBack: () => void;
  onContinue: (draft: MappingDraft) => void;
}

const IGNORE_VALUE = "__ignore__";
type MappingMode = "visual" | "catalog" | "upload";

const ENTITY_DEFINITIONS: Record<MigrationEntity, EntityDefinition> = {
  customers: {
    label: "Clientes",
    fields: [
      { name: "external_id", label: "ID externo", required: false },
      { name: "full_name", label: "Nome / razão social", required: true },
      { name: "document", label: "CPF / CNPJ", required: true },
      { name: "email", label: "E-mail", required: false },
      { name: "phone", label: "Telefone", required: false },
      { name: "postal_code", label: "CEP", required: false },
      { name: "city", label: "Cidade", required: false },
      { name: "state", label: "UF", required: false },
      { name: "created_at", label: "Data de cadastro", required: false },
    ],
  },
  contacts: {
    label: "Contatos",
    fields: [
      { name: "external_id", label: "ID externo", required: false },
      {
        name: "customer_document",
        label: "CPF / CNPJ do cliente",
        required: true,
      },
      { name: "name", label: "Nome do contato", required: true },
      { name: "role", label: "Cargo / função", required: false },
      { name: "email", label: "E-mail", required: false },
      { name: "phone", label: "Telefone", required: false },
    ],
  },
  invoices: {
    label: "Cobranças",
    fields: [
      { name: "external_id", label: "ID externo", required: true },
      {
        name: "customer_document",
        label: "CPF / CNPJ do cliente",
        required: true,
      },
      { name: "description", label: "Descrição", required: false },
      { name: "issued_at", label: "Data de emissão", required: true },
      { name: "due_at", label: "Data de vencimento", required: true },
      { name: "amount", label: "Valor", required: true },
      { name: "status", label: "Status", required: true },
    ],
  },
};

const TARGET_ALIASES: Record<string, string[]> = {
  external_id: ["codigo", "cod", "id", "idexterno", "externalid"],
  full_name: [
    "nome",
    "nomecliente",
    "razaosocial",
    "nomecompleto",
    "fullname",
  ],
  name: ["nome", "nomecontato", "contato"],
  document: ["cpf", "cnpj", "cpfcnpj", "documento", "document"],
  customer_document: [
    "cpf",
    "cnpj",
    "cpfcnpj",
    "documentocliente",
    "customerdocument",
  ],
  email: ["email", "correioeletronico", "mail"],
  phone: ["telefone", "fone", "celular", "phone"],
  postal_code: ["cep", "codigopostal", "postalcode"],
  city: ["cidade", "municipio", "city"],
  state: ["uf", "estado", "state"],
  created_at: ["datacadastro", "criadoem", "createdat"],
  role: ["cargo", "funcao", "role"],
  description: ["descricao", "historico", "description"],
  issued_at: ["dataemissao", "emissao", "issuedat"],
  due_at: ["datavencimento", "vencimento", "dueat"],
  amount: ["valor", "valortotal", "total", "amount"],
  status: ["status", "situacao"],
};

const SUGGESTED_TRANSFORMS: Record<string, string[]> = {
  external_id: ["clean_text"],
  full_name: ["clean_text", "title_case"],
  name: ["clean_text", "title_case"],
  role: ["clean_text", "title_case"],
  document: ["digits_only"],
  customer_document: ["digits_only"],
  email: ["email"],
  phone: ["brazilian_phone"],
  postal_code: ["postal_code"],
  city: ["clean_text", "title_case"],
  state: ["uf"],
  created_at: ["clean_text", "brazilian_date"],
  description: ["clean_text"],
  issued_at: ["clean_text", "brazilian_date"],
  due_at: ["clean_text", "brazilian_date"],
  amount: ["clean_text", "brazilian_money"],
  status: ["clean_text", "lowercase"],
};

export function MappingWorkspace({
  file,
  preview,
  apiAvailable,
  initialDraft = null,
  onBack,
  onContinue,
}: MappingWorkspaceProps) {
  const [entity, setEntity] = useState<MigrationEntity>(
    initialDraft?.entity ?? "customers",
  );
  const [assignments, setAssignments] = useState<Assignments>(() =>
    initialDraft?.assignments
      ? { ...initialDraft.assignments }
      : suggestAssignments(preview.columns, "customers"),
  );
  const [mode, setMode] = useState<MappingMode>("visual");
  const [catalog, setCatalog] = useState<MappingTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>();
  const [mappingUpload, setMappingUpload] = useState<File | null>(null);
  const [uploadedTemplate, setUploadedTemplate] =
    useState<MappingTemplate | null>(null);
  const [mappingError, setMappingError] = useState<string | null>(null);
  const [isLoadingMapping, setIsLoadingMapping] = useState(false);
  const definition = ENTITY_DEFINITIONS[entity];
  const mappedTargets = new Set(Object.values(assignments).filter(Boolean));
  const missingRequired = definition.fields.filter(
    (field) => field.required && !mappedTargets.has(field.name),
  );
  const selectedTemplate =
    catalog.find((template) => template.template_id === selectedTemplateId) ??
    null;
  const externalTemplate =
    mode === "catalog"
      ? selectedTemplate
      : mode === "upload"
        ? uploadedTemplate
        : null;
  // Espelha a regra do backend: falta coluna obrigatória impede a migração,
  // falta coluna opcional apenas deixa o campo canônico sem origem.
  const canonicalRequired = new Set(
    definition.fields.filter((field) => field.required).map((field) => field.name),
  );
  const externalAbsentFields =
    externalTemplate?.fields.filter(
      (field) => !preview.columns.includes(field.source),
    ) ?? [];
  const externalBlockingColumns = externalAbsentFields
    .filter((field) => field.required || canonicalRequired.has(field.target))
    .map((field) => field.source);
  const externalTolerableColumns = externalAbsentFields
    .filter(
      (field) => !(field.required || canonicalRequired.has(field.target)),
    )
    .map((field) => field.source);
  const canContinue =
    mode === "visual"
      ? missingRequired.length === 0
      : externalTemplate !== null && externalBlockingColumns.length === 0;

  const entityOptions = useMemo(
    () =>
      Object.entries(ENTITY_DEFINITIONS).map(([value, item]) => ({
        value,
        label: item.label,
      })),
    [],
  );

  useEffect(() => {
    if (mode !== "catalog" || !apiAvailable) {
      return;
    }
    let isCurrent = true;
    getMappings(entity, preview.source_format)
      .then((response) => {
        if (!isCurrent) {
          return;
        }
        setCatalog(response.templates);
        setSelectedTemplateId(response.templates[0]?.template_id);
      })
      .catch((caught: unknown) => {
        if (!isCurrent) {
          return;
        }
        setCatalog([]);
        setSelectedTemplateId(undefined);
        setMappingError(
          caught instanceof ApiRequestError
            ? caught.message
            : "Não foi possível carregar o catálogo de templates.",
        );
      })
      .finally(() => {
        if (isCurrent) {
          setIsLoadingMapping(false);
        }
      });
    return () => {
      isCurrent = false;
    };
  }, [apiAvailable, entity, mode, preview.source_format]);

  const changeEntity = (value: string) => {
    const nextEntity = value as MigrationEntity;
    setEntity(nextEntity);
    setAssignments(suggestAssignments(preview.columns, nextEntity));
    setUploadedTemplate(null);
    setMappingError(null);
    if (mode === "catalog") {
      setIsLoadingMapping(true);
    }
  };

  const changeMode = (value: string) => {
    const nextMode = value as MappingMode;
    setMode(nextMode);
    setMappingError(null);
    if (nextMode === "catalog") {
      setIsLoadingMapping(true);
    }
  };

  const changeMappingUpload = (next: File | File[] | null) => {
    setMappingUpload(next instanceof File ? next : null);
    setUploadedTemplate(null);
    setMappingError(null);
  };

  const validateUploadedMapping = async () => {
    if (mappingUpload === null) {
      setMappingError("Escolha um arquivo YAML antes de validar.");
      return;
    }
    setIsLoadingMapping(true);
    setMappingError(null);
    try {
      setUploadedTemplate(
        await previewMapping(mappingUpload, entity, preview.source_format),
      );
    } catch (caught) {
      setUploadedTemplate(null);
      setMappingError(
        caught instanceof ApiRequestError
          ? caught.message
          : "O template não pôde ser validado. Revise o YAML e tente novamente.",
      );
    } finally {
      setIsLoadingMapping(false);
    }
  };

  const assignTarget = (source: string, selected: string) => {
    const target = selected === IGNORE_VALUE ? null : selected;
    setAssignments((current) => {
      const next = { ...current };
      if (target !== null) {
        for (const [otherSource, otherTarget] of Object.entries(next)) {
          if (otherSource !== source && otherTarget === target) {
            next[otherSource] = null;
          }
        }
      }
      next[source] = target;
      return next;
    });
  };

  const downloadTemplate = () => {
    const draft = currentDraft();
    if (draft === null) {
      return;
    }
    const content = draft.content;
    const blob = new Blob([content], { type: "application/yaml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = draft.filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  const continueToValidation = () => {
    const draft = currentDraft();
    if (draft !== null) {
      onContinue(draft);
    }
  };

  const currentDraft = (): MappingDraft | null => {
    if (mode === "visual") {
      return createMappingDraft(file, preview, entity, assignments);
    }
    if (externalTemplate === null) {
      return null;
    }
    return draftFromTemplate(externalTemplate);
  };

  return (
    <div className="mapping-workspace">
      <Section className="mapping-section" width="100%" padding={6}>
        <div className="section-heading">
          <div>
            <Text as="p" type="label" color="accent">
              02 · MAPEAMENTO
            </Text>
            <Heading level={2}>Associe a origem ao destino</Heading>
          </div>
          <Badge
            variant="blue"
            label={`${preview.columns.length} colunas detectadas`}
          />
        </div>

        <div className="mapping-source-summary">
          <div>
            <Text as="p" type="label">
              {preview.source_name}
            </Text>
            <Text as="p" type="supporting">
              {preview.source_format.toUpperCase()} · arquivo mantido somente no
              navegador
            </Text>
          </div>
          <Badge variant="success" label="Inspecionado" />
        </div>

        <div className="entity-selector">
          <Selector
            label="Tipo de dado"
            description="Escolha o schema canônico que receberá as colunas."
            options={entityOptions}
            value={entity}
            onChange={changeEntity}
            width="100%"
          />
        </div>

        <div className="mapping-mode">
          <Text as="p" type="label">
            Como deseja definir o De/Para?
          </Text>
          <SegmentedControl
            value={mode}
            onChange={changeMode}
            label="Modo de mapeamento"
            layout="fill"
          >
            <SegmentedControlItem value="visual" label="Criar visualmente" />
            <SegmentedControlItem value="catalog" label="Template pronto" />
            <SegmentedControlItem value="upload" label="Enviar YAML" />
          </SegmentedControl>
        </div>

        {mappingError ? (
          <Banner
            status="error"
            title="Não foi possível usar o template"
            description={mappingError}
          />
        ) : null}

        {mode === "visual" ? (
          <>
            <div className="mapping-list-heading">
              <div>
                <Text as="p" type="label">
                  Coluna de origem
                </Text>
                <Text as="p" type="supporting">
                  Campo encontrado no arquivo
                </Text>
              </div>
              <div>
                <Text as="p" type="label">
                  Campo de destino
                </Text>
                <Text as="p" type="supporting">
                  Schema {definition.label.toLowerCase()}
                </Text>
              </div>
            </div>

            <div className="mapping-list">
              {preview.columns.map((source) => {
                const selectedTarget = assignments[source];
                const options = [
                  { value: IGNORE_VALUE, label: "Ignorar esta coluna" },
                  ...definition.fields.map((field) => ({
                    value: field.name,
                    label: `${field.label}${field.required ? " · obrigatório" : ""}`,
                    disabled:
                      mappedTargets.has(field.name) &&
                      selectedTarget !== field.name,
                  })),
                ];
                return (
                  <div className="mapping-row" key={source}>
                    <div className="mapping-source-column">
                      <Text as="p" type="label">
                        {source}
                      </Text>
                      <Text as="p" type="supporting">
                        {sampleValue(preview, source)}
                      </Text>
                    </div>
                    <span className="mapping-arrow" aria-hidden="true">
                      →
                    </span>
                    <Selector
                      label={`Destino para ${source}`}
                      isLabelHidden
                      options={options}
                      value={selectedTarget ?? IGNORE_VALUE}
                      onChange={(value) => assignTarget(source, value)}
                      width="100%"
                    />
                  </div>
                );
              })}
            </div>

            {missingRequired.length === 0 ? (
              <Banner
                status="success"
                title="Mapeamento mínimo completo"
                description="Os campos obrigatórios estão associados. Você já pode baixar um template válido para reutilizar no Waypoint."
              />
            ) : (
              <Banner
                status="warning"
                title="Ainda faltam campos obrigatórios"
                description={`Associe: ${missingRequired.map((field) => field.label).join(", ")}.`}
              />
            )}
          </>
        ) : null}

        {mode === "catalog" ? (
          <div className="mapping-external-panel">
            <div>
              <Text as="p" type="label">
                Catálogo versionado
              </Text>
              <Text as="p" type="supporting">
                Templates compatíveis com {definition.label.toLowerCase()} e{" "}
                {preview.source_format.toUpperCase()}.
              </Text>
            </div>
            <Selector
              label="Template pronto"
              options={catalog.map((template) => ({
                value: template.template_id,
                label: template.name,
              }))}
              value={selectedTemplateId}
              onChange={setSelectedTemplateId}
              placeholder={
                isLoadingMapping
                  ? "Carregando catálogo..."
                  : "Nenhum template compatível"
              }
              isLoading={isLoadingMapping}
              isDisabled={!apiAvailable || catalog.length === 0}
              disabledMessage={
                apiAvailable
                  ? "Não há template pronto compatível."
                  : "A API precisa estar disponível para consultar o catálogo."
              }
              width="100%"
            />
            {selectedTemplate ? (
              <TemplateSummary
                template={selectedTemplate}
                blockingColumns={externalBlockingColumns}
                tolerableColumns={externalTolerableColumns}
              />
            ) : (
              <Banner
                status="info"
                title="Nenhum template selecionado"
                description="Escolha outra entidade ou crie o mapeamento visualmente."
              />
            )}
          </div>
        ) : null}

        {mode === "upload" ? (
          <div className="mapping-external-panel">
            <div>
              <Text as="p" type="label">
                Template próprio
              </Text>
              <Text as="p" type="supporting">
                O YAML é validado pela API antes de entrar no pipeline.
              </Text>
            </div>
            <FileInput
              label="Template De/Para"
              description="Arquivo .yaml ou .yml · até 1 MB"
              value={mappingUpload}
              onChange={changeMappingUpload}
              accept=".yaml,.yml"
              maxSize={1024 * 1024}
              width="100%"
              placeholder="Escolha um template YAML"
              isLoading={isLoadingMapping}
            />
            <Button
              label="Validar YAML"
              variant="secondary"
              isLoading={isLoadingMapping}
              isDisabled={!apiAvailable || mappingUpload === null}
              tooltip={
                apiAvailable
                  ? undefined
                  : "A API precisa estar disponível para validar o YAML."
              }
              onClick={() => void validateUploadedMapping()}
            />
            {uploadedTemplate ? (
              <TemplateSummary
                template={uploadedTemplate}
                blockingColumns={externalBlockingColumns}
                tolerableColumns={externalTolerableColumns}
              />
            ) : null}
          </div>
        ) : null}

        <div className="mapping-actions">
          <Button label="Voltar para origem" variant="secondary" onClick={onBack} />
          <div className="mapping-actions-forward">
            <Button
              label="Baixar template YAML"
              variant="secondary"
              isDisabled={!canContinue}
              tooltip={
                !canContinue
                  ? "Conclua e valide o mapeamento antes de baixar."
                  : undefined
              }
              onClick={downloadTemplate}
            />
            <Button
              label="Continuar para validação"
              variant="primary"
              isDisabled={!canContinue}
              tooltip={
                !canContinue
                  ? "Conclua e valide o mapeamento para continuar."
                  : undefined
              }
              onClick={continueToValidation}
            />
          </div>
        </div>
      </Section>
    </div>
  );
}

function suggestAssignments(
  columns: string[],
  entity: MigrationEntity,
): Assignments {
  const availableTargets = new Set(
    ENTITY_DEFINITIONS[entity].fields.map((field) => field.name),
  );
  const usedTargets = new Set<string>();
  return Object.fromEntries(
    columns.map((source) => {
      const normalizedSource = normalizeName(source);
      const target = Object.entries(TARGET_ALIASES).find(
        ([candidate, aliases]) =>
          availableTargets.has(candidate) &&
          !usedTargets.has(candidate) &&
          (normalizeName(candidate) === normalizedSource ||
            aliases.includes(normalizedSource)),
      )?.[0];
      if (target) {
        usedTargets.add(target);
      }
      return [source, target ?? null];
    }),
  );
}

function normalizeName(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]/g, "")
    .toLowerCase();
}

function sampleValue(preview: SourcePreview, source: string): string {
  const value = preview.rows.find((row) => row[source])?.[source];
  if (!value) {
    return "Sem amostra na prévia";
  }
  const text = String(value);
  return text.length > 54 ? `${text.slice(0, 51)}…` : text;
}

function buildMappingYaml({
  entity,
  sourceName,
  sourceFormat,
  assignments,
}: {
  entity: MigrationEntity;
  sourceName: string;
  sourceFormat: string;
  assignments: Assignments;
}): string {
  const definition = ENTITY_DEFINITIONS[entity];
  const requiredTargets = new Set(
    definition.fields.filter((field) => field.required).map((field) => field.name),
  );
  const mapped = Object.entries(assignments).filter((entry) => entry[1] !== null);
  const ignored = Object.entries(assignments)
    .filter((entry) => entry[1] === null)
    .map(([source]) => source);
  const lines = [
    "version: 1",
    `name: ${yamlString(`Waypoint - ${sourceName}`)}`,
    `entity: ${entity}`,
    "source:",
    `  type: ${sourceFormat}`,
    "  header_row: 1",
    "fields:",
  ];

  for (const [source, target] of mapped) {
    if (target === null) {
      continue;
    }
    lines.push(
      `  ${yamlString(source)}:`,
      `    target: ${target}`,
      `    required: ${requiredTargets.has(target) ? "true" : "false"}`,
      `    transforms: [${(SUGGESTED_TRANSFORMS[target] ?? ["clean_text"])
        .map(yamlString)
        .join(", ")}]`,
    );
  }

  lines.push("ignored_fields:");
  for (const source of ignored) {
    lines.push(`  - ${yamlString(source)}`);
  }
  return `${lines.join("\n")}\n`;
}

function yamlString(value: string): string {
  return JSON.stringify(value);
}

function TemplateSummary({
  template,
  blockingColumns,
  tolerableColumns,
}: {
  template: MappingTemplate;
  blockingColumns: string[];
  tolerableColumns: string[];
}) {
  const status =
    blockingColumns.length > 0
      ? "blocking"
      : tolerableColumns.length > 0
        ? "tolerable"
        : "compatible";
  return (
    <div className="mapping-template-summary">
      <div className="mapping-template-heading">
        <div>
          <Text as="p" type="label">
            {template.name}
          </Text>
          <Text as="p" type="supporting">
            v{template.version} · {template.fields.length} associações
          </Text>
        </div>
        <Badge
          variant={
            status === "compatible"
              ? "success"
              : status === "tolerable"
                ? "warning"
                : "error"
          }
          label={
            status === "compatible"
              ? "Compatível"
              : status === "tolerable"
                ? "Campos vazios"
                : "Incompatível"
          }
        />
      </div>
      <div className="mapping-template-fields">
        {template.fields.map((field) => (
          <div key={field.source}>
            <Text as="span" type="supporting">
              {field.source}
            </Text>
            <span aria-hidden="true">→</span>
            <Text as="span" type="label">
              {field.target}
            </Text>
          </div>
        ))}
      </div>
      {blockingColumns.length > 0 ? (
        <Banner
          status="error"
          title="Este template não serve para este arquivo"
          description={
            `Faltam colunas obrigatórias: ${blockingColumns.join(", ")}. ` +
            "Escolha outro template, envie um YAML compatível ou monte o " +
            "De/Para visualmente."
          }
        />
      ) : tolerableColumns.length > 0 ? (
        <Banner
          status="warning"
          title="Algumas colunas opcionais não existem no arquivo"
          description={
            `Ficarão vazias: ${tolerableColumns.join(", ")}. ` +
            "A validação pode continuar normalmente."
          }
        />
      ) : null}
    </div>
  );
}

function createMappingDraft(
  file: File,
  preview: SourcePreview,
  entity: MigrationEntity,
  assignments: Assignments,
): MappingDraft {
  return {
    entity,
    assignments: { ...assignments },
    filename: `${file.name.replace(/\.[^.]+$/, "") || "waypoint"}-mapping.yaml`,
    content: buildMappingYaml({
      entity,
      sourceName: preview.source_name,
      sourceFormat: preview.source_format,
      assignments,
    }),
  };
}

function draftFromTemplate(template: MappingTemplate): MappingDraft {
  return {
    entity: template.entity,
    assignments: { ...template.assignments },
    filename: template.filename,
    content: template.content,
  };
}
