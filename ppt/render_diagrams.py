import asyncio
from playwright.async_api import async_playwright
import os

async def render_all():
    os.makedirs('ppt/rendered_diagrams', exist_ok=True)
    diagrams = [
        ('ppt/diagrams/slide2_solution.html', 'ppt/rendered_diagrams/slide2_solution_hd.png', 1400, 600),
        ('ppt/diagrams/slide3_architecture.html', 'ppt/rendered_diagrams/slide3_architecture_hd.png', 1400, 600),
        ('ppt/diagrams/slide5_workflow.html', 'ppt/rendered_diagrams/slide5_workflow_hd.png', 1400, 600)
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for html_path, out_png, width, height in diagrams:
            abs_html = os.path.abspath(html_path)
            page = await browser.new_page(
                viewport={'width': width, 'height': height},
                device_scale_factor=2 # 2x DPI for crisp presentation images
            )
            await page.goto(f'file:///{abs_html}')
            await page.wait_for_timeout(500)
            await page.screenshot(path=out_png)
            await page.close()
            print(f'Rendered {html_path} -> {out_png}')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(render_all())
