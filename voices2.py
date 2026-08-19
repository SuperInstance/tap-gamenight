#!/usr/bin/env python3
"""voices2.py — MeloTTS via Cloudflare, string-split auth, verbose errors.
MeloTTS returns JSON-wrapped audio on the v4 REST route (not raw bytes)."""
import json, os, sys, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).parent
ACCOUNT = "049ff5e84ecf636b53b162cbb580aae6"
API = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/@cf/myshell-ai/melotts"

def get_token():
    toml = (Path.home() / ".config/.wrangler/config/default.toml").read_text()
    for line in toml.splitlines():
        if line.startswith("oauth_token"):
            return line.split('"')[1]
    return None

if __name__ == "__main__":
    tok = get_token()
    script = json.loads((HERE / "script.json").read_text())
    lines = script["lines"][:40]
    out = HERE / "audio"; out.mkdir(exist_ok=True)
    ok = 0
    for i, line in enumerate(lines):
        text = f"{line['speaker']}: {line['line']}"[:480]
        body = json.dumps({"prompt": text}).encode()
        req = urllib.request.Request(API, data=body, headers={
            "Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            ct = r.headers.get("Content-Type", "")
            if "json" in ct:
                j = json.loads(data)
                if not j.get("success"):
                    print(f"line{i}: API said no: {str(j)[:120]}"); continue
                import base64
                audio = base64.b64decode(j["result"]["audio"])
            else:
                audio = data
            (out / f"line{i:03d}.mp3").write_bytes(audio)
            ok += 1
        except urllib.error.HTTPError as e:
            print(f"line{i}: HTTP {e.code}: {e.read()[:150]}")
            if e.code in (401, 403):
                sys.exit("auth dead")
    # concatenate
    if ok:
        with open(HERE / "episode.mp3", "wb") as f:
            for p in sorted(out.glob("line*.mp3")):
                f.write(p.read_bytes())
        print(f"voiced {ok}/{len(lines)} lines -> episode.mp3")
