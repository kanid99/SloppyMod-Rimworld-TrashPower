"""Lists every translatable string in this mod's defs, with its DefInjected path, into
defs_en.json beside this script. Run from the repo root after changing a def's text:

    python3 Source/Translations/dump_defs.py

Then add or update the translations in zh_defs.py (and zh_keyed.py for Languages/English/Keyed),
regenerate with gen.py and check with check.py:

    python3 -I Source/Translations/gen.py . ChineseSimplified
    python3 -I Source/Translations/check.py . ChineseSimplified
"""
import glob, json, os, xml.etree.ElementTree as ET
here = os.path.dirname(os.path.abspath(__file__))
out, named = [], {}
files = [(f, "main") for f in glob.glob("Defs/**/*.xml", recursive=True)] + \
        [(f, "dbh") for f in glob.glob("Mods/DubsBadHygiene/Defs/**/*.xml", recursive=True)]
for f, _ in files:
    for d in ET.parse(f).getroot():
        if d.get("Name"):
            named[d.get("Name")] = d


def lookup(d, tag):
    while d is not None:
        v = d.findtext(tag)
        if v:
            return v
        d = named.get(d.get("ParentName"))


for f, where in files:
    for d in ET.parse(f).getroot():
        dn = d.findtext("defName")
        if not dn or d.get("Abstract") == "True":
            continue
        for tag in ("label", "description", "reportString", "verb", "gerund", "jobString", "labelShort"):
            v = lookup(d, tag)
            if v:
                out.append(dict(where=where, type=d.tag, path=f"{dn}.{tag}", en=v.strip()))
        comps = d.find("comps")
        if comps is not None:
            for li in comps:
                for tag in ("fuelLabel", "fuelGizmoLabel", "outOfFuelMessage"):
                    v = li.findtext(tag)
                    if v:
                        out.append(dict(where=where, type=d.tag, path=f"{dn}.comps.{li.get('Class')}.{tag}", en=v.strip()))
        r = d.find("resource")
        if r is not None and r.findtext("name"):
            out.append(dict(where=where, type=d.tag, path=f"{dn}.resource.name", en=r.findtext("name")))
json.dump(out, open(f"{here}/defs_en.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "def strings")
