from fastapi import FastAPI, Request, Query, HTTPException
from typing import Annotated

from dht_api import btdigg
import structlog

log = structlog.get_logger(__name__)

app = FastAPI()


@app.get("/info")
async def info(
    request: Request,
    info_hash: Annotated[
        str, Query(description="Torrent Info Hash", min_length=40, max_length=40)
    ],
):
    torrent_info = await btdigg.get_torrent_info(info_hash)
    if torrent_info:
        return torrent_info
    raise HTTPException(status_code=404, detail="Not Found")
