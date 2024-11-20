from mot_toolkit.utils.path.web import is_valid_url


class WebVideo:
    title: str = ""
    description: str = ""

    def __init__(self, url: str = ""):
        if is_valid_url(url):
            self.url = url

    def is_valid(self) -> bool:
        return self.url.strip() != ""
