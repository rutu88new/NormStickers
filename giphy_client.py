import os
import re
import json
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List, Dict, Tuple

API_KEY = os.getenv("GIPHY_API_KEY", "").strip()

def _profile_from_input(s: str) -> str:
    s = s.strip()
    if s.startswith("http"):
        path = urlparse(s).path.strip("/")
        return path.split("/")[0] if path else s
    return s

async def fetch_collections(profile: str) -> List[str]:
    profile = _profile_from_input(profile)
    # Try API first (if key provided)
    if API_KEY:
        api_url = f"https://api.giphy.com/v1/channels/{profile}?api_key={API_KEY}"
        async with aiohttp.ClientSession() as sess:
            async with sess.get(api_url) as r:
                if r.status == 200:
                    data = await r.json()
                    cols = data.get("data", {}).get("featured_collections", [])
                    names = [c.get("name") for c in cols if c.get("name")]
                    return list(dict.fromkeys(names))
    # Fallback: HTML scrape
    url = f"https://giphy.com/{profile}"
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as r:
            html = await r.text()
    soup = BeautifulSoup(html, "lxml")
    # Collections appear as text labels in links; we pick distinct ones
    names = []
    for a in soup.find_all("a"):
        txt = (a.get_text() or "").strip()
        if txt and len(txt) < 40 and not any(x in txt.lower() for x in ["giphy", "share channel", "uploads"]):
            # very light heuristic: collection chips often short
            names.append(txt)
    # Deduplicate while preserving order
    seen = set()
    out = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    # Keep top few, it's a heuristic
    return out[:25]

async def fetch_items(profile: str, collection: str=None, limit: int=200) -> List[Dict]:
    profile = _profile_from_input(profile)
    items = []

    if API_KEY and collection:
        # Use search by collection tag (heuristic)
        search_url = f"https://api.giphy.com/v1/gifs/search?api_key={API_KEY}&q={collection}&limit={limit}&sort=relevant"
        async with aiohttp.ClientSession() as sess:
            async with sess.get(search_url) as r:
                if r.status == 200:
                    data = await r.json()
                    for d in data.get("data", []):
                        items.append({
                            "id": d.get("id"),
                            "url": d.get("images", {}).get("original", {}).get("url"),
                            "webp": d.get("images", {}).get("original", {}).get("webp"),
                            "title": d.get("title") or ""
                        })
        return items

    # HTML fallback: parse initial JSON blob
    url = f"https://giphy.com/{profile}"
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as r:
            html = await r.text()
    m = re.search(r'__NEXT_DATA__\">(.*?)</script>', html)
    if m:
        try:
            j = json.loads(m.group(1))
            # Walk a bit to the gifs list if present
            gifs = []
            try:
                gifs = j["props"]["pageProps"]["pageData"]["gifs"]
            except Exception:
                pass
            for g in gifs[:limit]:
                images = g.get("images", {})
                items.append({
                    "id": g.get("id"),
                    "url": images.get("original", {}).get("url"),
                    "webp": images.get("original", {}).get("webp"),
                    "title": g.get("title") or ""
                })
        except Exception:
            pass
    return items[:limit]
