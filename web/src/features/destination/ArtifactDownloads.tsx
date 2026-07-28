import { Badge } from "@astryxdesign/core/Badge";
import { Button } from "@astryxdesign/core/Button";
import { Text } from "@astryxdesign/core/Text";

import {
  resolveApiUrl,
  type ArtifactName,
  type DryRunResult,
} from "../../lib/api";

const ARTIFACTS: ReadonlyArray<{
  name: ArtifactName;
  title: string;
  description: string;
}> = [
  {
    name: "accepted.csv",
    title: "Registros válidos",
    description: "CSV normalizado, pronto para uso no sistema de destino.",
  },
  {
    name: "rejected.xlsx",
    title: "Registros rejeitados",
    description: "Planilha com os registros que precisam de revisão.",
  },
  {
    name: "duplicates.csv",
    title: "Duplicidades",
    description: "Ocorrências exatas e possíveis encontradas no lote.",
  },
  {
    name: "audit-report.json",
    title: "Relatório de auditoria",
    description: "Resumo rastreável da execução e das regras aplicadas.",
  },
];

interface ArtifactDownloadsProps {
  result: DryRunResult;
  compact?: boolean;
}

export function ArtifactDownloads({
  result,
  compact = false,
}: ArtifactDownloadsProps) {
  const artifacts = new Map(
    (result.artifacts ?? []).map((artifact) => [artifact.name, artifact]),
  );

  return (
    <div
      className={`artifact-downloads${compact ? " is-compact" : ""}`}
      aria-label="Artefatos da execução"
    >
      {ARTIFACTS.map((definition) => {
        const artifact = artifacts.get(definition.name);
        return (
          <article className="artifact-card" key={definition.name}>
            <div className="artifact-copy">
              <div className="artifact-title">
                <Text as="h3" type="label">
                  {definition.title}
                </Text>
                <Badge
                  variant={artifact ? "success" : "neutral"}
                  label={artifact ? "Disponível" : "Indisponível"}
                />
              </div>
              <Text as="p" type="supporting">
                {definition.description}
              </Text>
              <Text as="p" type="supporting" className="artifact-filename">
                {definition.name}
              </Text>
            </div>
            <Button
              label={`Baixar ${definition.name}`}
              variant="secondary"
              size="sm"
              href={
                artifact ? resolveApiUrl(artifact.download_url) : undefined
              }
              target={artifact ? "_blank" : undefined}
              rel={artifact ? "noopener noreferrer" : undefined}
              isDisabled={!artifact}
              tooltip={
                artifact
                  ? "O download é servido pela API do Waypoint."
                  : "Este artefato não está disponível nesta execução."
              }
            />
          </article>
        );
      })}
    </div>
  );
}
