# Telegram Sticker Pack Automation (GIPHY → Telegram)

A single-script automation that:
1. Lists GIPHY user **collections** (or falls back to the entire profile feed).
2. Scrapes up to **50** sticker-like assets (transparent when available).
3. **Deduplicates** using a tiny SQLite database (no images are kept after pack creation).
4. **Creates** a **static** Telegram sticker pack (PNG) titled: `<collection name> @hardstickers`.
5. **Posts** a professional message with an inline **View the pack** button to your channel,
   and attaches a short **preview animation** made from one of the scraped items (on a black background).

> Why static PNG stickers?
> Creating animated/video stickers requires strict WEBM/VP9 encoding and user/bot permissions.
> This project focuses on robust static stickers with transparency. You can extend `utils/media.py`
> if you want to add WEBM generation later.

---

## Quick Start

### 1) Install system dependencies
- Python 3.10+
- **ffmpeg** available on PATH (needed to render the preview clip)
- (Optional) A GIPHY API key (otherwise the script uses HTML scraping heuristics)

### 2) Create and fill `.env`

Create a file named `.env` in the project root:

```
BOT_TOKEN=123456:your-bot-token-here
OWNER_USER_ID=123456789           # numeric Telegram user id that will own the sticker pack
TARGET_CHANNEL_ID=@your_channel   # @username or numeric id (e.g. -100123456789)
GIPHY_API_KEY=                    # optional, leave blank to use HTML scraping
```

**Important:** The `OWNER_USER_ID` **must** have started your bot at least once (`/start`),
otherwise the Bot API won't let the bot create a sticker set for that user.

### 3) Install Python deps

```
pip install -r requirements.txt
```

### 4) Run

```
python main.py
```

You will be prompted for:
- The **GIPHY profile** (e.g. `circlecan` or a full URL).
- The **collection** to scrape (or `all` / `random` if you prefer the full feed).
- Confirmation to proceed (it shows how many **new** items it will fetch).

The script:
- Downloads to a temp folder,
- Converts the first frame to **512px max** PNG with transparency,
- Builds a **new** sticker pack if not existing, otherwise appends new stickers,
- Posts to your channel with a neat message and a **View the pack** inline button,
- Cleans up all downloaded files (only the small SQLite db remains to avoid duplicates).

---

## Notes & Assumptions

- **Naming:** The visual *title* becomes `<collection> @hardstickers`. Telegram also needs a *short name*
  that must be **globally unique** and **end with** `_by_<yourbotusername>`. The script auto-derives this
  from the collection name + your bot username (pulled from `getMe`). If a clash happens, a numeric suffix
  is added.
- **Duplicates:** We store only **URL hashes** and item ids in `data/state.sqlite`.
- **Transparency:** Preserved when the source has an alpha channel. Non-transparent sources remain opaque.
- **If a collection is fully scraped** already, the script will say so and exit gracefully.
- **If a collection partially scraped,** it will continue from the remaining items.

---

## Files

- `main.py` – CLI + orchestration
- `giphy_client.py` – collection discovery + item scraping (API when key provided; else HTML fallback)
- `telegram_sticker.py` – minimal Bot API wrappers for sticker pack ops and channel posting
- `utils/media.py` – image processing (PNG) + preview rendering
- `utils/db.py` – tiny SQLite helper to track processed items
- `.env` – your secrets
- `requirements.txt`
- `README.md`

---

## Safety & Respect

- Scrape only with permission and follow GIPHY and Telegram terms.
- Always credit creators when appropriate.
- This code is provided as-is; you’re responsible for compliance and moderation.
