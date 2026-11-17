"""Every English key/def string has a translation with the same placeholders and line breaks.
    python3 -I check.py <repo> <LanguageFolder>"""
import glob, json, os, re, sys, xml.etree.ElementTree as ET
repo, lang = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
tok = lambda s: sorted(re.findall(r"\{\d+\}|\\n|TargetA", s))
bad = 0
en = {e.tag: e.text or "" for e in ET.parse(f"{repo}/Languages/English/Keyed/TrashbrickBurning.xml").getroot()}
zh = {e.tag: e.text or "" for e in ET.parse(f"{repo}/Languages/{lang}/Keyed/TrashbrickBurning.xml").getroot()}
for k, v in en.items():
    if k not in zh: print("MISSING key", k); bad += 1
    elif tok(v) != tok(zh[k]): print("TOKENS", k, tok(v), tok(zh[k])); bad += 1
for k in zh:
    if k not in en: print("EXTRA key", k); bad += 1
got = {}
for f in glob.glob(f"{repo}/Languages/{lang}/DefInjected/**/*.xml", recursive=True) + glob.glob(f"{repo}/Mods/*/Languages/{lang}/DefInjected/**/*.xml", recursive=True):
    for e in ET.parse(f).getroot():
        got[e.tag] = e.text or ""
for o in json.load(open(f"{here}/defs_en.json")):
    if o["path"] not in got: print("MISSING def", o["path"]); bad += 1
    elif tok(o["en"]) != tok(got[o["path"]]): print("TOKENS", o["path"]); bad += 1
print(f"{lang}: {len(zh)} keys, {len(got)} def strings, {bad} problems")
sys.exit(1 if bad else 0)
