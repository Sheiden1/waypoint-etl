import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "@astryxdesign/core/reset.css";
import "@astryxdesign/core/astryx.css";

import { App } from "./app/App";
import {
  PreferencesProvider,
  PreferencesTheme,
} from "./features/preferences";
import "./styles/global.css";

const root = document.getElementById("root");

if (root === null) {
  throw new Error("Elemento raiz da aplicação não encontrado.");
}

createRoot(root).render(
  <StrictMode>
    <PreferencesProvider>
      <PreferencesTheme>
        <App />
      </PreferencesTheme>
    </PreferencesProvider>
  </StrictMode>,
);
