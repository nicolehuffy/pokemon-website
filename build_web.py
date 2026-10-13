"""build_web.py - makes share/pokemon-team-builder-web.html: one self-contained page for the shareable web link.
Like build_mirror.py, but every sprite is built in as one sprite sheet (the hosted page can't load images from other
sites, and one image keeps the page small), and the
page has no <html>/<head>/<body> wrapper because the host adds its own. Sprites are cached in your temp folder."""
import base64, io, json, os, re, tempfile
from concurrent.futures import ThreadPoolExecutor
import requests
from PIL import Image  # pip install pillow

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(tempfile.gettempdir(), "pokemon-team-builder-sprites")
IMG = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{}.png"


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def sprite(i):
    f = os.path.join(CACHE, f"{i}.png")
    if not os.path.exists(f):
        for _ in range(3):
            try:
                r = requests.get(IMG.format(i), timeout=30)
                if r.status_code == 200:
                    open(f, "wb").write(r.content)
                    break
            except requests.RequestException:
                pass
    return i, os.path.exists(f)


data = read("data/pokemon-data.js")
ids = [p["id"] for p in json.loads(data[data.index("["):data.rindex("]") + 1])]
os.makedirs(CACHE, exist_ok=True)
print("Getting", len(ids), "sprites (first run downloads them)...")
with ThreadPoolExecutor(8) as ex:
    got = [i for i, ok in ex.map(sprite, ids) if ok]
print("  got", len(got), "of", len(ids))

# Pack every sprite into ONE sprite sheet (a grid of 96x96 cells), so the page carries a single image instead of
# 1000+. The page shows each Pokemon by sliding the sheet to its cell (CSS background-position).
CELL, COLS = 96, 40
sheet = Image.new("RGBA", (CELL * COLS, CELL * -(-len(got) // COLS)), (0, 0, 0, 0))
for n, i in enumerate(got):
    im = Image.open(os.path.join(CACHE, f"{i}.png")).convert("RGBA")
    im.thumbnail((CELL, CELL))
    sheet.paste(im, ((n % COLS) * CELL + (CELL - im.width) // 2, (n // COLS) * CELL + (CELL - im.height) // 2))
buf = io.BytesIO()
sheet.save(buf, "WEBP", lossless=True, method=6)
uri = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
print(f"  sprite sheet: {sheet.width}x{sheet.height}, {len(buf.getvalue()) / 1e6:.1f} MB")
index = {i: n for n, i in enumerate(got)}

html = read("index.html")
html = html.replace('<link rel="stylesheet" href="style.css">', "<style>\n" + read("style.css") +
                    f"\n.sp.sh{{display:inline-block;background-image:url({uri});background-size:{COLS * 56}px auto}}\n</style>")
html = html.replace('<script src="data/pokemon-data.js"></script>',
                    "<script>window.OFFLINE=true;window.SHEET={cols:" + str(COLS) + ",idx:" +
                    json.dumps(index, separators=(",", ":")) + "}</script>\n<script>\n" + data + "\n</script>")
html = html.replace('<script src="app.js"></script>', "<script>\n" + read("app.js") + "\n</script>")
# The host page supplies <!doctype>, <html>, <head> and <body>, so keep only what goes inside them.
html = re.sub(r"<!DOCTYPE html>\s*<html[^>]*>\s*<head>", "", html, flags=re.I)
html = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>', "", html)
html = html.replace("</head><body>", "").replace("</body></html>", "")
html = html.lstrip()
assert html.startswith("<title>"), html[:80]

os.makedirs(os.path.join(ROOT, "share"), exist_ok=True)
out = os.path.join(ROOT, "share", "pokemon-team-builder-web.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print(f"Web version saved to: {out} ({os.path.getsize(out) / 1e6:.1f} MB)")
