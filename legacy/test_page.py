from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8765/tolltip.html"
errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 1000})
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    page.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="load")
    page.wait_for_timeout(2500)

    print("chips clase:", page.locator(".class-chip").count())
    print("chips spec:", page.locator(".spec-chip").count())
    print("nivel:", page.locator("#levelNumber").inner_text())
    print("tramo:", page.locator("#bracketLabel").inner_text())

    page.get_by_role("button", name="Mage", exact=True).click()
    page.get_by_role("button", name="Frost", exact=True).click()
    page.locator("#levelRange").fill("40")
    page.locator("#levelRange").dispatch_event("input")
    page.wait_for_timeout(1200)

    print("nivel tras slider:", page.locator("#levelNumber").inner_text())
    print("tramo tras slider:", page.locator("#bracketLabel").inner_text())
    print("armadura:", page.locator("#statusArmor").inner_text())
    print("gear primeros enlaces:", page.locator(".gear-link").first.inner_text())
    print("rel:", page.locator(".gear-link").first.get_attribute("rel"))
    print("filas:", page.locator(".gear-row").count())
    print("stats:", page.locator(".stat-list li").all_inner_texts())
    print("dungeons:", page.locator(".dungeon-list li.current").all_inner_texts())

    page.locator(".gear-link").first.hover()
    page.wait_for_timeout(1800)
    tip = page.locator("#tooltip, .tooltip, [id^='aowow']").first
    print("tooltip visible:", tip.is_visible() if tip.count() else "sin nodo")
    body_text = page.locator("body").inner_text()
    print("menciona Intelecto:", "Intelecto" in body_text)
    page.screenshot(path=r"C:\Users\user\AppData\Local\Temp\opencode\page.png", full_page=True)

    # DK min clamp
    page.get_by_role("button", name="Death Knight", exact=True).click()
    page.locator("#levelInput").fill("10")
    page.locator("#levelInput").dispatch_event("change")
    page.wait_for_timeout(300)
    print("DK nivel minimo:", page.locator("#levelInput").input_value(), page.locator("#levelNumber").inner_text())

    # persistence after reload
    page.reload(wait_until="load")
    page.wait_for_timeout(800)
    print("persistencia:", page.locator("#classes .class-chip[aria-pressed='true']").inner_text(), page.locator("#specs .spec-chip[aria-pressed='true']").inner_text(), page.locator("#levelNumber").inner_text())

    print("errores:", errors)
    browser.close()
