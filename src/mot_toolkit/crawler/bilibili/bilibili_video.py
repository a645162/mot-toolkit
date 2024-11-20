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
        bv = bv.strip()

        if not bv.startswith("BV"):
            return

        self._bv = bv

        self.url = get_url_from_bv(bv)

    def is_valid(self) -> bool:
        if not super().is_valid():
            return False

        return self.bv.strip() != ""
