import { expect, test } from "@playwright/test";

// One test, because the steps share the server's temporary gold directory.
test("a query is labelled from intent to the last judgement", async ({ page }) => {
  await page.goto("/label.html");
  await expect(page.locator("#synthetic-notice")).toContainText("Every listing here is synthetic");
  await expect(page.locator("#editor > h2")).toHaveText("Q001");

  await page.locator("[data-dimension=social][data-value=solitude]").click();
  await expect(page.locator("#status")).toHaveText("Q001 saved.");
  await page.getByLabel("Seeking").check();
  await expect(page.locator("#status")).toHaveText("Q001 saved.");

  await page.getByRole("button", { name: "Build the pool" }).click();
  await expect(page.locator("#status")).toHaveText(/^\d+ listings to judge\.$/);
  const size = await page.locator("#pool-list button").count();
  expect(size).toBeGreaterThanOrEqual(20);
  await expect(page.locator("#current-listing .synthetic")).toHaveText("Synthetic listing");

  for (let i = 0; i < size; i++) {
    const before = await page.locator("#judge-progress").textContent();
    await page.keyboard.press(i % 3 === 0 ? "1" : "0");
    await expect(page.locator("#judge-progress")).not.toHaveText(before!);
  }
  await expect(page.locator("#judge-progress")).toHaveText(`${size} of ${size} judged`);
  await expect(page.locator("#query-list .progress").first()).toHaveText("done");

  // Reloading reads the labels back from disk.
  await page.reload();
  await expect(page.locator("#judge-progress")).toHaveText(`${size} of ${size} judged`);
  await expect(page.locator("[data-value=solitude]")).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Seeking")).toBeChecked();
});

test("a new query can be added and opened", async ({ page }) => {
  await page.goto("/label.html");
  await page.getByLabel("Add a query, written the way a person would").fill("a weekend outdoors, walking");
  await page.getByRole("button", { name: "Add query" }).click();
  await expect(page.locator("#editor > h2")).toHaveText("Q002");
  await expect(page.locator("#query-text")).toHaveValue("a weekend outdoors, walking");
});
