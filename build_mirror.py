"""build_mirror.py - makes share/pokemon-team-builder-share.html, one standalone file
with no saving and no server, safe to send to friends."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


html = read("index.html")
html = html.replace('<link rel="stylesheet" href="style.css">', "<style>\n" + read("style.css") + "\n</style>")
html = html.replace('<script src="data/pokemon-data.js"></script>',
                    "<script>window.OFFLINE=true</script>\n<script>\n" + read("data/pokemon-data.js") + "\n</script>")
html = html.replace('<script src="app.js"></script>', "<script>\n" + read("app.js") + "\n</script>")

os.makedirs(os.path.join(ROOT, "share"), exist_ok=True)
out = os.path.join(ROOT, "share", "pokemon-team-builder-share.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("Shareable copy saved to:", out)