from fastapi import FastAPI, Request, Query
from typing import Annotated

from dht_api import btdigg

app = FastAPI()


@app.get("/info")
async def info(
    request: Request,
    info_hash: Annotated[
        str, Query(description="Torrent Info Hash", min_length=40, max_length=40)
    ],
):
    return await btdigg.get_torrent_info(info_hash)
