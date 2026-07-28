import { useMemo, useState } from "react";

import { Badge } from "@astryxdesign/core/Badge";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { FileInput } from "@astryxdesign/core/FileInput";
import { Heading } from "@astryxdesign/core/Heading";
import { Section } from "@astryxdesign/core/Section";
import { Table, proportional } from "@astryxdesign/core/Table";
import { Text } from "@astryxdesign/core/Text";

import {
  ApiRequestError,
  inspectSource,
  type PreviewRow,
  type SourcePreview,
} from "../../lib/api";

const ACCEPTED_FILES =
  ".csv,.xlsx,.pdf,.docx,.txt,.png,.jpg,.jpeg";

interface InspectionWorkspaceProps {
  maxUploadMb: number;
  ocrAvailable: boolean;
  apiAvailable: boolean;
  initialFile?: File | null;
  initialPreview?: SourcePreview | null;
  onContinue: (file: File, preview: SourcePreview) => void;
}

export function InspectionWorkspace({
  maxUploadMb,
  ocrAvailable,
  apiAvailable,
  initialFile = null,
  initialPreview = null,
  onContinue,
}: InspectionWorkspaceProps) {
  const [file, setFile] = useState<File | null>(initialFile);
  const [preview, setPreview] = useState<SourcePreview | null>(initialPreview);
  const [error, setError] = useState<string | null>(null);
  const [isInspecting, setIsInspecting] = useState(false);

  const inspect = async () => {
    if (file === null) {
      setError("Escolha um arquivo antes de iniciar a inspeção.");
      return;
    }
    setError(null);
    setPreview(null);
    setIsInspecting(true);
    try {
      setPreview(await inspectSource(file));
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? caught.message
          : "A inspeção falhou. Verifique se a API está disponível e tente novamente.",
      );
    } finally {
      setIsInspecting(false);
    }
  };

  const changeFile = (next: File | File[] | null) => {
    setFile(next instanceof File ? next : null);
    setPreview(null);
    setError(null);
  };

  return (
    <div className="workspace">
      <div className="workspace-primary">
        <Section className="source-section" width="100%" padding={6}>
          <div className="section-heading">
            <div>
              <Text as="p" type="label" color="accent">
                01 · ORIGEM
              </Text>
              <Heading level={2}>Escolha um arquivo</Heading>
            </div>
            <Text type="supporting">Nada é armazenado após a operação.</Text>
          </div>

          <div className="file-input-boundary">
            <FileInput
              label="Arquivo de origem"
              description={`CSV, Excel, PDF, Word, TXT ou imagem · até ${maxUploadMb} MB`}
              value={file}
              onChange={changeFile}
              accept={ACCEPTED_FILES}
              maxSize={maxUploadMb * 1024 * 1024}
              mode="dropzone"
              width="100%"
              placeholder="Arraste o arquivo ou escolha no computador"
              isRequired
              isLoading={isInspecting}
            />
          </div>

          {file ? <FileSummary file={file} /> : null}

          {error ? (
            <Banner
              status="error"
              title="Não foi possível inspecionar"
              description={error}
            />
          ) : null}

          <div className="primary-action">
            <Button
              label="Inspecionar arquivo"
              variant="primary"
              size="lg"
              isLoading={isInspecting}
              isDisabled={!apiAvailable || file === null}
              tooltip={
                apiAvailable
                  ? undefined
                  : "Inicie a API do Waypoint para inspecionar arquivos."
              }
              onClick={() => void inspect()}
            />
            <Text type="supporting">
              A inspeção detecta o formato e lê somente uma prévia.
            </Text>
          </div>
        </Section>

        {preview && file ? (
          <PreviewPanel
            preview={preview}
            onContinue={() => onContinue(file, preview)}
          />
        ) : null}
      </div>

      <aside className="workspace-aside" aria-labelledby="about-inspection">
        <Section variant="muted" padding={5}>
          <Heading id="about-inspection" level={2}>
            O que acontece agora
          </Heading>
          <ol className="explanation-list">
            <li>
              <span>1</span>
              <div>
                <Text as="p" type="label">
                  Detectar
                </Text>
                <Text as="p" type="supporting">
                  A extensão escolhe o extrator apropriado.
                </Text>
              </div>
            </li>
            <li>
              <span>2</span>
              <div>
                <Text as="p" type="label">
                  Extrair
                </Text>
                <Text as="p" type="supporting">
                  Colunas e linhas, ou um trecho do documento.
                </Text>
              </div>
            </li>
            <li>
              <span>3</span>
              <div>
                <Text as="p" type="label">
                  Conferir
                </Text>
                <Text as="p" type="supporting">
                  Você revisa antes de escolher o De/Para.
                </Text>
              </div>
            </li>
          </ol>
        </Section>

        <Section variant="transparent" padding={5} dividers={["top"]}>
          <div className="capability-row">
            <Text type="label">OCR local</Text>
            <Badge
              variant={ocrAvailable ? "success" : "warning"}
              label={ocrAvailable ? "Disponível" : "Indisponível"}
            />
          </div>
          <Text as="p" type="supporting">
            Imagens e PDFs escaneados precisam do Tesseract instalado na API.
          </Text>
        </Section>
      </aside>
    </div>
  );
}

function FileSummary({ file }: { file: File }) {
  return (
    <div className="file-summary" aria-live="polite">
      <div className="file-summary-details">
        <Text as="p" type="label">
          {file.name}
        </Text>
        <Text as="p" type="supporting">
          {formatBytes(file.size)}
        </Text>
      </div>
      <Badge variant="blue" label="Pronto para inspecionar" />
    </div>
  );
}

function PreviewPanel({
  preview,
  onContinue,
}: {
  preview: SourcePreview;
  onContinue: () => void;
}) {
  return (
    <Section padding={0} dividers={["top"]}>
      <div className="preview-heading">
        <div>
          <Text as="p" type="label" color="accent">
            PRÉVIA REAL
          </Text>
          <Heading level={2}>{preview.source_name}</Heading>
        </div>
        <div className="preview-meta">
          <Text type="supporting">
            Formato <strong>{preview.source_format.toUpperCase()}</strong>
          </Text>
          {preview.ocr_used ? <Badge variant="warning" label="OCR utilizado" /> : null}
        </div>
      </div>

      {preview.warnings.map((warning) => (
        <div className="preview-banner" key={warning}>
          <Banner status="warning" title="Atenção na extração" description={warning} />
        </div>
      ))}

      {preview.is_tabular ? (
        <TabularPreview preview={preview} />
      ) : (
        <DocumentPreview preview={preview} />
      )}

      <div className="preview-actions">
        <div>
          <Text as="p" type="label">
            Inspeção concluída
          </Text>
          <Text as="p" type="supporting">
            {preview.is_tabular
              ? "A estrutura está pronta para configurar o De/Para."
              : "Documentos podem ser conferidos aqui; o mapeamento estruturado aceita CSV e Excel."}
          </Text>
        </div>
        <Button
          label="Continuar para mapeamento"
          variant="primary"
          size="lg"
          isDisabled={!preview.is_tabular}
          tooltip={
            preview.is_tabular
              ? undefined
              : "Use um arquivo CSV ou Excel para seguir ao mapeamento."
          }
          onClick={onContinue}
        />
      </div>
    </Section>
  );
}

function TabularPreview({ preview }: { preview: SourcePreview }) {
  const columns = useMemo(
    () =>
      preview.columns.map((column) => ({
        key: column,
        header: column,
        width: proportional(1),
      })),
    [preview.columns],
  );
  const rows: PreviewRow[] = preview.rows;

  return (
    <div className="table-region">
      <div className="table-caption">
        <Text type="supporting">
          {preview.columns.length} colunas · {preview.rows.length} linhas na prévia
        </Text>
      </div>
      <Table
        data={rows}
        columns={columns}
        density="compact"
        dividers="grid"
        hasHover
        textOverflow="truncate"
      />
    </div>
  );
}

function DocumentPreview({ preview }: { preview: SourcePreview }) {
  return (
    <div className="document-preview">
      <Text type="supporting">
        {preview.page_count
          ? `${preview.page_count} página${preview.page_count === 1 ? "" : "s"}`
          : "Texto extraído"}
      </Text>
      <pre>{preview.text_preview || "Nenhum texto encontrado."}</pre>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
