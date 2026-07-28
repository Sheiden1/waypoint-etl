import {
  isDefinedTheme,
  type DefinedTheme,
} from "@astryxdesign/core/theme";

import { waypointTheme } from "./waypointTheme";

export const COMMUNITY_THEME_SCHEMA_VERSION = 1 as const;
export const WAYPOINT_THEME_ID = "waypoint";

/**
 * Metadata required from a community theme.
 *
 * Theme packages remain plain TypeScript modules: they export their Astryx
 * `DefinedTheme` together with this manifest. The id is persisted locally, so
 * it must stay stable between releases. License and author are mandatory to
 * keep redistributed themes auditable in an open-source installation.
 */
export interface CommunityThemeManifest {
  schemaVersion: typeof COMMUNITY_THEME_SCHEMA_VERSION;
  id: string;
  name: string;
  description: string;
  author: string;
  license: string;
  homepage?: string;
}

export interface CommunityThemeDefinition {
  manifest: CommunityThemeManifest;
  theme: DefinedTheme;
}

export interface ThemeCatalogEntry extends CommunityThemeDefinition {
  source: "built-in" | "community";
}

export const waypointThemeEntry: ThemeCatalogEntry = Object.freeze({
  source: "built-in",
  manifest: Object.freeze({
    schemaVersion: COMMUNITY_THEME_SCHEMA_VERSION,
    id: WAYPOINT_THEME_ID,
    name: "Waypoint",
    description: "Tema oficial e padrão do Waypoint.",
    author: "Waypoint contributors",
    license: "MIT",
  }),
  theme: waypointTheme,
});

/**
 * Validates and freezes a community theme at the module boundary.
 *
 * Use a namespaced lowercase id such as `community.acme.ocean`. A community
 * entry cannot replace the built-in Waypoint id, but may extend waypointTheme
 * when it calls Astryx `defineTheme`.
 */
export function defineCommunityTheme(
  definition: CommunityThemeDefinition,
): Readonly<CommunityThemeDefinition> {
  const { manifest, theme } = definition;

  if (manifest.schemaVersion !== COMMUNITY_THEME_SCHEMA_VERSION) {
    throw new Error(
      `Versão de tema comunitário incompatível: ${String(manifest.schemaVersion)}.`,
    );
  }
  if (!isValidThemeId(manifest.id) || manifest.id === WAYPOINT_THEME_ID) {
    throw new Error(
      "O id do tema deve ser estável, minúsculo, separado por pontos e diferente de waypoint.",
    );
  }
  if (
    !hasText(manifest.name) ||
    !hasText(manifest.description) ||
    !hasText(manifest.author) ||
    !hasText(manifest.license)
  ) {
    throw new Error(
      "Nome, descrição, autor e licença são obrigatórios em temas comunitários.",
    );
  }
  if (manifest.homepage !== undefined && !isSafeHomepage(manifest.homepage)) {
    throw new Error("A homepage do tema deve usar uma URL http ou https válida.");
  }
  if (!isDefinedTheme(theme)) {
    throw new Error("O tema deve ser criado com defineTheme do Astryx.");
  }
  if (theme.name === waypointTheme.name) {
    throw new Error("O nome interno do tema comunitário deve ser único.");
  }

  return Object.freeze({
    manifest: Object.freeze({ ...manifest }),
    theme,
  });
}

export function createThemeCatalog(
  communityThemes: readonly Readonly<CommunityThemeDefinition>[] = [],
): readonly ThemeCatalogEntry[] {
  const entries: ThemeCatalogEntry[] = [waypointThemeEntry];
  const ids = new Set([WAYPOINT_THEME_ID]);
  const internalNames = new Set([waypointTheme.name]);

  for (const candidate of communityThemes) {
    const theme = defineCommunityTheme(candidate);
    if (ids.has(theme.manifest.id)) {
      throw new Error(`Id de tema duplicado: ${theme.manifest.id}.`);
    }
    if (internalNames.has(theme.theme.name)) {
      throw new Error(`Nome interno de tema duplicado: ${theme.theme.name}.`);
    }
    ids.add(theme.manifest.id);
    internalNames.add(theme.theme.name);
    entries.push({
      ...theme,
      source: "community",
    });
  }

  return Object.freeze(entries);
}

export function resolveThemeEntry(
  themeId: string,
  catalog: readonly ThemeCatalogEntry[],
): ThemeCatalogEntry {
  return (
    catalog.find((entry) => entry.manifest.id === themeId) ??
    waypointThemeEntry
  );
}

function isValidThemeId(value: string): boolean {
  return (
    value.startsWith("community.") &&
    /^[a-z0-9]+(?:[.-][a-z0-9]+)*$/.test(value)
  );
}

function hasText(value: string): boolean {
  return value.trim().length > 0;
}

function isSafeHomepage(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}
