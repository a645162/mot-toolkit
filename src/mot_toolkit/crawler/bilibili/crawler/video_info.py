import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)  # 设置 headless=True 以无头模式运行
        page = await browser.new_page()

        # 打开 URL
        url = 'https://www.bilibili.com/video/BV14UUAYmExC/'  # 替换为你要抓取的 URL
        await page.goto(url)

        # 等待页面加载完成
        await page.wait_for_load_state('networkidle')

        # 抓取指定的 XPath 元素
        xpath = '//*[@id="viewbox_report"]/div[1]'
        element = page.locator(xpath).first

        # 获取元素的文本内容
        text_content = await element.text_content()
        print(f"抓取到的文本内容: {text_content}")

        # 获取元素的 HTML 内容
        html_content = await element.inner_html()
        print(f"抓取到的 HTML 内容: {html_content}")

        # 关闭浏览器
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
