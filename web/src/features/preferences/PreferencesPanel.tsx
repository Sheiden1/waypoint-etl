import { useState } from "react";

import { Button } from "@astryxdesign/core/Button";
import { Dialog, DialogHeader } from "@astryxdesign/core/Dialog";
import {
  Layout,
  LayoutContent,
  LayoutFooter,
} from "@astryxdesign/core/Layout";
import {
  SegmentedControl,
  SegmentedControlItem,
} from "@astryxdesign/core/SegmentedControl";
import { Text } from "@astryxdesign/core/Text";

import {
  type ColorModePreference,
  type DensityPreference,
  type MotionPreference,
} from "./preferences";
import { usePreferences } from "./PreferencesContext";

interface PreferencesPanelProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  isInline?: boolean;
}

interface PreferencesLauncherProps {
  label?: string;
  size?: "sm" | "md" | "lg";
  variant?: "primary" | "secondary" | "ghost";
  isInlinePanel?: boolean;
}

export function PreferencesPanel({
  isOpen,
  onOpenChange,
  isInline = false,
}: PreferencesPanelProps) {
  const {
    preferences,
    resolvedMotion,
    persistence,
    setColorMode,
    setDensity,
    setMotion,
    resetPreferences,
  } = usePreferences();

  return (
    <Dialog
      isOpen={isOpen}
      isInline={isInline}
      onOpenChange={onOpenChange}
      purpose="info"
      width={560}
      maxHeight="min(760px, 90vh)"
      className="waypoint-preferences-dialog"
    >
      <Layout
        height="auto"
        header={
          <DialogHeader
            title="Aparência e acessibilidade"
            subtitle="Ajustes salvos somente neste navegador."
            onOpenChange={onOpenChange}
            hasDivider
          />
        }
        content={
          <LayoutContent isScrollable>
            <div className="waypoint-preferences-fields">
              <PreferenceField
                title="Esquema de cores"
                description="Use as cores do sistema ou fixe uma aparência."
              >
                <SegmentedControl
                  value={preferences.colorMode}
                  onChange={(value) =>
                    setColorMode(value as ColorModePreference)
                  }
                  label="Esquema de cores"
                  layout="fill"
                >
                  <SegmentedControlItem value="system" label="Sistema" />
                  <SegmentedControlItem value="light" label="Claro" />
                  <SegmentedControlItem value="dark" label="Escuro" />
                </SegmentedControl>
              </PreferenceField>

              <PreferenceField
                title="Densidade"
                description="Escolha quanto conteúdo cabe em cada tela."
              >
                <SegmentedControl
                  value={preferences.density}
                  onChange={(value) =>
                    setDensity(value as DensityPreference)
                  }
                  label="Densidade da interface"
                  layout="fill"
                >
                  <SegmentedControlItem
                    value="comfortable"
                    label="Confortável"
                  />
                  <SegmentedControlItem value="compact" label="Compacta" />
                </SegmentedControl>
              </PreferenceField>

              <PreferenceField
                title="Movimento"
                description={`Animações em uso: ${
                  resolvedMotion === "reduced" ? "reduzidas" : "completas"
                }.`}
              >
                <SegmentedControl
                  value={preferences.motion}
                  onChange={(value) => setMotion(value as MotionPreference)}
                  label="Preferência de movimento"
                  layout="fill"
                >
                  <SegmentedControlItem value="system" label="Sistema" />
                  <SegmentedControlItem value="reduced" label="Reduzir" />
                  <SegmentedControlItem value="full" label="Completo" />
                </SegmentedControl>
              </PreferenceField>

              <Text
                as="p"
                type="supporting"
                color={persistence === "saved" ? "secondary" : "accent"}
                role="status"
                aria-live="polite"
              >
                {persistence === "saved"
                  ? "Preferências salvas neste navegador."
                  : "O navegador bloqueou o armazenamento. Os ajustes valem somente nesta sessão."}
              </Text>
            </div>
          </LayoutContent>
        }
        footer={
          <LayoutFooter hasDivider>
            <div className="waypoint-preferences-actions">
              <Button
                label="Restaurar padrão"
                variant="ghost"
                onClick={resetPreferences}
              />
              <Button
                label="Concluir"
                variant="primary"
                onClick={() => onOpenChange(false)}
              />
            </div>
          </LayoutFooter>
        }
      />
    </Dialog>
  );
}

export function PreferencesLauncher({
  label = "Personalizar interface",
  size = "sm",
  variant = "ghost",
  isInlinePanel = false,
}: PreferencesLauncherProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button
        label={label}
        size={size}
        variant={variant}
        onClick={() => setIsOpen(true)}
        aria-haspopup="dialog"
        aria-expanded={isOpen}
      />
      <PreferencesPanel
        isOpen={isOpen}
        isInline={isInlinePanel}
        onOpenChange={setIsOpen}
      />
    </>
  );
}

function PreferenceField({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="waypoint-preferences-field">
      <div>
        <Text as="h3" type="label" weight="semibold">
          {title}
        </Text>
        <Text as="p" type="supporting" color="secondary">
          {description}
        </Text>
      </div>
      {children}
    </section>
  );
}
