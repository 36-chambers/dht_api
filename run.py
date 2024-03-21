# this file runs the fastapi under dht_api/app.py with uvicorn

import uvicorn

if __name__ == "__main__":
    uvicorn.run("dht_api.api:app", host="0.0.0.0", port=8000, reload=False, workers=10)
