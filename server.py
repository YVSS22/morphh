#!/usr/bin/env python3
"""Photoreal — transforme un personnage (dessin animé, photo, etc.) en version photoréaliste.

Backend minimal : sert le frontend + POST /api/photoreal (image -> Gemini Nano Banana).
"""
import base64
import json
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = Path(__file__).resolve().parent
PORT = 8649
OUT = BASE / "out"

def _key(name):
    for line in Path("/root/.hermes/profiles/jorvas/.env").read_text().splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

GEMINI = _key("GEMINI_API_KEY")
MODEL = "gemini-nano-banana-2.1"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={GEMINI}"

PROMPT = (
    "Recreate this character as a real person in a casual smartphone photo, "
    "exactly as if someone had just taken it with a phone camera. "
    "Keep the exact same facial features, proportions, hairstyle, hair color, "
    "outfit, accessories and expression. "
    "Natural everyday lighting — window light or outdoor daylight, no studio light, "
    "no professional flash. Slightly imperfect amateur framing, realistic skin with "
    "visible pores, fine lines, blemishes and subtle imperfections, natural relaxed "
    "expression, ordinary real-world background. "
    "Authentic candid phone-photo look, high resolution, 4k."
)


def gemini_photoreal(image_b64, mime):
    body = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime, "data": image_b64}},
            {"text": PROMPT},
        ]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"imageSize": "4K"}},
    }
    req = urllib.request.Request(GEMINI_URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = json.loads(r.read().decode())
    for part in (d.get("candidates") or [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part and part["inlineData"].get("data"):
            return part["inlineData"]["data"]
    raise RuntimeError("pas d'image dans la réponse Gemini")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._send(200, (BASE / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/style.css":
            return self._send(200, (BASE / "style.css").read_bytes(), "text/css")
        if path == "/app.js":
            return self._send(200, (BASE / "app.js").read_bytes(), "application/javascript")
        if path.startswith("/out/"):
            f = BASE / path.lstrip("/")
            if f.is_file():
                return self._send(200, f.read_bytes(), "image/jpeg")
        self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path.split("?")[0] != "/api/photoreal":
            return self._send(404, b"not found", "text/plain")
        try:
            n = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(n).decode())
            img = data["image"]
            mime = data.get("mime", "image/png")
            # si le client envoie déjà un data URI, on enlève le préfixe
            if "," in img and img.lstrip().startswith("data:"):
                head, img = img.split(",", 1)
                m = re.search(r"data:([^;]+);", head)
                if m:
                    mime = m.group(1)
            out_b64 = gemini_photoreal(img, mime)
            name = f"morphh_{int(time.time() * 1000)}.jpg"
            (OUT / name).write_bytes(base64.b64decode(out_b64))
            self._send(200, json.dumps({"url": f"/out/{name}"}).encode(),
                       "application/json")
        except urllib.error.HTTPError as e:
            self._send(e.code, e.read(), "application/json")
        except Exception as e:
            self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")

    def log_message(self, fmt, *args):
        pass  # silencieux


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Morphh sur http://0.0.0.0:{PORT}")
    srv.serve_forever()
