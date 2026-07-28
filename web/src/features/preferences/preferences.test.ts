import { describe, expect, it, vi } from "vitest";

import {
  canPersistPreferences,
  clearPreferences,
  DEFAULT_PREFERENCES,
  LEGACY_THEME_STORAGE_KEY,
  loadPreferences,
  parsePreferences,
  PREFERENCES_STORAGE_KEY,
  resolveMotionPreference,
  savePreferences,
  type PreferencesStorage,
} from "./preferences";

class MemoryStorage implements PreferencesStorage {
  readonly values = new Map<string, string>();

  getItem(key: string) {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string) {
    this.values.set(key, value);
  }

  removeItem(key: string) {
    this.values.delete(key);
  }
}

describe("preferences persistence", () => {
  it("returns independent defaults without browser storage", () => {
    const first = loadPreferences(null);
    const second = loadPreferences(null);

    expect(first).toEqual(DEFAULT_PREFERENCES);
    expect(first).not.toBe(DEFAULT_PREFERENCES);
    expect(second).not.toBe(first);
  });

  it("normalizes invalid fields from a versioned payload", () => {
    const parsed = parsePreferences(
      JSON.stringify({
        version: 1,
        themeId: "",
        colorMode: "sepia",
        density: "compact",
        motion: "reduced",
      }),
    );

    expect(parsed).toEqual({
      ...DEFAULT_PREFERENCES,
      density: "compact",
      motion: "reduced",
    });
  });

  it("rejects malformed JSON and unknown schema versions", () => {
    expect(parsePreferences("{oops")).toBeNull();
    expect(parsePreferences('{"version":2}')).toBeNull();
  });

  it("migrates the former theme-only preference", () => {
    const storage = new MemoryStorage();
    storage.setItem(LEGACY_THEME_STORAGE_KEY, "dark");

    const preferences = loadPreferences(storage);

    expect(preferences.colorMode).toBe("dark");
    expect(storage.getItem(LEGACY_THEME_STORAGE_KEY)).toBeNull();
    expect(
      JSON.parse(storage.getItem(PREFERENCES_STORAGE_KEY) ?? ""),
    ).toEqual(preferences);
  });

  it("saves and clears the complete preference object", () => {
    const storage = new MemoryStorage();
    const preferences = {
      ...DEFAULT_PREFERENCES,
      colorMode: "light" as const,
      density: "compact" as const,
    };

    expect(savePreferences(preferences, storage)).toBe(true);
    expect(loadPreferences(storage)).toEqual(preferences);
    expect(clearPreferences(storage)).toBe(true);
    expect(storage.values.size).toBe(0);
  });

  it("survives storage implementations that throw", () => {
    const storage: PreferencesStorage = {
      getItem: vi.fn(() => {
        throw new Error("blocked");
      }),
      setItem: vi.fn(() => {
        throw new Error("blocked");
      }),
      removeItem: vi.fn(() => {
        throw new Error("blocked");
      }),
    };

    expect(loadPreferences(storage)).toEqual(DEFAULT_PREFERENCES);
    expect(savePreferences({ ...DEFAULT_PREFERENCES }, storage)).toBe(false);
    expect(clearPreferences(storage)).toBe(false);
    expect(canPersistPreferences(storage)).toBe(false);
  });

  it("resolves system motion without overriding explicit choices", () => {
    expect(resolveMotionPreference("system", true)).toBe("reduced");
    expect(resolveMotionPreference("system", false)).toBe("full");
    expect(resolveMotionPreference("full", true)).toBe("full");
    expect(resolveMotionPreference("reduced", false)).toBe("reduced");
  });
});
