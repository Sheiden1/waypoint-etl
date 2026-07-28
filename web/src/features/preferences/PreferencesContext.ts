import { createContext, useContext } from "react";

import {
  type ColorModePreference,
  type DensityPreference,
  type MotionPreference,
  type ResolvedMotion,
  type UserPreferences,
} from "./preferences";

export type PreferencesPersistence = "saved" | "unavailable";

export interface PreferencesContextValue {
  preferences: UserPreferences;
  resolvedMotion: ResolvedMotion;
  persistence: PreferencesPersistence;
  setThemeId: (themeId: string) => void;
  setColorMode: (colorMode: ColorModePreference) => void;
  setDensity: (density: DensityPreference) => void;
  setMotion: (motion: MotionPreference) => void;
  resetPreferences: () => void;
}

export const PreferencesContext =
  createContext<PreferencesContextValue | null>(null);

export function usePreferences(): PreferencesContextValue {
  const context = useContext(PreferencesContext);
  if (context === null) {
    throw new Error(
      "usePreferences deve ser usado dentro de PreferencesProvider.",
    );
  }
  return context;
}
