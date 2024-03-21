from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Annotated

import structlog
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query

from dht_api import btdigg, db, schemas

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    await db.init()
    yield


app = FastAPI(lifespan=lifespan)


async def refresh_torrent_info(info_hash: str) -> None:
    torrent_info = await btdigg.get_torrent_info(info_hash)
    if torrent_info:
        log.info("updating torrent_info", info_hash=info_hash)
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


@app.get("/info")
async def info(
    background_tasks: BackgroundTasks,
    info_hash: Annotated[str, Query(description="Torrent Info Hash", min_length=40, max_length=40)],
) -> schemas.Torrent:
    torrent_info = await db.get_torrent(info_hash)
    if torrent_info:
        diff = datetime.utcnow() - torrent_info.updated_at
        log.info("diff", diff=diff.total_seconds())
        if diff.total_seconds() > timedelta(days=7).total_seconds():
            log.info("torrent_info is stale, refreshing")
            background_tasks.add_task(refresh_torrent_info, info_hash)
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
