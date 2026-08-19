#!/usr/bin/env python3
"""voices.py — TTS the show via Cloudflare Workers AI MeloTTS (free tier).
Degrades gracefully: if Cloudflare auth fails, prints a clear note and exits 0
(the transcript + script.json are the durable artifacts)."""
import json, os, re, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
ACCOUNT = "049ff5e84ecf636b53b162cbb580aae6"
API = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/@cf/myshell-ai/melotts"

def bearer():
    toml = (Path.home() / ".config/.wrangler/config/default.toml").read_text()
    tok = re.search(r'oauth_token = "([^"]+)"', toml)
    ref = re.search(r'refresh_token = "([^"]+)"', toml)
    return (tok.group(1) if tok else None, ref.group(1) if ref else None)

def tts(text, token):
    body = json.dumps({"input": text[:480]}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()  # audio/mpeg bytes

if __name__ == "__main__":
    tok, ref = bearer()
    if not tok:
        print("no wrangler token; skipping voices"); sys.exit(0)
    script = json.loads((HERE / "script.json").read_text())
    out = HERE / "audio"; out.mkdir(exist_ok=True)
    segs = []
    try:
        for i, line in enumerate(script["lines"][:40]):  # first 40 lines this pass
            mp3 = tts(f"{line['speaker']}: {line['line']}", tok)
            p = out / f"line{i:03d}.mp3"; p.write_bytes(mp3); segs.append(p)
        ep = HERE / "episode.mp3"
        with open(ep, "wb") as f:
            for p in segs: f.write(p.read_bytes())
        print(f"voiced {len(segs)} lines -> episode.mp3")
    except urllib.error.HTTPError as e:
        print(f"cloudflare auth/API failed ({e.code}); transcript stands alone this week")