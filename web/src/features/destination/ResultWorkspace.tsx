import { Badge } from "@astryxdesign/core/Badge";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { Heading } from "@astryxdesign/core/Heading";
import { Section } from "@astryxdesign/core/Section";
import { Text } from "@astryxdesign/core/Text";

import type { DryRunResult } from "../../lib/api";
import { ArtifactDownloads } from "./ArtifactDownloads";
import { artifactExpirationLabel } from "./artifactUtils";
import "./destination.css";

interface ResultWorkspaceProps {
  validationResult: DryRunResult;
  loadResult?: DryRunResult | null;
  onBack: () => void;
  onRestart: () => void;
}

export function ResultWorkspace({
  validationResult,
  loadResult = null,
  onBack,
  onRestart,
}: ResultWorkspaceProps) {
  const result = loadResult ?? validationResult;
  const loadedRecords =
    loadResult?.loaded_records ?? (loadResult ? loadResult.summary.valid : 0);

  return (
    <div className="result-workspace">
      <Section className="journey-result" width="100%" padding={0}>
        <div className="journey-result-hero">
          <div>
            <Text as="p" type="label" color="accent">
              05 · RESULTADO
            </Text>
            <Heading level={2}>Jornada concluída</Heading>
            <Text as="p" type="large" color="secondary">
              O lote foi processado com rastreabilidade e está pronto para o
              próximo passo que você escolher.
            </Text>
          </div>
          <Badge
            variant="success"
            label={loadResult ? "Importado" : "Dry-run concluído"}
          />
        </div>

        <div className="journey-result-metrics" aria-label="Resumo final">
          <ResultMetric label="Processados" value={result.summary.total} />
          <ResultMetric
            label="Válidos"
            value={result.summary.valid}
            tone="success"
          />
          <ResultMetric
            label="Rejeitados"
            value={result.summary.rejected}
            tone="error"
          />
          <ResultMetric
            label="Duplicidades"
            value={result.summary.duplicates}
            tone="warning"
          />
        </div>

        <div className="journey-result-details">
          <ResultDetail label="run_id" value={result.run_id} isCode />
          <ResultDetail label="Origem" value={result.source_name} />
          <ResultDetail
            label="Destino"
            value={loadResult ? "PostgreSQL + artefatos" : "Artefatos"}
          />
          <ResultDetail
            label="Duração"
            value={`${result.summary.duration_ms} ms`}
          />
        </div>
      </Section>

      <Banner
        status="success"
        title={
          loadResult
            ? "Registros aprovados gravados"
            : "Processamento concluído sem alterar o banco"
        }
        description={
          loadResult
            ? `${loadedRecords} registro${loadedRecords === 1 ? "" : "s"} gravado${
                loadedRecords === 1 ? "" : "s"
              } no PostgreSQL.`
            : "Você optou por manter esta execução como dry-run. Nenhum registro foi gravado no PostgreSQL."
        }
      />

      <Section className="destination-section" width="100%" padding={6}>
        <div className="destination-block-heading">
          <div>
            <Text as="p" type="label" color="accent">
              DOWNLOADS
            </Text>
            <Heading level={2}>Leve os resultados com você</Heading>
            <Text as="p" type="supporting">
              {artifactExpirationLabel(result.artifacts_expires_in_seconds)}
            </Text>
          </div>
        </div>

        {result.artifacts?.length ? (
          <ArtifactDownloads result={result} compact />
        ) : (
          <Banner
            status="warning"
            title="Downloads não disponíveis"
            description="Os artefatos desta execução não estão ativos. Inicie uma nova jornada para gerá-los novamente."
          />
        )}
      </Section>

      <div className="destination-actions">
        <Button label="Voltar ao destino" variant="secondary" onClick={onBack} />
        <Button label="Nova jornada" variant="primary" onClick={onRestart} />
      </div>
    </div>
  );
}

function ResultMetric({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: number;
  tone?: "neutral" | "success" | "warning" | "error";
}) {
  return (
    <div className={`journey-result-metric is-${tone}`}>
      <Text as="p" type="supporting">
        {label}
      </Text>
      <Text as="p" type="display-3" weight="bold">
        {value}
      </Text>
    </div>
  );
}

function ResultDetail({
  label,
  value,
  isCode = false,
}: {
  label: string;
  value: string;
  isCode?: boolean;
}) {
  return (
    <div className={isCode ? "journey-result-code" : undefined}>
      <Text as="p" type="supporting">
        {label}
      </Text>
      <Text as="p" type="label">
        {value}
      </Text>
    </div>
  );
}
