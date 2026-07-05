import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Run sequentially to avoid DB lock in SQLite
  reporter: "line",
  use: {
    baseURL: "http://localhost:8000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "cd ../backend && .venv\\Scripts\\python -m uvicorn app.main:app --port 8000",
    url: "http://localhost:8000/api/v1/health",
    reuseExistingServer: true,
    timeout: 30000,
  },
});
