#!/usr/bin/env python3
"""Capture agent-generator SPA screenshots + verify Batch 9 (de-demo).

Captures the main desktop routes in the normal (non-demo) state, asserting the
"Demo mode" badge is absent. Then it mocks `/api/auth/me` to return the demo
backend's `x-agent-generator-channel: hf-space` header and confirms the badge
appears — proving the runtime capability check (not a compile-time constant)
drives the DEMO affordance.
"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

ROUTES = [
    ("generate", "/generate"),
    ("pipeline", "/pipeline"),
    ("run", "/run"),
    ("marketplace", "/marketplace"),
    ("export", "/export"),
    ("docker", "/docker"),
    ("projects", "/projects"),
    ("history", "/history"),
]

DEMO_BADGE = '[aria-label="Demo mode"]'


async def settle(page, ms: int = 900):
    await page.wait_for_timeout(ms)


async def shot(page, out_dir: Path, name: str):
    await settle(page)
    path = out_dir / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
    print(f"shot: {path.name}")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:4173")
    ap.add_argument("--out", default="docs/assets/screenshots")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()

    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=args.scale,
            color_scheme="light",
        )
        page = await ctx.new_page()

        # ── Non-demo state: capture every route, assert no DEMO badge ──
        demo_seen = False
        for name, route in ROUTES:
            try:
                await page.goto(f"{args.base_url}{route}", wait_until="networkidle")
            except Exception as exc:
                print(f"skip {name}: {exc}")
                continue
            await shot(page, out_dir, name)
            if await page.locator(DEMO_BADGE).count() > 0:
                demo_seen = True
        print(f"[verify] DEMO badge present in non-demo state: {demo_seen}  (expect False)")

        # ── Demo state: mock the demo backend header, expect the badge ──
        async def demo_me(route):
            await route.fulfill(
                status=404,
                headers={"x-agent-generator-channel": "hf-space"},
                content_type="application/json",
                body='{"detail":"not found"}',
            )

        await page.route("**/api/auth/me", demo_me)
        await page.goto(f"{args.base_url}/generate", wait_until="networkidle")
        await settle(page, 1200)
        badge = await page.locator(DEMO_BADGE).count()
        await shot(page, out_dir, "generate-demo-mode")
        print(f"[verify] DEMO badge present when backend says hf-space: {badge > 0}  (expect True)")

        await browser.close()

        ok = (not demo_seen) and (badge > 0)
        print(f"\nBATCH 9 VERIFICATION: {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
