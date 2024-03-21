# DHT API

A JSON API wrapper to fetch **metadata** about torrents from info hashes. This application uses **Tor network** and requires a socks5 proxy (included in the docker-compose.yaml)

## How to Use

```
$ docker compose up -d
 ✔ Container dht_api-torproxy-1  Started
 ✔ Container dht_api-dht_api-1   Started
 
$ curl -D /dev/stderr -SLs 'http://127.0.0.1:8000/info?info_hash=f1d0336509ec07fb7801ca56cbbb7b5d000f8f10' | jq .

HTTP/1.1 200 OK
date: Thu, 21 Mar 2024 04:16:59 GMT
server: uvicorn
content-length: 513
content-type: application/json

{
  "name": "The Lord of the Rings - The Extended Trilogy [HDR 2160p NVEnc 10Bit HVEC][Dolby TrueHD-Atmos 7.1Ch][BDRip][Multi Sub]",
  "size": 69943542415,
  "age": "1 year",
  "files": [
    {
      "filename": "[1] The Lord of the Rings - The Fellowship of the Ring (2001) - Extended Edition.mkv",
      "size": 21882858373
    },
    {
      "filename": "[2] The Lord of the Rings - The Two Towers (2002) - Extended Edition.mkv",
      "size": 22666689904
    },
    {
      "filename": "[3] The Lord of the Rings - The Return of the King (2003) - Extended Edition.mkv",
      "size": 25393994137
    }
  ]
}

```

---

### Disclaimer

:warning: *This application only fetches metadata about info hashes and does not interact with any torrent protocols. However, it may still be illegal in your region. I am not responsible if you run this application in a country where it might be illegal or for what you do with the content.*  :warning:
