from mot_toolkit.crawler.common.video_info import VideoInfo


class BilibiliVideoInfo(VideoInfo):

    def __init__(self, url: str = ""):
        super().__init__(url=url)
