import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  DEFAULT_PREFERENCES,
  PREFERENCES_STORAGE_KEY,
  type PreferencesStorage,
} from "./preferences";
import { PreferencesLauncher } from "./PreferencesPanel";
import { PreferencesProvider } from "./PreferencesProvider";
import { PreferencesTheme } from "./PreferencesTheme";

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

beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn(function (
    this: HTMLDialogElement,
  ) {
    this.setAttribute("open", "");
  });
  HTMLDialogElement.prototype.close = vi.fn(function (
    this: HTMLDialogElement,
  ) {
    this.removeAttribute("open");
  });
});

describe("PreferencesPanel", () => {
  it("opens an accessible Astryx dialog and saves every option", async () => {
    const storage = new MemoryStorage();
    renderLauncher(storage);

    const launcher = screen.getByRole("button", {
      name: "Personalizar interface",
    });
    fireEvent.click(launcher);

    expect(
      screen.getByRole("dialog", { name: "Aparência e acessibilidade" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radiogroup", { name: "Esquema de cores" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radiogroup", { name: "Densidade da interface" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radiogroup", { name: "Preferência de movimento" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: "Escuro" }));
    fireEvent.click(screen.getByRole("radio", { name: "Compacta" }));
    fireEvent.click(screen.getByRole("radio", { name: "Reduzir" }));

    await waitFor(() => {
      expect(screen.getByRole("radio", { name: "Escuro" })).toHaveAttribute(
        "aria-checked",
        "true",
      );
    });
    expect(
      JSON.parse(storage.getItem(PREFERENCES_STORAGE_KEY) ?? ""),
    ).toMatchObject({
      colorMode: "dark",
      density: "compact",
      motion: "reduced",
    });

    fireEvent.click(screen.getByRole("button", { name: "Concluir" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(launcher).toHaveAttribute("aria-expanded", "false");
  });

  it("restores the Waypoint defaults with a working action", async () => {
    const storage = new MemoryStorage();
    storage.setItem(
      PREFERENCES_STORAGE_KEY,
      JSON.stringify({
        ...DEFAULT_PREFERENCES,
        colorMode: "dark",
        density: "compact",
        motion: "reduced",
      }),
    );
    renderLauncher(storage);
    fireEvent.click(
      screen.getByRole("button", { name: "Personalizar interface" }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Restaurar padrão" }));

    await waitFor(() => {
      const colorGroup = screen.getByRole("radiogroup", {
        name: "Esquema de cores",
      });
      const motionGroup = screen.getByRole("radiogroup", {
        name: "Preferência de movimento",
      });
      expect(
        within(colorGroup).getByRole("radio", { name: "Sistema" }),
      ).toHaveAttribute("aria-checked", "true");
      expect(
        within(motionGroup).getByRole("radio", { name: "Sistema" }),
      ).toHaveAttribute("aria-checked", "true");
      expect(
        screen.getByRole("radio", { name: "Confortável" }),
      ).toHaveAttribute("aria-checked", "true");
    });
    expect(storage.getItem(PREFERENCES_STORAGE_KEY)).toBeNull();
  });
});

function renderLauncher(storage: PreferencesStorage) {
  return render(
    <PreferencesProvider storage={storage}>
      <PreferencesTheme>
        <PreferencesLauncher />
      </PreferencesTheme>
    </PreferencesProvider>,
  );
}
