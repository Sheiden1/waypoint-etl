import { useState } from "react";

import { Badge } from "@astryxdesign/core/Badge";
import { Banner } from "@astryxdesign/core/Banner";
import { Button } from "@astryxdesign/core/Button";
import { CheckboxInput } from "@astryxdesign/core/CheckboxInput";
import { Heading } from "@astryxdesign/core/Heading";
import { Section } from "@astryxdesign/core/Section";
import { Text } from "@astryxdesign/core/Text";

import {
  ApiRequestError,
  loadPostgres,
  type DryRunResult,
} from "../../lib/api";
import type { MappingDraft } from "../mapping/MappingWorkspace";
import { ArtifactDownloads } from "./ArtifactDownloads";
import { artifactExpirationLabel } from "./artifactUtils";
import "./destination.css";

interface DestinationWorkspaceProps {
  file: File;
  mapping: MappingDraft;
  validationResult: DryRunResult;
  apiAvailable: boolean;
  databaseAvailable: boolean;
  initialLoadResult?: DryRunResult | null;
  onBack: () => void;
  onContinue: () => void;
  onLoadResult: (result: DryRunResult) => void;
}

export function DestinationWorkspace({
  file,
  mapping,
  validationResult,
  apiAvailable,
  databaseAvailable,
  initialLoadResult = null,
  onBack,
  onContinue,
  onLoadResult,
}: DestinationWorkspaceProps) {
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadResult, setLoadResult] = useState<DryRunResult | null>(
    initialLoadResult,
  );
  const [error, setError] = useState<string | null>(null);
  const hasAcceptedRows = validationResult.summary.valid > 0;
  const canLoad =
    apiAvailable &&
    databaseAvailable &&
    hasAcceptedRows &&
    isConfirmed &&
    loadResult === null;

  const executeLoad = async () => {
    if (!canLoad) {
      return;
    }

    setError(null);
    setIsLoading(true);
    try {
      const nextResult = await loadPostgres(
        file,
        mapping.content,
        mapping.entity,
        mapping.filename,
      );
      setLoadResult(nextResult);
      setIsConfirmed(false);
      onLoadResult(nextResult);
    } catch (caught) {
      setError(
        caught instanceof ApiRequestError
          ? caught.message
          : "A importação não foi concluída. Verifique a API e tente novamente.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="destination-workspace">
      <Section className="destination-section" width="100%" padding={6}>
        <div className="section-heading">
          <div>
            <Text as="p" type="label" color="accent">
              04 · DESTINO
            </Text>
            <Heading level={2}>Escolha como usar o lote validado</Heading>
          </div>
          <Badge variant="success" label="Dry-run concluído" />
        </div>

        <div className="destination-context">
          <ContextItem label="Origem" value={file.name} />
          <ContextItem
            label="Registros válidos"
            value={String(validationResult.summary.valid)}
          />
          <ContextItem label="run_id" value={validationResult.run_id} isCode />
        </div>
      </Section>

      <Section className="destination-section" width="100%" padding={6}>
        <div className="destination-block-heading">
          <div>
            <Text as="p" type="label" color="accent">
              EXPORTAR
            </Text>
            <Heading level={2}>Artefatos desta execução</Heading>
            <Text as="p" type="supporting">
              {artifactExpirationLabel(
                validationResult.artifacts_expires_in_seconds,
              )}
            </Text>
          </div>
          <Badge
            variant="blue"
            label={`${validationResult.artifacts?.length ?? 0} arquivos`}
          />
        </div>

        {validationResult.artifacts?.length ? (
          <ArtifactDownloads result={validationResult} />
        ) : (
          <Banner
            status="warning"
            title="Downloads não disponíveis"
            description="Esta execução não possui artefatos ativos. Volte à validação e execute o dry-run novamente."
          />
        )}
      </Section>

      <Section className="destination-section" width="100%" padding={6}>
        <div className="destination-block-heading">
          <div>
            <Text as="p" type="label" color="accent">
              POSTGRESQL · OPCIONAL
            </Text>
            <Heading level={2}>Gravar registros aprovados</Heading>
            <Text as="p" type="supporting">
              Esta ação executa novamente o pipeline e persiste somente os
              registros válidos.
            </Text>
          </div>
          <Badge
            variant={databaseAvailable ? "success" : "warning"}
            label={databaseAvailable ? "Banco disponível" : "Indisponível"}
          />
        </div>

        {!apiAvailable ? (
          <Banner
            status="error"
            title="API indisponível"
            description="Reconecte a API do Waypoint antes de importar para o PostgreSQL."
          />
        ) : !databaseAvailable ? (
          <Banner
            status="info"
            title="PostgreSQL indisponível"
            description="Os downloads continuam funcionando. Configure DATABASE_URL na API para habilitar a importação opcional."
          />
        ) : !hasAcceptedRows ? (
          <Banner
            status="warning"
            title="Nenhum registro aprovado"
            description="Não há registros válidos para gravar. Revise as rejeições antes de tentar novamente."
          />
        ) : null}

        {error ? (
          <Banner
            status="error"
            title="Não foi possível importar o lote"
            description={error}
          />
        ) : null}

        {loadResult ? (
          <Banner
            status="success"
            title="Importação concluída"
            description={`${loadResult.loaded_records ?? loadResult.summary.valid} registro${
              (loadResult.loaded_records ?? loadResult.summary.valid) === 1
                ? ""
                : "s"
            } gravado${
              (loadResult.loaded_records ?? loadResult.summary.valid) === 1
                ? ""
                : "s"
            } no PostgreSQL. run_id: ${loadResult.run_id}`}
          />
        ) : (
          <div className="destination-confirmation">
            <CheckboxInput
              label={`Confirmo a gravação de ${validationResult.summary.valid} registro${
                validationResult.summary.valid === 1 ? "" : "s"
              } válido${
                validationResult.summary.valid === 1 ? "" : "s"
              } no PostgreSQL.`}
              description="A confirmação vale somente para esta tentativa e não pode ser presumida pelo Waypoint."
              value={isConfirmed}
              isRequired
              isDisabled={
                !apiAvailable || !databaseAvailable || !hasAcceptedRows
              }
              disabledMessage={loadDisabledReason({
                apiAvailable,
                databaseAvailable,
                hasAcceptedRows,
              })}
              onChange={setIsConfirmed}
              width="100%"
            />
            <Button
              label="Importar para PostgreSQL"
              variant="primary"
              size="lg"
              isDisabled={!canLoad}
              isLoading={isLoading}
              tooltip={
                canLoad
                  ? undefined
                  : "Confirme explicitamente a gravação para habilitar a importação."
              }
              onClick={() => void executeLoad()}
            />
          </div>
        )}
      </Section>

      <div className="destination-actions">
        <Button
          label="Voltar à validação"
          variant="secondary"
          onClick={onBack}
        />
        <Button
          label="Continuar para resultado"
          variant="primary"
          onClick={onContinue}
        />
      </div>
    </div>
  );
}

function ContextItem({
  label,
  value,
  isCode = false,
}: {
  label: string;
  value: string;
  isCode?: boolean;
}) {
  return (
    <div className={isCode ? "destination-context-code" : undefined}>
      <Text as="p" type="supporting">
        {label}
      </Text>
      <Text as="p" type="label">
        {value}
      </Text>
    </div>
  );
}

function loadDisabledReason({
  apiAvailable,
  databaseAvailable,
  hasAcceptedRows,
}: {
  apiAvailable: boolean;
  databaseAvailable: boolean;
  hasAcceptedRows: boolean;
}): string | undefined {
  if (!apiAvailable) {
    return "A API do Waypoint está indisponível.";
  }
  if (!databaseAvailable) {
    return "Configure o PostgreSQL na API para habilitar esta opção.";
  }
  if (!hasAcceptedRows) {
    return "Não há registros válidos para importar.";
  }
  return undefined;
}
