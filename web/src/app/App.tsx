import { useEffect, useState } from "react";

import { AppShell } from "@astryxdesign/core/AppShell";
import { Heading } from "@astryxdesign/core/Heading";
import { StatusDot } from "@astryxdesign/core/StatusDot";
import { Text } from "@astryxdesign/core/Text";
import { TopNav } from "@astryxdesign/core/TopNav";

import { DestinationWorkspace } from "../features/destination/DestinationWorkspace";
import { ResultWorkspace } from "../features/destination/ResultWorkspace";
import { InspectionWorkspace } from "../features/inspection/InspectionWorkspace";
import {
  MappingWorkspace,
  type MappingDraft,
} from "../features/mapping/MappingWorkspace";
import { PreferencesLauncher } from "../features/preferences";
import { ValidationWorkspace } from "../features/validation/ValidationWorkspace";
import {
  type DryRunResult,
  getHealth,
  type HealthResponse,
  type SourcePreview,
} from "../lib/api";

const JOURNEY_STEPS = [
  "Origem",
  "Mapeamento",
  "Validação",
  "Destino",
  "Resultado",
] as const;
const PAGE_COPY = [
  {
    eyebrow: "JORNADA WEB · FASE 1",
    title: "Encontre o caminho dos seus dados.",
    description:
      "Inspecione uma origem legada sem gravar o arquivo. O Waypoint mostra sua estrutura antes de qualquer transformação.",
  },
  {
    eyebrow: "JORNADA WEB · FASE 2",
    title: "Defina o destino de cada coluna.",
    description:
      "Associe os campos encontrados ao schema canônico e gere um template De/Para reutilizável.",
  },
  {
    eyebrow: "JORNADA WEB · FASE 3",
    title: "Meça a qualidade antes de migrar.",
    description:
      "Execute o pipeline em dry-run, revise rejeições e duplicidades e acompanhe cada transformação.",
  },
  {
    eyebrow: "JORNADA WEB · FASE 4",
    title: "Escolha o próximo destino.",
    description:
      "Baixe os relatórios da execução ou confirme uma carga opcional no PostgreSQL, sem perder a rastreabilidade.",
  },
  {
    eyebrow: "JORNADA WEB · FASE 5",
    title: "Feche esta jornada com clareza.",
    description:
      "Revise o resultado final, guarde os artefatos temporários e comece outra exploração quando quiser.",
  },
] as const;

interface JourneySource {
  file: File;
  preview: SourcePreview;
}

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthFailed, setHealthFailed] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [journeySource, setJourneySource] = useState<JourneySource | null>(null);
  const [mappingDraft, setMappingDraft] = useState<MappingDraft | null>(null);
  const [validationResult, setValidationResult] =
    useState<DryRunResult | null>(null);
  const [loadResult, setLoadResult] = useState<DryRunResult | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal)
      .then((response) => {
        setHealth(response);
        setHealthFailed(false);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setHealthFailed(true);
        }
      });
    return () => {
      controller.abort();
    };
  }, []);

  const pageCopy = PAGE_COPY[currentStep] ?? PAGE_COPY[0];

  const continueToMapping = (file: File, preview: SourcePreview) => {
    setJourneySource({ file, preview });
    setMappingDraft(null);
    setValidationResult(null);
    setLoadResult(null);
    setCurrentStep(1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const returnToSource = () => {
    setCurrentStep(0);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const continueToValidation = (draft: MappingDraft) => {
    if (draft.content !== mappingDraft?.content) {
      setValidationResult(null);
      setLoadResult(null);
    }
    setMappingDraft(draft);
    setCurrentStep(2);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const returnToMapping = () => {
    setCurrentStep(1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const continueToDestination = () => {
    setCurrentStep(3);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleValidationResult = (result: DryRunResult) => {
    setValidationResult(result);
    setLoadResult(null);
  };

  const returnToValidation = () => {
    setCurrentStep(2);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const continueToResult = () => {
    setCurrentStep(4);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const returnToDestination = () => {
    setCurrentStep(3);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const restartJourney = () => {
    setJourneySource(null);
    setMappingDraft(null);
    setValidationResult(null);
    setLoadResult(null);
    setCurrentStep(0);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <AppShell
      height="auto"
      variant="section"
      contentPadding={0}
      topNav={
        <TopNav
          label="Navegação principal"
          heading={
            <div className="brand-lockup" aria-label="Waypoint">
              <span className="brand-mark" aria-hidden="true">
                W
              </span>
              <span>
                <Text as="span" type="label" weight="bold">
                  Waypoint
                </Text>
                <Text as="span" type="supporting" display="block">
                  Data migration toolkit
                </Text>
              </span>
            </div>
          }
          endContent={
            <div className="top-nav-actions">
              <div className="api-status">
                <StatusDot
                  variant={healthFailed ? "error" : health ? "success" : "neutral"}
                  label={
                    healthFailed
                      ? "API indisponível"
                      : health
                        ? "API disponível"
                        : "Verificando API"
                  }
                  isPulsing={health === null && !healthFailed}
                />
                <Text type="supporting">
                  {healthFailed
                    ? "API indisponível"
                    : health
                      ? `API ${health.version}`
                      : "Conectando"}
                </Text>
              </div>
              <PreferencesLauncher />
            </div>
          }
        />
      }
    >
      <main className="app-content">
        <header className="page-heading">
          <Text as="p" type="label" color="accent">
            {pageCopy.eyebrow}
          </Text>
          <Heading level={1} type="display-3" textWrap="balance">
            {pageCopy.title}
          </Heading>
          <Text as="p" type="large" color="secondary">
            {pageCopy.description}
          </Text>
        </header>

        <ol className="journey-steps" aria-label="Etapas da migração">
          {JOURNEY_STEPS.map((step, index) => {
            const state =
              index === currentStep
                ? "is-current"
                : index < currentStep
                  ? "is-complete"
                  : "is-upcoming";
            return (
              <li
                className={`journey-step ${state}`}
                key={step}
                aria-current={index === currentStep ? "step" : undefined}
              >
                <span className="journey-number">{index + 1}</span>
                <span>{step}</span>
              </li>
            );
          })}
        </ol>

        {currentStep === 0 ? (
          <InspectionWorkspace
            maxUploadMb={health?.max_upload_mb ?? 25}
            ocrAvailable={health?.features.ocr ?? false}
            apiAvailable={!healthFailed}
            initialFile={journeySource?.file}
            initialPreview={journeySource?.preview}
            onContinue={continueToMapping}
          />
        ) : currentStep === 1 && journeySource ? (
          <MappingWorkspace
            file={journeySource.file}
            preview={journeySource.preview}
            apiAvailable={!healthFailed}
            initialDraft={mappingDraft}
            onBack={returnToSource}
            onContinue={continueToValidation}
          />
        ) : currentStep === 2 && journeySource && mappingDraft ? (
          <ValidationWorkspace
            file={journeySource.file}
            mapping={mappingDraft}
            apiAvailable={!healthFailed}
            initialResult={validationResult}
            onBack={returnToMapping}
            onContinue={continueToDestination}
            onResult={handleValidationResult}
          />
        ) : currentStep === 3 &&
          journeySource &&
          mappingDraft &&
          validationResult ? (
          <DestinationWorkspace
            file={journeySource.file}
            mapping={mappingDraft}
            validationResult={validationResult}
            apiAvailable={!healthFailed}
            databaseAvailable={health?.features.database ?? false}
            initialLoadResult={loadResult}
            onBack={returnToValidation}
            onContinue={continueToResult}
            onLoadResult={setLoadResult}
          />
        ) : currentStep === 4 && validationResult ? (
          <ResultWorkspace
            validationResult={validationResult}
            loadResult={loadResult}
            onBack={returnToDestination}
            onRestart={restartJourney}
          />
        ) : null}
      </main>
    </AppShell>
  );
}
