import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  DEFAULT_PREFERENCES,
  PREFERENCES_STORAGE_KEY,
  type PreferencesStorage,
} from "./preferences";
import {
  usePreferences,
} from "./PreferencesContext";
import { PreferencesProvider } from "./PreferencesProvider";

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

function PreferencesProbe() {
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
    <div>
      <output data-testid="snapshot">
        {JSON.stringify({ preferences, resolvedMotion, persistence })}
      </output>
      <button type="button" onClick={() => setColorMode("dark")}>
        dark
      </button>
      <button type="button" onClick={() => setDensity("compact")}>
        compact
      </button>
      <button type="button" onClick={() => setMotion("reduced")}>
        reduced
      </button>
      <button type="button" onClick={resetPreferences}>
        reset
      </button>
    </div>
  );
}

describe("PreferencesProvider", () => {
  it("persists changes and applies the document contract", async () => {
    const storage = new MemoryStorage();
    render(
      <PreferencesProvider storage={storage}>
        <PreferencesProbe />
      </PreferencesProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "dark" }));
    fireEvent.click(screen.getByRole("button", { name: "compact" }));
    fireEvent.click(screen.getByRole("button", { name: "reduced" }));

    await waitFor(() => {
      expect(document.documentElement.dataset.waypointColorMode).toBe("dark");
      expect(document.documentElement.dataset.waypointDensity).toBe("compact");
      expect(document.documentElement.dataset.waypointMotion).toBe("reduced");
    });
    expect(
      JSON.parse(storage.getItem(PREFERENCES_STORAGE_KEY) ?? ""),
    ).toMatchObject({
      colorMode: "dark",
      density: "compact",
      motion: "reduced",
    });
  });

  it("resets state and removes persisted preferences", async () => {
    const storage = new MemoryStorage();
    storage.setItem(
      PREFERENCES_STORAGE_KEY,
      JSON.stringify({
        ...DEFAULT_PREFERENCES,
        colorMode: "dark",
        density: "compact",
      }),
    );
    render(
      <PreferencesProvider storage={storage}>
        <PreferencesProbe />
      </PreferencesProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "reset" }));

    await waitFor(() => {
      expect(screen.getByTestId("snapshot")).toHaveTextContent(
        '"density":"comfortable"',
      );
    });
    expect(storage.getItem(PREFERENCES_STORAGE_KEY)).toBeNull();
  });

  it("synchronizes a preference written by another browser tab", async () => {
    const storage = new MemoryStorage();
    render(
      <PreferencesProvider storage={storage}>
        <PreferencesProbe />
      </PreferencesProvider>,
    );
    const next = {
      ...DEFAULT_PREFERENCES,
      colorMode: "light" as const,
      density: "compact" as const,
    };

    act(() => {
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: PREFERENCES_STORAGE_KEY,
          newValue: JSON.stringify(next),
        }),
      );
    });

    await waitFor(() => {
      expect(screen.getByTestId("snapshot")).toHaveTextContent(
        '"colorMode":"light"',
      );
      expect(screen.getByTestId("snapshot")).toHaveTextContent(
        '"density":"compact"',
      );
    });
  });
});
