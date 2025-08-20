import os
import requests
from utils.scraper import scrape_giphy_channel
from utils.telegram_api import TelegramAPI
from utils.media import process_media
from utils.db import DB

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")

def main():
    url = input("Enter Giphy channel/collection URL: ").strip()
    db = DB("used_ids.db")
    tg = TelegramAPI(BOT_TOKEN)

    items, title = scrape_giphy_channel(url)
    new_items = [item for item in items if not db.is_used(item["id"])]

    if not new_items:
        print("All items already scraped for this source.")
        return

    selected = new_items[:50]
    sticker_files = []
    for item in selected:
        try:
            filepath = process_media(item["url"], item["id"])
            sticker_files.append(filepath)
            db.mark_used(item["id"])
        except Exception as e:
            print(f"Failed to process {item['id']}: {e}")

    if not sticker_files:
        print("No stickers processed.")
        return

    set_name = f"{title.replace(' ', '_')}_hardstickers"
    tg.create_or_update_pack(set_name, title + " @hardstickers", sticker_files)

    preview = sticker_files[0]
    tg.post_announcement(TARGET_CHANNEL_ID, title, set_name, preview)

    # cleanup temp files
    for f in sticker_files:
        os.remove(f)

if __name__ == "__main__":
    main()
