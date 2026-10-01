import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test("states that every listing is synthetic before any search", async ({ page }) => {
  await expect(page.locator("#synthetic-notice")).toContainText("Every listing here is synthetic");
});

test("a described state returns ten ranked synthetic listings", async ({ page }) => {
  await page.getByLabel("Describe what you are looking for").fill("a quiet weekend in silence");
  await page.getByRole("button", { name: "Search" }).click();

  await expect(page.locator("#status")).toHaveText(
    "10 listings, ranked by similarity to your description.",
  );
  const cards = page.locator("article.result");
  await expect(cards).toHaveCount(10);
  await expect(cards.locator(".synthetic")).toHaveCount(10);
  await expect(cards.first().locator(".meta")).toHaveText(/^Rank 1 · similarity -?\d\.\d{3}$/);
  await expect(cards.first().locator(".dimensions li")).toHaveCount(9);
});

test("the description is posted in the body, not the URL", async ({ page }) => {
  const request = page.waitForRequest("**/api/search");
  await page.getByLabel("Describe what you are looking for").fill("running on empty");
  await page.getByRole("button", { name: "Search" }).click();
  const sent = await request;
  expect(sent.method()).toBe("POST");
  expect(sent.url()).not.toContain("running");
  expect(sent.postDataJSON()).toEqual({ query: "running on empty", k: 10 });
});

test("a blank description asks for one and shows no results", async ({ page }) => {
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.locator("#status")).toHaveText("Describe what you are looking for first.");
  await expect(page.locator("article.result")).toHaveCount(0);
});
