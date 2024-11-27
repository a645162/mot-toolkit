import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
