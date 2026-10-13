"""
make_data.py (v7) - downloads every Pokemon from PokeAPI and saves:
  pokemon-data.js (website) and pokemon.csv (Excel), next to this script.
New in v6: story-order (gym timing) tables for every game, not just Kanto.
New in v7: then runs add_extras.py (regional forms + PokemonDB route data for every game).
"""
import csv, json, os, re, time, requests
from concurrent.futures import ThreadPoolExecutor

BASE = "https://pokeapi.co/api/v2"
LAST_ID = 1025
FOLDER = os.path.dirname(os.path.abspath(__file__))
STARTERS = {"bulbasaur", "charmander", "squirtle", "chikorita", "cyndaquil", "totodile",
            "treecko", "torchic", "mudkip", "turtwig", "chimchar", "piplup", "snivy", "tepig",
            "oshawott", "chespin", "fennekin", "froakie", "rowlet", "litten", "popplio",
            "grookey", "scorbunny", "sobble", "sprigatito", "fuecoco", "quaxly"}
ROMAN = {"generation-i": 1, "generation-ii": 2, "generation-iii": 3, "generation-iv": 4,
         "generation-v": 5, "generation-vi": 6, "generation-vii": 7, "generation-viii": 8,
         "generation-ix": 9}
session = requests.Session()


def get(url):
    """Download one address. Retries up to 6 times, waiting longer each time (PokeAPI sometimes says 'slow down')."""
    for attempt in range(6):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(1 + attempt * 2)
    return None


def pretty(text):
    return text.replace("-", " ").title()


FAILED = []


def fetch(number):
    poke = get(f"{BASE}/pokemon/{number}")
    species = get(f"{BASE}/pokemon-species/{number}")
    encounters = get(f"{BASE}/pokemon/{number}/encounters")
    if encounters is None:
        FAILED.append(number)
        encounters = []
    print("Downloaded", number, "of", LAST_ID)
    return number, poke, species, encounters


def fetch_chain(chain_id):
    return get(f"{BASE}/evolution-chain/{chain_id}")


def describe(d):
    """Turns PokeAPI evolution details into (plain-English text, level or 0)."""
    if not d:
        return "Special condition", 0
    trig = d["trigger"]["name"]
    level = 0
    if trig == "level-up":
        if d.get("min_level"):
            level = d["min_level"]
            s = f"Level {level}"
        elif d.get("min_happiness"):
            s = "Level up with high friendship"
        else:
            s = "Level up"
        if d.get("time_of_day"):
            s += " during the " + d["time_of_day"]
        if d.get("held_item"):
            s += " holding " + pretty(d["held_item"]["name"])
        if d.get("known_move"):
            s += " knowing " + pretty(d["known_move"]["name"])
        if d.get("location"):
            s += " at " + pretty(d["location"]["name"])
    elif trig == "trade":
        s = "Trade" + (" holding " + pretty(d["held_item"]["name"]) if d.get("held_item") else "")
    elif trig == "use-item" and d.get("item"):
        s = "Use " + pretty(d["item"]["name"])
    else:
        s = pretty(trig)
    return s, level


def walk_chain(node, evmap):
    name = pretty(node["species"]["name"])
    for child in node["evolves_to"]:
        d = child["evolution_details"][0] if child["evolution_details"] else None
        how, level = describe(d)
        evmap.setdefault(name, []).append({"to": pretty(child["species"]["name"]), "how": how, "l": level})
        walk_chain(child, evmap)


def make_where(name, encounters, previous, legendary):
    if name in STARTERS:
        return "Your starter! Choose it from the professor at the start of the game."
    parts = []
    if encounters:
        places = []
        for e in encounters[:3]:
            games = ", ".join(pretty(v["version"]["name"]) for v in e["version_details"][:3])
            places.append(pretty(e["location_area"]["name"]) + " (" + games + ")")
        parts.append("Wild encounters: " + "; ".join(places) + ".")
    if previous:
        parts.append("Evolves from " + pretty(previous) + ", so catch or hatch that one first.")
    if legendary:
        parts.append("Legendary or Mythical: a special one-time encounter, usually late in the game.")
    if not parts:
        parts.append("Not found in the wild in most games. Try a gift, trade, egg or special event.")
    return " ".join(parts)


METHOD = {"walk": "walking", "old-rod": "Old Rod", "good-rod": "Good Rod", "super-rod": "Super Rod",
          "surf": "surfing", "rock-smash": "Rock Smash", "headbutt": "Headbutt", "gift": "gift",
          "gift-egg": "egg gift", "static": "one-time encounter", "only-one": "one-time encounter",
          "pokeflute": "Poke Flute", "dark-grass": "dark grass", "horde": "horde battle",
          "roaming-grass": "roaming", "roaming-water": "roaming", "overworld": "overworld",
          "seaweed": "diving", "honey-tree": "Honey Tree", "hidden-grotto": "Hidden Grotto",
          "island-scan": "Island Scan", "sos": "SOS call", "max-raid": "Max Raid Battle"}

# Ways of getting a Pokemon that need another game, another player, or a special disc. We skip these.
EXCLUDED = {"npc-trade", "pokemon-channel-pal", "colosseum-bonus-disc-jpn", "colosseum-bonus-disc-us",
            "pokemon-ranger", "snag", "snag-rematch"}
GIFTY = {"gift", "gift-egg", "static", "only-one"}

CAP = [12, 18, 22, 27, 32, 38, 43, 48, 54, 60]  # rough team level after each gym (same as the website)


def level_stage(lv):
    for i, c in enumerate(CAP):
        if lv <= c:
            return i
    return 9


# ---- Story order (stage = gym badges earned, or island progress in Alola). 10 = post-game. ----
# Each rule is (stage, regex). The first rule that matches an area name wins.
def _sw(*pairs):
    return list(pairs)


KANTO_RULES = [
    (10, r"(cerulean-cave|one-island|kindle-road|mt-ember|treasure-beach|cape-brink|bond-bridge|three-isle|"
         r"berry-forest|four-island|icefall|five-is|resort-gorgeous|water-labyrinth|lost-cave|outcast|green-path|"
         r"water-path|ruin-valley|memorial-pillar|pattern-bush|canyon-entrance|sevault|tanoby|dilford|liptoo|"
         r"monean|rixy|scufib|viapos|weepth|kanto-altering|birth-island|navel-rock|trainer-tower|kanto-pokecenter).*"),
    (0, r"(pallet-town-area|kanto-route-(1|22)-area|viridian-city-area|kanto-route-2-(south|north).*|viridian-forest-area)"),
    (1, r"(kanto-route-(3|4|24|25)-area|kanto-route-(3|4)-pokemon-center|mt-moon-.*|cerulean-city-area)"),
    (2, r"(kanto-route-(5|6|9|10|11)-area|vermilion-city-area|vermilion-city-ss-anne-dock|ss-anne-area|digletts-cave-area)"),
    (3, r"(rock-tunnel-.*|kanto-route-(7|8)-area|celadon-city-area|celadon-city-celadon-mansion)"),
    (4, r"(pokemon-tower-.*|kanto-route-(12|13|14|15|16|17|18)-area|fuchsia-city-area|kanto-safari-zone-.*|"
        r"celadon-city-prize-corner|kanto-underground-path-area)"),
    (5, r"(saffron-city-.*|kanto-power-plant-area)"),
    (6, r"(kanto-sea-route-(19|20|21)-area|seafoam-islands-.*|cinnabar-island-.*|pokemon-mansion-.*)"),
    (8, r"kanto-route-23-area"),
    (9, r"(kanto-victory-road-.*|roaming-kanto-area)"),
]
KANTO_MINS = {"old-rod": 2, "good-rod": 4, "super-rod": 5, "surf": 5, "pokeflute": 4}

# Johto (Gold, Silver, Crystal, HeartGold, SoulSilver). Kanto areas in these games are post-game.
JOHTO_RULES = [
    (10, r"(kanto-.*|celadon-city.*|cerulean-.*|cinnabar-.*|digletts-.*|fuchsia-.*|mt-moon.*|pallet-.*|pewter-.*|"
         r"rock-tunnel.*|saffron-.*|seafoam-.*|vermilion-.*|viridian-.*|mt-silver.*|sinjoh.*|embedded-tower.*|unknown-.*)"),
    (0, r"(new-bark-town-area|johto-route-(29|30|31)-area|cherrygrove-city-area|violet-city-.*|sprout-tower-.*|"
        r"dark-cave-violet-city-entrance)"),
    (1, r"(johto-route-(32|33|46)-area|ruins-of-alph-.*|union-cave-.*|azalea-town-area|slowpoke-well-.*)"),
    (2, r"(ilex-forest-area|johto-route-(34|35)-area|goldenrod-city-(area|bills-house|north-gate)|national-park-area)"),
    (3, r"(johto-route-(36|37)-area|ecruteak-city-area|burned-tower-.*|goldenrod-city-(department-store-5f|game-corner))"),
    (4, r"(johto-route-(38|39)-area|olivine-city-.*|johto-sea-route-(40|41)-area|cianwood-city-.*)"),
    (5, r"(johto-route-42-area|mt-mortar-.*)"),
    (6, r"(johto-route-(43|47|48)-area|johto-route-47-.*|lake-of-rage-area|team-rocket-hq-area|whirl-islands-.*|"
        r"bell-tower-.*|johto-safari-zone-.*|safari-zone-gate-area|johto-pokemart-area)"),
    (7, r"(johto-route-(44|45)-area|ice-path-.*|blackthorn-city-area|dragons-den-area|dark-cave-blackthorn-city-entrance)"),
    (8, r"tohjo-falls-area"),
    (9, r"roaming-johto-area"),
]
JOHTO_MINS = {"old-rod": 1, "good-rod": 4, "super-rod": 10, "surf": 4}

# Hoenn (Ruby, Sapphire, Emerald, Omega Ruby, Alpha Sapphire)
HOENN_RULES = [
    (10, r"(faraway-island-area|birth-island-area|navel-rock-area|southern-island-area|hoenn-battle-frontier-area|"
         r"hoenn-altering-cave-area|mirage-spot-.*|battle-resort-area|crescent-isle-area|fabled-cave-area|gnarled-den-area|"
         r"nameless-cavern-area|pathless-plain-area|trackless-forest-area|soaring-in-the-sky-area|sea-mauville-inside|"
         r"mossdeep-space-center-area|scorched-slab-.*|mirage-tower-area|hoenn-pokecenter-area|artisan-cave-area)"),
    (0, r"(littleroot-town-area|hoenn-route-(101|102|103)-area|hoenn-route-104-.*|petalburg-city-area|petalburg-woods-area|rustboro-city-area)"),
    (1, r"(rusturf-tunnel-area|hoenn-route-(106|116)-area|dewford-town-area|granite-cave-.*)"),
    (2, r"(hoenn-route-(109|110|117)-area|slateport-city-(area|contest-hall))"),
    (3, r"(verdanturf-town-contest-hall|fallarbor-town-contest-hall|hoenn-route-(111|112|118)-area|fiery-path-area|jagged-pass-area|lavaridge-town-area|magma-hideout-area|team-magma-hideout-area)"),
    (4, r"(hoenn-route-(113|114|115)-area)"),
    (5, r"(hoenn-route-(105|107|108|119)-area|hoenn-route-119-weather-institute|abandoned-ship-area|meteor-falls-.*|"
        r"new-mauville-.*|fortree-city-area)"),
    (6, r"(hoenn-route-(120|121|122|123|124|125)-area|hoenn-safari-zone-.*|lilycove-city-(area|contest-hall)|mt-pyre-.*|"
        r"team-aqua-hideout-area|desert-underpass-area|mossdeep-city-area|shoal-cave-.*|jagged-pass-ruins)"),
    (7, r"(sootopolis-city-area|hoenn-route-(126|127|128)-area|hoenn-route-(124|126)-underwater|seafloor-cavern-area|"
        r"cave-of-origin-.*|mossdeep-city-stevens-house)"),
    (8, r"(hoenn-route-(129|130|131|132|133|134)-area|pacifidlog-town-area|island-cave-area|desert-ruins-area|"
        r"ancient-tomb-area|terra-cave-area|marine-cave-area)"),
    (9, r"(hoenn-victory-road-.*|ever-grande-city-area|sky-pillar-.*|roaming-hoenn-area|mirage-island-area)"),
]
HOENN_MINS = {"old-rod": 0, "good-rod": 3, "super-rod": 7, "surf": 5, "rock-smash": 2, "seaweed": 7}

# Sinnoh. Platinum fights Fantina 3rd; Diamond and Pearl fight her 5th. Each rule: (DP stage, Platinum stage, regex).
SINNOH_DP_PT = [
    (10, 10, r"(turnback-cave-.*|spear-pillar-area|sinnoh-hall-of-origin-.*|distortion-world-area|newmoon-island-area|"
             r"flower-paradise-area|sendoff-spring-area|maniac-tunnel-.*|ruin-maniac-cave-.*|snowpoint-temple-.*|"
             r"stark-mountain-heatran-chamber|lake-(valor|acuity)-cavern|sinnoh-route-(224|225|226|227|228|229)-area|"
             r"sinnoh-sea-route-(226|230)-area|sinnoh-sea-route-226-island-house|resort-area-area|fuego-ironworks-area|"
             r"snowpoint-city-north-west-house|sinnoh-pokemart-area)"),
    (0, 0, r"(twinleaf-town-area|sinnoh-route-(201|202|203)-area|sinnoh-route-204-south-.*|oreburgh-.*|lake-verity-before-.*)"),
    (1, 1, r"(sinnoh-route-204-north-.*|ravaged-path-area|floaroma-meadow-area|valley-windworks-area|sinnoh-route-205-.*|"
           r"eterna-forest-area|eterna-city-.*|lake-verity-after-.*)"),
    (2, 2, r"(sinnoh-route-(206|207|208)-area|wayward-cave-.*|mt-coronet-1f-route-207|hearthome-city-.*|"
           r"sinnoh-route-212-north-.*)"),
    (2, 3, r"(sinnoh-route-209-area|lost-tower-.*|solaceon-ruins-.*|sinnoh-route-210-.*|sinnoh-route-211-.*|"
           r"celestic-town-area|mt-coronet-1f-route-211|sinnoh-route-215-area|veilstone-city-area)"),
    (3, 3, r"(trophy-garden-area|old-chateau-.*)"),
    (3, 4, r"(sinnoh-route-(212-east|213|214)-.*|pastoria-city-area|great-marsh-.*|valor-lakefront-area|lake-valor-area)"),
    (4, 4, r"(mt-coronet-(2f|3f|b1f|4f.*|5f|6f)|mt-coronet-1f-from-exterior)"),
    (5, 5, r"(sinnoh-route-218-area|canalave-city-area|iron-island-.*)"),
    (6, 6, r"(sinnoh-route-(216|217|219|221)-area|sinnoh-sea-route-220-area|mt-coronet-1f-route-216|mt-coronet-exterior-.*|"
           r"acuity-lakefront-area|lake-acuity-area|snowpoint-city-area)"),
    (7, 7, r"(sinnoh-route-222-area|sunyshore-city-area|valor-lakefront-area)"),
    (8, 8, r"(sinnoh-sea-route-223-area|sinnoh-route-(224|225)-area)"),
    (9, 9, r"(sinnoh-victory-road-.*|sinnoh-pokemon-league-area|stark-mountain-.*|roaming-sinnoh-area)"),
]
SINNOH_MINS = {"old-rod": 1, "good-rod": 4, "super-rod": 6, "surf": 4}

# Unova
UNOVA_BW = [
    (10, r"(undella-.*|giant-chasm-.*|unova-route-13-area|abundant-shrine-.*|reversal-mountain-.*|challengers-cave-.*|"
         r"nature-sanctuary-area|liberty-garden-.*|village-bridge-area|seaside-cave-.*|trial-chamber-area|guidance-chamber-area|"
         r"p2-laboratory-area|iron-room-area|glacier-room-area|rocky-mountain-room-area|cold-storage-area|"
         r"underground-ruins-area|clay-tunnel-area|unova-route-(11|12|14)-area|humilau-.*|marvelous-bridge-area)"),
    (0, r"(nuvema-town-area|unova-route-(1|2)-area|accumula-town-area|striaton-city-area|dreamyard-.*)"),
    (1, r"(unova-route-3-area|wellspring-cave-area|nacrene-city-.*|pinwheel-forest-.*)"),
    (2, r"(castelia-city-.*)"),
    (3, r"(unova-route-(4|16)-area|desert-resort-.*|relic-castle-.*|relic-passage-.*|castelia-sewers-.*|lostlorn-forest-area)"),
    (4, r"(unova-route-5-area|driftveil-drawbridge-area|driftveil-city-area)"),
    (5, r"(unova-route-6-.*|chargestone-cave-.*|mistralton-cave-area)"),
    (6, r"(unova-route-7-area|celestial-tower-.*|twist-mountain-.*|icirrus-city-area)"),
    (7, r"(unova-route-(8|9)-area|moor-of-icirrus-area)"),
    (8, r"(dragonspiral-tower-.*|unova-route-10-.*|relic-castle-.*)"),
    (8, r"unova-route-15-area"),
    (9, r"(unova-victory-road-.*|ns-castle-throne-room)"),
    (10, r"(unova-route-(17|18)-area|team-flare-secret-hq-area)"),
]
UNOVA_B2W2 = [
    (10, r"(giant-chasm-.*|abundant-shrine-.*|challengers-cave-.*|nature-sanctuary-area|liberty-garden-.*|"
         r"guidance-chamber-area|p2-laboratory-area|iron-room-area|glacier-room-area|rocky-mountain-room-area|"
         r"cold-storage-area|strange-house-.*|trial-chamber-area|seaside-cave-.*|reversal-mountain-.*)"),
    (0, r"(aspertia-city-area|unova-route-(19|20)-area|floccesy-.*|unova-route-19-hidden-.*)"),
    (1, r"(virbank-.*)"),
    (2, r"(castelia-city-.*|unova-route-22-.*)"),
    (3, r"(unova-route-(4|16)-area|desert-resort-.*|relic-castle-.*|relic-passage-.*|castelia-sewers-.*|lostlorn-forest-area)"),
    (4, r"(unova-route-5-.*|driftveil-drawbridge-area|driftveil-city-area|clay-tunnel-area)"),
    (5, r"(unova-route-6-.*|chargestone-cave-.*|mistralton-cave-area)"),
    (6, r"(unova-route-(7|8|9)-.*|celestial-tower-.*|twist-mountain-.*|icirrus-city-area|moor-of-icirrus-area)"),
    (7, r"(dragonspiral-tower-.*|undella-.*|unova-route-(11|12|13|14|21)-.*|village-bridge-area|marvelous-bridge-area|humilau-.*)"),
    (8, r"(unova-route-(10|15|23)-.*|unova-victory-road-.*)"),
    (3, r"(striaton-city-area|dreamyard-.*|unova-route-(1|2|3)-.*|pinwheel-forest-.*|wellspring-cave-area|nacrene-city-.*|"
        r"lostlorn-forest-hidden-grotto)"),
    (10, r"(unova-route-(17|18)-.*|underground-ruins-area)"),
]

# Kalos (X, Y): route numbers rise with the story.
KALOS_RULES = [
    (10, r"(terminus-cave-.*|pokemon-village-area|unknown-dungeon-area|kalos-route-(21|22)-area|sea-spirits-den-area)"),
    (0, r"(aquacorde-town-area|kalos-route-(2|3)-area|santalune-forest-area)"),
    (1, r"(kalos-route-(4|5|6)-area|kalos-berry-fields-area|lumiose-city-area|parfum-palace-area|connecting-cave-area)"),
    (2, r"(kalos-route-(7|8|9)-area|cyllage-city-area|ambrette-town-area|azure-bay-area)"),
    (3, r"(shalour-city-area|tower-of-mastery-area|kalos-route-(10|11|12)-area|glittering-cave-.*|reflection-cave-.*)"),
    (4, r"(kalos-route-13-area|team-flare-secret-hq-area)"),
    (5, r"(kalos-route-14-area|laverre-city-area|lost-hotel-area)"),
    (6, r"(kalos-route-(15|16)-area|couriway-town-area)"),
    (7, r"(kalos-route-(17|18)-area|frost-cavern-.*)"),
    (8, r"(kalos-route-(19|20)-area)"),
    (9, r"(kalos-victory-road-.*|roaming-kalos-area)"),
]

# Alola (Sun, Moon, Ultra Sun, Ultra Moon). No gyms: stage follows island progress.
ALOLA_RULES = [
    (10, r"(ultra-.*|resolution-cave-area|team-rockets-castle-area|poke-pelago-elite-four-defeated|exeggutor-island-area|"
         r"new-mauville-area)"),
    (0, r"(iki-town-area|alola-route-1-.*|hauoli-city-.*|alola-route-2-.*|trainers-school-area|alola-route-3-.*|"
        r"verdant-cavern.*|melemele-meadow-area)"),
    (1, r"(melemele-sea-area|ten-carat-hill-.*|seaward-cave-area|kalae-bay-area|hauoli-cemetery-area|memorial-hill-area|"
        r"alola-route-4-area|paniola-town-area)"),
    (2, r"(akala-outskirts-area|alola-route-(5|7)-area|alola-route-6-.*|heahea-.*|paniola-ranch-area|brooklet-hill-.*|hano-beach-area|"
        r"digletts-tunnel-area)"),
    (3, r"(wela-volcano-park-area|lush-jungle-.*|konikoni-city-area|alola-route-(8|9)-.*|alola-berry-fields-area|"
        r"secluded-shore-area)"),
    (4, r"(alola-route-(10|11|12)-area|ulaula-beach-area|malie-city-.*|malie-garden-area|mount-hokulani-.*|haina-desert-area|"
        r"ulaula-meadow-area|blush-mountain-area|tapu-village-area|royal-avenue-area|mahalo-trail-area|dividing-peak-tunnel-area|"
        r"poke-pelago-ulaula-island-reached)"),
    (5, r"(alola-route-(13|14)-area|thrifty-megamart-abandoned-site|lake-of-the-(sunne|moone)-area|altar-of-the-(sunne|moone)-area|"
        r"aether-paradise-2f)"),
    (6, r"(alola-route-(15|16|17)-.*|seafolk-village-.*|sandy-cave-area)"),
    (7, r"(poni-wilds-area|ancient-poni-path-area|poke-pelago-poni-island-reached)"),
    (8, r"(vast-poni-canyon-.*|poni-(grove|meadow|breaker-coast|gauntlet)-area|poni-plains-.*|ruins-of-.*)"),
    (9, r"(mount-lanakila-.*)"),
]

# Galar (Sword, Shield). Gym order: Turffield, Hulbury, Motostoke, Stow-on-Side, Ballonlea, Circhester, Spikemuth, Hammerlocke.
GALAR_RULES = [
    (10, r"(galar-battle-tower-area|lake-of-outrage-area|turffield-area)"),
    (3, r".*max-den.*"),
    (0, r"(postwick-.*|galar-route-(1-area|2-main|3-east|3-west)|slumbering-weald-main|galar-mine-area|turffield-gym)"),
    (1, r"(galar-route-(4-area|2-lake|2-lakeside))"),
    (2, r"(hulbury-area|galar-route-5-area|rolling-fields-.*|bridge-field-area|dusty-bowl-area|giants-seat-area|"
        r"stony-wilderness-.*|giants-mirror-.*|giants-cap-.*|axews-eye-area|south-lake-miloch-.*|north-lake-miloch-area|"
        r"west-lake-axewell-area|east-lake-axewell-area|motostoke-outskirts-area|meetup-spot-area|watchtower-ruins-area|"
        r"dappled-grove-area|hammerlocke-hills-area|galar-mine-no-2-area|motostoke-riverbank-area)"),
    (3, r"(motostoke-.*|galar-route-6-area|glimwood-tangle-area|galar-wild-area-max-dens-area|stow-on-side-area)"),
    (4, r"(galar-route-7-area|ballonlea-gym)"),
    (5, r"(galar-route-8-.*)"),
    (6, r"(circhester-area|galar-route-9-main|galar-route-9-circhester-bay)"),
    (7, r"(spikemuth-area|galar-route-9-outer-spikemuth|hammerlocke-area|slumbering-weald-deep)"),
    (8, r"(wyndon-area|galar-route-10-.*)"),
    (9, r"energy-plant-tower-summit"),
]

STORY = {}
for _g in ("red", "blue", "yellow", "firered", "leafgreen"):
    STORY[_g] = ([(s, p) for s, p in KANTO_RULES], KANTO_MINS)
for _g in ("gold", "silver", "crystal", "heartgold", "soulsilver"):
    STORY[_g] = (JOHTO_RULES, JOHTO_MINS)
for _g in ("ruby", "sapphire", "emerald", "omega-ruby", "alpha-sapphire"):
    STORY[_g] = (HOENN_RULES, HOENN_MINS)
STORY["diamond"] = STORY["pearl"] = ([(a, r) for a, b, r in SINNOH_DP_PT], SINNOH_MINS)
STORY["platinum"] = ([(b, r) for a, b, r in SINNOH_DP_PT], SINNOH_MINS)
STORY["black"] = STORY["white"] = (UNOVA_BW, {})
STORY["black-2"] = STORY["white-2"] = (UNOVA_B2W2, {})
STORY["x"] = STORY["y"] = (KALOS_RULES, {})
for _g in ("sun", "moon", "ultra-sun", "ultra-moon"):
    STORY[_g] = (ALOLA_RULES, {})
STORY["sword"] = STORY["shield"] = (GALAR_RULES, {})

# Needs other players or special hardware, so never suggested.
EXCLUDED_AREAS = re.compile(r"friend-safari-.*")

AREA_MED = {}  # (game, area) -> typical wild level, filled in by main() before stages are worked out


def area_stage(game, area, methods, lo):
    """Story stage (0-10) when this encounter becomes available in this game."""
    st = None
    rules, mins = STORY.get(game, ([], {}))
    for s, pat in rules:
        if re.fullmatch(pat, area):
            st = s
            break
    typical = AREA_MED.get((game, area), lo)
    if st is not None and st < 10:
        # A curated area can still be too early for a high-level Pokemon found there, so also look at its own level.
        st = max([st, level_stage(lo) - 1] + [mins.get(x, 0) for x in methods])
    elif st is None and re.search(r"(cerulean-cave|mt-silver)", area):
        st = 10
    if st is None:
        st = min(level_stage(typical) + 1, 9)
        if methods and all(x in GIFTY for x in methods):
            st = max(st, 3)  # gifts and one-time encounters: levels say little, so assume mid-game
    return min(st, 10)


def game_data(encounters):
    """Per game: lowest level (e), plain-English places (L) and story stage (S). Trades are skipped."""
    per = {}
    for e in encounters:
        area = e["location_area"]["name"]
        if EXCLUDED_AREAS.fullmatch(area):
            continue
        place = pretty(area).replace(" Area", "")
        for vd in e["version_details"]:
            v = vd["version"]["name"]
            for d in vd["encounter_details"]:
                mname = d["method"]["name"]
                if mname in EXCLUDED:
                    continue
                slot = per.setdefault(v, {}).setdefault(area, {"place": place, "lo": 999, "hi": 0, "m": set()})
                slot["lo"] = min(slot["lo"], d["min_level"])
                slot["hi"] = max(slot["hi"], d["max_level"])
                slot["m"].add(mname)
    lows, texts, stages = {}, {}, {}
    for v, areas in per.items():
        rows = []
        for area, s in areas.items():
            rows.append((area_stage(v, area, s["m"], s["lo"]), s["lo"], s))
        rows.sort(key=lambda r: (r[0], r[1]))
        best = rows[0][0]
        stages[v] = best
        lows[v] = min(r[1] for r in rows if r[0] == best)
        parts = []
        for st, lo, s in rows[:3]:
            lv = f"Lv {lo}" if lo == s["hi"] else f"Lv {lo}-{s['hi']}"
            hows = set()
            for x in s["m"]:
                t = METHOD.get(x, pretty(x).lower())
                if x in ("gift", "static", "only-one") and "Prize Corner" in s["place"]:
                    t = "Game Corner prize (coins)"
                elif x == "gift" and "Pokemon Center" in s["place"]:
                    t = "gift or purchase"
                hows.add(t)
            how = ", ".join(sorted(hows))
            parts.append(("Post-game: " if st == 10 else "") + s["place"] + " (" + how + ", " + lv + ")")
        texts[v] = "; ".join(parts)
    return lows, texts, stages


def fetch_dex(dex_id):
    d = get(f"{BASE}/pokedex/{dex_id}")
    return {e["pokemon_species"]["name"] for e in d["pokemon_entries"]} if d else set()


DEXES = {}


def main():
    print("Downloading... this takes several minutes. Please wait.")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch, range(1, LAST_ID + 1)))
        chain_ids = sorted({int(s["evolution_chain"]["url"].rstrip("/").split("/")[-1])
                            for _, _, s, _ in results if s and s.get("evolution_chain")})
        print("Downloading", len(chain_ids), "evolution chains...")
        chains = list(pool.map(fetch_chain, chain_ids))

    evmap = {}
    for c in chains:
        if c:
            walk_chain(c["chain"], evmap)

    # Typical wild level of every area in every game (used to place areas the story tables do not cover).
    seen = {}
    for _, _, _, enc in results:
        for e in enc:
            for vd in e["version_details"]:
                for d in vd["encounter_details"]:
                    if d["method"]["name"] in EXCLUDED or d["method"]["name"] in GIFTY:
                        continue
                    seen.setdefault((vd["version"]["name"], e["location_area"]["name"]), []).append(
                        (d["min_level"] + d["max_level"]) / 2)
    for key, levels in seen.items():
        levels.sort()
        AREA_MED[key] = levels[len(levels) // 2]

    # Games with no catch data in PokeAPI: use the game's own Pokedex instead.
    global DEXES
    DEXES = {"sv": fetch_dex(31), "la": fetch_dex(30)}

    parents = set()
    for _, _, species, _ in results:
        if species and species["evolves_from_species"]:
            parents.add(species["evolves_from_species"]["name"])

    output = []
    for number, poke, species, encounters in results:
        if not poke or not species:
            print("Skipped number", number, "(download failed)")
            continue
        name = species["name"]
        stats = {s["stat"]["name"]: s["base_stat"] for s in poke["stats"]}
        types = [t["type"]["name"][:3] for t in sorted(poke["types"], key=lambda t: t["slot"])]
        legendary = bool(species["is_legendary"] or species["is_mythical"])
        previous = species["evolves_from_species"]["name"] if species["evolves_from_species"] else None
        e_levels, loc_text, stage_map = game_data(encounters)
        dexes = [k for k, names in DEXES.items() if name in names]
        output.append({
            "id": number, "n": pretty(name), "t": types,
            "hp": stats["hp"], "at": stats["attack"], "df": stats["defense"],
            "sa": stats["special-attack"], "sd": stats["special-defense"], "sp": stats["speed"],
            "g": ROMAN.get(species["generation"]["name"], 9),
            "st": name in STARTERS, "lg": legendary, "fe": name not in parents,
            "pre": pretty(previous) if previous else "",
            "ev": evmap.get(pretty(name), []),
            "e": e_levels,
            "L": loc_text,
            "S": stage_map,
            "D": dexes,
            "w": make_where(name, encounters, previous, legendary),
        })

    if len(FAILED) > 25:
        print("STOP: the download of", len(FAILED), "Pokemon failed (PokeAPI was busy or your internet dropped).")
        print("Nothing was saved, so your old data file is untouched. Wait a minute and run this again.")
        return
    with open(os.path.join(FOLDER, "pokemon-data.js"), "w", encoding="utf-8") as f:
        f.write("const P = ")
        json.dump(output, f, separators=(",", ":"))
        f.write(";")

    with open(os.path.join(FOLDER, "pokemon.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Number", "Name", "Types", "HP", "Attack", "Defense", "Sp Atk", "Sp Def", "Speed",
                    "Generation", "Starter", "Legendary", "Final Evolution", "Evolves From",
                    "Evolves Into", "Where To Get It"])
        for p in output:
            into = "; ".join(e["to"] + " (" + e["how"] + ")" for e in p["ev"])
            w.writerow([p["id"], p["n"], "/".join(p["t"]), p["hp"], p["at"], p["df"], p["sa"], p["sd"],
                        p["sp"], p["g"], p["st"], p["lg"], p["fe"], p["pre"], into, p["w"]])
    print("Done! Saved", len(output), "Pokemon to", FOLDER)
    print("Now adding regional forms and route data for the newer games...")
    import add_extras
    add_extras.main()


if __name__ == "__main__":
    main()