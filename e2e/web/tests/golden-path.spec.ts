// Golden path — the smoke flow the wizard absolutely must support.
//
//   1. The SPA bootstraps and lands on /generate.
//   2. Step 1 (Describe) accepts a prompt + advances to Step 2.
//   3. Step 2 (Framework) renders the hyperscaler rail, framework
//      grid, Pattern card, Model row.
//   4. We can toggle a hyperscaler, see a framework appear/disappear,
//      and pick a different framework / pattern / model.
//   5. Advancing all the way to Step 4 (Review) renders the
//      Compatibility card with at least one OK row.

import { expect, test } from '@playwright/test';

test('wizard renders the four steps and the compatibility card', async ({ page }) => {
  await page.goto('/generate');

  // Step 1 — Describe
  await expect(page.getByText('STEP 1 / 4', { exact: false })).toBeVisible();
  const prompt = page.locator('textarea').first();
  await prompt.fill(
    'Multi-agent research crew that drafts arXiv digests with citations.',
  );
  await page.getByRole('button', { name: /continue|next/i }).first().click();

  // Step 2 — Framework & Model
  await expect(page.getByText('STEP 2 / 4', { exact: false })).toBeVisible();
  await expect(page.getByText(/HYPERSCALER/i)).toBeVisible();
  await expect(page.getByText(/PHILOSOPHY/i)).toBeVisible();
  await expect(page.getByText(/FRAMEWORK/i).first()).toBeVisible();
  await expect(page.getByText(/ORCHESTRATION PATTERN/i)).toBeVisible();
  await expect(page.getByText(/MODEL/i).first()).toBeVisible();

  // Toggle on-prem so every framework is visible.
  await page.getByRole('button', { name: /On.?prem/ }).first().click();

  // Pick LangGraph + Supervisor.
  await page.getByRole('button', { name: /LangGraph/ }).first().click();
  await page.getByRole('button', { name: /Supervisor/i }).first().click();

  await page.getByRole('button', { name: /continue|tools|next/i }).first().click();

  // Step 3 — Tools (the existing page renders a continue button)
  await expect(page.getByText('STEP 3 / 4', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: /continue|review|next/i }).first().click();

  // Step 4 — Review with Compatibility card
  await expect(page.getByText('STEP 4 / 4', { exact: false })).toBeVisible();
  await expect(page.getByText(/Compatibility/i)).toBeVisible();
  await expect(page.getByText(/LangGraph/).first()).toBeVisible();
  // At least one OK badge in the compatibility card.
  await expect(page.locator('text=/^ok\\b/i').first()).toBeVisible();
});

test('marketplace renders sample fixture', async ({ page }) => {
  await page.goto('/marketplace');
  // The Marketplace page renders some catalogue UI — confirm we got past
  // an empty white screen.
  await expect(page.locator('body')).not.toHaveText('');
});

test('docker wizard redirects without project id', async ({ page }) => {
  await page.goto('/docker');
  await expect(page).toHaveURL(/\/generate/);
});
