import requests
import re
import json

def scrape_giphy_channel(url: str):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if r.status_code != 200:
        raise Exception("Failed to fetch Giphy page")

    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
    if not m:
        raise Exception("Unable to locate __NEXT_DATA__ JSON")

    data = json.loads(m.group(1))
    gifs = []

    try:
        media = data["props"]["pageProps"]["gifs"]
    except KeyError:
        media = []

    for gif in media:
        gif_id = gif["id"]
        title = gif.get("title") or "Giphy Pack"
        url = gif["images"]["original"]["url"]
        gifs.append({"id": gif_id, "url": url})

    pack_title = data["props"]["pageProps"].get("channel", {}).get("display_name", "Giphy Pack")

    return gifs, pack_title
