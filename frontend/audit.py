#!/usr/bin/env python3
"""Live link/route audit against the deployed Space.

For each SPA route: load it, assert the app shell rendered, and collect
(a) uncaught JS errors and (b) failed same-origin /api requests. Then open the
account menu and assert there is NO dead 'Sign in with GitHub' link on the demo.
"""

from __future__ import annotations

import asyncio
import sys

from playwright.async_api import async_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://ruslanmv-agent-generator.hf.space"
ROUTES = ["/generate", "/pipeline", "/run", "/test", "/projects", "/history",
          "/marketplace", "/export", "/docker"]


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900}, ignore_https_errors=True
        )

        ok = True
        for route in ROUTES:
            page = await ctx.new_page()
            errors, api_fail = [], []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("response", lambda r: (
                api_fail.append(f"{r.status} {r.url.split('?')[0].split('/api/')[-1]}")
                if "/api/" in r.url and r.status >= 500 else None))
            try:
                await page.goto(f"{BASE}{route}", wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(1200)
                # App shell present? (left rail has the brand mark / nav buttons)
                rendered = await page.locator("nav, aside, [class*='rail'], button").count() > 0
                body_len = len(await page.inner_text("body"))
                status = "OK" if (rendered and body_len > 40 and not errors) else "FAIL"
                if status == "FAIL":
                    ok = False
                print(f"  {route:14} {status:4}  body={body_len:>5}ch  "
                      f"js_errors={len(errors)}  api_5xx={len(api_fail)}")
                if errors:
                    print(f"       JS: {errors[:2]}")
                if api_fail:
                    print(f"       API5xx: {api_fail[:3]}")
            except Exception as exc:
                ok = False
                print(f"  {route:14} FAIL  ({exc})")
            await page.close()

        # ── Account menu: no dead sign-in on the demo ──
        page = await ctx.new_page()
        await page.goto(f"{BASE}/generate", wait_until="networkidle")
        await page.wait_for_timeout(1500)
        signin = -1
        try:
            # The avatar/account button sits at the bottom of the left rail.
            await page.locator("aside button, nav button").last.click(timeout=5000)
            await page.wait_for_timeout(800)
            signin = await page.get_by_text("Sign in with GitHub").count()
        except Exception as exc:
            print(f"  account-menu: could not open ({exc})")
        print(f"\n  account menu 'Sign in with GitHub' items on demo: {signin}  (expect 0)")
        if signin != 0:
            ok = False

        await browser.close()
        print(f"\nLINK AUDIT: {'PASS' if ok else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
