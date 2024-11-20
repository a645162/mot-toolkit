def format_bv(bv: str) -> str:
    # Find '-'
    index = bv.find("-")
    if index != -1:
        bv = bv[:index]

    return bv.strip()


def get_url_from_bv(bv: str) -> str:
    """
    Get video url from bv

    Args:
        bv: Video bv

    Returns:
        Video url
    """

    return f"https://www.bilibili.com/video/{bv}"


def parse_bv_from_url(url: str) -> str:
    """
    Parse bv from url

    Args:
        url: Video url

    Returns:
        Video bv
    """
    if url.startswith("https://www.bilibili.com/video/"):
        url = url[30:]

        # Find '/?'
        index = url.find("/?")
        if index != -1:
            url = url[:index]

        return format_bv(url)
    else:
        return ""
