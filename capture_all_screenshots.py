import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("day1_task3_documentation/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def capture_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 1. Desktop Full Workbench (Empty State & Overview)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        await page.goto("http://127.0.0.1:8001")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "ss_01_desktop_workbench.png"))
        print("Captured ss_01_desktop_workbench.png")

        # 2. Knowledge RAG Chat with sources
        await page.click(".suggestion-card:first-child")
        await page.wait_for_timeout(500)
        await page.click("#sendBtn")
        # Wait for send button to be re-enabled after Ollama finishes
        await page.wait_for_selector("#sendBtn:not([disabled])", timeout=90000)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "ss_02_rag_response_sources.png"))
        print("Captured ss_02_rag_response_sources.png")

        # 3. Chunk Preview Modal
        source_item = await page.query_selector(".source-item")
        if source_item:
            await source_item.click()
            await page.wait_for_selector("#chunkModal", state="visible")
            await page.wait_for_timeout(500)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "ss_03_chunk_modal.png"))
            print("Captured ss_03_chunk_modal.png")
            await page.click("#chunkModal button:last-child")
            await page.wait_for_timeout(500)

        # 4. Code Generation & Sandbox Execution
        await page.fill("#promptInput", "write a python script to calculate pipeline pressure loss using Darcy-Weisbach equation and print the result")
        await page.click("#sendBtn")
        await page.wait_for_selector("#sendBtn:not([disabled])", timeout=90000)
        await page.wait_for_timeout(1000)
        
        # Click Run Code
        run_btn = await page.query_selector("button:has-text('▶ Run Code')")
        if run_btn:
            await run_btn.click()
            await page.wait_for_timeout(2000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "ss_04_code_sandbox_execution.png"))
        print("Captured ss_04_code_sandbox_execution.png")

        # 5. Swagger API Docs
        api_page = await context.new_page()
        await api_page.goto("http://127.0.0.1:8001/docs")
        await api_page.wait_for_timeout(2000)
        await api_page.screenshot(path=str(SCREENSHOTS_DIR / "ss_05_swagger_api_docs.png"), full_page=True)
        print("Captured ss_05_swagger_api_docs.png")
        await api_page.close()

        # 6. Responsive Views
        # Laptop (1366x768)
        laptop_ctx = await browser.new_context(viewport={'width': 1366, 'height': 768})
        p_laptop = await laptop_ctx.new_page()
        await p_laptop.goto("http://127.0.0.1:8001")
        await p_laptop.wait_for_timeout(1000)
        await p_laptop.screenshot(path=str(SCREENSHOTS_DIR / "ss_06_responsive_laptop_1366.png"))
        print("Captured ss_06_responsive_laptop_1366.png")
        await laptop_ctx.close()

        # Tablet (768x1024)
        tablet_ctx = await browser.new_context(viewport={'width': 768, 'height': 1024})
        p_tablet = await tablet_ctx.new_page()
        await p_tablet.goto("http://127.0.0.1:8001")
        await p_tablet.wait_for_timeout(1000)
        await p_tablet.screenshot(path=str(SCREENSHOTS_DIR / "ss_07_responsive_tablet_768.png"))
        print("Captured ss_07_responsive_tablet_768.png")
        await tablet_ctx.close()

        # Mobile (375x812)
        mobile_ctx = await browser.new_context(viewport={'width': 375, 'height': 812})
        p_mobile = await mobile_ctx.new_page()
        await p_mobile.goto("http://127.0.0.1:8001")
        await p_mobile.wait_for_timeout(1000)
        await p_mobile.screenshot(path=str(SCREENSHOTS_DIR / "ss_08_responsive_mobile_375.png"))
        print("Captured ss_08_responsive_mobile_375.png")
        await mobile_ctx.close()

        await browser.close()
        print("All live screenshots captured successfully!")

if __name__ == "__main__":
    asyncio.run(capture_all())
