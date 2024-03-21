from contextlib import asynccontextmanager
from typing import Annotated

import structlog
from fastapi import FastAPI, HTTPException, Query

from dht_api import btdigg, db, schemas

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    await db.init()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/info")
async def info(
    info_hash: Annotated[str, Query(description="Torrent Info Hash", min_length=40, max_length=40)],
) -> schemas.Torrent:
    torrent_info = await db.get_torrent(info_hash)
    if torrent_info:
        return torrent_info

    torrent_info = await btdigg.get_torrent_info(info_hash)
    if torrent_info:
        await db.add_torrent(
            db.Torrent(
                info_hash=torrent_info.info_hash,
                name=torrent_info.name,
                size=torrent_info.size,
                age=torrent_info.age,
                files=[
                    db.TorrentFile(name=file.name, size=file.size) for file in torrent_info.files
                ],
            )
        )
        return torrent_info
    raise HTTPException(status_code=404, detail="Not Found")
