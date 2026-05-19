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

  // The wizard's Step 1 "Generate" button now hits POST /api/plan.
  // The preview server doesn't bundle the backend; stub the response
  // so the test exercises the real wiring without a live API.
  await page.route('**/api/plan', async (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        spec: {
          name: 'arxiv-digest',
          framework: 'langgraph',
          artifact_mode: 'code_only',
          agents: [
            { id: 'researcher', tools: ['web_search', 'pdf_reader'] },
            { id: 'summarizer', tools: ['pdf_reader'] },
            { id: 'writer', tools: ['email_send'] },
          ],
        },
        warnings: [],
      }),
    }),
  );

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
  // Step 2 now promotes OllaBridge as the default Model access
  // gateway with named aliases instead of surfacing a flat "MODEL"
  // header. Assert the new copy.
  await expect(main.getByText('Model access', { exact: true })).toBeVisible();
  await expect(main.getByText('OllaBridge', { exact: true }).first()).toBeVisible();
  await expect(main.getByText('local-private', { exact: true })).toBeVisible();

  // Toggle on-prem so every framework is visible.
  await main.getByRole('button', { name: /On.?prem/ }).first().click();

  // Pick LangGraph + Supervisor.
  await main.getByRole('button', { name: /LangGraph/ }).first().click();
  await main.getByRole('button', { name: /Supervisor/i }).first().click();

  await main.getByRole('button', { name: /Continue to tools/i }).click();

  // Step 3 — Tools
  await expect(main.getByText('STEP 3 / 4', { exact: false })).toBeVisible();
  await main.getByRole('button', { name: /Review project/i }).click();

  // Step 4 — Review (v2) lands on the Overview sub-page. We assert
  // the substep nav rendered (Overview · Agents · Configuration ·
  // Files · Safety · Generate), the executive-summary stat strip is
  // present (Framework / Agents / Tools / Files), and the
  // Compatibility drill-in card with its OK status is visible.
  await expect(main.getByRole('tab', { name: /^Overview$/ })).toBeVisible();
  await expect(main.getByRole('tab', { name: /^Generate$/ })).toBeVisible();
  await expect(main.getByText('Framework', { exact: true }).first()).toBeVisible();
  await expect(main.getByText('Compatibility', { exact: true })).toBeVisible();
  await expect(main.getByText(/all passing/i).first()).toBeVisible();
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

test('agent projects workspace renders hub + detail', async ({ page, viewport }) => {
  test.skip(!!viewport && viewport.width < 768, 'desktop-only route');

  // Hub view: header, quick views, at least one row from the sample
  // catalogue. Strict-mode collisions are avoided with .first().
  await page.goto('/projects');
  await expect(page.getByRole('heading', { name: 'Agent Projects' })).toBeVisible();
  await expect(page.getByText(/Saved generations · drafts · templates/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /^All projects/ })).toBeVisible();
  await expect(page.getByText('arxiv-digest').first()).toBeVisible();

  // Drill into the curated sample. The id is stable.
  await page.goto('/projects/sample-arxiv');
  await expect(page.getByRole('tab', { name: /^Overview$/ })).toBeVisible();
  await expect(page.getByText(/Generation status/i)).toBeVisible();
  await expect(page.getByRole('tab', { name: /^Setup$/ })).toBeVisible();
});

test('generation history surfaces workspace events', async ({ page, viewport }) => {
  test.skip(!!viewport && viewport.width < 768, 'desktop-only route');

  await page.goto('/history');
  await expect(page.getByRole('heading', { name: 'Generation history' })).toBeVisible();
  await expect(page.getByText(/What you generated, edited, and exported/i)).toBeVisible();
  await expect(page.getByRole('tab', { name: /^Generations$/ })).toBeVisible();
  // At least one feed row should be reachable.
  await expect(page.getByText(/generated project/i).first()).toBeVisible();
});

test('publish to Hugging Face surfaces the connect screen', async ({ page, viewport }) => {
  test.skip(!!viewport && viewport.width < 768, 'desktop-only route');

  // Disconnected backend: stub the status endpoint so the flow lands
  // on the Connect screen instead of trying to fetch live data.
  await page.route('**/api/hf/status', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ connected: false, username: null, namespaces: [] }),
    }),
  );

  await page.goto('/projects/sample-arxiv/publish/hf');
  await expect(page.getByRole('heading', { name: 'Connect Hugging Face.' })).toBeVisible();
  await expect(page.getByText(/What you can publish/i)).toBeVisible();
  await expect(page.getByText(/Best for Hugging Face/i)).toBeVisible();
  await expect(page.getByText(/Gradio \+ smolagents/i)).toBeVisible();
});

test('docker landing page surfaces wizard call-to-action', async ({ page, viewport }) => {
  // /docker only exists in the desktop shell; the mobile shell hands
  // /docker off to the catch-all redirect.
  test.skip(!!viewport && viewport.width < 768, 'desktop-only route');

  // Without a `?project=` query parameter the Docker wizard now
  // shows a friendly landing page that walks the user to /generate
  // instead of silently redirecting (the old behaviour).
  await page.goto('/docker');
  await expect(page).toHaveURL(/\/docker/);
  await expect(page.getByRole('heading', { name: /Bundle a generated project/i })).toBeVisible();
  await expect(page.getByRole('button', { name: /Open the wizard/i })).toBeVisible();
});
