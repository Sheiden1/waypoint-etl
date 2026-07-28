import { defineTheme } from "@astryxdesign/core/theme";
import { describe, expect, it } from "vitest";

import { waypointTheme } from "./waypointTheme";
import {
  createThemeCatalog,
  defineCommunityTheme,
  resolveThemeEntry,
  waypointThemeEntry,
} from "./communityThemes";

function makeCommunityTheme(
  id = "community.example.ocean",
  internalName = "community-example-ocean",
) {
  return {
    manifest: {
      schemaVersion: 1 as const,
      id,
      name: "Ocean",
      description: "Uma variação azul criada pela comunidade.",
      author: "Example contributor",
      license: "MIT",
      homepage: "https://example.com/ocean",
    },
    theme: defineTheme({
      name: internalName,
      extends: waypointTheme,
      tokens: {
        "--color-accent": ["#075985", "#7dd3fc"],
      },
    }),
  };
}

describe("community theme contract", () => {
  it("keeps the existing Waypoint theme as the catalog default", () => {
    const catalog = createThemeCatalog();

    expect(catalog).toEqual([waypointThemeEntry]);
    expect(catalog[0]?.theme).toBe(waypointTheme);
    expect(resolveThemeEntry("missing", catalog)).toBe(waypointThemeEntry);
  });

  it("registers a valid, namespaced Astryx theme", () => {
    const community = defineCommunityTheme(makeCommunityTheme());
    const catalog = createThemeCatalog([community]);

    expect(catalog).toHaveLength(2);
    expect(catalog[1]).toMatchObject({
      source: "community",
      manifest: { id: "community.example.ocean" },
    });
    expect(resolveThemeEntry("community.example.ocean", catalog)).toBe(
      catalog[1],
    );
  });

  it("rejects reserved, unsafe and duplicate ids", () => {
    expect(() =>
      defineCommunityTheme(makeCommunityTheme("waypoint")),
    ).toThrow(/id do tema/i);
    expect(() =>
      defineCommunityTheme(makeCommunityTheme("Ocean Theme")),
    ).toThrow(/id do tema/i);

    const first = makeCommunityTheme();
    const second = makeCommunityTheme(
      "community.example.ocean",
      "community-example-ocean-2",
    );
    expect(() => createThemeCatalog([first, second])).toThrow(/duplicado/i);
  });

  it("requires attribution and safe homepage metadata", () => {
    const missingAuthor = makeCommunityTheme();
    missingAuthor.manifest.author = "";
    expect(() => defineCommunityTheme(missingAuthor)).toThrow(/autor/i);

    const unsafeHomepage = makeCommunityTheme();
    unsafeHomepage.manifest.homepage = "javascript:alert(1)";
    expect(() => defineCommunityTheme(unsafeHomepage)).toThrow(/http/i);
  });
});
