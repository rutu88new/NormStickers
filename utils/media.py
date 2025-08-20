import requests
from PIL import Image
from io import BytesIO

def process_media(url, gid):
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        raise Exception("Failed to download media")
    img = Image.open(BytesIO(r.content)).convert("RGBA")
    img.thumbnail((512, 512))
    out_path = f"{gid}.png"
    img.save(out_path, "PNG")
    return out_path
