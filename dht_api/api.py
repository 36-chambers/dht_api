import math
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from os import environ
from typing import Annotated

import structlog
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Response

from dht_api import btdigg, db, schemas

log = structlog.get_logger(__name__)

STALE_TORRENT_DAYS = int(environ.get("STALE_TORRENT_DAYS") or "7")


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
    response: Response,
    background_tasks: BackgroundTasks,
    info_hash: Annotated[str, Query(description="Torrent Info Hash", min_length=40, max_length=40)],
) -> schemas.Torrent:
    torrent_info = await db.get_torrent(info_hash)
    if torrent_info:
        diff = datetime.utcnow() - torrent_info.updated_at
        log.info("diff", diff=diff.total_seconds())
        if diff.total_seconds() > timedelta(days=STALE_TORRENT_DAYS).total_seconds():
            log.info("torrent_info is stale, refreshing")
            background_tasks.add_task(refresh_torrent_info, info_hash)
        expiration_seconds = math.ceil(
            max(0, timedelta(days=STALE_TORRENT_DAYS).total_seconds() - diff.total_seconds())
        )
        response.headers["Cache-Control"] = f"max-age={expiration_seconds}"
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
        response.headers["Cache-Control"] = f"max-age={STALE_TORRENT_DAYS * 86400}"
        return torrent_info
    raise HTTPException(status_code=404, detail="Not Found")
