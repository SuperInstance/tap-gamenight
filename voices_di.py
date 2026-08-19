#!/usr/bin/env python3
"""voices_di.py — fallback TTS trailer via DeepInfra (Cloudflare OAuth expired).
No regex — the key is parsed by string split (a certain character class kept
getting mangled in transit)."""
import json, os, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).parent

def get_key():
    bashrc = open(os.path.expanduser("~/.bashrc")).read()
    for line in bashrc.splitlines():
        if line.startswith("export DEEPINFRA_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get("DEEPINFRA_API_KEY", "")

API = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-TTS-VoiceDesign"

if __name__ == "__main__":
    key = get_key()
    if not key:
        sys.exit("no key")
    script = json.loads((HERE / "script.json").read_text())
    picks = [l for l in script["lines"] if l["speaker"] in ("Lucineer", "Wesley")][:4]
    out = HERE / "audio"; out.mkdir(exist_ok=True)
    try:
        for i, line in enumerate(picks):
            body = json.dumps({"input": f"{line['speaker']}: {line['line']}"[:400]}).encode()
            req = urllib.request.Request(API, data=body, headers={
                "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                (out / f"trailer{i}.mp3").write_bytes(r.read())
        print(f"trailer voiced: {len(picks)} lines")
    except Exception as e:
        print(f"deepinfra tts unavailable ({e}); transcript stands alone")
