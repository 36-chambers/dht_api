from pydantic import BaseModel


class TorrentFile(BaseModel):
    name: str
    size: int

    class Config:
        orm_mode = True


class Torrent(BaseModel):
    info_hash: str
    name: str
    size: int
    age: str
    files: list[TorrentFile]

    class Config:
        orm_mode = True
