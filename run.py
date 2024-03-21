# this file runs the fastapi under dht_api/app.py with uvicorn

import uvicorn
from os import environ

WORKERS = int(environ.get("WORKERS") or "2")
PORT = int(environ.get("PORT") or "8000")
HOST = environ.get("HOST") or "0.0.0.0"

if __name__ == "__main__":
    uvicorn.run("dht_api.api:app", host=HOST, port=PORT, reload=False, workers=WORKERS)
