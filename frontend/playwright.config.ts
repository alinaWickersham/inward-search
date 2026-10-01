import { defineConfig } from "@playwright/test";

const SEARCH_PORT = 8765;
const LABEL_PORT = 8766;

// Both servers index the same test database on startup, so tests run one at a time.
export default defineConfig({
  testDir: "e2e",
  workers: 1,
  projects: [
    { name: "search", testMatch: "search.spec.ts", use: { baseURL: `http://127.0.0.1:${SEARCH_PORT}` } },
    { name: "label", testMatch: "label.spec.ts", use: { baseURL: `http://127.0.0.1:${LABEL_PORT}` } },
  ],
  webServer: [
    {
      // Run from the repo root so `tests.e2e_server` is importable.
      command: `python -m uvicorn --factory tests.e2e_server:app --port ${SEARCH_PORT}`,
      cwd: "..",
      url: `http://127.0.0.1:${SEARCH_PORT}`,
      reuseExistingServer: false,
    },
    {
      command: `python -m uvicorn --factory tests.e2e_server:label_app --port ${LABEL_PORT}`,
      cwd: "..",
      url: `http://127.0.0.1:${LABEL_PORT}/label.html`,
      reuseExistingServer: false,
    },
  ],
});
