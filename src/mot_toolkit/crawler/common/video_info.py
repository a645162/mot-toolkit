class VideoInfo:
    url: str

    def __init__(self, url: str = ""):
        self.url = url

    def is_valid(self) -> bool:
        return self.url.strip() != ""
