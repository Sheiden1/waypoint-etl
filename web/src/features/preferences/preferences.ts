import { WAYPOINT_THEME_ID } from "../../theme/communityThemes";

export const PREFERENCES_STORAGE_KEY = "waypoint.preferences";
export const LEGACY_THEME_STORAGE_KEY = "waypoint.theme";
export const PREFERENCES_VERSION = 1 as const;

export type ColorModePreference = "system" | "light" | "dark";
export type DensityPreference = "comfortable" | "compact";
export type MotionPreference = "system" | "reduced" | "full";
export type ResolvedMotion = Exclude<MotionPreference, "system">;

export interface UserPreferences {
  version: typeof PREFERENCES_VERSION;
  themeId: string;
  colorMode: ColorModePreference;
  density: DensityPreference;
  motion: MotionPreference;
}

export interface PreferencesStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export const DEFAULT_PREFERENCES: Readonly<UserPreferences> = Object.freeze({
  version: PREFERENCES_VERSION,
  themeId: WAYPOINT_THEME_ID,
  colorMode: "system",
  density: "comfortable",
  motion: "system",
});

export function getBrowserPreferencesStorage(): PreferencesStorage | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function loadPreferences(
  storage: PreferencesStorage | null = getBrowserPreferencesStorage(),
): UserPreferences {
  if (storage === null) {
    return copyDefaults();
  }

  const current = safeGet(storage, PREFERENCES_STORAGE_KEY);
  const parsed = parsePreferences(current);
  if (parsed !== null) {
    return parsed;
  }

  const legacyColorMode = safeGet(storage, LEGACY_THEME_STORAGE_KEY);
  if (isColorMode(legacyColorMode)) {
    const migrated = {
      ...copyDefaults(),
      colorMode: legacyColorMode,
    };
    if (savePreferences(migrated, storage)) {
      safeRemove(storage, LEGACY_THEME_STORAGE_KEY);
    }
    return migrated;
  }

  return copyDefaults();
}

export function parsePreferences(serialized: string | null): UserPreferences | null {
  if (serialized === null) {
    return null;
  }

  let input: unknown;
  try {
    input = JSON.parse(serialized);
  } catch {
    return null;
  }
  if (!isRecord(input) || input.version !== PREFERENCES_VERSION) {
    return null;
  }

  return {
    version: PREFERENCES_VERSION,
    themeId: isThemeId(input.themeId)
      ? input.themeId
      : DEFAULT_PREFERENCES.themeId,
    colorMode: isColorMode(input.colorMode)
      ? input.colorMode
      : DEFAULT_PREFERENCES.colorMode,
    density: isDensity(input.density)
      ? input.density
      : DEFAULT_PREFERENCES.density,
    motion: isMotion(input.motion)
      ? input.motion
      : DEFAULT_PREFERENCES.motion,
  };
}

export function savePreferences(
  preferences: UserPreferences,
  storage: PreferencesStorage | null = getBrowserPreferencesStorage(),
): boolean {
  if (storage === null) {
    return false;
  }
  try {
    storage.setItem(PREFERENCES_STORAGE_KEY, JSON.stringify(preferences));
    return true;
  } catch {
    return false;
  }
}

export function clearPreferences(
  storage: PreferencesStorage | null = getBrowserPreferencesStorage(),
): boolean {
  if (storage === null) {
    return false;
  }
  const removedCurrent = safeRemove(storage, PREFERENCES_STORAGE_KEY);
  const removedLegacy = safeRemove(storage, LEGACY_THEME_STORAGE_KEY);
  return removedCurrent && removedLegacy;
}

export function canPersistPreferences(
  storage: PreferencesStorage | null = getBrowserPreferencesStorage(),
): boolean {
  if (storage === null) {
    return false;
  }

  const probeKey = `${PREFERENCES_STORAGE_KEY}.probe`;
  try {
    storage.setItem(probeKey, "1");
    storage.removeItem(probeKey);
    return true;
  } catch {
    return false;
  }
}

export function resolveMotionPreference(
  preference: MotionPreference,
  systemReducesMotion: boolean,
): ResolvedMotion {
  return preference === "system"
    ? systemReducesMotion
      ? "reduced"
      : "full"
    : preference;
}

function copyDefaults(): UserPreferences {
  return { ...DEFAULT_PREFERENCES };
}

function safeGet(storage: PreferencesStorage, key: string): string | null {
  try {
    return storage.getItem(key);
  } catch {
    return null;
  }
}

function safeRemove(storage: PreferencesStorage, key: string): boolean {
  try {
    storage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isThemeId(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isColorMode(value: unknown): value is ColorModePreference {
  return value === "system" || value === "light" || value === "dark";
}

function isDensity(value: unknown): value is DensityPreference {
  return value === "comfortable" || value === "compact";
}

function isMotion(value: unknown): value is MotionPreference {
  return value === "system" || value === "reduced" || value === "full";
}
