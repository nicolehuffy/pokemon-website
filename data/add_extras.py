"""
add_extras.py - runs automatically at the end of make_data.py (or run it alone to refresh). Adds to pokemon-data.js:
  * Regional forms (Alolan, Galarian, Hisuian, Paldean) as their own Pokemon, with their own stats, types and evolutions.
  * Route-by-route catch data from PokemonDB for every main game. This fills the gaps in PokeAPI and is the only
    source for Let's Go, Brilliant Diamond / Shining Pearl, Legends: Arceus and Scarlet / Violet.
  * Which regional Pokedexes each Pokemon is in (games without a National Dex can't evolve into anything else).
Downloads are cached in your temp folder, so running it again is quick.
"""
import csv, hashlib, html, json, os, re, statistics, tempfile, time
import requests
from make_data import (STORY, KANTO_RULES, KANTO_MINS, SINNOH_DP_PT, SINNOH_MINS, GALAR_RULES, HOENN_RULES, HOENN_MINS,
                       AREA_MED, area_stage, level_stage, pretty)

FOLDER = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get("PTB_CACHE") or os.path.join(tempfile.gettempdir(), "pokemon-team-builder-cache")
H = {"User-Agent": "Mozilla/5.0 (Pokemon team builder data script, personal use)"}


def get(url, as_json=False):
    """Download a page once (cached on disk). Waits between requests so we don't overload the sites."""
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + (".json" if as_json else ".html"))
    if os.path.exists(f):
        text = open(f, encoding="utf-8").read()
        return json.loads(text) if as_json else text
    for attempt in range(6):
        try:
            r = requests.get(url, headers=H, timeout=30)
            if r.status_code == 200:
                open(f, "w", encoding="utf-8").write(r.text)
                time.sleep(0.8)
                return r.json() if as_json else r.text
            if r.status_code == 404:
                break
        except requests.RequestException:
            pass
        time.sleep(5 + attempt * 10)
    print("  could not download", url)
    return None if as_json else ""


# ---------- Games ----------
CODES = {"R1": "red", "B1": "blue", "Y1": "yellow", "G2": "gold", "S2": "silver", "C2": "crystal", "R3": "ruby",
         "S3": "sapphire", "E3": "emerald", "FR3": "firered", "LG3": "leafgreen", "D4": "diamond", "P4": "pearl",
         "Pt4": "platinum", "HG4": "heartgold", "SS4": "soulsilver", "B5": "black", "W5": "white", "B25": "black-2",
         "W25": "white-2", "X6": "x", "Y6": "y", "OR6": "omega-ruby", "AS6": "alpha-sapphire", "S7": "sun", "M7": "moon",
         "US7": "ultra-sun", "UM7": "ultra-moon", "LGP7": "lets-go-pikachu", "LGE7": "lets-go-eevee", "Sw8": "sword",
         "Sh8": "shield", "BD8": "brilliant-diamond", "SP8": "shining-pearl", "LA8": "legends-arceus", "S9": "scarlet",
         "V9": "violet"}
GAME_NAME = {v: pretty(v).replace("Lets Go ", "Let's Go ") for v in CODES.values()}
OPEN_WORLD = {"legends-arceus", "scarlet", "violet"}  # no fixed gym order: story stage follows the wild level

# Story-order rules for the games PokeAPI has no data for, plus PokemonDB's area names that differ from PokeAPI's.
GALAR_DLC = (r"(fields-of-honor|soothing-wetlands|forest-of-focus|challenge-beach|brawlers-cave|challenge-road|"
             r"courageous-cavern|loop-lagoon|training-lowlands|warm-up-tunnel|potbottom-desert|workout-sea|"
             r"stepping-stone-sea|insular-sea|honeycalm-sea|honeycalm-island|slippery-slope|frostpoint-field|giants-bed|"
             r"old-cemetery|snowslide-slope|path-to-the-peak|tunnel-to-the-top|giants-foot|roaring-sea-caves|frigid-sea|"
             r"three-point-pass|ballimere-lake|lakeside-cave|dyna-tree-hill|crown-shrine)-area")
EXTRA = {
    "kanto": [(0, r"kanto-route-2-area")],
    "hoenn": [(10, r"(mirage-spots|sea-mauville|battle-resort|battle-tower|mirage-island)-area")],
    "galar": [(10, GALAR_DLC), (0, r"(galar-route-2|slumbering-weald|galar-mine)-area")],
    "unova": [(10, r"(white-forest|black-city)-area")],
    # Grand Underground: opens in Eterna City; later Pokemon are gated by the status rows (Strength, Defog...)
    "bdsp": [(1, r"(big-bluff-cavern|bogsunk-cavern|dazzling-cave|fountainspring-cave|glacial-cavern|grassland-cave|"
                 r"icy-cave|riverbank-cave|rocky-cave|sandsear-cave|spacious-cave|stargleam-cavern|still-water-cavern|"
                 r"sunlit-cavern|swampy-cave|typhlo-cavern|volcanic-cave|whiteout-cave)-area")],
}
for _g in ("lets-go-pikachu", "lets-go-eevee"):
    STORY[_g] = (KANTO_RULES, {"surf": 5})
for _g in ("brilliant-diamond", "shining-pearl"):
    STORY[_g] = ([(a, r) for a, b, r in SINNOH_DP_PT], SINNOH_MINS)
REGION_OF = {}
for v in CODES.values():
    REGION_OF[v] = ("kanto" if v in ("red", "blue", "yellow", "firered", "leafgreen", "lets-go-pikachu", "lets-go-eevee")
                    else "hoenn" if v in ("ruby", "sapphire", "emerald", "omega-ruby", "alpha-sapphire")
                    else "galar" if v in ("sword", "shield") else "unova" if v in ("black", "white")
                    else "bdsp" if v in ("brilliant-diamond", "shining-pearl") else "")
DLC_TEXT = re.compile(GALAR_DLC)

METHOD = {"Walking": "walking", "Walking - Overworld": "overworld", "Old Rod": "Old Rod", "Good Rod": "Good Rod",
          "Super Rod": "Super Rod", "Surfing": "surfing", "Interact": "one-time encounter", "Gift": "gift",
          "Shaking Trees": "shaking trees", "Headbutt": "Headbutt", "Headbutt (Special)": "Headbutt",
          "Rock Smash": "Rock Smash", "Berry Piles": "berry piles", "Flying": "flying"}
API_METHOD = {"Old Rod": "old-rod", "Good Rod": "good-rod", "Super Rod": "super-rod", "Surfing": "surf",
              "Rock Smash": "rock-smash", "Gift": "gift", "Interact": "static"}
POSTGAME = re.compile(r"post-game|elite four|post-national|national dex(?! -)|delta episode|hall of fame|swarm|"
                      r"hoenn sound|sinnoh sound", re.I)
NEEDS_CART = re.compile(r"GBA slot")  # Diamond/Pearl encounters that need a second game in the DS
# Grand Underground (Brilliant Diamond / Shining Pearl): Pokemon unlocked by story progress.
STATUS_MIN = [(r"Strength obtained", 3), (r"Defog obtained", 4), (r"Icicle Badge", 7), (r"Waterfall obtained", 8)]

# ---------- Regional forms ----------
REGION = {"alola": ("Alolan", 7), "galar": ("Galarian", 8), "hisui": ("Hisuian", 8), "paldea": ("Paldean", 9)}
FORM_SKIP = {"raticate-totem-alola", "pikachu-alola-cap", "darmanitan-galar-zen"}
SPECIAL_NAMES = {"basculin-white-striped": "Basculin (White-Striped)",
                 "tauros-paldea-combat-breed": "Paldean Tauros (Combat)",
                 "tauros-paldea-blaze-breed": "Paldean Tauros (Blaze)",
                 "tauros-paldea-aqua-breed": "Paldean Tauros (Aqua)",
                 "darmanitan-galar-standard": "Galarian Darmanitan"}
# How a regional form evolves when it differs from the normal species.
HOW = {"Alolan Ninetales": ("Use Ice Stone", 0), "Alolan Sandslash": ("Use Ice Stone", 0),
       "Galarian Darmanitan": ("Use Ice Stone", 0), "Galarian Slowbro": ("Use Galarica Cuff", 0),
       "Galarian Slowking": ("Use Galarica Wreath", 0), "Alolan Persian": ("Level up with high friendship", 0),
       "Hisuian Electrode": ("Use Leaf Stone", 0), "Alolan Raticate": ("Level 20 at night", 20),
       "Alolan Marowak": ("Level 28 at night", 28), "Alolan Exeggutor": ("Use Leaf Stone", 0)}
# New species that only come from a regional form (Galarian Meowth -> Perrserker, never Kantonian Meowth).
REGIONAL_ONLY = {"Perrserker": ("Galarian Meowth", "Level 28", 28),
                 "Sirfetchd": ("Galarian Farfetchd", "Land 3 critical hits in one battle", 0),
                 "Mr Rime": ("Galarian Mr Mime", "Level 42", 42), "Cursola": ("Galarian Corsola", "Level 38", 38),
                 "Obstagoon": ("Galarian Linoone", "Level 35 at night", 35),
                 "Runerigus": ("Galarian Yamask", "Take 49+ damage, then walk under the Dusty Bowl rock arch", 0),
                 "Overqwil": ("Hisuian Qwilfish", "Use Barb Barrage 20 times in Strong Style, then level up", 0),
                 "Sneasler": ("Hisuian Sneasel", "Level up holding a Razor Claw during the day", 0),
                 "Clodsire": ("Paldean Wooper", "Level 20", 20),
                 "Basculegion": ("Basculin (White-Striped)", "Take 294+ recoil damage, then level up", 0)}
ALOLA = ["sun", "moon", "ultra-sun", "ultra-moon"]
GALAR = ["sword", "shield"]
LA = ["legends-arceus"]
# Normal Pokemon that evolve into the regional form when evolved in that region's games.
AUTO = {"Pikachu": ("Raichu", "Alolan Raichu", ALOLA), "Exeggcute": ("Exeggutor", "Alolan Exeggutor", ALOLA),
        "Cubone": ("Marowak", "Alolan Marowak", ALOLA), "Koffing": ("Weezing", "Galarian Weezing", GALAR),
        "Mime Jr": ("Mr Mime", "Galarian Mr Mime", GALAR), "Quilava": ("Typhlosion", "Hisuian Typhlosion", LA),
        "Dewott": ("Samurott", "Hisuian Samurott", LA), "Dartrix": ("Decidueye", "Hisuian Decidueye", LA),
        "Petilil": ("Lilligant", "Hisuian Lilligant", LA), "Rufflet": ("Braviary", "Hisuian Braviary", LA),
        "Goomy": ("Sliggoo", "Hisuian Sliggoo", LA), "Bergmite": ("Avalugg", "Hisuian Avalugg", LA)}
LA_ONLY = {("Stantler", "Wyrdeer"), ("Scyther", "Kleavor"), ("Ursaring", "Ursaluna")}
DEXES = {"lgpe": [26], "swsh": [27, 28, 29], "la": [30], "sv": [31, 32, 33]}


def build_forms(P, by_id, by_name):
    api = "https://pokeapi.co/api/v2/"
    names = [x["name"] for x in get(api + "pokemon?limit=2000", True)["results"]]
    names = [n for n in names if (re.search(r"-(alola|galar|hisui|paldea)", n) or n == "basculin-white-striped")
             and n not in FORM_SKIP]
    forms = []
    for n in names:
        d = get(api + "pokemon/" + n, True)
        if not d:
            continue
        num = int(d["species"]["url"].rstrip("/").split("/")[-1])
        base = by_id.get(num)
        if not base:
            continue
        reg = "hisui" if n == "basculin-white-striped" else re.search(r"(alola|galar|hisui|paldea)", n).group(1)
        adj, gen = REGION[reg]
        stats = {s["stat"]["name"]: s["base_stat"] for s in d["stats"]}
        forms.append({
            "id": d["id"], "num": num, "n": SPECIAL_NAMES.get(n, adj + " " + base["n"]), "rf": reg, "base": base["n"],
            "t": [t["type"]["name"][:3] for t in sorted(d["types"], key=lambda t: t["slot"])],
            "hp": stats["hp"], "at": stats["attack"], "df": stats["defense"], "sa": stats["special-attack"],
            "sd": stats["special-defense"], "sp": stats["speed"], "g": gen, "st": False, "lg": base["lg"],
            "pre": "", "ev": [], "e": {}, "L": {}, "S": {}, "D": [], "w": ""})
    fn = {f["n"]: f for f in forms}
    adj_of = lambda f: REGION[f["rf"]][0]
    for f in forms:
        base = by_name[f["base"]]
        if base["pre"]:
            f["pre"] = adj_of(f) + " " + base["pre"] if adj_of(f) + " " + base["pre"] in fn else base["pre"]
        for e in base["ev"]:
            t = adj_of(f) + " " + e["to"]
            if t in fn and fn[t]["rf"] == f["rf"]:
                how, lv = HOW.get(t, (e["how"], e["l"]))
                f["ev"].append({"to": t, "how": how, "l": lv})
    for t, (src, how, lv) in REGIONAL_ONLY.items():
        if t not in by_name or src not in fn:
            continue
        base = by_name[fn[src]["base"]]
        base["ev"] = [e for e in base["ev"] if e["to"] != t]
        fn[src]["ev"].append({"to": t, "how": how, "l": lv})
        by_name[t]["pre"] = src
    for b, (normal, regional, versions) in AUTO.items():
        if b not in by_name or regional not in fn:
            continue
        evs = by_name[b]["ev"]
        for e in evs:
            if e["to"] == normal:
                e["x"] = versions
                how, lv = HOW.get(regional, (e["how"], e["l"]))
                evs.append({"to": regional, "how": how + " (" + ("Alola" if versions is ALOLA else "Galar" if versions is GALAR else "Hisui") + ")", "l": lv, "v": versions})
                break
    for b, t in LA_ONLY:
        for e in by_name.get(b, {}).get("ev", []):
            if e["to"] == t:
                e["v"] = LA
    for f in forms:
        f["fe"] = not f["ev"]
    return forms


# ---------- PokemonDB locations ----------
def area_names(slug):
    """PokemonDB 'kanto-mt-moon' -> the PokeAPI-style names our story rules use ('kanto-mt-moon-area', 'mt-moon-area')."""
    region, rest = slug.split("-", 1)
    return [slug + "-area", rest + "-area"]


# Legends: Arceus areas unlock in story order. Serebii lists which locations are in which area.
LA_AREAS = [("obsidianfieldlands", 0, "Obsidian Fieldlands"), ("crimsonmirelands", 2, "Crimson Mirelands"),
            ("cobaltcoastlands", 4, "Cobalt Coastlands"), ("coronethighlands", 5, "Coronet Highlands"),
            ("alabastericelands", 7, "Alabaster Icelands")]
LA_FIXED = {"hisui-natures-pantry": 0, "hisui-the-heartwood": 0, "hisui-jubilife-village": 0, "hisui-space-time-distortion": 2}
LA_STAGE, LA_NAME = {}, {}


def load_la_areas(slug_places):
    pages = [(html.unescape(re.sub(r"<[^>]+>", " ", get(f"https://www.serebii.net/pokearth/hisui/{a}.shtml"))), s, n)
             for a, s, n in LA_AREAS]
    for slug, place in slug_places.items():
        # Every page names every location once in its menu; a location's own area page names it again.
        best = max(pages, key=lambda p: p[0].count(place))
        if best[0].count(place) >= 2:
            LA_STAGE[slug], LA_NAME[slug] = best[1], best[2]
        else:
            LA_STAGE[slug] = LA_FIXED.get(slug, 0)
            LA_NAME[slug] = "Obsidian Fieldlands" if LA_STAGE[slug] == 0 else ""


def stage_for(v, slug, methods, lo, details):
    if POSTGAME.search(details) and "Pre-National" not in details:
        return 10
    if v == "legends-arceus":
        return LA_STAGE.get(slug, level_stage(lo))
    if v in OPEN_WORLD:
        return level_stage(lo)
    floor = max([s for pat, s in STATUS_MIN if re.search(pat, details)] + [0])
    return max(floor, _stage(v, slug, methods, lo))


def _stage(v, slug, methods, lo):
    rules, mins = STORY.get(v, ([], {}))
    rules = EXTRA.get(REGION_OF.get(v, ""), []) + rules
    cands = area_names(slug)
    for cand in cands:
        for s, pat in rules:
            if re.fullmatch(pat, cand):
                if s >= 10:
                    return 10
                return min(10, max([s, level_stage(lo) - 1] + [mins.get(m, 0) for m in methods]))
    return area_stage(v, cands[0], methods, lo)


def scrape_locations():
    idx = get("https://pokemondb.net/location")
    slugs = sorted(set(re.findall(r'href="/location/([a-z0-9-]+)"', idx[idx.find("<main"):])))
    print("Reading", len(slugs), "PokemonDB location pages (first run downloads them, about 15 minutes)...")
    rows, la_places = [], {}
    for i, slug in enumerate(slugs):
        h = get("https://pokemondb.net/location/" + slug)
        m = h[h.find("<main"):h.find("</main>")]
        title = re.sub(r"<[^>]+>", "", re.search(r"<h1>(.*?)</h1>", m, re.S).group(1)).replace("(location)", "").strip()
        place = html.unescape(re.sub(r",\s*\w+$", "", title).strip())
        if slug.startswith("hisui-"):
            la_places[slug] = place
        for sec in re.split(r"(?=<h2 )", m)[1:]:
            h2 = re.sub(r"<[^>]+>", "", re.search(r"<h2[^>]*>(.*?)</h2>", sec).group(1))
            sub = h2.split(" - ", 1)[1].strip() if " - " in h2 else ""
            sub = "" if sub in ("Main", place) else sub
            for blk in re.split(r"(?=<h3>)", sec)[1:]:
                meth = re.search(r"<h3>(.*?)</h3>", blk).group(1).replace("&amp;", "&")
                if meth not in METHOD:
                    continue  # trades and info tables
                status = ""  # heading rows like "After Strength obtained" apply to the rows below them
                for r in re.findall(r"<tr>(.*?)</tr>", blk, re.S):
                    st = re.search(r'class="cell-loc-status">(.*?)</th>', r)
                    if st:
                        status = re.sub(r"<[^>]+>", "", st.group(1)).strip()
                        continue
                    num = re.search(r'title="View Pokedex for #(\d+)', r)
                    if not num:
                        continue
                    form = re.search(r'<small class="text-muted">(.*?)</small>', r)
                    alt = re.search(r'icon-pkmn"[^>]*alt="([^"]*)"', r)
                    nm = re.search(r'class="ent-name"[^>]*>(.*?)</a>', r)
                    label = form.group(1) if form else alt.group(1) if alt and nm and alt.group(1) != nm.group(1) else ""
                    games = [CODES[c] for c in re.findall(r'cell-loc-game-([A-Za-z0-9]+)"', r) if c in CODES]
                    cells = re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)
                    lv = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r'<td class="cell-num">(.*?)</td>', r, re.S)]
                    lvs = [int(x) for x in re.findall(r"\d+", lv[-1] if lv else "")]
                    details = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", cells[-1])).strip() if cells else ""
                    details = (details + " | " + status).strip(" |")
                    if games == ["legends-arceus"] and not lvs:
                        lvs = [0]  # Legends: Arceus has no fixed wild levels; its timing comes from the area instead
                    if not games or not lvs or "Starter Pok" in details or NEEDS_CART.search(details):
                        continue
                    rows.append({"num": int(num.group(1)), "form": html.unescape(label),
                                 "games": games, "slug": slug, "place": place + (" – " + sub if sub else ""),
                                 "meth": meth, "lo": min(lvs), "hi": max(lvs), "det": details})
        if (i + 1) % 100 == 0:
            print("  ", i + 1, "of", len(slugs))
    load_la_areas(la_places)
    return rows


def form_targets(row, by_id, fn):
    """Which of our Pokemon a PokemonDB row is: the species, or one of its regional forms."""
    base = by_id.get(row["num"])
    if not base:
        return []
    if row["games"] == ["legends-arceus"] and "Hisuian " + base["n"] in fn:
        return [fn["Hisuian " + base["n"]]]  # Legends: Arceus only has the Hisuian form (it isn't labelled there)
    if row["games"] == ["legends-arceus"] and base["n"] == "Basculin":
        return [base, fn["Basculin (White-Striped)"]]
    if set(row["games"]) <= set(ALOLA) and "Alolan " + base["n"] in fn:
        return [fn["Alolan " + base["n"]]]  # Alola's wild Rattata, Vulpix... are always the Alolan form
    return [form_target(row, base, fn)]


def form_target(row, base, fn):
    f = row["form"]
    m = re.match(r"(Alolan|Galarian|Hisuian|Paldean) ", f)
    if m:
        return fn.get(m.group(1) + " " + base["n"])
    if "White-Striped" in f:
        return fn.get("Basculin (White-Striped)")
    for b in ("Blaze", "Aqua", "Combat"):
        if b in f or (b == "Combat" and f.startswith("Paldean Tauros")):
            return fn.get(f"Paldean Tauros ({b})")
    return base


def merge_locations(P, by_id, fn, rows):
    per = {}  # name -> version -> list of (stage, lo, hi, place, method, slug)
    # typical wild level of each area (used when an area isn't in the story rules)
    lv = {}
    for r in rows:
        if r["meth"] in ("Gift", "Interact"):
            continue
        for v in r["games"]:
            lv.setdefault((v, area_names(r["slug"])[0]), []).append((r["lo"] + r["hi"]) / 2)
    for k, x in lv.items():
        AREA_MED.setdefault(k, statistics.median(x))
    for r in rows:
        api_m = [API_METHOD[r["meth"]]] if r["meth"] in API_METHOD else ["walk"]
        for tgt in form_targets(r, by_id, fn):
            if not tgt:
                continue
            for v in r["games"]:
                st = stage_for(v, r["slug"], api_m, r["lo"], r["det"])
                if v in ("sword", "shield") and DLC_TEXT.fullmatch(area_names(r["slug"])[1]):
                    st = 10
                place = (LA_NAME[r["slug"]] + " – " + r["place"]) if v == "legends-arceus" and LA_NAME.get(r["slug"]) else r["place"]
                per.setdefault(tgt["n"], {}).setdefault(v, []).append((st, r["lo"], r["hi"], place, METHOD[r["meth"]], r["slug"]))
    added = 0
    print("  regional forms with catch data:", sum(1 for f in fn.values() if f["n"] in per), "of", len(fn))
    for p in P + list(fn.values()):
        for v, lst in per.get(p["n"], {}).items():
            lst.sort(key=lambda x: (x[0], x[1]))
            best = lst[0]
            if v in p["S"] and p["S"][v] <= best[0]:
                continue  # PokeAPI already has it this early
            added += v not in p["S"]
            p["S"][v] = best[0]
            p["e"][v] = best[1]
            parts, seen = [], set()
            for st, lo, hi, place, meth, slug in lst:
                if place in seen:
                    continue
                seen.add(place)
                lvl = "" if not hi else f", Lv {lo}" if lo == hi else f", Lv {lo}-{hi}"
                pre = "DLC: " if v in ("sword", "shield") and DLC_TEXT.fullmatch(area_names(slug)[1]) else "Post-game: " if st == 10 else ""
                parts.append(f"{pre}{place} ({meth}{lvl})")
                if len(parts) == 3:
                    break
            p["L"][v] = "; ".join(parts)
    # In games with regional forms, PokemonDB says which form lives there. Drop PokeAPI rows that credited the
    # normal species (e.g. Rattata in Ultra Sun is really Alolan Rattata).
    dropped = 0
    forms_by_base = {}
    for f in fn.values():
        forms_by_base.setdefault(f["base"], []).append(f)
    for p in P:
        if p.get("rf") or p["n"] not in forms_by_base:
            continue
        mine = per.get(p["n"], {})
        for f in forms_by_base[p["n"]]:
            for v in per.get(f["n"], {}):
                if v not in mine and v in p["S"]:
                    del p["S"][v]
                    p["e"].pop(v, None)
                    p["L"].pop(v, None)
                    dropped += 1
    # Short "where" text for regional forms (shown in "Any game" mode).
    for f in fn.values():
        games = sorted(per.get(f["n"], {}), key=lambda v: list(CODES.values()).index(v))
        f["w"] = (f"{REGION[f['rf']][0]} form. Found in: " + ", ".join(GAME_NAME[v] for v in games) + "."
                  if games else f"{REGION[f['rf']][0]} form. Get it by evolving, trading or from an event.")
    print(f"  added {added} new game appearances, removed {dropped} that were really regional forms")


def main():
    path = os.path.join(FOLDER, "pokemon-data.js")
    src = open(path, encoding="utf-8").read()
    P = [p for p in json.loads(src[src.index("["):src.rindex("]") + 1]) if not p.get("rf")]
    base_names = {p["n"] for p in P}
    for p in P:
        p["num"] = p["id"]
        for k in ("S", "e", "L"):
            p[k] = p.get(k) or {}
        p["ev"] = [e for e in p.get("ev", []) if e["to"] in base_names]  # drop regional entries from an earlier run
        for e in p["ev"]:
            e.pop("x", None)
            e.pop("v", None)
    by_id = {p["id"]: p for p in P}
    by_name = {p["n"]: p for p in P}
    print("Adding regional forms...")
    forms = build_forms(P, by_id, by_name)
    fn = {f["n"]: f for f in forms}
    print("  ", len(forms), "regional forms")
    merge_locations(P, by_id, fn, scrape_locations())
    print("Reading regional Pokedexes...")
    for p in P:
        p["D"] = []
    for key, ids in DEXES.items():
        names = set()
        for i in ids:
            d = get(f"https://pokeapi.co/api/v2/pokedex/{i}", True)
            names |= {e["pokemon_species"]["name"] for e in d["pokemon_entries"]} if d else set()
        slug_ok = {pretty(n) for n in names}
        for p in P:
            if p["n"] in slug_ok:
                p["D"].append(key)
    for f in forms:
        f["D"] = list(by_name[f["base"]]["D"])
    for p in P:
        p["fe"] = not p["ev"]
    out = P + forms
    with open(path, "w", encoding="utf-8") as f:
        f.write("const P = ")
        json.dump(out, f, separators=(",", ":"))
        f.write(";")
    with open(os.path.join(FOLDER, "pokemon.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Number", "Name", "Types", "HP", "Attack", "Defense", "Sp Atk", "Sp Def", "Speed", "Generation",
                    "Starter", "Legendary", "Final Evolution", "Evolves From", "Evolves Into", "Games You Can Catch It In"])
        for p in out:
            into = "; ".join(e["to"] + " (" + e["how"] + ")" for e in p["ev"])
            games = ", ".join(GAME_NAME.get(v, pretty(v)) for v in CODES.values() if v in p["S"])
            w.writerow([p["num"], p["n"], "/".join(p["t"]), p["hp"], p["at"], p["df"], p["sa"], p["sd"], p["sp"], p["g"],
                        p["st"], p["lg"], p["fe"], p["pre"], into, games])
    print("Done! Saved", len(out), "Pokemon and forms to", FOLDER)


if __name__ == "__main__":
    main()
