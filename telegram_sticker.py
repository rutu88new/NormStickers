import os
import re
import aiohttp
import asyncio
from typing import List, Tuple

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_USER_ID = int(os.getenv("OWNER_USER_ID", "0"))
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID", "").strip()

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def _api(method: str, data=None, files=None):
    url = f"{API_BASE}/{method}"
    async with aiohttp.ClientSession() as sess:
        if files:
            form = aiohttp.FormData()
            if data:
                for k, v in data.items():
                    form.add_field(k, str(v))
            for k, (fname, fobj, ctype) in files.items():
                form.add_field(k, fobj, filename=fname, content_type=ctype)
            async with sess.post(url, data=form) as r:
                return await r.json()
        else:
            async with sess.post(url, json=data or {}) as r:
                return await r.json()

async def get_me():
    return await _api("getMe")

def slugify_short_name(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9_]+", "_", name).strip("_").lower()
    base = base[:48] if len(base) > 48 else base
    return base or "stickerpack"

async def ensure_pack(title: str, short_base: str) -> Tuple[str, str]:
    me = await get_me()
    if not me.get("ok"):
        raise RuntimeError("Invalid BOT_TOKEN or network issue")
    bot_username = me["result"]["username"]
    # short name must end with _by_<botusername>
    suffix = f"_by_{bot_username}"
    short_name_try = slugify_short_name(short_base)
    short_name = short_name_try + suffix

    # Try creating; if name taken, add numeric suffix
    attempt = 0
    while True:
        resp = await _api("createNewStickerSet", data={
            "user_id": OWNER_USER_ID,
            "name": short_name,
            "title": title,
            "sticker_format": "static"
        })
        if resp.get("ok"):
            return title, short_name
        elif "SHORTNAME_OCCUPIED" in str(resp):
            attempt += 1
            short_name = f"{short_name_try}_{attempt}{suffix}"
            continue
        elif "STICKERSET_INVALID" in str(resp) or "name is already occupied" in str(resp).lower():
            attempt += 1
            short_name = f"{short_name_try}_{attempt}{suffix}"
            continue
        else:
            # Maybe it already exists; return it
            return title, short_name

async def add_png_sticker(short_name: str, png_path: str, emoji: str="🙂"):
    with open(png_path, "rb") as f:
        files = {"sticker": (os.path.basename(png_path), f, "image/png")}
        data = {
            "user_id": OWNER_USER_ID,
            "name": short_name,
            "sticker": "attach://sticker",
            "emoji_list": [emoji]
        }
        return await _api("addStickerToSet", data=data, files=files)

async def send_channel_post(caption: str, button_text: str, button_url: str, animation_path: str=None):
    # Build inline keyboard
    keyboard = {
        "inline_keyboard": [[{"text": button_text, "url": button_url}]]
    }
    data = {
        "chat_id": TARGET_CHANNEL_ID,
        "parse_mode": "HTML",
        "reply_markup": keyboard,
        "disable_notification": True,
        "caption": caption
    }
    if animation_path:
        with open(animation_path, "rb") as f:
            files = {"animation": (os.path.basename(animation_path), f, "video/mp4")}
            data["animation"] = "attach://animation"
            return await _api("sendAnimation", data=data, files=files)
    else:
        return await _api("sendMessage", data=data)
