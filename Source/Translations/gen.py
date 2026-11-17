"""Writes a RimWorld language from zh_keyed.K and zh_defs.D (Simplified), optionally converted.
    python3 -I gen.py <repo> <LanguageFolder> [opencc-config]"""
import json, os, re, sys, xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
from zh_keyed import K
from zh_defs import D
repo, lang = sys.argv[1], sys.argv[2]
conv = None
if len(sys.argv) > 3:
    import opencc
    conv = opencc.OpenCC(sys.argv[3]).convert
tr = (lambda s: conv(s)) if conv else (lambda s: s)

en = ET.parse(f"{repo}/Languages/English/Keyed/TrashbrickBurning.xml").getroot()
lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>"]
for e in en:
    lines.append(f"\t<{e.tag}>{escape(tr(K[e.tag]))}</{e.tag}>")
lines.append("</LanguageData>\n")
p = f"{repo}/Languages/{lang}/Keyed/TrashbrickBurning.xml"
os.makedirs(os.path.dirname(p), exist_ok=True)
open(p, "w", encoding="utf-8").write("\n".join(lines))

defs = json.load(open(f"{here}/defs_en.json"))
groups = {}
for o in defs:
    root = repo if o["where"] == "main" else f"{repo}/Mods/DubsBadHygiene"
    groups.setdefault((root, o["type"]), []).append(o)
for (root, typ), items in groups.items():
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<LanguageData>", ""]
    for o in items:
        lines.append(f"\t<!-- EN: {escape(o['en']).replace('--', '- -')} -->")
        lines.append(f"\t<{o['path']}>{escape(tr(D[o['path']]))}</{o['path']}>")
        lines.append("")
    lines.append("</LanguageData>\n")
    p = f"{root}/Languages/{lang}/DefInjected/{typ}/TrashbrickBurning.xml"
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write("\n".join(lines))
print("wrote", lang)
