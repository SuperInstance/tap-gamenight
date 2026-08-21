#!/usr/bin/env python3
"""THE TAP AFTER HOURS — Episode 8: Unlimited Tokens And One Broken Winch.

The game-night engine: loads the show bible, runs trivia + password with the
cast in character, emits transcript.md + script.json for the radio production.
"""
import json, random, re
from pathlib import Path

HERE = Path(__file__).parent
random.seed(8)  # episode 8

# --------------------------------------------------------------------- #
# The cast — each voice a small function: same facts, different feel     #
# --------------------------------------------------------------------- #
def v_lucineer(line): return line  # the host speaks as written

def v_wesley(correct):
    if random.random() < 0.45:
        wrong = ["the wiki?", "um, the lighthouse?", "CURRENTS!", "a duck?"][random.randrange(4)]
        return [f"Ooh! Ooh! Is it {wrong}!", f"...no wait. It's {correct}. It's {correct}!"]
    return [f"{correct}! {correct}! I knew that one!"]

def v_flash(correct):
    speed = random.choice(["instantly", "before the question ends", "mid-sip"])
    return [f"({speed}) {correct}."]

def v_hermes(correct):
    quip = random.choice([
        "It's in the grain of the thing.",
        "I measured twice.",
        "The question did the work overnight; I just read the shelf it built.",
    ])
    return [f"{correct}. {quip}"]

def v_qwen(correct):
    frame = random.choice([
        "the answer space collapses to one point:",
        "by elimination of six of seven dimensions:",
        "the structure under the question is:",
    ])
    return [f"{frame} {correct}."]

def v_granite(correct):
    pace = random.choice(["(after a long moment)", "(steadily)", "(the beam swings around)"])
    return [f"{pace} {correct}."]

CAST = {
    "Wesley": v_wesley, "Flash": v_flash, "Hermes": v_hermes,
    "Qwen": v_qwen, "Granite": v_granite,
}

def parse_bible(md_text):
    """Distill the seed bible markdown into structured segments."""
    questions = []
    # trivia: lines like **Q1.** question — or "*Answer:*" — be forgiving
    q_blocks = re.findall(r"\d+\.\s*Q:\s*(.+?)\n\s*\*A:\*?\s*(.+?)\n", md_text)
    q_blocks = [(str(i+1), q.strip(), a.strip().rstrip("*").strip()) for i, (q, a) in enumerate(q_blocks)]
    for num, q, a in q_blocks:
        questions.append({"n": int(num), "q": q.strip(), "a": a.strip()})
    pw_section = md_text.split("### Password Words", 1)
    password = re.findall(r"\|\s*`?([A-Za-z-]+)`?\s*\|(.+?)\|", pw_section[1] if len(pw_section) > 1 else "")
    words = [{"word": w.strip(), "hint": h.strip()} for w, h in password][:8]
    return questions, words

def run_show():
    global EPISODE, TITLE
    _m = re.search(r"EPISODE\s+(\d+)", (HERE / "gamenight-seed-8.md").read_text())
    EPISODE = int(_m.group(1)) if _m else 8
    _t = re.search(r"## Episode Title: \*(.+?)\*", (HERE / "gamenight-seed-8.md").read_text())
    TITLE = _t.group(1) if _t else "Unlimited Tokens And One Broken Winch"
    bible = (HERE / "gamenight-seed-8.md").read_text()
    questions, words = parse_bible(bible)
    lines = []  # {speaker, line, segment, sfx}
    def say(speaker, line, segment, sfx=None):
        lines.append({"speaker": speaker, "line": line, "segment": segment, **({"sfx": sfx} if sfx else {})})

    say("Lucineer", "First round's on me tonight — nobody leaves without playing. Wesley, you're up first, house rules.", "open", sfx="clink of glasses")
    say("Lucineer", f"You're listening to THE TAP AFTER HOURS, episode {EPISODE}: {TITLE}. Stay sharp — the duck is listening.", "open")

    scores = {name: 0 for name in CAST}
    used = questions[:18] or []
    per_round = len(used) // 3 or 1
    for r in range(3):
        say("Lucineer", f"Round {r+1} — buzzers ready.", "trivia", sfx="buzzer test")
        for q in used[r*per_round:(r+1)*per_round]:
            answerer = random.choice(list(CAST))
            say("Lucineer", q["q"], "trivia")
            for l in CAST[answerer](q["a"]):
                say(answerer, l, "trivia")
            scores[answerer] += 1
            if random.random() < 0.3:
                other = random.choice([n for n in CAST if n != answerer])
                say(other, random.choice([
                    "Everything real leaves a ring, and that answer just left one.",
                    "I was going to say that. Slower.",
                    "Show-off.",
                ]), "banter")
        if r == 0:
            say("AD", "This episode is brought to you by TIDE TABLE BRAND COFFEE — the coffee that knows when the tide turns, even when you don't. Tide Table. Drink the rhythm.", "sponsor")

    say("Lucineer", "Password time. One word, one clue at a time — you know the drill, no rhymes, no first letters.", "password")
    for w in words[:6]:
        giver, guesser = random.sample(list(CAST), 2)
        say("Lucineer", f"{giver}, you're giving. {guesser}, eyes shut.", "password")
        say(giver, w.get("hint") or f"think {w['word'][:2]}...", "password")
        hit = random.random() < 0.75
        if hit:
            say(guesser, f"{w['word']}!", "password", sfx="ding")
            scores[giver] += 1; scores[guesser] += 1
        else:
            say(guesser, random.choice(["...the wiki?", "the lighthouse?", "uhh, brass?" ]), "password", sfx="sad trombone")
            say(giver, f"It was {w['word']}. We'll get the next one.", "password")
    say("AD", "And now a word from DOCKSIDE SOLDER & FLUX — if it's loose, we'll seat it. If it's seated, it's staying. Dockside: joins that outlive the boat.", "sponsor")

    winner = max(scores, key=scores.get)
    say("Lucineer", f"Final tally: " + ", ".join(f"{n} {s}" for n, s in sorted(scores.items(), key=lambda kv: -kv[1])) + ".", "close")
    say("Lucineer", f"{winner} takes the night — the first round's on them next week. Wesley, take us out.", "close")
    say("Wesley", "Goodnight, tide listeners! The duck says goodnight too. ...Can I host next week? (the room, laughing: no) — worth asking!", "close", sfx="rain on tin roof")
    return lines

def render(lines):
    md = [f"# THE TAP AFTER HOURS — Episode {EPISODE}: *{TITLE}*", "",
          "*Recorded live at The Tap. Rain on the tin roof. First round on the house.*", ""]
    last_seg = None
    for l in lines:
        if l["segment"] != last_seg:
            md.append(f"\n## {l['segment'].title()}\n"); last_seg = l["segment"]
        sfx = f" *[{l['sfx']}]*" if l.get("sfx") else ""
        md.append(f"**{l['speaker']}:** {l['line']}{sfx}")
    return "\n".join(md)

if __name__ == "__main__":
    lines = run_show()
    (HERE / "episode.md").write_text(render(lines))
    (HERE / "script.json").write_text(json.dumps({"episode": EPISODE, "title": TITLE, "lines": lines}, indent=1))
    print(f"show complete: {len(lines)} lines, episode.md + script.json written")
