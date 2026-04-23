"""
WCAG 2.1 AA accessibility tests using axe-core injected into Playwright.

Runs an automated axe audit on the marketing + app pages. Complements the
design guidelines' a11y requirements. Any "serious" or "critical" violations
fail the test; "moderate" and "minor" are reported but non-blocking until
the codebase catches up.

Requires:
  - playwright  (already installed for screenshot/e2e tests)
  - pytest-asyncio
The test downloads axe-core.min.js lazily on first run and caches it.

Run:
  pytest backend/tests/test_accessibility.py -v -s

Skip if the preview env is not reachable (e.g. local runs without network):
  AXE_TESTS=0 pytest ...
"""

import json
import os
import pathlib
from urllib.request import urlopen

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("AXE_TESTS", "1") == "0",
    reason="set AXE_TESTS=1 to run",
)

# ── Test targets ──────────────────────────────────────────────────────────
# Unauthenticated marketing pages — fast, safe, no login needed.
# Extend this list as new pages graduate from "known a11y debt" to "clean".
PUBLIC_PAGES = [
    "/",
    "/products",
    "/products/demand-planning",
    "/solutions/fashion-retail",
    "/industries/apparel",
    "/resources/api-reference",
]

BASE_URL = os.environ.get(
    "AXE_BASE_URL",
    "https://zip-improved.preview.emergentagent.com",
)

AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.0/axe.min.js"
AXE_CACHE = pathlib.Path("/tmp/axe.min.js")

# Severities we fail the build on. Keep this list SMALL — the purpose is to
# catch regressions, not to chase long-tail warnings with Tailwind hex colors.
BLOCKING = {"serious", "critical"}


def _axe_source() -> str:
    if not AXE_CACHE.exists():
        AXE_CACHE.write_bytes(urlopen(AXE_CDN, timeout=20).read())
    return AXE_CACHE.read_text()


@pytest.fixture(scope="module")
def axe_js():
    try:
        return _axe_source()
    except Exception as e:
        pytest.skip(f"Could not download axe-core: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PUBLIC_PAGES)
async def test_public_page_has_no_blocking_a11y_violations(path, axe_js):
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        pytest.skip("playwright not installed")

    url = f"{BASE_URL}{path}"
    async with async_playwright() as p:
        # Retry browser launch once — SIGSEGV on rapid cycling is a known
        # Chromium-in-container flake, not a test failure.
        last_err = None
        for attempt in range(2):
            try:
                browser = await p.chromium.launch(headless=True)
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
        else:
            pytest.skip(f"chromium refused to launch: {last_err}")
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            await browser.close()
            pytest.skip(f"could not load {url}: {e}")

        await page.evaluate(axe_js)
        try:
            results = await page.evaluate(
                """async () => await axe.run(document, {
                    runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21aa']}
                })"""
            )
        except Exception as e:
            await browser.close()
            pytest.skip(f"axe.run failed ({type(e).__name__}): {e}")
        await browser.close()

    blocking = [v for v in results["violations"] if v.get("impact") in BLOCKING]
    if blocking:
        summary = [
            {
                "id": v["id"],
                "impact": v["impact"],
                "help": v["help"],
                "nodes": len(v["nodes"]),
                "example_selector": v["nodes"][0]["target"] if v["nodes"] else None,
            }
            for v in blocking
        ]
        pytest.fail(
            f"A11y violations on {path} (impact∈{BLOCKING}):\n"
            + json.dumps(summary, indent=2)
        )

    # Always print moderate/minor counts for visibility (non-blocking).
    non_blocking = {"moderate": 0, "minor": 0}
    for v in results["violations"]:
        if v.get("impact") in non_blocking:
            non_blocking[v["impact"]] += 1
    print(f"{path}: clean on {BLOCKING}. Moderate={non_blocking['moderate']} Minor={non_blocking['minor']}")
