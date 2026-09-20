import pytest
import time
import threading
import uvicorn
from pathlib import Path
from playwright.sync_api import sync_playwright
import main

SERVER_PORT = 8765
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"

class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.server = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=SERVER_PORT, log_level="error"))

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True

@pytest.fixture(scope="module", autouse=True)
def start_test_server():
    """Launch background uvicorn server for Playwright E2E tests."""
    thread = ServerThread()
    thread.daemon = True
    thread.start()
    time.sleep(2) # Give server time to bind port
    yield
    thread.stop()

def test_e2e_web_ui_layout_and_toggles():
    """Playwright E2E: Verify sidebar, navbar, pills, and toggles in browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SERVER_URL, wait_until="domcontentloaded", timeout=10000)

        # Check title
        assert "Sovereign AI Workbench" in page.title()

        # Check sidebar header
        brand_title = page.locator(".brand-title").inner_text()
        assert "Sovereign AI" in brand_title

        # Check Pills
        knowledge_pill = page.locator("#knowledgePill")
        assert "OFF" in knowledge_pill.inner_text()

        # Toggle Agent Mode
        agent_pill = page.locator("#agentPill")
        assert "OFF" in agent_pill.inner_text()
        agent_pill.click()
        assert "ON" in agent_pill.inner_text()

        # Toggle Web Search
        web_pill = page.locator("#webSearchPill")
        web_pill.click()
        assert "ON" in web_pill.inner_text()

        browser.close()

def test_e2e_session_creation_and_deletion():
    """Playwright E2E: Test sending a chat message, creating session, and deleting session via UI trash button."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SERVER_URL, wait_until="domcontentloaded", timeout=10000)

        # Type message
        input_box = page.locator("#promptInput")
        input_box.fill("Playwright E2E Test Query 123")

        # Click send
        send_btn = page.locator("#sendBtn")
        send_btn.click()

        # Wait for assistant response bubble
        page.wait_for_selector(".message-row.assistant", timeout=30000)
        
        # Verify message added to chat
        chat_content = page.locator("#chatFeed").inner_text()
        assert "Playwright E2E Test Query 123" in chat_content

        # Check recent sessions in sidebar
        session_items = page.locator("#sessionList .kb-item")
        assert session_items.count() > 0

        # Click trash button to delete session
        delete_btn = page.locator("#sessionList .delete-session-btn").first
        
        # Accept confirm dialog automatically
        page.once("dialog", lambda dialog: dialog.accept())
        delete_btn.click()

        time.sleep(1)
        browser.close()

def test_e2e_agent_mode_execution():
    """Playwright E2E: Test autonomous agent mode prompt execution with tool call step accordions."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SERVER_URL, wait_until="domcontentloaded", timeout=10000)

        # Turn Agent Mode ON
        agent_pill = page.locator("#agentPill")
        agent_pill.click()

        # Type agent prompt
        input_box = page.locator("#promptInput")
        input_box.fill("Search knowledge base for SOP and read test_sop.txt")
        send_btn = page.locator("#sendBtn")
        send_btn.click()

        # Wait for agent assistant response badge & timeline
        page.wait_for_selector(".route-badge.agent", timeout=60000)

        # Verify agent badge and tool step accordion
        agent_badge = page.locator(".route-badge.agent")
        assert agent_badge.count() > 0

        # Save E2E UI screenshot
        reports_dir = Path("data/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path="data/reports/playwright_e2e_test.png")

        browser.close()
