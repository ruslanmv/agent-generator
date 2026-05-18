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
//
// The SPA renders a different 6-step flow on viewports narrower than
// the 768 px breakpoint (see frontend/src/lib/use-media.ts and
// frontend/src/App.tsx). The wizard test below targets the desktop
// flow and is skipped on the mobile project; a tiny mobile smoke
// test below it covers the MobileGenerate surface.

import { expect, test } from '@playwright/test';

test('wizard renders the four steps and the compatibility card', async ({ page, viewport }) => {
  test.skip(!!viewport && viewport.width < 768, 'desktop wizard — mobile flow has its own test');

  // Scope every locator to <main> so the sidebar "Generate" link and
  // the form's "Generate" submit don't collide.
  const main = page.locator('main');

  await page.goto('/generate');

  // Step 1 — Describe
  await expect(main.getByText('STEP 1 / 4', { exact: false })).toBeVisible();
  await main.locator('textarea').first().fill(
    'Multi-agent research crew that drafts arXiv digests with citations.',
  );
  await main.getByRole('button', { name: /^Generate$/i }).click();

  // Step 2 — Framework & Model
  await expect(main.getByText('STEP 2 / 4', { exact: false })).toBeVisible();
  await expect(main.getByText('HYPERSCALER', { exact: true })).toBeVisible();
  await expect(main.getByText('PHILOSOPHY', { exact: true })).toBeVisible();
  await expect(main.getByText('FRAMEWORK', { exact: true }).first()).toBeVisible();
  await expect(main.getByText('ORCHESTRATION PATTERN', { exact: true })).toBeVisible();
  await expect(main.getByText('MODEL', { exact: true }).first()).toBeVisible();

  // Toggle on-prem so every framework is visible.
  await main.getByRole('button', { name: /On.?prem/ }).first().click();

  // Pick LangGraph + Supervisor.
  await main.getByRole('button', { name: /LangGraph/ }).first().click();
  await main.getByRole('button', { name: /Supervisor/i }).first().click();

  await main.getByRole('button', { name: /Continue to tools/i }).click();

  // Step 3 — Tools
  await expect(main.getByText('STEP 3 / 4', { exact: false })).toBeVisible();
  await main.getByRole('button', { name: /Review project/i }).click();

  // Step 4 — Review with Compatibility card.
  //
  // The Review page renders demo content for the framework, model,
  // and tools — we don't assert against the values the wizard picked
  // because that copy is currently fixture-driven. The contract we
  // care about is: step 4 loaded, the Compatibility card rendered,
  // and at least one OK row is present.
  await expect(main.getByText('STEP 4 / 4', { exact: false })).toBeVisible();
  await expect(main.getByText('COMPATIBILITY', { exact: true })).toBeVisible();
  await expect(main.getByText(/\bok\b/i).first()).toBeVisible();
});

test('mobile generate flow renders the first step', async ({ page, viewport }) => {
  test.skip(!viewport || viewport.width >= 768, 'mobile-only smoke');

  await page.goto('/generate');

  // MobileGenerate renders an "AHeader" titled "New project" plus an
  // "AStepDots" component that surfaces a 1/6 step label.
  await expect(page.getByRole('heading', { name: /new project/i })).toBeVisible();
  await expect(page.getByText(/1\s*\/\s*6/)).toBeVisible();
  await expect(page.locator('textarea').first()).toBeVisible();
});

test('marketplace renders sample fixture', async ({ page }) => {
  await page.goto('/marketplace');
  // The Marketplace page renders some catalogue UI — confirm we got past
  // an empty white screen.
  await expect(page.locator('body')).not.toHaveText('');
});

test('docker wizard redirects without project id', async ({ page, viewport }) => {
  // /docker only exists in the desktop shell; the mobile shell hands
  // /docker off to the catch-all redirect.
  test.skip(!!viewport && viewport.width < 768, 'desktop-only route');

  await page.goto('/docker');
  await expect(page).toHaveURL(/\/generate/);
});
