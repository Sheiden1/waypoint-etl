import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import {
  canPersistPreferences,
  clearPreferences,
  DEFAULT_PREFERENCES,
  getBrowserPreferencesStorage,
  LEGACY_THEME_STORAGE_KEY,
  loadPreferences,
  parsePreferences,
  PREFERENCES_STORAGE_KEY,
  resolveMotionPreference,
  savePreferences,
  type ColorModePreference,
  type DensityPreference,
  type MotionPreference,
  type PreferencesStorage,
  type ResolvedMotion,
  type UserPreferences,
} from "./preferences";
import {
  PreferencesContext,
  type PreferencesContextValue,
  type PreferencesPersistence,
} from "./PreferencesContext";
import "./preferences.css";

interface PreferencesProviderProps {
  children: ReactNode;
  storage?: PreferencesStorage | null;
}

const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";

export function PreferencesProvider({
  children,
  storage: storageOverride,
}: PreferencesProviderProps) {
  const storage = useMemo(
    () =>
      storageOverride === undefined
        ? getBrowserPreferencesStorage()
        : storageOverride,
    [storageOverride],
  );
  const [preferences, setPreferences] = useState<UserPreferences>(() =>
    loadPreferences(storage),
  );
  const preferencesRef = useRef(preferences);
  const [persistence, setPersistence] = useState<PreferencesPersistence>(() =>
    canPersistPreferences(storage) ? "saved" : "unavailable",
  );
  const [resolvedMotion, setResolvedMotion] = useState<ResolvedMotion>(() =>
    resolveMotionPreference(
      preferences.motion,
      systemPrefersReducedMotion(),
    ),
  );

  const commit = useCallback(
    (next: UserPreferences) => {
      preferencesRef.current = next;
      setPreferences(next);
      setPersistence(savePreferences(next, storage) ? "saved" : "unavailable");
    },
    [storage],
  );

  const patch = useCallback(
    (next: Partial<Omit<UserPreferences, "version">>) => {
      commit({
        ...preferencesRef.current,
        ...next,
        version: DEFAULT_PREFERENCES.version,
      });
    },
    [commit],
  );

  const setThemeId = useCallback(
    (themeId: string) => {
      if (themeId.trim().length > 0) {
        patch({ themeId });
      }
    },
    [patch],
  );
  const setColorMode = useCallback(
    (colorMode: ColorModePreference) => {
      patch({ colorMode });
    },
    [patch],
  );
  const setDensity = useCallback(
    (density: DensityPreference) => {
      patch({ density });
    },
    [patch],
  );
  const setMotion = useCallback(
    (motion: MotionPreference) => {
      patch({ motion });
    },
    [patch],
  );
  const resetPreferences = useCallback(() => {
    const next = { ...DEFAULT_PREFERENCES };
    preferencesRef.current = next;
    setPreferences(next);
    setPersistence(clearPreferences(storage) ? "saved" : "unavailable");
  }, [storage]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const syncPreferences = (event: StorageEvent) => {
      if (
        event.key !== PREFERENCES_STORAGE_KEY &&
        event.key !== LEGACY_THEME_STORAGE_KEY &&
        event.key !== null
      ) {
        return;
      }

      const next =
        event.key === PREFERENCES_STORAGE_KEY
          ? parsePreferences(event.newValue) ?? { ...DEFAULT_PREFERENCES }
          : loadPreferences(storage);
      preferencesRef.current = next;
      setPreferences(next);
    };

    window.addEventListener("storage", syncPreferences);
    return () => {
      window.removeEventListener("storage", syncPreferences);
    };
  }, [storage]);

  useEffect(() => {
    if (typeof document === "undefined") {
      return;
    }

    const root = document.documentElement;
    root.dataset.waypointTheme = preferences.themeId;
    root.dataset.waypointColorMode = preferences.colorMode;
    root.dataset.waypointDensity = preferences.density;
    root.dataset.waypointMotionPreference = preferences.motion;

    const mediaQuery =
      typeof window === "undefined"
        ? null
        : window.matchMedia(REDUCED_MOTION_QUERY);
    const applyMotion = () => {
      const next = resolveMotionPreference(
        preferences.motion,
        mediaQuery?.matches ?? false,
      );
      root.dataset.waypointMotion = next;
      setResolvedMotion(next);
    };

    applyMotion();
    mediaQuery?.addEventListener("change", applyMotion);
    return () => {
      mediaQuery?.removeEventListener("change", applyMotion);
    };
  }, [preferences]);

  useEffect(
    () => () => {
      if (typeof document === "undefined") {
        return;
      }
      const root = document.documentElement;
      delete root.dataset.waypointTheme;
      delete root.dataset.waypointColorMode;
      delete root.dataset.waypointDensity;
      delete root.dataset.waypointMotionPreference;
      delete root.dataset.waypointMotion;
    },
    [],
  );

  const value = useMemo<PreferencesContextValue>(
    () => ({
      preferences,
      resolvedMotion,
      persistence,
      setThemeId,
      setColorMode,
      setDensity,
      setMotion,
      resetPreferences,
    }),
    [
      preferences,
      resolvedMotion,
      persistence,
      setThemeId,
      setColorMode,
      setDensity,
      setMotion,
      resetPreferences,
    ],
  );

  return (
    <PreferencesContext.Provider value={value}>
      {children}
    </PreferencesContext.Provider>
  );
}

function systemPrefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    window.matchMedia(REDUCED_MOTION_QUERY).matches
  );
}
