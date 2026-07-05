import { test, expect } from "@playwright/test";

test.describe("Pocket Single-Deploy E2E Tests", () => {
  test("should render the dashboard welcome screen", async ({ page }) => {
    // 1. Load the single-deploy host root
    await page.goto("/");

    // 2. Verify the welcome header is present
    await expect(page.locator("h2")).toContainText("Welcome to");
    await expect(page.locator("p")).toContainText("Manage, version, and optimize your prompts");
  });

  test("should navigate to contexts page and render lists", async ({ page }) => {
    // 1. Load root
    await page.goto("/");

    // 2. Click on the Contexts navigation link (usually in sidebar/header or navigate directly)
    await page.goto("/contexts");

    // 3. Verify context page header is loaded
    await expect(page.locator("h1, h2, h3")).toContainText("Contexts");
  });
});
