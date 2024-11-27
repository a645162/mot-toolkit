from typing import Optional

from playwright.async_api import Browser

from mot_toolkit.crawler.bilibili.api.bv import get_url_from_bv, parse_bv_from_url
from mot_toolkit.crawler.common.web_video import WebVideo


class BilibiliVideo(WebVideo):
    _bv: str = ""

    def __init__(self, url: str = ""):
        super().__init__(url=url)

    @property
    def bv(self) -> str:
        if len(self._bv) == 0:
            self._bv = parse_bv_from_url(self.url)

        return self._bv

    @bv.setter
    def bv(self, bv: str):
        index = bv.rfind("/")
        if index != -1:
            bv = bv[index + 1:]

        bv = bv.strip()

        if not bv.upper().startswith("BV"):
            return

        self._bv = bv

        self.url = get_url_from_bv(bv)

    def is_valid(self) -> bool:
        if not super().is_valid():
            return False

        return self.bv.strip() != ""

    def __str__(self) -> str:
        if self.title:
            return f"[{self.bv}]{self.title}"
        else:
            return self.bv

    async def async_get_info(self, browser: Optional[Browser] = None) -> bool:
        if not self.is_valid():
            return False

        async def get_title(page):
            xpath = '//*[@id="viewbox_report"]/div[1]'
            element = page.locator(xpath).first

            text_content = await element.text_content()
            text_content = text_content.strip()

            return text_content

        async def get_description(page):
            xpath = '//*[@id="v_desc"]/div'
            element = page.locator(xpath).first

            text_content = await element.text_content()
            text_content = text_content.strip()

            return text_content

        page = await browser.new_page()

        await page.goto(self.url)

        # Wait for the page to load
        await page.wait_for_load_state('networkidle')

        title = await get_title(page)
        description = await get_description(page)

        title = title.strip()
        description = description.strip()

        if title:
            self.title = title
        if description:
            self.description = description

        await page.close()

        return True
