export interface HealthResponse {
  status: string;
  version: string;
  max_upload_mb: number;
  features: {
    ocr: boolean;
    database: boolean;
  };
}

export interface PreviewRow {
  [key: string]: string | null;
}

export interface SourcePreview {
  source_name: string;
  source_format: string;
  is_tabular: boolean;
  columns: string[];
  rows: PreviewRow[];
  available_sheets: string[];
  text_preview?: string;
  page_count?: number;
  ocr_used: boolean;
  warnings: string[];
}

export type MigrationEntity = "customers" | "contacts" | "invoices";

export interface ResultRow {
  [key: string]: string | number | boolean | null;
}

export interface DryRunSummary {
  total: number;
  valid: number;
  rejected: number;
  duplicates: number;
  possible_duplicates: number;
  duration_ms: number;
}

export interface ValidationIssue {
  row_number: number;
  sheet?: string;
  field?: string;
  code: string;
  severity: "warning" | "error";
  message: string;
  original_value?: string;
  normalized_value?: string;
}

export interface DuplicateMatch {
  row_number: number;
  matched_row_number: number;
  kind: "exact" | "possible";
  key: string;
  value: string;
  similarity: number;
}

export interface StageDuration {
  name: string;
  duration_ms: number;
}

export type ArtifactName =
  | "accepted.csv"
  | "rejected.xlsx"
  | "duplicates.csv"
  | "audit-report.json";

export interface MigrationArtifact {
  name: ArtifactName;
  media_type: string;
  download_url: string;
}

export interface DryRunResult {
  run_id: string;
  status: string;
  entity: MigrationEntity;
  source_name: string;
  mapping_name: string;
  mapping_version: number;
  dry_run: boolean;
  summary: DryRunSummary;
  accepted_rows: ResultRow[];
  issues: ValidationIssue[];
  duplicates: DuplicateMatch[];
  stages: StageDuration[];
  transforms_applied: Record<string, number>;
  warnings: string[];
  artifacts?: MigrationArtifact[];
  artifacts_expires_in_seconds?: number;
  loaded_records?: number;
}

export interface MappingField {
  source: string;
  target: string;
  required: boolean;
  transforms: string[];
}

export interface MappingTemplate {
  template_id: string;
  filename: string;
  name: string;
  version: number;
  entity: MigrationEntity;
  source_format?: string;
  sheet?: string;
  header_row: number;
  fields: MappingField[];
  ignored_fields: string[];
  assignments: Record<string, string | null>;
  content: string;
}

export interface MappingCatalog {
  templates: MappingTemplate[];
}

interface ApiErrorPayload {
  detail?: {
    code?: string;
    message?: string;
  };
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/health`, { signal });
  return parseResponse<HealthResponse>(response);
}

export async function inspectSource(
  file: File,
  options: {
    headerRow?: number;
    sheet?: string;
  } = {},
): Promise<SourcePreview> {
  const body = new FormData();
  body.set("file", file);
  body.set("header_row", String(options.headerRow ?? 1));
  if (options.sheet) {
    body.set("sheet", options.sheet);
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/inspect`, {
    method: "POST",
    body,
  });
  return parseResponse<SourcePreview>(response);
}

export async function runDryRun(
  file: File,
  mappingContent: string,
  entity: MigrationEntity,
  mappingFilename = "waypoint-mapping.yaml",
): Promise<DryRunResult> {
  const body = new FormData();
  body.set("file", file);
  body.set(
    "mapping",
    new File([mappingContent], mappingFilename, {
      type: "application/yaml",
    }),
  );
  body.set("entity", entity);

  const response = await fetch(`${apiBaseUrl}/api/v1/migrations/dry-run`, {
    method: "POST",
    body,
  });
  return parseResponse<DryRunResult>(response);
}

export async function getMappings(
  entity?: MigrationEntity,
  sourceFormat?: string,
): Promise<MappingCatalog> {
  const query = new URLSearchParams();
  if (entity) {
    query.set("entity", entity);
  }
  if (sourceFormat) {
    query.set("source_format", sourceFormat);
  }
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  const response = await fetch(`${apiBaseUrl}/api/v1/mappings${suffix}`);
  return parseResponse<MappingCatalog>(response);
}

export async function previewMapping(
  mapping: File,
  entity: MigrationEntity,
  sourceFormat: string,
): Promise<MappingTemplate> {
  const body = new FormData();
  body.set("mapping", mapping);
  body.set("entity", entity);
  body.set("source_format", sourceFormat);
  const response = await fetch(`${apiBaseUrl}/api/v1/mappings/preview`, {
    method: "POST",
    body,
  });
  return parseResponse<MappingTemplate>(response);
}

export async function loadPostgres(
  file: File,
  mappingContent: string,
  entity: MigrationEntity,
  mappingFilename = "waypoint-mapping.yaml",
): Promise<DryRunResult> {
  const body = new FormData();
  body.set("file", file);
  body.set(
    "mapping",
    new File([mappingContent], mappingFilename, {
      type: "application/yaml",
    }),
  );
  body.set("entity", entity);
  body.set("confirm", "true");
  const response = await fetch(
    `${apiBaseUrl}/api/v1/migrations/load-postgres`,
    {
      method: "POST",
      body,
    },
  );
  return parseResponse<DryRunResult>(response);
}

export function resolveApiUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  return `${apiBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

async function parseResponse<T>(response: Response): Promise<T> {
  const payload: unknown = await response.json();
  if (!response.ok) {
    const error = isApiErrorPayload(payload) ? payload.detail : undefined;
    throw new ApiRequestError(
      error?.message ?? "Não foi possível concluir a operação.",
      response.status,
      error?.code ?? "request_failed",
    );
  }
  return payload as T;
}

function isApiErrorPayload(value: unknown): value is ApiErrorPayload {
  return typeof value === "object" && value !== null && "detail" in value;
}
