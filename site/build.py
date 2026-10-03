#!/usr/bin/env python3
"""Build the game from the YAML seed.

Reads ../ai_incident_game_seed_v3.yaml, ../translations/<lang>.yaml and src/game.html, writes:
  ../docs/index.html  the published site (GitHub Pages serves the /docs folder of main)
  dist/index.html     the same standalone page, for opening locally
  dist/artifact.html  body-only fragment (for publishing as a claude.ai artifact)
"""
import json
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent
SEED = ROOT.parent / "ai_incident_game_seed_v3.yaml"
TEMPLATE = ROOT / "src" / "game.html"
DIST = ROOT / "dist"
DOCS = ROOT.parent / "docs"  # published by GitHub Pages

TRANSLATIONS = ROOT.parent / "translations"
# Order = order in the language menu. First one is the source language (comes from the seed file).
MAIN_LANGS = ["en", "fr", "de", "ru", "it", "es"]
MORE_LANGS = ["ko", "zh", "sr", "bs", "ro", "vi", "uk", "pl", "ta", "sv", "tr"]  # hi.yaml exists too; swap "ta" for "hi" to use Hindi
LANGS = MAIN_LANGS + MORE_LANGS
FIELDS = ["title", "domain", "hook", "real", "fake", "excerpt", "explanation", "whyBad", "escalation"]

# translations/<lang>.yaml uses the seed's field names; the page uses these shorter ones.
# Which building on the city map each incident belongs to.
# Incidents that are in the seed but not listed here (#1701, #1628, #1556, #1672) are left out of the game.
BUILDINGS = {
    1374: "hospital", 1623: "school", 1717: "police", 1379: "court", 1596: "bank",
    1604: "office", 1505: "homes", 1606: "cityhall", 1258: "media", 1238: "lab",
}

RENAME = {
    "game_statement": "real", "counterfactual": "fake",
    "simple_explanation": "explanation", "why_bad": "whyBad", "future_escalation": "escalation",
}


def load_lang(lang):
    """Returns (meta, ui, incidents) from translations/<lang>.yaml."""
    path = TRANSLATIONS / f"{lang}.yaml"
    data = (yaml.safe_load(path.read_text()) or {}) if path.exists() else {}
    incidents = {}
    for k, v in (data.get("incidents") or {}).items():
        v = v or {}
        row = {RENAME.get(f, f): clean(x) for f, x in v.items() if isinstance(x, str)}
        row["_highlight"] = v.get("highlight") or {}
        incidents[int(k)] = row
    return data.get("meta") or {}, data.get("ui") or {}, incidents


def clean(text):
    return " ".join((text or "").split())


def emphasise(text, phrases, where):
    """Wrap the key phrases of a statement in **…** so the page can show them in bold."""
    for ph in phrases or []:
        if ph in text:
            text = text.replace(ph, f"**{ph}**", 1)
        else:
            print(f"  ! {where}: highlight phrase not found: {ph!r}")
    return text


def main():
    seed = yaml.safe_load(SEED.read_text())
    loaded = {lang: load_lang(lang) for lang in LANGS}
    langs = {lang: loaded[lang][2] for lang in LANGS}

    base_ui = loaded[LANGS[0]][1]
    ui, menu = {}, []
    for lang in LANGS:
        meta, strings, _ = loaded[lang]
        missing = [k for k in base_ui if k not in strings]
        if missing:
            print(f"  ! {lang} ui: missing {', '.join(missing)} (falls back to {LANGS[0]})")
        ui[lang] = {**base_ui, **strings}
        menu.append({"code": lang, "name": meta.get("name", lang), "flag": meta.get("flag", ""),
                     "group": "main" if lang in MAIN_LANGS else "more"})
    incidents = []
    for inc in seed["incidents"]:
        iid = inc["incident_id"]
        if iid not in BUILDINGS:
            continue
        source = {
            "title": inc["title"],
            "real": clean(inc["game_statement"]),
            "fake": clean(inc["counterfactual"]["statement"]),
            "excerpt": clean(inc["original_aiid_text"]["verbatim_excerpt"]),
            "explanation": clean(inc["simple_explanation"]),
            "whyBad": clean(inc.get("why_bad")),
            "escalation": clean(inc["future_escalation"]),
            **langs[LANGS[0]].get(iid, {}),
        }
        text = {LANGS[0]: source}
        for lang in LANGS[1:]:
            tr = langs[lang].get(iid, {})
            missing = [f for f in FIELDS if not tr.get(f)]
            if missing:
                print(f"  ! {lang} #{iid}: missing {', '.join(missing)} (falls back to {LANGS[0]})")
            text[lang] = {f: tr.get(f) or source.get(f, "") for f in FIELDS}
        for lang in LANGS:
            hl = langs[lang].get(iid, {}).get("_highlight", {})
            text[lang] = {f: text[lang].get(f, "") for f in FIELDS}
            text[lang]["real"] = emphasise(text[lang]["real"], hl.get("real"), f"{lang} #{iid} real")
            text[lang]["fake"] = emphasise(text[lang]["fake"], hl.get("fake"), f"{lang} #{iid} fake")
        incidents.append({"id": iid, "url": inc["source"], "building": BUILDINGS[iid], "text": text})

    data = json.dumps(incidents, ensure_ascii=False).replace("</", "<\\/")
    i18n = json.dumps({"langs": menu, "ui": ui}, ensure_ascii=False).replace("</", "<\\/")
    fragment = (TEMPLATE.read_text()
                .replace("/*__INCIDENTS__*/[]", data)
                .replace("/*__I18N__*/{}", i18n))

    # Standalone page: the same small reset the claude.ai artifact skeleton provides, plus share metadata.
    page = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="description" content="You are the mayor. Spot the real AI incident behind each building of your city, or watch it get hit.">\n'
        '<meta property="og:title" content="Incident or Fiction?">\n'
        '<meta property="og:description" content="A city game about AI safety, built on real cases from the AI Incident Database.">\n'
        '<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
        "</head>\n<body>\n" + fragment + "\n</body>\n</html>\n"
    )
    DIST.mkdir(exist_ok=True)
    (DIST / "artifact.html").write_text(fragment)   # body-only, for claude.ai artifacts
    (DIST / "index.html").write_text(page)
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(page)          # served by GitHub Pages (main branch, /docs folder)
    (DOCS / ".nojekyll").write_text("")
    print(f"Built {len(incidents)} rounds x {len(LANGS)} languages -> {DIST} and {DOCS}")


if __name__ == "__main__":
    main()
