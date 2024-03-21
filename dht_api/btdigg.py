from lxml import html
from os import environ
from pydantic import BaseModel
import aiohttp
from aiohttp_socks import ProxyConnector

SOCKS_PROXY_URL = environ.get("SOCKS_PROXY_URL") or "socks5://127.0.0.1:9050"


class TorrentFile(BaseModel):
    filename: str
    size: int


class Torrent(BaseModel):
    name: str
    size: int
    age: str
    files: list[TorrentFile]


async def get_torrent_info(info_hash: str) -> Torrent | None:
    html_text = await get_html(info_hash)
    if html_text is None:
        return None
    tree = html.fromstring(html_text)

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
    file_elements = doc.xpath('//div[contains(@class, "fa fa-file-video-o")]')

    files: list[TorrentFile] = []

    for file_element in file_elements:
        filename = file_element.text.strip()
        size = file_element.xpath("following-sibling::span[1]/text()")[0].strip()
        files.append(TorrentFile(filename=filename, size=convert_to_bytes(size)))

    return files


async def get_html(info_hash: str) -> str | None:
    url: str = (
        "http://btdigggink2pdqzqrik3blmqemsbntpzwxottujilcdjfz56jumzfsyd.onion/search"
    )
    params: dict = {"order": 0, "q": info_hash}
    headers: dict = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    }

    connector: ProxyConnector = ProxyConnector.from_url(SOCKS_PROXY_URL)

    async with aiohttp.ClientSession(connector=connector) as session, session.get(
        url, params=params, headers=headers
    ) as response:
        if response.status == 404:
            return None
        return await response.text()


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
