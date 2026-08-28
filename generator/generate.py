from pathlib import Path
import json, shutil, re

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
ICON_OUT = DOCS / "assets" / "icons"

def is_weapon_json(path):
    return any(p.lower() == "weapons" for p in path.parts[:-1])

def asset_name_from_json(path, obj):
    props = next((x.get("Properties") for x in obj if isinstance(x, dict) and isinstance(x.get("Properties"), dict)), {})
    name = props.get("Name")
    if isinstance(name, dict):
        return name.get("LocalizedString") or name.get("SourceString")
    return path.stem

def val(props, key):
    v=props.get(key)
    if isinstance(v, dict):
        return v.get("LocalizedString") or v.get("SourceString") or v.get("AssetPathName") or v.get("ObjectName")
    return v

def find_icon(props):
    icon=props.get("Icon")
    if isinstance(icon,dict):
        ap=icon.get("AssetPathName","")
        stem=Path(ap.split(".")[0]).name if ap else ""
        if stem:
            for ext in (".png",".PNG",".jpg",".jpeg",".webp",".dds"):
                hits=list(ASSETS.rglob(stem+ext))
                if hits: return hits[0]
    return None

rows=[]
scanned=0
for path in ASSETS.rglob("*.json"):
    scanned+=1
    if not is_weapon_json(path): continue
    try: raw=json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print("SKIP",path,e); continue
    if not isinstance(raw,list): raw=[raw]
    # FModel exports commonly contain BlueprintGeneratedClass + CDO.
    # Select the object containing Properties; this includes all actual weapon CDOs.
    obj=next((x for x in raw if isinstance(x,dict) and isinstance(x.get("Properties"),dict)), None)
    if not obj: continue
    p=obj["Properties"]
    name=asset_name_from_json(path, raw)
    icon=find_icon(p)
    icon_md="—"
    if icon:
        ICON_OUT.mkdir(parents=True,exist_ok=True)
        shutil.copy2(icon, ICON_OUT/icon.name)
        icon_md=f'<img src="assets/icons/{icon.name}" alt="{name}" width="48">'
    skill=p.get("SkillRequirements",[])
    strength="—"
    if isinstance(skill,list):
        for s in skill:
            if isinstance(s,dict) and "Strength" in str(s.get("Key","")):
                strength=s.get("Value","—")
                break
    wt=p.get("WeaponType")
    if isinstance(wt,dict): wt=Path(wt.get("AssetPathName","").split(".")[0]).name or wt.get("ObjectName","—")
    rows.append({
      "Icon":icon_md, "Name":name, "Type":wt or "—",
      "Tier":p.get("Tier","—"), "Damage":p.get("Damage","—"),
      "Thrust":p.get("ThrustDamage","—"), "Speed":p.get("WeaponSpeed","—"),
      "Impact":p.get("Impact","—"), "Stability":p.get("Stability","—"),
      "Length":p.get("WeaponLength","—"), "Max Durability":p.get("MaxDurability",p.get("Durability","—")),
      "Price":p.get("ExpectedPrice",p.get("Price","—")), "Strength":strength,
      "Source":str(path.relative_to(ASSETS)).replace("\\","/")
    })

rows.sort(key=lambda r:str(r["Name"]).lower())
headers=["Icon","Name","Type","Tier","Damage","Thrust","Speed","Impact","Stability","Length","Max Durability","Price","Strength"]
lines=["---","layout: default","title: All Weapons","---","","# All Weapons","",
       f"*{len(rows)} weapon assets from the raw FModel export.*","",
       '<input class="table-search" type="search" placeholder="Search weapons...">',"",
       "| "+" | ".join(headers)+" |",
       "| "+" | ".join(["---"]*3+["---:"]*(len(headers)-3))+" |"]
for r in rows:
    lines.append("| "+" | ".join(str(r[h]).replace("|",r"\|").replace("\n"," ") for h in headers)+" |")
(DOCS/"weapons.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
(DOCS/"generation-report.md").write_text(
    "# Generation Report\n\n"
    f"- JSON files scanned: {scanned}\n"
    f"- Weapon CDOs generated: {len(rows)}\n"
    f"- Icons found: {sum(1 for r in rows if r['Icon'] != '—')}\n\n"
    "The generator processes every JSON whose path contains an exact `Weapons` directory. "
    "It does not filter by tier, rarity, or weapon type.\n", encoding="utf-8")
print(f"Scanned {scanned}; generated {len(rows)} weapons.")
