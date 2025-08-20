import requests

class TelegramAPI:
    def __init__(self, bot_token):
        self.token = bot_token
        self.base = f"https://api.telegram.org/bot{bot_token}"

    def create_or_update_pack(self, name, title, files):
        # NOTE: For simplicity, this demo uses static stickers (PNG).
        # For animated stickers you'd need TGS/Lottie conversion and User API session.
        for i, f in enumerate(files):
            if i == 0:
                method = "createNewStickerSet"
            else:
                method = "addStickerToSet"

            with open(f, "rb") as img:
                r = requests.post(
                    f"{self.base}/{method}",
                    data={
                        "user_id": 123456789,  # replace with your telegram user id
                        "name": name,
                        "title": title,
                        "emojis": "😀"
                    },
                    files={"png_sticker": img}
                )
                print(r.json())

    def post_announcement(self, channel_id, title, set_name, preview_path):
        with open(preview_path, "rb") as img:
            r = requests.post(
                f"{self.base}/sendAnimation",
                data={
                    "chat_id": channel_id,
                    "caption": f"<b>New Sticker Pack Released!</b>\n{title}\nSubscribe for more 🙂",
                    "parse_mode": "HTML",
                    "reply_markup": json.dumps({
                        "inline_keyboard": [[
                            {"text": "View the pack", "url": f"https://t.me/addstickers/{set_name}"}
                        ]]
                    })
                },
                files={"animation": img}
            )
            print(r.json())
