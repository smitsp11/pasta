import { expect, test } from "@playwright/test";

test("the full show plays through and each stage renders", async ({ page }) => {
  await page.goto("/?speed=6");
  await expect(page.getByText("Send your customers in first.")).toBeVisible();
  await page.screenshot({ path: "e2e/screens/01-input.png" });
  await page.getByRole("textbox").fill("https://northwindoutfitters.com");
  await page.getByRole("button", { name: "RUN IRIS →" }).click();

  await expect(page.getByText("Learning your customers and your site.")).toBeVisible();
  await expect(page.getByText("checkout resets on my phone every time")).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: "e2e/screens/02-learning.png", fullPage: false });

  await expect(page.getByText("Here's who we'll send.")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("MATCHED PAIR · DEVICE")).toBeVisible();
  await page.screenshot({ path: "e2e/screens/03-brief.png" });

  await expect(page.getByText("Watch them try.")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("RUNNING", { exact: true }).first()).toBeVisible();
  await page.screenshot({ path: "e2e/screens/04-swarm-running.png" });
  await expect(page.getByText("TOOLING ERROR · EXCLUDED")).toBeVisible({ timeout: 40_000 });

  await expect(page.getByText("What broke, for whom, and why.")).toBeVisible({ timeout: 40_000 });
  await expect(page.getByText("IRIS MEASURED · 8 real agents, 3 journeys")).toBeVisible();
  await expect(page.getByText("58", { exact: true })).toBeVisible({ timeout: 5_000 });
  await page.screenshot({ path: "e2e/screens/05-report.png", fullPage: true });
  await expect(page.getByText("REPORT", { exact: true })).toHaveCSS("color", "rgb(255, 90, 31)");
});

test("seek to a stage renders it instantly (rehearsal / screenshot mode)", async ({ page }) => {
  await page.goto("/?stage=run");
  await expect(page.getByText("Here's who we'll send.")).toBeVisible();
  await expect(page.getByText("Watch them try.")).toHaveCount(0);   // seeking stops at the 'run' marker; feeds arrive after it
  await page.goto("/?stage=done");
  await expect(page.getByText("What broke, for whom, and why.")).toBeVisible();
  await expect(page.getByText(/OF SHOPPERS/)).toHaveCount(4);
});

for (const id of ["ikea", "zara", "northwind"]) {
  test(`target ${id}: seek to done renders its report`, async ({ page }) => {
    const res = await page.goto(`/?target=${id}&stage=done`);
    expect(res?.ok()).toBeTruthy();
    await expect(page.getByText("What broke, for whom, and why.")).toBeVisible();
    await expect(page.getByText("PROPOSED FIX")).toBeVisible();
    await page.screenshot({ path: `e2e/screens/report-${id}.png`, fullPage: true });
  });
}
