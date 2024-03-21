import requests
from lxml import html
from pydantic import BaseModel


class TorrentFile(BaseModel):
    filename: str
    size: int


class Torrent(BaseModel):
    name: str
    size: int
    age: str
    files: list[TorrentFile]


async def get_torrent_info(info_hash: str):
    tree = html.fromstring(get_html(info_hash))

    torrent_name = tree.xpath("//td[text()='Name:']/following-sibling::td[1]")
    torrent_size = tree.xpath("//td[text()='Size:']/following-sibling::td[1]")
    torrent_age = tree.xpath("//td[text()='Age:']/following-sibling::td[1]")
    torrent_files = get_files(tree)

    return Torrent(
        name=torrent_name[0].text_content(),
        size=convert_to_bytes(torrent_size[0].text_content()),
        age=torrent_age[0].text_content(),
        files=torrent_files,
    )


def get_files(doc: html.HtmlElement) -> list[TorrentFile]:
    # Find all file elements
    file_elements = doc.xpath('//div[contains(@class, "fa fa-file-video-o")]')

    # Initialize an empty dictionary to store your filename: size pairs
    files: list[TorrentFile] = []

    for file_element in file_elements:
        filename = file_element.text.strip()
        size = file_element.xpath("following-sibling::span[1]/text()")[0].strip()
        files.append(TorrentFile(filename=filename, size=convert_to_bytes(size)))

    return files


def get_html(info_hash: str) -> str:
    # Ensure proper type assertions
    url: str = (
        "http://btdigggink2pdqzqrik3blmqemsbntpzwxottujilcdjfz56jumzfsyd.onion/search"
    )
    params: dict = {"order": 0, "q": info_hash}
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    }

    # Use Tor's SOCKS proxy
    proxies: dict = {
        "http": "socks5h://localhost:9050",
        "https": "socks5h://localhost:9050",
    }

    return requests.get(url, params=params, headers=headers, proxies=proxies).text


def convert_to_bytes(size_str: str) -> int:
    """Convert human-readable file sizes to bytes.

    Args:
    size_str (str): The size string in human-readable format (e.g., "600.44 MB", "1.5 GB").

    Returns:
    int: The size in bytes.
    """
    size_str = size_str.replace("\u00a0", " ")  # Replace non-breaking space
    num, unit = size_str.split()
    num = float(num)

    if unit == "MB":
        return int(num * 1024**2)
    elif unit == "GB":
        return int(num * 1024**3)
    return 0
