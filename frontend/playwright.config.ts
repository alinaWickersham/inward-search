import { defineConfig } from "@playwright/test";

const PORT = 8765;

export default defineConfig({
  testDir: "e2e",
  use: { baseURL: `http://127.0.0.1:${PORT}` },
  webServer: {
    // Run from the repo root so `tests.e2e_server` is importable.
    command: `python -m uvicorn --factory tests.e2e_server:app --port ${PORT}`,
    cwd: "..",
    url: `http://127.0.0.1:${PORT}`,
    reuseExistingServer: false,
  },
});
