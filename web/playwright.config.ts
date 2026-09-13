import { defineConfig } from "@playwright/test";
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:4173";
export default defineConfig({
  testDir: "e2e", timeout: 90_000, retries: 0,
  use: { baseURL, viewport: { width: 1440, height: 900 }, screenshot: "only-on-failure" },
  webServer: process.env.PLAYWRIGHT_BASE_URL ? undefined : { command: "npm run build && npm run preview -- --host 127.0.0.1 --port 4173", url: "http://127.0.0.1:4173", reuseExistingServer: true, timeout: 120_000 },
});
