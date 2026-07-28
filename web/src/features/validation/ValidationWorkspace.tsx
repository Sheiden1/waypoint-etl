import { useMemo, useState } from "react";

import { Badge } from "@astryxdesign/core/Badge";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { EmptyState } from "@astryxdesign/core/EmptyState";
import { Heading } from "@astryxdesign/core/Heading";
import { Section } from "@astryxdesign/core/Section";
import { Selector } from "@astryxdesign/core/Selector";
import { Tab, TabList } from "@astryxdesign/core/TabList";
import { Table, pixel, proportional } from "@astryxdesign/core/Table";
import { Text } from "@astryxdesign/core/Text";

import {
  ApiRequestError,
  runDryRun,
  type DryRunResult,
  type DuplicateMatch,
  type ResultRow,
  type ValidationIssue,
} from "../../lib/api";
import type { MappingDraft } from "../mapping/MappingWorkspace";

interface ValidationWorkspaceProps {
  file: File;
  mapping: MappingDraft;
  apiAvailable: boolean;
  initialResult?: DryRunResult | null;
  onBack: () => void;
  onContinue: () => void;
  onResult: (result: DryRunResult) => void;
}

type ResultView = "accepted" | "issues" | "duplicates" | "pipeline";
type IssueFilter = "all" | "error" | "warning";

export function ValidationWorkspace({
  file,
  mapping,
  apiAvailable,
  initialResult = null,
  onBack,
  onContinue,
  onResult,
}: ValidationWorkspaceProps) {
  const [result, setResult] = useState<DryRunResult | null>(initialResult);
  const [error, setError] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [resultView, setResultView] = useState<ResultView>(
    initialResult && initialResult.summary.rejected === 0 ? "accepted" : "issues",
  );
  const [issueFilter, setIssueFilter] = useState<IssueFilter>("all");

  const executeValidation = async () => {
    setError(null);
    setIsValidating(true);
    try {
      const nextResult = await runDryRun(
        file,
        mapping.content,
        mapping.entity,
        mapping.filename,
      );
      setResult(nextResult);
      setResultView(
        nextResult.summary.rejected === 0 ? "accepted" : "issues",
      );
      onResult(nextResult);
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? caught.message
          : "A validação não foi concluída. Verifique a API e tente novamente.",
      );
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="validation-workspace">
      <Section className="validation-section" width="100%" padding={6}>
        <div className="section-heading">
          <div>
            <Text as="p" type="label" color="accent">
              03 · VALIDAÇÃO
            </Text>
            <Heading level={2}>Execute o pipeline em segurança</Heading>
          </div>
          <Badge variant="blue" label="DRY-RUN" />
        </div>

        <div className="validation-context">
          <div>
            <Text as="p" type="supporting">
              Origem
            </Text>
            <Text as="p" type="label">
              {file.name}
            </Text>
          </div>
          <div>
            <Text as="p" type="supporting">
              Entidade
            </Text>
            <Text as="p" type="label">
              {entityLabel(mapping.entity)}
            </Text>
          </div>
          <div>
            <Text as="p" type="supporting">
              Template
            </Text>
            <Text as="p" type="label">
              {mapping.filename}
            </Text>
          </div>
        </div>

        <Banner
          status="info"
          title="Nenhuma tabela será alterada"
          description="O Waypoint extrai, transforma, valida e procura duplicidades, mas não grava registros no destino durante o dry-run."
        />

        {error ? (
          <Banner
            status="error"
            title="Não foi possível concluir o dry-run"
            description={error}
          />
        ) : null}

        <div className="validation-launch">
          <Button
            label={result ? "Executar novamente" : "Executar validação"}
            variant="primary"
            size="lg"
            isLoading={isValidating}
            isDisabled={!apiAvailable}
            tooltip={
              apiAvailable
                ? undefined
                : "Inicie a API do Waypoint para executar o dry-run."
            }
            onClick={() => void executeValidation()}
          />
          <Text type="supporting">
            O processamento usa o mesmo núcleo da CLI e da interface clássica.
          </Text>
        </div>
      </Section>

      {result ? (
        <ValidationResult
          result={result}
          resultView={resultView}
          issueFilter={issueFilter}
          onResultViewChange={(value) => setResultView(value as ResultView)}
          onIssueFilterChange={(value) => setIssueFilter(value as IssueFilter)}
        />
      ) : (
        <Section className="validation-waiting" variant="muted" padding={5}>
          <EmptyState
            headingLevel={3}
            title="Pronto para validar"
            description="Execute o dry-run para ver registros válidos, rejeições, duplicidades e o tempo de cada etapa."
            isCompact
          />
        </Section>
      )}

      <div className="validation-actions">
        <Button label="Voltar ao mapeamento" variant="secondary" onClick={onBack} />
        <Button
          label="Continuar para destino"
          variant="primary"
          isDisabled={result === null}
          tooltip={
            result === null
              ? "Execute a validação antes de escolher o destino."
              : undefined
          }
          onClick={onContinue}
        />
      </div>
    </div>
  );
}

function ValidationResult({
  result,
  resultView,
  issueFilter,
  onResultViewChange,
  onIssueFilterChange,
}: {
  result: DryRunResult;
  resultView: ResultView;
  issueFilter: IssueFilter;
  onResultViewChange: (value: string) => void;
  onIssueFilterChange: (value: string) => void;
}) {
  const summary = result.summary;
  const filteredIssues = result.issues.filter(
    (issue) => issueFilter === "all" || issue.severity === issueFilter,
  );

  return (
    <Section className="validation-result" width="100%" padding={0}>
      <div className="result-overview">
        <div>
          <Text as="p" type="label" color="accent">
            DRY-RUN CONCLUÍDO
          </Text>
          <Heading level={2}>Qualidade da origem</Heading>
        </div>
        <div className="run-identity">
          <Text as="p" type="supporting">
            run_id
          </Text>
          <Text as="p" type="label">
            {result.run_id}
          </Text>
        </div>
      </div>

      <div className="quality-metrics" aria-label="Resumo da validação">
        <Metric label="Processados" value={summary.total} tone="neutral" />
        <Metric label="Válidos" value={summary.valid} tone="success" />
        <Metric label="Rejeitados" value={summary.rejected} tone="error" />
        <Metric
          label="Duplicidades"
          value={summary.duplicates}
          supporting={`${summary.possible_duplicates} possíveis`}
          tone="warning"
        />
      </div>

      <div className="result-meta">
        <Text type="supporting">
          {summary.duration_ms} ms · {result.mapping_name} v
          {result.mapping_version}
        </Text>
        <Badge
          variant={summary.rejected === 0 ? "success" : "warning"}
          label={
            summary.rejected === 0
              ? "Sem rejeições"
              : "Revisão necessária"
          }
        />
      </div>

      {result.warnings.map((warning) => (
        <div className="result-warning" key={warning}>
          <Banner
            status="warning"
            title="Atenção durante o processamento"
            description={warning}
          />
        </div>
      ))}

      <div className="result-tabs">
        <TabList
          value={resultView}
          onChange={onResultViewChange}
          layout="fill"
          hasDivider
        >
          <Tab
            value="accepted"
            label="Válidos"
            endContent={<Badge variant="success" label={summary.valid} />}
          />
          <Tab
            value="issues"
            label="Problemas"
            endContent={<Badge variant="error" label={result.issues.length} />}
          />
          <Tab
            value="duplicates"
            label="Duplicidades"
            endContent={<Badge variant="warning" label={result.duplicates.length} />}
          />
          <Tab value="pipeline" label="Pipeline" />
        </TabList>
      </div>

      <div
        className="result-panel"
        role="tabpanel"
        aria-label={resultViewLabel(resultView)}
      >
        {resultView === "accepted" ? (
          <AcceptedPanel rows={result.accepted_rows} />
        ) : null}
        {resultView === "issues" ? (
          <IssuesPanel
            issues={filteredIssues}
            totalIssues={result.issues.length}
            filter={issueFilter}
            onFilterChange={onIssueFilterChange}
          />
        ) : null}
        {resultView === "duplicates" ? (
          <DuplicatesPanel duplicates={result.duplicates} />
        ) : null}
        {resultView === "pipeline" ? <PipelinePanel result={result} /> : null}
      </div>
    </Section>
  );
}

function Metric({
  label,
  value,
  supporting,
  tone,
}: {
  label: string;
  value: number;
  supporting?: string;
  tone: "neutral" | "success" | "warning" | "error";
}) {
  return (
    <div className={`quality-metric is-${tone}`}>
      <Text as="p" type="supporting">
        {label}
      </Text>
      <Text as="p" type="display-3" weight="bold">
        {value}
      </Text>
      {supporting ? (
        <Text as="p" type="supporting">
          {supporting}
        </Text>
      ) : null}
    </div>
  );
}

function AcceptedPanel({ rows }: { rows: ResultRow[] }) {
  const columns = useMemo(
    () =>
      Object.keys(rows[0] ?? {}).map((key) => ({
        key,
        header: fieldLabel(key),
        width: proportional(1),
      })),
    [rows],
  );

  if (rows.length === 0) {
    return (
      <EmptyState
        title="Nenhum registro válido"
        description="Revise os problemas encontrados e ajuste o arquivo ou o mapeamento."
        isCompact
      />
    );
  }

  return (
    <>
      <PanelHeading
        title="Registros válidos"
        description="Amostra normalizada e pronta para a próxima etapa."
      />
      <div className="result-table">
        <Table
          data={rows.slice(0, 50)}
          columns={columns}
          density="compact"
          dividers="grid"
          hasHover
          textOverflow="truncate"
        />
      </div>
      {rows.length > 50 ? (
        <Text as="p" type="supporting" className="result-table-note">
          Exibindo 50 de {rows.length} registros válidos.
        </Text>
      ) : null}
    </>
  );
}

function IssuesPanel({
  issues,
  totalIssues,
  filter,
  onFilterChange,
}: {
  issues: ValidationIssue[];
  totalIssues: number;
  filter: IssueFilter;
  onFilterChange: (value: string) => void;
}) {
  const rows = issues.map((issue) => ({
    row: issue.row_number,
    severity: issue.severity === "error" ? "Erro" : "Aviso",
    field: issue.field ? fieldLabel(issue.field) : "Registro",
    message: issue.message,
    original: issue.original_value ?? "—",
  }));
  const columns = [
    { key: "row", header: "Linha", width: pixel(76) },
    { key: "severity", header: "Severidade", width: pixel(110) },
    { key: "field", header: "Campo", width: proportional(1) },
    { key: "message", header: "Problema", width: proportional(2) },
    { key: "original", header: "Valor original", width: proportional(1) },
  ];

  return (
    <>
      <div className="panel-heading-with-filter">
        <PanelHeading
          title="Problemas encontrados"
          description={`${totalIssues} ocorrência${totalIssues === 1 ? "" : "s"} no lote.`}
        />
        <Selector
          label="Filtrar problemas"
          isLabelHidden
          options={[
            { value: "all", label: "Todos" },
            { value: "error", label: "Somente erros" },
            { value: "warning", label: "Somente avisos" },
          ]}
          value={filter}
          onChange={onFilterChange}
          width={190}
          size="sm"
        />
      </div>
      {rows.length === 0 ? (
        <EmptyState
          title={totalIssues === 0 ? "Nenhum problema encontrado" : "Nenhum resultado"}
          description={
            totalIssues === 0
              ? "Todos os registros passaram pelas regras de qualidade."
              : "Não há ocorrências com o filtro selecionado."
          }
          isCompact
        />
      ) : (
        <div className="result-table">
          <Table
            data={rows}
            columns={columns}
            density="compact"
            dividers="rows"
            hasHover
            verticalAlign="top"
          />
        </div>
      )}
    </>
  );
}

function DuplicatesPanel({
  duplicates,
}: {
  duplicates: DuplicateMatch[];
}) {
  const rows = duplicates.map((duplicate) => ({
    row: duplicate.row_number,
    match: duplicate.matched_row_number,
    kind: duplicate.kind === "exact" ? "Exata" : "Possível",
    key: fieldLabel(duplicate.key),
    value: duplicate.value,
    similarity: `${Math.round(duplicate.similarity * 100)}%`,
  }));
  const columns = [
    { key: "row", header: "Linha", width: pixel(76) },
    { key: "match", header: "Corresponde à", width: pixel(120) },
    { key: "kind", header: "Tipo", width: pixel(100) },
    { key: "key", header: "Chave", width: proportional(1) },
    { key: "value", header: "Valor", width: proportional(1) },
    { key: "similarity", header: "Similaridade", width: pixel(110) },
  ];

  if (rows.length === 0) {
    return (
      <EmptyState
        title="Nenhuma duplicidade encontrada"
        description="O lote não possui correspondências exatas nem suspeitas pelos critérios atuais."
        isCompact
      />
    );
  }

  return (
    <>
      <PanelHeading
        title="Duplicidades para revisar"
        description="O Waypoint apenas sinaliza correspondências; nenhum registro é mesclado automaticamente."
      />
      <div className="result-table">
        <Table
          data={rows}
          columns={columns}
          density="compact"
          dividers="rows"
          hasHover
        />
      </div>
    </>
  );
}

function PipelinePanel({ result }: { result: DryRunResult }) {
  const stageRows = result.stages.map((stage) => ({
    stage: stageLabel(stage.name),
    duration: `${stage.duration_ms} ms`,
  }));
  const transformRows = Object.entries(result.transforms_applied)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([name, count]) => ({
      transform: transformLabel(name),
      count,
    }));

  return (
    <div className="pipeline-panels">
      <div>
        <PanelHeading
          title="Duração por etapa"
          description="Tempo medido no backend durante esta execução."
        />
        <Table
          data={stageRows}
          columns={[
            { key: "stage", header: "Etapa", width: proportional(1) },
            { key: "duration", header: "Duração", width: pixel(110) },
          ]}
          density="compact"
          dividers="rows"
        />
      </div>
      <div>
        <PanelHeading
          title="Transformações aplicadas"
          description="Quantidade de valores efetivamente alterados."
        />
        {transformRows.length === 0 ? (
          <EmptyState
            title="Nenhuma transformação alterou valores"
            isCompact
          />
        ) : (
          <Table
            data={transformRows}
            columns={[
              {
                key: "transform",
                header: "Transformação",
                width: proportional(1),
              },
              { key: "count", header: "Alterações", width: pixel(110) },
            ]}
            density="compact"
            dividers="rows"
          />
        )}
      </div>
    </div>
  );
}

function PanelHeading({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="result-panel-heading">
      <Heading level={3}>{title}</Heading>
      <Text as="p" type="supporting">
        {description}
      </Text>
    </div>
  );
}

function entityLabel(entity: MappingDraft["entity"]): string {
  return {
    customers: "Clientes",
    contacts: "Contatos",
    invoices: "Cobranças",
  }[entity];
}

function resultViewLabel(view: ResultView): string {
  return {
    accepted: "Registros válidos",
    issues: "Problemas encontrados",
    duplicates: "Duplicidades",
    pipeline: "Detalhes do pipeline",
  }[view];
}

function fieldLabel(field: string): string {
  const labels: Record<string, string> = {
    external_id: "ID externo",
    full_name: "Nome / razão social",
    document: "CPF / CNPJ",
    document_type: "Tipo de documento",
    customer_document: "CPF / CNPJ do cliente",
    name: "Nome",
    role: "Cargo / função",
    email: "E-mail",
    phone: "Telefone",
    postal_code: "CEP",
    city: "Cidade",
    state: "UF",
    created_at: "Data de cadastro",
    description: "Descrição",
    issued_at: "Data de emissão",
    due_at: "Data de vencimento",
    amount: "Valor",
    status: "Status",
  };
  return labels[field] ?? field;
}

function stageLabel(stage: string): string {
  return {
    load_mapping: "Carregar mapeamento",
    extract: "Extrair",
    map: "Mapear e transformar",
    validate: "Validar",
    deduplicate: "Deduplicar",
    export: "Gerar artefatos",
  }[stage] ?? stage;
}

function transformLabel(transform: string): string {
  return {
    clean_text: "Limpeza de texto",
    title_case: "Capitalização",
    digits_only: "Somente dígitos",
    email: "Normalização de e-mail",
    brazilian_phone: "Telefone brasileiro",
    postal_code: "CEP",
    uf: "UF",
    brazilian_date: "Data brasileira",
    brazilian_money: "Moeda brasileira",
    lowercase: "Minúsculas",
  }[transform] ?? transform;
}
