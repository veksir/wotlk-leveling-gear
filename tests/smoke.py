from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = (ROOT / "tolltip.html").as_uri()
errors = []


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 1000})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(1800)

        assert page.locator(".chip").count() == 10
        assert page.locator("#factions button").count() == 2
        assert page.locator(".slot").count() >= 15
        assert "undefined" not in page.locator("body").inner_text().lower()

        page.get_by_role("button", name="Mage", exact=True).click()
        page.get_by_role("button", name="Frost", exact=True).click()
        page.locator("#levelInput").fill("40")
        page.locator("#levelInput").dispatch_event("change")
        page.wait_for_timeout(400)
        assert page.locator("#levelNumber").inner_text() == "40"
        assert page.locator(".slot").first.inner_text().startswith("Cabeza")
        assert "Sin objeto" not in page.locator(".slot").first.inner_text()

        page.get_by_role("button", name="Death Knight", exact=True).click()
        page.wait_for_timeout(300)
        assert page.locator("#levelNumber").inner_text() == "55"

        page.locator('#factions button[data-faction="alliance"]').click()
        page.locator('.lang-switch button[data-lang="en"]').click()
        page.wait_for_timeout(500)
        assert page.locator("h1").inner_text().startswith("What to wear")
        assert page.locator("#classLabel").inner_text() == "Class"
        assert page.locator("#factions button[aria-pressed='true']").inner_text() == "Alliance"
        assert page.locator(".slot").first.inner_text().startswith("Head")

        page.reload(wait_until="load")
        page.wait_for_timeout(900)
        assert page.locator("#levelNumber").inner_text() == "55"
        assert page.locator("#factions button[aria-pressed='true']").inner_text() == "Alliance"
        assert page.locator("h1").inner_text().startswith("What to wear")

        assert not errors, errors
        print("smoke ok:", page.locator(".slot").count(), "slots")
        browser.close()


if __name__ == "__main__":
    main()
