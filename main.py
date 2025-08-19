import os
import asyncio
import tempfile
import hashlib
from pathlib import Path
from typing import List, Tuple
from dotenv import load_dotenv
from tqdm import tqdm
import aiohttp

from utils import db
from utils import media
from giphy_client import fetch_collections, fetch_items
from telegram_sticker import ensure_pack, add_png_sticker, send_channel_post

def hash_url(u: str) -> str:
    return hashlib.sha256((u or "").encode("utf-8")).hexdigest()

def bold(s: str) -> str:
    return f"<b>{s}</b>"

def titlecase(s: str) -> str:
    return s.strip().title()

async def download_file(url: str, out_path: Path):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as r:
            r.raise_for_status()
            out_path.write_bytes(await r.read())

async def choose_collection(profile: str) -> str:
    cols = await fetch_collections(profile)
    cols = [c for c in cols if len(c) >= 1]
    print("\nAvailable collections:")
    if not cols:
        print("  (No collections discovered. We'll scrape the profile feed instead.)")
        return ""
    for i, c in enumerate(cols, 1):
        print(f"  {i}. {c}")
    print("  0. All/Random from profile feed")
    while True:
        pick = input("Choose a collection by number (or 0): ").strip()
        if pick.isdigit():
            n = int(pick)
            if n == 0:
                return ""
            if 1 <= n <= len(cols):
                return cols[n-1]
        print("Invalid choice, try again.")

async def main():
    load_dotenv()
    db.init()

    profile = input("Enter GIPHY channel/profile (username or URL): ").strip()
    collection = await choose_collection(profile)

    # Determine target list
    print("Gathering items...")
    items = await fetch_items(profile, collection=collection or None, limit=300)
    # Filter URL-bearing items
    items = [it for it in items if it.get("webp") or it.get("url")]
    # Dedup by id and url
    uniq = {}
    for it in items:
        key = it.get("id") or it.get("url")
        if key and key not in uniq:
            uniq[key] = it
    items = list(uniq.values())

    # Remove already processed
    source = profile
    coll_name = collection or "full_feed"
    remaining = []
    for it in items:
        item_id = it.get("id") or hash_url(it.get("url") or it.get("webp") or "")
        if not db.is_seen(source, coll_name, item_id):
            remaining.append(it)

    if not remaining:
        print(f"Collection '{coll_name}' is already fully scraped. Nothing to do.")
        return

    # Cap at 50
    target = remaining[:50]
    print(f"{len(target)} new items will be scraped (max 50).")

    confirm = input("Proceed? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    # Prepare pack naming
    visual_title = f"{titlecase(coll_name)} @hardstickers"
    short_base = coll_name.replace(" ", "_")

    # Ensure pack
    title, short_name = await ensure_pack(visual_title, short_base)
    print(f"Using pack short name: {short_name}")

    # Temp workspace
    tmpdir = Path(tempfile.mkdtemp(prefix="stickers_"))
    preview_src = None
    try:
        for it in tqdm(target, desc="Processing", unit="item"):
            url = it.get("webp") or it.get("url")
            if not url:
                continue
            item_id = it.get("id") or hash_url(url)
            # Download
            src_path = tmpdir / f"{item_id}.bin"
            try:
                await download_file(url, src_path)
            except Exception as e:
                continue

            # Convert to PNG sticker
            png_path = tmpdir / f"{item_id}.png"
            try:
                media.best_guess_to_png(src_path, png_path)
            except Exception as e:
                continue

            # Add to pack
            try:
                await add_png_sticker(short_name, str(png_path), emoji="🙂")
            except Exception as e:
                # Try continue to next
                continue

            # Remember (even if add failed, so we don't loop on bad files)
            db.remember_item(source, coll_name, item_id, hash_url(url))

            # Keep one source for preview
            if preview_src is None:
                preview_src = str(src_path)

        # Post to channel
        if preview_src:
            preview_mp4 = tmpdir / "preview.mp4"
            try:
                media.make_black_bg_preview(preview_src, preview_mp4, seconds=2)
                button_text = "View the pack"
                button_url = f"https://t.me/addstickers/{short_name}"
                caption = (bold("New sticker pack released") + "\n" +
                           bold(titlecase(coll_name)) + "\n" +
                           "Subscribe for more 🙂")
                await send_channel_post(caption=caption,
                                        button_text=button_text,
                                        button_url=button_url,
                                        animation_path=str(preview_mp4))
            except Exception as e:
                # fall back to text-only
                button_text = "View the pack"
                button_url = f"https://t.me/addstickers/{short_name}"
                caption = (bold("New sticker pack released") + "\n" +
                           bold(titlecase(coll_name)) + "\n" +
                           "Subscribe for more 🙂")
                await send_channel_post(caption=caption,
                                        button_text=button_text,
                                        button_url=button_url,
                                        animation_path=None)
        else:
            print("No preview source found; skipping channel animation.")
    finally:
        # Clean temp folder to save space
        try:
            for p in tmpdir.glob("*"):
                p.unlink(missing_ok=True)
            tmpdir.rmdir()
        except Exception:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
