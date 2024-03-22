from pydantic import BaseModel, root_validator


class TorrentFile(BaseModel):
    name: str
    size: int


class Torrent(BaseModel):
    info_hash: str
    name: str
    size: int
    age: str
    video_files: list[TorrentFile]

    @root_validator(pre=True)
    @classmethod
    def rename_files(cls, values):
        if "files" in values:
            values["video_files"] = values.pop("files")
        return values
