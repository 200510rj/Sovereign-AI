import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = Path("day2_task1_documentation/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:8000"

def capture_all():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1. Desktop Full Workbench View
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE_URL)
        page.wait_for_selector("#chatFeed")
        time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "01_workbench_overview.png"), full_page=True)
        print("Captured 01_workbench_overview.png")

        # 2. Swagger Interactive API Docs
        page.goto(f"{BASE_URL}/docs")
        page.wait_for_selector(".swagger-ui")
        time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "02_swagger_api_docs.png"), full_page=True)
        print("Captured 02_swagger_api_docs.png")

        # 3. Air-Gap Network Audit Toast
        page.goto(BASE_URL)
        time.sleep(1)
        page.click("#airgapPill")
        time.sleep(1.5)
        page.screenshot(path=str(SCREENSHOT_DIR / "03_network_airgap_audit.png"), full_page=True)
        print("Captured 03_network_airgap_audit.png")

        # 4. Interactive Chat & Session View (Preload existing session)
        page.goto(BASE_URL)
        time.sleep(2)
        session_items = page.query_selector_all("#sessionList .kb-item")
        if session_items:
            session_items[0].click()
            time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "04_chat_and_session_history.png"), full_page=True)
        print("Captured 04_chat_and_session_history.png")

        # 5. Chunk Modal Inspection
        sources = page.query_selector_all(".source-item")
        if sources:
            sources[0].click()
            time.sleep(1.5)
            page.screenshot(path=str(SCREENSHOT_DIR / "05_chunk_modal_inspection.png"), full_page=True)
            print("Captured 05_chunk_modal_inspection.png")
            page.click("#closeChunkModal")
            time.sleep(1)

        # 6. Tablet Viewport
        tablet_page = browser.new_page(viewport={"width": 768, "height": 1024})
        tablet_page.goto(BASE_URL)
        time.sleep(2)
        tablet_page.screenshot(path=str(SCREENSHOT_DIR / "06_responsive_tablet.png"), full_page=True)
        print("Captured 06_responsive_tablet.png")
        tablet_page.close()

        # 7. Mobile Viewport
        mobile_page = browser.new_page(viewport={"width": 375, "height": 812})
        mobile_page.goto(BASE_URL)
        time.sleep(2)
        mobile_page.screenshot(path=str(SCREENSHOT_DIR / "07_responsive_mobile.png"), full_page=True)
        print("Captured 07_responsive_mobile.png")
        mobile_page.close()

        browser.close()

if __name__ == "__main__":
    capture_all()
    print("All Day 2 Task 1 screenshots captured successfully!")
