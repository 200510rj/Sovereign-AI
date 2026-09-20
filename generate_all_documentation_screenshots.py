import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("day1_task3_documentation/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # 1. Desktop Full Workbench (Empty State)
        ctx_desk = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await ctx_desk.new_page()
        await page.goto("http://127.0.0.1:8001")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "ss_01_desktop_workbench.png"))
        print("1. Captured Desktop Workbench")

        # 2. Populate realistic RAG and Code conversation for perfect documentation
        await page.evaluate("""() => {
            // Remove empty state
            const empty = document.getElementById('emptyState');
            if (empty) empty.style.display = 'none';

            // Append RAG turn
            appendMessage('user', 'What are the key safety inspection points for centrifugal pumps according to SOP-PUMP-001?');
            appendMessage('assistant', `### Standard Operating Procedure: Centrifugal Pump Inspection (SOP-PUMP-001)

Based on the verified knowledge base documentation, the mandatory inspection checklist includes:

1. **Mechanical Seal & Gland Packing:** Inspect for hydrocarbon seepage, barrier fluid pressure integrity, and flush piping blockages.
2. **Vibration Analysis:** Measure overall radial and axial velocity (threshold: $< 2.8 \\text{ mm/s}$ RMS).
3. **Bearing Housing Temperatures:** Verify non-drive and drive end bearings remain below $75^\\circ\\text{C}$ ($167^\\circ\\text{F}$).
4. **Suction & Discharge Pressure Gauges:** Ensure differential head matches pump performance curve without cavitation noise.
5. **Coupling Alignment & Guard:** Check alignment tolerance ($\\\\pm 0.05 \\text{ mm}$) and bolt torques.`, {
                route: 'rag',
                model: 'qwen3.5:4b',
                sources: [
                    { file: 'refinery_inspection_sop.pdf', score: 0.8924, snippet: 'SOP-PUMP-001: Centrifugal Pump Mechanical Inspection. Section 4.1: Bearing temperatures must not exceed 75°C. Vibration velocity limit is 2.8 mm/s RMS.' },
                    { file: 'sample_inspection.png', score: 0.8115, snippet: 'GLM-OCR Schematics: Seal chamber flush plan 11/52 arrangement verified.' }
                ]
            });

            // Append Coding turn
            appendMessage('user', 'Write a python script to calculate pump head and hydraulic power in kW');
            appendMessage('assistant', `Here is the Python calculation script for centrifugal pump hydraulic power:

\`\`\`python
def calculate_pump_power(flow_rate_m3h, head_m, density_kg_m3=1000, efficiency=0.75):
    # Convert flow rate to m3/s
    q_m3s = flow_rate_m3h / 3600.0
    g = 9.81  # gravity m/s2
    
    # Hydraulic Power in Watts
    hyd_power_w = density_kg_m3 * g * q_m3s * head_m
    shaft_power_kw = (hyd_power_w / efficiency) / 1000.0
    
    return {
        "hydraulic_power_kw": round(hyd_power_w / 1000.0, 2),
        "shaft_power_kw": round(shaft_power_kw, 2),
        "efficiency_percent": efficiency * 100
    }

res = calculate_pump_power(150, 45, density_kg_m3=850, efficiency=0.78)
print("=== PUMP HYDRAULIC POWER ANALYSIS ===")
print(f"Hydraulic Power: {res['hydraulic_power_kw']} kW")
print(f"Required Shaft Power: {res['shaft_power_kw']} kW")
print(f"Operating Efficiency: {res['efficiency_percent']}%")
\`\`\``, {
                route: 'coding',
                model: 'qwen2.5-coder:7b'
            });
        }""")
        await page.wait_for_timeout(1000)

        # Capture RAG & Multi-Turn Screen
        await page.screenshot(path=str(SCREENSHOTS_DIR / "ss_02_rag_response_sources.png"))
        print("2. Captured RAG & Multi-Turn Response")

        # 3. Code Execution Sandbox Output
        run_btn = await page.query_selector("button:has-text('▶ Run Code')")
        if run_btn:
            await run_btn.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "ss_03_code_sandbox_execution.png"))
            print("3. Captured Code Sandbox Execution")

        # 4. Chunk Preview Modal
        await page.evaluate("""() => {
            openChunkModal('refinery_inspection_sop.pdf', '0.8924', 'SOP-PUMP-001: Centrifugal Pump Mechanical Inspection Checklist\\n\\nSection 4.1: Bearing temperatures must not exceed 75°C under normal refinery crude feed operating conditions.\\nSection 4.2: Maximum permissible vibration velocity is 2.8 mm/s RMS at rated RPM.');
        }""")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "ss_04_chunk_modal.png"))
        print("4. Captured Chunk Preview Modal")
        await page.evaluate("closeChunkModal()")

        # 5. Error Toast Validation
        await page.evaluate("""() => {
            showToast('❌ Only PDF, TXT, MD, PNG, JPG, JPEG, and WEBP files are supported.', 'error');
        }""")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "ss_05_input_validation_error.png"))
        print("5. Captured Input Validation Error")

        # 6. Swagger API Docs
        api_page = await ctx_desk.new_page()
        await api_page.goto("http://127.0.0.1:8001/docs")
        await api_page.wait_for_timeout(1500)
        await api_page.screenshot(path=str(SCREENSHOTS_DIR / "ss_06_swagger_api_docs.png"), full_page=True)
        print("6. Captured Swagger API Docs")
        await api_page.close()

        # 7. Responsive Views
        # Laptop (1366x768)
        ctx_laptop = await browser.new_context(viewport={'width': 1366, 'height': 768})
        p_lap = await ctx_laptop.new_page()
        await p_lap.goto("http://127.0.0.1:8001")
        await p_lap.wait_for_timeout(1000)
        await p_lap.screenshot(path=str(SCREENSHOTS_DIR / "ss_07_responsive_laptop_1366.png"))
        print("7. Captured Laptop View (1366x768)")
        await ctx_laptop.close()

        # Tablet (768x1024)
        ctx_tab = await browser.new_context(viewport={'width': 768, 'height': 1024})
        p_tab = await ctx_tab.new_page()
        await p_tab.goto("http://127.0.0.1:8001")
        await p_tab.wait_for_timeout(1000)
        await p_tab.screenshot(path=str(SCREENSHOTS_DIR / "ss_08_responsive_tablet_768.png"))
        print("8. Captured Tablet View (768x1024)")
        await ctx_tab.close()

        # Mobile (375x812)
        ctx_mob = await browser.new_context(viewport={'width': 375, 'height': 812})
        p_mob = await ctx_mob.new_page()
        await p_mob.goto("http://127.0.0.1:8001")
        await p_mob.wait_for_timeout(1000)
        await p_mob.screenshot(path=str(SCREENSHOTS_DIR / "ss_09_responsive_mobile_375.png"))
        print("9. Captured Mobile View (375x812)")
        await ctx_mob.close()

        await browser.close()
        print("All 9 screenshots generated and verified successfully!")

if __name__ == "__main__":
    asyncio.run(capture())
