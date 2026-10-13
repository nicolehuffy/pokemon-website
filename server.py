"""server.py - runs the site on your computer and saves teams to data/teams.csv"""
import csv, json, os, threading, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
TEAMS = os.path.join(ROOT, "data", "teams.csv")
PORT = 8000


def read_teams():
    if not os.path.exists(TEAMS):
        return []
    with open(TEAMS, encoding="utf-8-sig", newline="") as f:
        return [{"id": r["id"], "name": r["name"], "game": r["game"],
                 "members": [m for m in r["members"].split(";") if m]}
                for r in csv.DictReader(f)]


def write_teams(teams):
    with open(TEAMS, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "game", "members"])
        for t in teams:
            w.writerow([t["id"], t["name"], t["game"], ";".join(t["members"])])


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def reply(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/teams":
            return self.reply(read_teams())
        super().do_GET()

    def do_POST(self):
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/api/teams":
            write_teams(json.loads(data))
            return self.reply({"ok": True})
        if self.path == "/api/shutdown":
            self.reply({"ok": True})
            threading.Thread(target=server.shutdown).start()
            return
        self.send_error(404)


server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
print(f"Pokemon Team Builder running at http://localhost:{PORT}/")
print("Use the 'Stop server' button on the site, or close this window, to quit.")
threading.Timer(1, lambda: webbrowser.open(f"http://localhost:{PORT}/")).start()
server.serve_forever()