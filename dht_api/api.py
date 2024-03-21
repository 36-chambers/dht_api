from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from os import environ
from typing import Annotated

import structlog
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Response

from dht_api import btdigg
from dht_api.bucket import S3Manager, S3Object
from dht_api.schemas import Torrent

log = structlog.get_logger(__name__)

STALE_TORRENT_DAYS = int(environ.get("STALE_TORRENT_DAYS") or "7")
AWS_BUCKET_NAME = environ.get("AWS_BUCKET_NAME") or ""

s3 = S3Manager(AWS_BUCKET_NAME)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    yield


app = FastAPI(lifespan=lifespan)


async def refresh_torrent(obj: S3Object, info_hash: str) -> None:
    diff = datetime.now(timezone.utc) - obj.last_modified
    log.debug("cache age", info_hash=info_hash, age=diff)
    if diff <= timedelta(days=STALE_TORRENT_DAYS):
        log.debug("cache is fresh", info_hash=info_hash)
        return

    log.info("cache is stale, refreshing", info_hash=info_hash)
    torrent_info = await btdigg.get_torrent_info(info_hash)
    if torrent_info:
        if await s3.write(info_hash, torrent_info):
            log.info("refreshed", info_hash=info_hash)
        else:
            log.error("failed to refresh", info_hash=info_hash)


@app.get("/info")
async def info(
    response: Response,
    background_tasks: BackgroundTasks,
    info_hash: Annotated[
        str,
        Query(description="Torrent Info Hash", min_length=40, max_length=40, transform=str.upper),
    ],
) -> Torrent:
    obj = await s3.read(info_hash, Torrent)
    if obj:
        background_tasks.add_task(refresh_torrent, obj, info_hash)
        response.headers["Cache-Control"] = f"max-age={STALE_TORRENT_DAYS * 86400}"
        return obj.item

    torrent_info = await btdigg.get_torrent_info(info_hash)
    if torrent_info:
        await s3.write(info_hash, torrent_info)
        response.headers["Cache-Control"] = f"max-age={STALE_TORRENT_DAYS * 86400}"
        return torrent_info
    raise HTTPException(status_code=404, detail="Not Found")
