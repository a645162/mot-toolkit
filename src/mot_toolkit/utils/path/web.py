import re


def is_valid_url(url: str = "") -> bool:
    url_pattern = re.compile(
        r'^(http|https)://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[\w./]*)?(\?[\w.&=]*)?$'
    )

    if url_pattern.match(url):
        return True
    else:
        return False


if __name__ == "__main__":
    urls = [
        "http://example.com",
        "https://www.example.com/path/to/page",
        "ftp://example.com",  # 不合法的 URL
        "http://example",  # 不合法的 URL
        "https://example.com/path with space",  # 不合法的 URL
        "https://example.com/path/to/page?query=string&another=param",
        "https://sub.domain.example.com/path/to/page",
    ]

    for url in urls:
        print(f"{url}: {is_valid_url(url)}")
