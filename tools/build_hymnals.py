"""Builds the downloadable hymnals served from this repository.

Reads the raw sources (default: F:/church/Hymnals) and writes
  index.json             - the catalog the app shows on its download screen
  hymnals/<code>.json    - one file per hymnal

Usage: python tools/build_hymnals.py [SOURCE_DIR]

Hymnal ids and hymn ids are used by the app to remember bookmarks, so never
renumber an existing hymnal: add new ones at the end of HYMNALS.
"""

import csv
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = sys.argv[1] if len(sys.argv) > 1 else "F:/church/Hymnals"

# id must stay stable forever, bump "version" whenever a hymnal's content changes
# so installed copies are offered an update
HYMNALS = [
    {"id": 1, "code": "sda-hymnal-en", "name": "SDA Hymnal", "language": "English",
     "description": "Seventh-day Adventist Hymnal", "version": 1,
     "loader": "sda_english"},
    {"id": 2, "code": "memeneda-akwanhwefo-nnwom", "name": "Memeneda Akwanhwefo Nnwom",
     "language": "Twi", "description": "Seventh-day Adventist Twi hymnal", "version": 1,
     "loader": "memeneda"},
    {"id": 3, "code": "kristo-asore-nnwom", "name": "Kristo Asore Nnwom", "language": "Twi",
     "description": "Twi hymns", "version": 1,
     "loader": "lyrics_json", "source": "kristo_asore_nnwom", "title_keys": ["twi_title", "english_title"]},
    {"id": 4, "code": "twi-praises", "name": "Twi Praises", "language": "Twi",
     "description": "Twi praise songs", "version": 1,
     "loader": "lyrics_json", "source": "twi_praises", "title_keys": ["twi_title", "title"]},
    {"id": 5, "code": "dangme-hymns", "name": "Dangme Hymns", "language": "Dangme",
     "description": "Dangme hymns", "version": 1,
     "loader": "lyrics_json", "source": "dangme_hymn", "title_keys": ["dangme_title", "english_title"]},
    {"id": 6, "code": "dangme-praises", "name": "Dangme Praises", "language": "Dangme",
     "description": "Dangme praise songs", "version": 1,
     "loader": "lyrics_json", "source": "dangme_praises", "title_keys": ["dangme_title", "twi_title"]},
    {"id": 7, "code": "ss-en", "name": "SS", "language": "English",
     "description": "English hymns (SS)", "version": 1,
     "loader": "lyrics_json", "source": "ss", "title_keys": ["english_title", "twi_title"],
     "join_syllables": True},
    {"id": 8, "code": "soc-en", "name": "SOC", "language": "English",
     "description": "English choruses (SOC)", "version": 1,
     "loader": "lyrics_json", "source": "soc", "title_keys": ["english_title", "twi_title"],
     "join_syllables": True},
]


def clean(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def join_syllables(text):
    # "A - las! and did my Sav - ior bleed?" -> "Alas! and did my Savior bleed?"
    return re.sub(r"(?<=[^\W\d_])(?: - | -|- )(?=[^\W\d_]|[‘’'])", "", text)


def fix_title(title):
    title = re.sub(r"\s+", " ", title or "").strip().strip("(").strip()
    if not re.search(r"[a-z]", title):
        title = title.title()  # "ADEɛ KɛSEɛ A WAYɛ" -> "Adeɛ Kɛseɛ A Wayɛ"
    # "We’Re Marching" -> "We’re Marching"
    return re.sub(r"(?<=[A-Za-z])(['’])(Re|S|Ll|Ve|T|D|M)\b",
                  lambda m: m.group(1) + m.group(2).lower(), title)


def number_key(number):
    m = re.match(r"(\d*)(.*)", number)
    return (int(m.group(1)) if m.group(1) else -1, m.group(2))


def first_line(verses):
    for v in verses:
        line = v["text"].split("\n")[0].strip().rstrip(",;:")
        if line:
            return line
    return ""


def load_sda_english(cfg):
    folder = os.path.join(SOURCE, "sdahymns_english", "raw_text")
    hymns = []
    for name in sorted(os.listdir(folder)):
        with open(os.path.join(folder, name), encoding="utf-8") as f:
            lines = f.read().replace("\r\n", "\n").split("\n")
        m = re.match(r"\s*(\d+)\s*[–-]\s*(.*)", lines[0])
        number, title = str(int(m.group(1))), m.group(2)
        verses, label, buf = [], None, []

        def flush():
            text = clean("\n".join(buf))
            if text:
                verses.append({"label": label or "", "text": text})

        for line in lines[1:]:
            s = line.strip()
            if re.fullmatch(r"\d{1,2}", s) or s in ("Refrain", "Chorus"):
                flush()
                label, buf = s, []
            else:
                buf.append(line)
        flush()
        hymns.append({"number": number, "title": fix_title(title), "verses": verses})
    return hymns


def load_memeneda(cfg):
    with open(os.path.join(SOURCE, "Memeneda Akwanhwefo Nnwom Lyrics.json"), encoding="utf-8") as f:
        data = json.load(f)
    hymns = []
    for song in data["Songs"]:
        verses, n = [], 0
        for v in song["Verses"]:
            if v.get("Tag") == 1:
                label = "Chorus"
                if any(x["label"] == "Chorus" and x["text"] == clean(v["Text"]) for x in verses):
                    continue  # the chorus is repeated after every verse, show it once
            else:
                n = v.get("ID") or n + 1
                label = str(n)
            verses.append({"label": label, "text": clean(v["Text"])})
        hymns.append({"number": str(song["ID"]), "title": fix_title(song.get("Text")), "verses": verses})
    return hymns


def load_lyrics_json(cfg):
    src = cfg["source"]
    with open(os.path.join(SOURCE, src + "_lyrics.json"), encoding="utf-8") as f:
        lyrics = json.load(f)
    titles = {}
    with open(os.path.join(SOURCE, src + "_list.csv"), encoding="utf-8-sig") as f:
        for row in list(csv.reader(f))[1:]:
            if len(row) >= 2 and row[-1].strip():
                titles.setdefault(row[-1].strip(), row[0].strip())

    hymns = []
    for number, item in lyrics.items():
        verses = []
        raw = item.get("verses") or ([item["verse"]] if isinstance(item.get("verse"), dict) else [])
        for v in raw:
            text = clean(v.get("text", ""))
            if cfg.get("join_syllables"):
                text = join_syllables(text)
            if text:
                verses.append({"label": str(v.get("number", "")).strip(), "text": text})
        chorus = clean(item.get("chorus") or "")
        if chorus:
            if cfg.get("join_syllables"):
                chorus = join_syllables(chorus)
            verses.insert(min(1, len(verses)), {"label": "Chorus", "text": chorus})
        for part, lines in (item.get("parts") or {}).items():
            text = clean("\n".join(lines) if isinstance(lines, list) else str(lines))
            if text:
                verses.append({"label": part, "text": text})
        if not verses:
            continue  # listed in the source but no lyrics yet

        title = next((item.get(k) for k in cfg["title_keys"] if (item.get(k) or "").strip()), "")
        title = fix_title(title) or fix_title(titles.get(number, "")) or first_line(verses)
        subtitle = fix_title(item.get("english_title", ""))
        hymn = {"number": number.strip(), "title": title, "verses": verses}
        if subtitle and subtitle.lower() != title.lower():
            hymn["subtitle"] = subtitle
        hymns.append(hymn)
    return hymns


LOADERS = {"sda_english": load_sda_english, "memeneda": load_memeneda, "lyrics_json": load_lyrics_json}


def build():
    os.makedirs(os.path.join(REPO, "hymnals"), exist_ok=True)
    catalog = []
    for cfg in HYMNALS:
        hymns = LOADERS[cfg["loader"]](cfg)
        hymns.sort(key=lambda h: number_key(h["number"]))
        seen, unique = set(), []
        for h in hymns:
            if h["number"] in seen:
                print(f"  {cfg['code']}: duplicate hymn number {h['number']} skipped")
                continue
            seen.add(h["number"])
            unique.append(h)
        # hymn id = hymnal id * 100000 + position, stable as long as numbers are only appended
        for i, h in enumerate(unique, start=1):
            h["id"] = cfg["id"] * 100000 + i
            h.update({k: h.pop(k) for k in ["number", "title", "subtitle", "verses"] if k in h})

        meta = {k: cfg[k] for k in ["id", "code", "name", "language", "description", "version"]}
        meta["count"] = len(unique)
        path = "hymnals/" + cfg["code"] + ".json"
        with open(os.path.join(REPO, path), "w", encoding="utf-8", newline="\n") as f:
            json.dump(dict(meta, hymns=unique), f, ensure_ascii=False, separators=(",", ":"))
        meta["file"] = path
        meta["size"] = os.path.getsize(os.path.join(REPO, path))
        catalog.append(meta)
        print(f"{cfg['code']}: {len(unique)} hymns, {meta['size'] // 1024} KB")

    with open(os.path.join(REPO, "index.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"hymnals": catalog}, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    build()
