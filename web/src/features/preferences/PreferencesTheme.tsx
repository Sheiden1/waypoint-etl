import { useMemo, type ReactNode } from "react";

import { Theme } from "@astryxdesign/core/theme";

import {
  createThemeCatalog,
  resolveThemeEntry,
  type CommunityThemeDefinition,
} from "../../theme/communityThemes";
import { usePreferences } from "./PreferencesContext";

interface PreferencesThemeProps {
  children: ReactNode;
  communityThemes?: readonly Readonly<CommunityThemeDefinition>[];
}

/**
 * Bridges persisted Waypoint preferences to Astryx.
 *
 * With no community themes it always resolves to the existing waypointTheme.
 * Unknown or removed ids also fall back to Waypoint without corrupting the
 * stored preference.
 */
export function PreferencesTheme({
  children,
  communityThemes = [],
}: PreferencesThemeProps) {
  const { preferences } = usePreferences();
  const catalog = useMemo(
    () => createThemeCatalog(communityThemes),
    [communityThemes],
  );
  const activeTheme = resolveThemeEntry(preferences.themeId, catalog);

  return (
    <Theme theme={activeTheme.theme} mode={preferences.colorMode}>
      {children}
    </Theme>
  );
}
