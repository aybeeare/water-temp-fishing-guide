"""
Initialize the SQLite database and seed the fishing_logic and location_aliases tables.
Run once before first deployment:  python db/init_db.py
"""
import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "fishing.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

# ---------------------------------------------------------------------------
# Seed rows for fishing_logic
# All strings are static and pre-approved — no LLM generation.
# Replace ASIN placeholders with live products before deployment.
# ---------------------------------------------------------------------------
FISHING_LOGIC_SEED = [
    # (temp_min_f, temp_max_f, fish_behavior, recommended_gear, asin, water_type)
    (32,  40,
     "Ice-cold conditions. Most species are lethargic and holding tight to bottom structure. "
     "Target bluegill and perch under the ice with tiny jigs tipped with waxworms.",
     "Northland Buck-Shot Ice Fishing Rattle Spoon",
     "B0891QB6G9", "freshwater"),

    (40,  50,
     "Cold water slows metabolism. Walleye and northern pike are your best bets — "
     "they stay active in cold water longer than bass. Jig slowly near rocky points.",
     "TRUSCEND Jigging Spinner Bait for Freshwater",
     "B08ZMQQF8H", "freshwater"),

    (50,  55,
     "Bass are holding deep on structure and moving slowly. Trout are feeding near "
     "the surface at dawn. Use a drop-shot rig and work it patiently.",
     "TRUSCEND Shadtale Soft Fishing Lures with BKK Hooks",
     "B08W2Z6VT8", "freshwater"),

    (55,  60,
     "Bass are transitioning from winter to pre-spawn. Trout are at their peak. "
     "Crappie are moving shallow. This is a great multi-species window.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "freshwater"),

    (60,  65,
     "Bass entering pre-spawn feeding frenzy. Prime topwater and crankbait window. "
     "Fish points and channel edges early in the morning.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "freshwater"),

    (65,  72,
     "Peak activity for bass, crappie, and panfish. Almost all freshwater species "
     "are active throughout the water column. Excellent all-around fishing.",
     "Ned Rig Finesse Kit — Soft Plastic Worms",
     "B09M3F2PQZ", "freshwater"),

    (72,  78,
     "Largemouth bass are at their peak feeding. Catfish are becoming very active, "
     "especially at night. Use soft plastics and scent-based baits.",
     "Topwater Frog Lure Bass Kit",
     "B091GG71M2", "freshwater"),

    (78,  84,
     "Warm water pushes trout and salmon to deeper, cooler zones. Bass go deep "
     "midday but stay active early morning and evening. Catfish prime at night.",
     "Catfish Punch Bait",
     "B0FBYF917T", "freshwater"),

    (84,  110,
     "Heat stress for most species. Fish very early morning or after dark near "
     "cool inflows and shaded structure. Keep sessions short.",
     "Bulk Fishing Hooks Set — Worm and Catfish Hooks",
     "B09R1GQPZK", "freshwater"),

    # Saltwater generic fallbacks
    (45,  58,
     "Cold saltwater keeps fish active near structure. "
     "Striped bass and flounder are your best bets — work bucktail jigs near bottom.",
     "Circle Hook Bottom Rig — Flounder Halibut Snapper",
     "B0F1CMB7DD", "saltwater"),

    (58,  68,
     "Excellent inshore action across the board. Multiple species are feeding actively "
     "on flats and near structure. Prime kayak fishing conditions.",
     "Berkley Gulp! Alive! Shrimp and Peeler Crab Assortment",
     "B001E25LLQ", "saltwater"),

    (68,  78,
     "Inshore fishing at its best. Expect multiple species near structure and in the surf. "
     "Offshore: mahi-mahi and kingfish are active near weed lines.",
     "Popping Cork Rig for Redfish and Speckled Trout",
     "B09ZNQ8JTM", "saltwater"),

    (78,  90,
     "Peak summer saltwater action. Offshore species are thriving near weed lines and structure. "
     "Inshore night fishing near bridges and passes produces the best results.",
     "Yellowtail Snapper Jigs — Saltwater Jigging",
     "B0CNPFJS1Z", "saltwater"),
]

# ---------------------------------------------------------------------------
# Species-specific fishing_logic rows — take priority over generic fallbacks
# when the location has known target species.
# (temp_min_f, temp_max_f, fish_behavior, recommended_gear, asin, water_type, target_species)
# ---------------------------------------------------------------------------
SPECIES_LOGIC_SEED = [
    # ── Walleye ──────────────────────────────────────────────────────────────
    (40, 68,
     "Walleye are highly active and feeding aggressively near bottom structure, rocky points, "
     "and channel edges. They're most active at dawn and dusk — jig vertically near the bottom "
     "with blade baits or jigging spoons.",
     "Jig Heads for Walleye Bass Trout",
     "B0F5PTZDK3", "freshwater", "walleye"),

    (68, 80,
     "Walleye have shifted to night feeding patterns. Troll spinner rigs with nightcrawlers "
     "along weed edges and channel breaks after sunset — stay out late for the best action.",
     "TRUSCEND Jigging Spinner Bait — Walleye Night Rig",
     "B08ZMQQF8H", "freshwater", "walleye"),

    # ── Trout (rainbow, brown, lake, brook) ──────────────────────────────────
    (42, 65,
     "Trout are in their prime feeding window. They're rising to hatches near riffles and "
     "undercut banks throughout the day. Work inline spinners along current seams or drift "
     "natural bait through the deeper pools.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "freshwater", "trout"),

    # ── Salmon and Steelhead ─────────────────────────────────────────────────
    (44, 58,
     "Salmon and steelhead are in their prime feeding zone. Troll flasher-and-spoon rigs "
     "at depth, or work river mouths with heavy spoons and plugs during the upstream migration.",
     "Berkley Gulp! Floating Salmon Eggs",
     "B000GAYF3M", "freshwater", "salmon"),

    # ── Northern Pike ────────────────────────────────────────────────────────
    (45, 65,
     "Northern pike are in aggressive ambush mode near weed beds and fallen timber. "
     "They'll slam large flashy spoons and jerkbaits without hesitation — use heavy line, "
     "they explode directly into cover the instant they're hooked.",
     "Hard Metal Buzzbait Spinnerbait for Pike and Bass",
     "B07DC4GB43", "freshwater", "northern_pike"),

    # ── Largemouth Bass ──────────────────────────────────────────────────────
    (58, 68,
     "Largemouth bass are in pre-spawn mode and feeding heavily near shallow cover and spawning flats. "
     "This is the most productive time of year — work jerkbaits, swimbaits, "
     "and square-bill crankbaits through transition zones.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "freshwater", "largemouth_bass"),

    (68, 82,
     "Largemouth bass are at peak aggression early morning and evening. Throw topwater frogs "
     "and poppers over matted vegetation at dawn. Go deep and slow with soft plastics midday "
     "when they push down to cooler water.",
     "Topwater Frog Lure Bass Kit",
     "B091GG71M2", "freshwater", "largemouth_bass"),

    # ── Smallmouth Bass ──────────────────────────────────────────────────────
    (55, 72,
     "Smallmouth bass are feeding aggressively on rocky points, boulders, and current seams. "
     "Tubes, drop-shots, and inline spinners are all producing — "
     "they hit hard and fight harder than their size suggests.",
     "Worm-Tube Jigs Kit for Smallmouth and Largemouth Bass",
     "B0D8PRTY9S", "freshwater", "smallmouth_bass"),

    # ── Catfish ──────────────────────────────────────────────────────────────
    (65, 86,
     "Catfish are becoming very active, especially at night near deep holes and current breaks. "
     "Bottom rigs with cut bait or stink bait near channel edges and scour holes produce best — "
     "set up after dark for the biggest fish.",
     "Catfish Punch Bait",
     "B0FBYF917T", "freshwater", "catfish"),

    # ── Striped Bass ─────────────────────────────────────────────────────────
    (50, 68,
     "Striped bass are feeding hard on bunker and herring schools near current rips and "
     "rocky structure. Look for diving birds over breaking fish and work metal jigs "
     "through the blitz — it can be explosive.",
     "TRUSCEND Shadtale Soft Fishing Lures with BKK Hooks",
     "B08W2Z6VT8", "saltwater", "striped_bass"),

    # ── Redfish ──────────────────────────────────────────────────────────────
    (62, 82,
     "Redfish are tailing and feeding actively on shallow flats near oyster bars and marsh edges. "
     "Work a popping cork with live shrimp, or slow-roll a gold spoon along the grass line — "
     "look for the tails breaking the surface in calm water.",
     "Popping Cork Rig for Redfish and Speckled Trout",
     "B09ZNQ8JTM", "saltwater", "redfish"),

    # ── Tarpon ───────────────────────────────────────────────────────────────
    (74, 92,
     "Tarpon are rolling and feeding near passes, bridges, and beach fronts — peak season. "
     "Present live crabs or mullet near structure at night, or throw large topwater lures at first light. "
     "Use heavy 80-pound leader — their mouths are like sandpaper and they'll jump instantly.",
     "Chartreuse Tarpon Saltwater Streamer Fly",
     "B07SW7ZN9G", "saltwater", "tarpon"),

    # ── Bonefish ─────────────────────────────────────────────────────────────
    (72, 88,
     "Bonefish are tailing on the flats in crystal-clear water — sight fishing at its finest. "
     "Cast small crab or shrimp patterns 6 feet ahead of a tailing fish and let it sink slowly. "
     "Stealth is everything — they spook in an instant in skinny water.",
     "Bonefish Fly Fishing Flies",
     "B07RRDYN6H", "saltwater", "bonefish"),

    # ── Flounder ─────────────────────────────────────────────────────────────
    (55, 74,
     "Flounder are lying in ambush on sandy and muddy bottoms near channel edges and pilings. "
     "Slow-drag a Gulp shrimp or bucktail jig along the bottom and pause frequently — "
     "they strike on the pause when the bait appears to be fleeing.",
     "Berkley Gulp! Alive! Shrimp and Peeler Crab Assortment",
     "B001E25LLQ", "saltwater", "flounder"),

    # ── Peacock Bass ─────────────────────────────────────────────────────────
    (76, 92,
     "Peacock bass are explosively aggressive near lily pads and submerged structure. "
     "They attack topwater lures with incredible force and sprint directly for cover when hooked. "
     "Use heavy 30-pound braid — do not give them an inch.",
     "Bass Fishing Topwater Popper Lures",
     "B0CGR81YDZ", "freshwater", "peacock_bass"),

    # ── Yellowtail (Pacific) ─────────────────────────────────────────────────
    (62, 76,
     "Yellowtail are feeding aggressively on bait schools near kelp paddies and offshore structure. "
     "Live sardine fishing is most effective, or work a flat-fall jig on the initial drop "
     "while the bait is sinking — they hit it on the way down.",
     "Yellowtail Snapper Jigs Fishing",
     "B0CNPFJS1Z", "saltwater", "yellowtail"),

    # ── Halibut (Pacific / Alaska) ───────────────────────────────────────────
    (46, 60,
     "Halibut are feeding on the bottom near sandy flats, channel edges, and deep drop-offs. "
     "Work large swimbaits, herring rigs, or bucktail jigs slowly along the bottom and pause — "
     "they ambush from below and need a slow presentation.",
     "Circle Hook Bottom Rig for Halibut Flounder Snapper",
     "B0F1CMB7DD", "saltwater", "halibut"),
]

# ---------------------------------------------------------------------------
# Site-to-species mapping
# Sources: USGS station IDs, NOAA station IDs, seatemperature.info slugs
# ---------------------------------------------------------------------------
SITE_SPECIES_SEED = [
    # ── Great Lakes (USGS) ───────────────────────────────────────────────────
    ("04085427", "walleye"),       ("04085427", "salmon"),         ("04085427", "smallmouth_bass"), ("04085427", "trout"),
    ("04085068", "walleye"),       ("04085068", "salmon"),         ("04085068", "smallmouth_bass"),
    ("040851385", "trout"),        ("040851385", "salmon"),        ("040851385", "walleye"),        ("040851385", "smallmouth_bass"), ("040851385", "northern_pike"),
    ("04002000", "trout"),         ("04002000", "walleye"),        ("04002000", "smallmouth_bass"), ("04002000", "northern_pike"),
    ("04063700", "walleye"),       ("04063700", "trout"),          ("04063700", "smallmouth_bass"), ("04063700", "northern_pike"),
    ("04124000", "walleye"),       ("04124000", "salmon"),         ("04124000", "smallmouth_bass"),
    ("04173500", "walleye"),       ("04173500", "smallmouth_bass"),("04173500", "salmon"),          ("04173500", "catfish"),
    ("04214500", "walleye"),       ("04214500", "smallmouth_bass"),("04214500", "salmon"),
    ("04240010", "walleye"),       ("04240010", "smallmouth_bass"),("04240010", "salmon"),          ("04240010", "trout"),
    # ── US Rivers (USGS) ─────────────────────────────────────────────────────
    ("01372500", "striped_bass"),  ("01372500", "largemouth_bass"),("01372500", "smallmouth_bass"), ("01372500", "catfish"),
    ("01646500", "largemouth_bass"),("01646500","smallmouth_bass"),("01646500", "striped_bass"),    ("01646500", "catfish"),
    ("07010000", "largemouth_bass"),("07010000","catfish"),        ("07010000", "walleye"),
    ("06935965", "catfish"),       ("06935965", "walleye"),        ("06935965", "smallmouth_bass"),
    ("03612500", "largemouth_bass"),("03612500","smallmouth_bass"),("03612500", "catfish"),         ("03612500", "walleye"),
    ("09380000", "trout"),         ("09380000", "largemouth_bass"),("09380000", "striped_bass"),    ("09380000", "catfish"),
    ("12472600", "salmon"),        ("12472600", "trout"),          ("12472600", "smallmouth_bass"), ("12472600", "walleye"),
    ("11447650", "salmon"),        ("11447650", "trout"),          ("11447650", "largemouth_bass"), ("11447650", "striped_bass"),
    ("14211720", "salmon"),        ("14211720", "trout"),          ("14211720", "largemouth_bass"),
    ("02084557", "largemouth_bass"),("02084557","striped_bass"),   ("02084557", "catfish"),
    ("02232500", "largemouth_bass"),("02232500","catfish"),
    ("02306647", "redfish"),       ("02306647", "flounder"),
    ("08116650", "redfish"),       ("08116650", "flounder"),
    # ── NOAA Northeast ───────────────────────────────────────────────────────
    ("8443970", "striped_bass"),   ("8443970", "flounder"),
    ("8461490", "striped_bass"),   ("8461490", "flounder"),
    ("8510560", "striped_bass"),   ("8510560", "flounder"),        ("8510560", "yellowtail"),
    ("8516945", "striped_bass"),   ("8516945", "flounder"),
    ("8518750", "striped_bass"),   ("8518750", "flounder"),
    ("8534720", "striped_bass"),   ("8534720", "flounder"),
    ("8557380", "striped_bass"),   ("8557380", "flounder"),
    # ── NOAA Mid-Atlantic ────────────────────────────────────────────────────
    ("8570283", "striped_bass"),   ("8570283", "flounder"),
    ("8575512", "striped_bass"),   ("8575512", "largemouth_bass"), ("8575512", "catfish"),
    ("8638610", "striped_bass"),   ("8638610", "flounder"),        ("8638610", "redfish"),
    # ── NOAA Southeast ───────────────────────────────────────────────────────
    ("8651370", "striped_bass"),   ("8651370", "flounder"),        ("8651370", "redfish"),
    ("8656483", "redfish"),        ("8656483", "flounder"),
    ("8661070", "redfish"),        ("8661070", "flounder"),
    ("8665530", "redfish"),        ("8665530", "flounder"),
    ("8670870", "redfish"),        ("8670870", "flounder"),        ("8670870", "tarpon"),
    ("8720218", "redfish"),        ("8720218", "flounder"),        ("8720218", "tarpon"),
    ("8723214", "tarpon"),         ("8723214", "bonefish"),        ("8723214", "flounder"),
    ("8724580", "tarpon"),         ("8724580", "bonefish"),        ("8724580", "flounder"),
    ("8725520", "redfish"),        ("8725520", "tarpon"),          ("8725520", "flounder"),
    ("8726520", "redfish"),        ("8726520", "tarpon"),          ("8726520", "flounder"),
    ("8727520", "redfish"),        ("8727520", "flounder"),
    # ── NOAA Gulf Coast ──────────────────────────────────────────────────────
    ("8735180", "redfish"),        ("8735180", "flounder"),
    ("8761724", "redfish"),        ("8761724", "flounder"),
    ("8771341", "redfish"),        ("8771341", "flounder"),
    ("8771450", "redfish"),        ("8771450", "flounder"),
    ("8775870", "redfish"),        ("8775870", "flounder"),
    ("8779748", "redfish"),        ("8779748", "flounder"),
    # ── NOAA West Coast ──────────────────────────────────────────────────────
    ("9410170", "yellowtail"),     ("9410170", "halibut"),
    ("9410230", "yellowtail"),     ("9410230", "halibut"),
    ("9410840", "yellowtail"),     ("9410840", "halibut"),
    ("9413450", "halibut"),        ("9413450", "trout"),           ("9413450", "salmon"),
    ("9414290", "striped_bass"),   ("9414290", "halibut"),         ("9414290", "salmon"),
    ("9415020", "halibut"),        ("9415020", "salmon"),
    ("9419750", "halibut"),        ("9419750", "salmon"),
    ("9435380", "halibut"),        ("9435380", "salmon"),
    ("9439040", "salmon"),         ("9439040", "halibut"),         ("9439040", "trout"),
    ("9444900", "salmon"),         ("9444900", "halibut"),
    ("9447130", "salmon"),         ("9447130", "halibut"),
    ("9449880", "salmon"),         ("9449880", "halibut"),
    # ── NOAA Alaska ──────────────────────────────────────────────────────────
    ("9452210", "salmon"),         ("9452210", "halibut"),
    ("9455920", "salmon"),         ("9455920", "halibut"),         ("9455920", "trout"),
    ("9461380", "salmon"),         ("9461380", "halibut"),         ("9461380", "trout"),
    # ── NOAA Hawaii ──────────────────────────────────────────────────────────
    ("1612340", "bonefish"),       ("1612340", "yellowtail"),
    ("1617760", "bonefish"),       ("1617760", "yellowtail"),
    # ── Scrape-only: US Lakes ────────────────────────────────────────────────
    ("lake-tahoe",      "trout"),          ("lake-tahoe",      "largemouth_bass"), ("lake-tahoe",      "smallmouth_bass"), ("lake-tahoe",      "salmon"),
    ("lake-mead",       "largemouth_bass"),("lake-mead",       "striped_bass"),    ("lake-mead",       "trout"),           ("lake-mead",       "catfish"),
    ("lake-okeechobee", "largemouth_bass"),("lake-okeechobee", "catfish"),
    ("lake-champlain",  "walleye"),        ("lake-champlain",  "largemouth_bass"), ("lake-champlain",  "smallmouth_bass"), ("lake-champlain",  "northern_pike"),
    ("crater-lake",     "trout"),          ("crater-lake",     "salmon"),
    ("flathead-lake",   "trout"),          ("flathead-lake",   "northern_pike"),   ("flathead-lake",   "largemouth_bass"),
    ("lake-powell",     "largemouth_bass"),("lake-powell",     "striped_bass"),    ("lake-powell",     "trout"),           ("lake-powell",     "catfish"),
    # ── Scrape-only: US Coastal ──────────────────────────────────────────────
    ("biscayne-bay",    "bonefish"),       ("biscayne-bay",    "tarpon"),          ("biscayne-bay",    "flounder"),
    ("florida-bay",     "bonefish"),       ("florida-bay",     "redfish"),         ("florida-bay",     "tarpon"),
    ("gulf-of-mexico",  "redfish"),        ("gulf-of-mexico",  "flounder"),        ("gulf-of-mexico",  "tarpon"),
    ("long-island-sound","striped_bass"),  ("long-island-sound","flounder"),
    ("puget-sound",     "salmon"),         ("puget-sound",     "halibut"),
    ("san-francisco-bay","striped_bass"),  ("san-francisco-bay","halibut"),        ("san-francisco-bay","salmon"),
    # ── Scrape-only: Canada ──────────────────────────────────────────────────
    ("georgian-bay",          "walleye"),        ("georgian-bay",          "smallmouth_bass"), ("georgian-bay",          "northern_pike"), ("georgian-bay",    "trout"),   ("georgian-bay",    "salmon"),
    ("lake-winnipeg",         "walleye"),        ("lake-winnipeg",         "northern_pike"),   ("lake-winnipeg",         "trout"),
    ("fraser-river",          "salmon"),         ("fraser-river",          "trout"),
    ("saint-lawrence-river",  "walleye"),        ("saint-lawrence-river",  "northern_pike"),   ("saint-lawrence-river",  "smallmouth_bass"), ("saint-lawrence-river", "salmon"),
    # ── Scrape-only: Europe ──────────────────────────────────────────────────
    ("loch-ness",   "trout"),       ("loch-ness",   "northern_pike"),
    ("loch-lomond", "trout"),       ("loch-lomond", "northern_pike"),  ("loch-lomond", "salmon"),
    ("lake-geneva", "trout"),       ("lake-geneva", "northern_pike"),
    ("lake-como",   "trout"),       ("lake-como",   "northern_pike"),
    ("lake-garda",  "trout"),       ("lake-garda",  "largemouth_bass"),("lake-garda",  "northern_pike"),
    # ── Scrape-only: Brazil / South America ─────────────────────────────────
    ("amazon-river", "peacock_bass"), ("amazon-river", "catfish"),
    ("pantanal",     "peacock_bass"), ("pantanal",     "catfish"),
]


# ---------------------------------------------------------------------------
# Seed rows for location_aliases
# alias: normalized (lowercase, hyphens) — what the API receives after
#        normalizing the user's spoken location name
# site_id: USGS station number (source='usgs') OR seatemperature.info slug (source='scrape')
# source: 'usgs' | 'scrape'
# ---------------------------------------------------------------------------
ALIAS_SEED = [
    # ── Great Lakes (USGS) ────────────────────────────────────────────────
    ("lake-michigan",           "04085427",  "usgs"),
    ("michigan",                "04085427",  "usgs"),
    ("lake-michigan-milwaukee", "04085427",  "usgs"),
    ("lake-michigan-chicago",   "04085068",  "usgs"),
    ("lake-superior",           "040851385", "usgs"),
    ("superior",                "040851385", "usgs"),
    ("lake-superior-duluth",    "040851385", "usgs"),
    ("lake-superior-sault",     "04002000",  "usgs"),
    ("lake-huron",              "04063700",  "usgs"),
    ("huron",                   "04063700",  "usgs"),
    ("lake-huron-mackinaw",     "04063700",  "usgs"),
    ("lake-michigan-muskegon",  "04124000",  "usgs"),
    ("lake-erie",               "04173500",  "usgs"),
    ("erie",                    "04173500",  "usgs"),
    ("lake-erie-toledo",        "04173500",  "usgs"),
    ("lake-erie-buffalo",       "04214500",  "usgs"),
    ("lake-ontario",            "04240010",  "usgs"),
    ("ontario",                 "04240010",  "usgs"),
    ("lake-ontario-oswego",     "04240010",  "usgs"),

    # ── US Rivers (USGS) ─────────────────────────────────────────────────
    ("hudson-river",            "01372500",  "usgs"),
    ("the-hudson",              "01372500",  "usgs"),
    ("potomac-river",           "01646500",  "usgs"),
    ("the-potomac",             "01646500",  "usgs"),
    ("mississippi-river",       "07010000",  "usgs"),
    ("the-mississippi",         "07010000",  "usgs"),
    ("missouri-river",          "06935965",  "usgs"),
    ("the-missouri",            "06935965",  "usgs"),
    ("ohio-river",              "03612500",  "usgs"),
    ("the-ohio",                "03612500",  "usgs"),
    ("colorado-river",          "09380000",  "usgs"),
    ("the-colorado",            "09380000",  "usgs"),
    ("columbia-river",          "12472600",  "usgs"),
    ("the-columbia",            "12472600",  "usgs"),
    ("willamette-river",        "14211720",  "usgs"),
    ("the-willamette",          "14211720",  "usgs"),
    ("sacramento-river",        "11447650",  "usgs"),
    ("the-sacramento",          "11447650",  "usgs"),
    ("neuse-river",             "02084557",  "usgs"),
    ("st-johns-river",          "02232500",  "usgs"),
    ("saint-johns-river",       "02232500",  "usgs"),

    # ── US Coastal/Bays with USGS proxy ──────────────────────────────────
    ("chesapeake-bay",          "01646500",  "usgs"),
    ("tampa-bay",               "02306647",  "usgs"),
    ("galveston-bay",           "08116650",  "usgs"),

    # ── Scrape-only: US Lakes ────────────────────────────────────────────
    ("lake-tahoe",              "lake-tahoe",              "scrape"),
    ("tahoe",                   "lake-tahoe",              "scrape"),
    ("lake-mead",               "lake-mead",               "scrape"),
    ("lake-powell",             "lake-powell",             "scrape"),
    ("lake-okeechobee",         "lake-okeechobee",         "scrape"),
    ("okeechobee",              "lake-okeechobee",         "scrape"),
    ("lake-champlain",          "lake-champlain",          "scrape"),
    ("champlain",               "lake-champlain",          "scrape"),
    ("crater-lake",             "crater-lake",             "scrape"),
    ("flathead-lake",           "flathead-lake",           "scrape"),

    # ── Scrape-only: US Coastal ──────────────────────────────────────────
    ("ocean-city",              "ocean-city",              "scrape"),  # triggers disambiguation
    ("ocean-city-maryland",     "ocean-city-maryland",     "scrape"),
    ("ocean-city-new-jersey",   "ocean-city-new-jersey",   "scrape"),
    ("long-island-sound",       "long-island-sound",       "scrape"),
    ("puget-sound",             "puget-sound",             "scrape"),
    ("san-francisco-bay",       "san-francisco-bay",       "scrape"),
    ("biscayne-bay",            "biscayne-bay",            "scrape"),
    ("florida-bay",             "florida-bay",             "scrape"),
    ("green-bay",               "green-bay",               "scrape"),
    ("delaware-bay",            "delaware-bay",            "scrape"),
    ("monterey-bay",            "monterey-bay",            "scrape"),
    ("pamlico-sound",           "pamlico-sound",           "scrape"),
    ("albemarle-sound",         "albemarle-sound",         "scrape"),
    ("cook-inlet",              "cook-inlet",              "scrape"),
    ("myrtle-beach",            "myrtle-beach",            "scrape"),
    ("outer-banks",             "outer-banks",             "scrape"),
    ("miami-beach",             "miami-beach",             "scrape"),
    ("virginia-beach",          "virginia-beach",          "scrape"),
    ("newport-rhode-island",    "newport-rhode-island",    "scrape"),
    ("newport-oregon",          "newport-oregon",          "scrape"),

    # ── Scrape-only: Open ocean / seas ───────────────────────────────────
    ("gulf-of-mexico",          "gulf-of-mexico",          "scrape"),
    ("the-gulf",                "gulf-of-mexico",          "scrape"),
    ("atlantic-ocean",          "atlantic-ocean",          "scrape"),
    ("the-atlantic",            "atlantic-ocean",          "scrape"),
    ("pacific-ocean",           "pacific-ocean",           "scrape"),
    ("the-pacific",             "pacific-ocean",           "scrape"),
    ("caribbean-sea",           "caribbean-sea",           "scrape"),
    ("the-caribbean",           "caribbean-sea",           "scrape"),
    ("bering-sea",              "bering-sea",              "scrape"),
    ("gulf-of-alaska",          "gulf-of-alaska",          "scrape"),

    # ── Scrape-only: Canada ──────────────────────────────────────────────
    ("georgian-bay",            "georgian-bay",            "scrape"),
    ("lake-winnipeg",           "lake-winnipeg",           "scrape"),
    ("hudson-bay",              "hudson-bay",              "scrape"),
    ("bay-of-fundy",            "bay-of-fundy",            "scrape"),
    ("fraser-river",            "fraser-river",            "scrape"),
    ("saint-lawrence-river",    "saint-lawrence-river",    "scrape"),
    ("st-lawrence-river",       "saint-lawrence-river",    "scrape"),
    ("gulf-of-saint-lawrence",  "gulf-of-saint-lawrence",  "scrape"),

    # ── Scrape-only: Europe ──────────────────────────────────────────────
    ("north-sea",               "north-sea",               "scrape"),
    ("baltic-sea",              "baltic-sea",              "scrape"),
    ("english-channel",         "english-channel",         "scrape"),
    ("the-channel",             "english-channel",         "scrape"),
    ("irish-sea",               "irish-sea",               "scrape"),
    ("bay-of-biscay",           "bay-of-biscay",           "scrape"),
    ("adriatic-sea",            "adriatic-sea",            "scrape"),
    ("mediterranean-sea",       "mediterranean-sea",       "scrape"),
    ("the-mediterranean",       "mediterranean-sea",       "scrape"),
    ("black-sea",               "black-sea",               "scrape"),
    ("thames-river",            "thames-river",            "scrape"),
    ("rhine-river",             "rhine-river",             "scrape"),
    ("danube-river",            "danube-river",            "scrape"),
    ("lake-geneva",             "lake-geneva",             "scrape"),
    ("lake-como",               "lake-como",               "scrape"),
    ("lake-garda",              "lake-garda",              "scrape"),
    ("loch-ness",               "loch-ness",               "scrape"),
    ("loch-lomond",             "loch-lomond",             "scrape"),

    # ── Scrape-only: Brazil / South America ─────────────────────────────
    ("amazon-river",            "amazon-river",            "scrape"),
    ("the-amazon",              "amazon-river",            "scrape"),
    ("rio-negro",               "rio-negro",               "scrape"),
    ("parana-river",            "parana-river",            "scrape"),
    ("pantanal",                "pantanal",                "scrape"),
    ("guanabara-bay",           "guanabara-bay",           "scrape"),

    # ── Nearby beaches → nearest NOAA station ────────────────────────────────
    # Temperature and tides from NOAA. User's location name is preserved in
    # the API response via location.title() override (not the station name).
    # Scrape tide fallback (sea_temp_scraper.scrape_tides) handles international
    # and remote beaches that have no nearby NOAA coverage.

    # Boston Harbor (8443970) — MA North Shore, South Shore, Cape Cod & Islands
    ("revere-beach",        "8443970", "noaa"),
    ("winthrop",            "8443970", "noaa"),
    ("hull",                "8443970", "noaa"),
    ("nantasket-beach",     "8443970", "noaa"),
    ("nahant",              "8443970", "noaa"),
    ("swampscott",          "8443970", "noaa"),
    ("marblehead",          "8443970", "noaa"),
    ("scituate",            "8443970", "noaa"),
    ("marshfield",          "8443970", "noaa"),
    ("duxbury-beach",       "8443970", "noaa"),
    ("plymouth-beach",      "8443970", "noaa"),
    ("rockport",            "8443970", "noaa"),
    ("plum-island",         "8443970", "noaa"),
    ("salisbury-beach",     "8443970", "noaa"),
    ("hampton-beach",       "8443970", "noaa"),
    ("rye-beach",           "8443970", "noaa"),
    ("york-beach",          "8443970", "noaa"),
    ("ogunquit",            "8443970", "noaa"),
    ("wells-beach",         "8443970", "noaa"),
    ("kennebunk-beach",     "8443970", "noaa"),
    ("old-orchard-beach",   "8443970", "noaa"),
    ("portland-maine",      "8443970", "noaa"),
    ("cape-elizabeth",      "8443970", "noaa"),
    ("provincetown",        "8443970", "noaa"),
    ("truro",               "8443970", "noaa"),
    ("wellfleet",           "8443970", "noaa"),
    ("chatham",             "8443970", "noaa"),
    ("harwich",             "8443970", "noaa"),
    ("dennis",              "8443970", "noaa"),
    ("yarmouth",            "8443970", "noaa"),
    ("hyannis",             "8443970", "noaa"),
    ("falmouth",            "8443970", "noaa"),
    ("woods-hole",          "8443970", "noaa"),
    ("buzzards-bay",        "8443970", "noaa"),
    ("nantucket",           "8443970", "noaa"),
    ("marthas-vineyard",    "8443970", "noaa"),
    ("edgartown",           "8443970", "noaa"),
    ("oak-bluffs",          "8443970", "noaa"),

    # New London (8461490) — CT / RI coast
    ("mystic",              "8461490", "noaa"),
    ("stonington",          "8461490", "noaa"),
    ("niantic",             "8461490", "noaa"),
    ("narragansett",        "8461490", "noaa"),
    ("point-judith",        "8461490", "noaa"),
    ("galilee",             "8461490", "noaa"),
    ("block-island",        "8461490", "noaa"),
    ("watch-hill",          "8461490", "noaa"),
    ("misquamicut",         "8461490", "noaa"),
    ("newport-ri",          "8461490", "noaa"),

    # Montauk (8510560) — Long Island East End
    ("montauk",             "8510560", "noaa"),
    ("east-hampton",        "8510560", "noaa"),
    ("southampton",         "8510560", "noaa"),
    ("fire-island",         "8510560", "noaa"),
    ("shelter-island",      "8510560", "noaa"),
    ("orient-point",        "8510560", "noaa"),
    ("greenport",           "8510560", "noaa"),

    # New York Harbor (8518750) — NYC beaches
    ("jones-beach",         "8518750", "noaa"),
    ("long-beach-new-york", "8518750", "noaa"),
    ("coney-island",        "8518750", "noaa"),
    ("rockaway-beach",      "8518750", "noaa"),

    # Sandy Hook (8516945) — NJ Northern Shore
    ("sea-bright",          "8516945", "noaa"),
    ("long-branch",         "8516945", "noaa"),
    ("asbury-park",         "8516945", "noaa"),
    ("belmar",              "8516945", "noaa"),
    ("point-pleasant-beach","8516945", "noaa"),
    ("barnegat-light",      "8516945", "noaa"),
    ("beach-haven",         "8516945", "noaa"),

    # Atlantic City (8534720) — NJ Southern Shore
    ("sea-isle-city",       "8534720", "noaa"),
    ("wildwood",            "8534720", "noaa"),
    ("cape-may",            "8534720", "noaa"),

    # Lewes (8557380) — Delaware beaches
    ("rehoboth-beach",      "8557380", "noaa"),
    ("dewey-beach",         "8557380", "noaa"),
    ("bethany-beach",       "8557380", "noaa"),
    ("fenwick-island",      "8557380", "noaa"),

    # Outer Banks (8651370) — NC Outer Banks & Crystal Coast
    ("kill-devil-hills",    "8651370", "noaa"),
    ("kitty-hawk",          "8651370", "noaa"),
    ("nags-head",           "8651370", "noaa"),
    ("cape-hatteras",       "8651370", "noaa"),
    ("ocracoke",            "8651370", "noaa"),
    ("wrightsville-beach",  "8656483", "noaa"),
    ("carolina-beach",      "8656483", "noaa"),
    ("topsail-beach",       "8656483", "noaa"),
    ("emerald-isle",        "8656483", "noaa"),

    # Charleston (8665530) — SC coast
    ("folly-beach",         "8665530", "noaa"),
    ("isle-of-palms",       "8665530", "noaa"),
    ("sullivan-island",     "8665530", "noaa"),
    ("kiawah-island",       "8665530", "noaa"),
    ("pawleys-island",      "8661070", "noaa"),
    ("hilton-head-island",  "8670870", "noaa"),
    ("hilton-head",         "8670870", "noaa"),
    ("tybee-island",        "8670870", "noaa"),
    ("hunting-island",      "8670870", "noaa"),

    # Jacksonville (8720218) — NE Florida
    ("amelia-island",       "8720218", "noaa"),
    ("fernandina-beach",    "8720218", "noaa"),
    ("ponte-vedra-beach",   "8720218", "noaa"),
    ("st-augustine-beach",  "8720218", "noaa"),
    ("flagler-beach",       "8720218", "noaa"),
    ("daytona-beach",       "8720218", "noaa"),
    ("new-smyrna-beach",    "8720218", "noaa"),
    ("cocoa-beach",         "8720218", "noaa"),
    ("melbourne-beach",     "8720218", "noaa"),
    ("vero-beach",          "8720218", "noaa"),
    ("sebastian-inlet",     "8720218", "noaa"),
    ("fort-pierce",         "8720218", "noaa"),
    ("jensen-beach",        "8720218", "noaa"),

    # Miami (8723214) — SE Florida
    ("palm-beach",          "8723214", "noaa"),
    ("delray-beach",        "8723214", "noaa"),
    ("boca-raton",          "8723214", "noaa"),
    ("deerfield-beach",     "8723214", "noaa"),
    ("pompano-beach",       "8723214", "noaa"),
    ("fort-lauderdale-beach","8723214","noaa"),
    ("hollywood-beach",     "8723214", "noaa"),
    ("hallandale-beach",    "8723214", "noaa"),
    ("sunny-isles-beach",   "8723214", "noaa"),
    ("south-beach",         "8723214", "noaa"),

    # Key West (8724580) — Florida Keys
    ("islamorada",          "8724580", "noaa"),
    ("marathon",            "8724580", "noaa"),
    ("big-pine-key",        "8724580", "noaa"),
    ("bahia-honda",         "8724580", "noaa"),
    ("duck-key",            "8724580", "noaa"),
    ("tavernier",           "8724580", "noaa"),

    # Fort Myers (8725520) — SW Florida
    ("naples",              "8725520", "noaa"),
    ("marco-island",        "8725520", "noaa"),
    ("sanibel-island",      "8725520", "noaa"),
    ("captiva-island",      "8725520", "noaa"),
    ("bonita-beach",        "8725520", "noaa"),
    ("fort-myers-beach",    "8725520", "noaa"),
    ("boca-grande",         "8725520", "noaa"),

    # Tampa Bay (8726520) — Gulf beaches
    ("anna-maria-island",   "8726520", "noaa"),
    ("bradenton-beach",     "8726520", "noaa"),
    ("sarasota",            "8726520", "noaa"),
    ("venice-florida",      "8726520", "noaa"),
    ("englewood-beach",     "8726520", "noaa"),
    ("clearwater-beach",    "8726520", "noaa"),
    ("st-pete-beach",       "8726520", "noaa"),
    ("treasure-island",     "8726520", "noaa"),
    ("madeira-beach",       "8726520", "noaa"),
    ("indian-rocks-beach",  "8726520", "noaa"),
    ("honeymoon-island",    "8726520", "noaa"),

    # Cedar Key (8727520) — Nature Coast
    ("crystal-river",       "8727520", "noaa"),
    ("homosassa",           "8727520", "noaa"),

    # Dauphin Island (8735180) — AL/FL Panhandle/MS Gulf Coast
    ("gulf-shores",         "8735180", "noaa"),
    ("orange-beach",        "8735180", "noaa"),
    ("perdido-key",         "8735180", "noaa"),
    ("pensacola-beach",     "8735180", "noaa"),
    ("navarre-beach",       "8735180", "noaa"),
    ("fort-walton-beach",   "8735180", "noaa"),
    ("destin",              "8735180", "noaa"),
    ("panama-city-beach",   "8735180", "noaa"),
    ("mexico-beach",        "8735180", "noaa"),
    ("cape-san-blas",       "8735180", "noaa"),
    ("st-george-island",    "8735180", "noaa"),
    ("apalachicola",        "8735180", "noaa"),
    ("biloxi",              "8735180", "noaa"),
    ("gulfport",            "8735180", "noaa"),
    ("pass-christian",      "8735180", "noaa"),

    # Grand Isle (8761724) — Louisiana
    ("port-fourchon",       "8761724", "noaa"),

    # Galveston (8771450) — TX Gulf Coast
    ("bolivar-peninsula",   "8771450", "noaa"),
    ("freeport",            "8771450", "noaa"),

    # Rockport (8775870) — TX
    ("port-aransas",        "8775870", "noaa"),
    ("corpus-christi",      "8775870", "noaa"),

    # South Padre Island (8779748) — TX
    ("padre-island",        "8779748", "noaa"),
    ("boca-chica",          "8779748", "noaa"),

    # San Diego (9410170) — SoCal Southern
    ("coronado-beach",      "9410170", "noaa"),
    ("ocean-beach",         "9410170", "noaa"),
    ("pacific-beach",       "9410170", "noaa"),
    ("mission-beach",       "9410170", "noaa"),
    ("la-jolla-cove",       "9410230", "noaa"),
    ("la-jolla-shores",     "9410230", "noaa"),
    ("del-mar-beach",       "9410230", "noaa"),
    ("carlsbad-beach",      "9410230", "noaa"),
    ("oceanside",           "9410230", "noaa"),
    ("encinitas",           "9410230", "noaa"),

    # Santa Monica (9410840) — SoCal Northern
    ("san-clemente",        "9410840", "noaa"),
    ("dana-point",          "9410840", "noaa"),
    ("laguna-beach",        "9410840", "noaa"),
    ("newport-beach",       "9410840", "noaa"),
    ("huntington-beach",    "9410840", "noaa"),
    ("seal-beach",          "9410840", "noaa"),
    ("long-beach-california","9410840","noaa"),
    ("redondo-beach",       "9410840", "noaa"),
    ("hermosa-beach",       "9410840", "noaa"),
    ("manhattan-beach",     "9410840", "noaa"),
    ("venice-beach",        "9410840", "noaa"),
    ("malibu",              "9410840", "noaa"),
    ("santa-barbara",       "9410840", "noaa"),
    ("pismo-beach",         "9410840", "noaa"),
    ("morro-bay",           "9413450", "noaa"),

    # Monterey (9413450) — Central CA coast
    ("carmel-beach",        "9413450", "noaa"),
    ("pacific-grove",       "9413450", "noaa"),
    ("santa-cruz",          "9413450", "noaa"),
    ("capitola",            "9413450", "noaa"),

    # San Francisco (9414290) — Bay Area coast
    ("half-moon-bay",       "9414290", "noaa"),
    ("pacifica",            "9414290", "noaa"),
    ("stinson-beach",       "9415020", "noaa"),
    ("bodega-bay",          "9415020", "noaa"),
    ("fort-bragg",          "9415020", "noaa"),

    # Crescent City (9419750) — NorCal
    ("eureka",              "9419750", "noaa"),
    ("brookings",           "9419750", "noaa"),
    ("gold-beach",          "9419750", "noaa"),

    # Newport Oregon (9435380) — Oregon coast
    ("coos-bay",            "9435380", "noaa"),
    ("florence",            "9435380", "noaa"),
    ("lincoln-city",        "9435380", "noaa"),
    ("depoe-bay",           "9435380", "noaa"),
    ("pacific-city",        "9435380", "noaa"),
    ("tillamook-bay",       "9435380", "noaa"),
    ("cannon-beach",        "9439040", "noaa"),
    ("seaside-oregon",      "9439040", "noaa"),

    # Astoria (9439040) / Port Townsend (9444900) — WA coast
    ("long-beach-washington","9439040","noaa"),
    ("westport",            "9444900", "noaa"),
    ("ocean-shores",        "9444900", "noaa"),
    ("la-push",             "9444900", "noaa"),
    ("neah-bay",            "9444900", "noaa"),
    ("port-angeles",        "9444900", "noaa"),

    # Seattle / Puget Sound (9447130) — Salish Sea
    ("edmonds",             "9447130", "noaa"),
    ("mukilteo",            "9447130", "noaa"),
    ("anacortes",           "9449880", "noaa"),
    ("bellingham",          "9449880", "noaa"),
    ("orcas-island",        "9449880", "noaa"),
    ("lopez-island",        "9449880", "noaa"),

    # Alaska NOAA stations
    ("homer",               "9455920", "noaa"),
    ("seward",              "9455920", "noaa"),
    ("sitka",               "9452210", "noaa"),
    ("ketchikan",           "9452210", "noaa"),
    ("cordova",             "9455920", "noaa"),
    ("valdez",              "9455920", "noaa"),

    # Honolulu (1612340) — Oahu beaches
    ("waikiki-beach",       "1612340", "noaa"),
    ("kailua-beach",        "1612340", "noaa"),
    ("lanikai-beach",       "1612340", "noaa"),
    ("sandy-beach-hawaii",  "1612340", "noaa"),
    ("hanauma-bay",         "1612340", "noaa"),
    ("north-shore-oahu",    "1612340", "noaa"),

    # Maui (1617760) — Maui beaches
    ("kaanapali-beach",     "1617760", "noaa"),
    ("wailea-beach",        "1617760", "noaa"),
    ("makena-beach",        "1617760", "noaa"),
    ("hookipa-beach",       "1617760", "noaa"),

    # Big Island / Kauai — no NOAA coverage, fall back to scraper
    ("kona",                "kona",                "scrape"),
    ("hilo",                "hilo",                "scrape"),
    ("poipu-beach",         "poipu-beach",         "scrape"),
    ("hanalei-bay",         "hanalei-bay",         "scrape"),

    # ── NOAA CO-OPS coastal stations (override scrape/usgs proxies) ──────
    # Northeast
    ("boston-harbor",           "8443970",  "noaa"),
    ("boston",                  "8443970",  "noaa"),
    ("new-london",              "8461490",  "noaa"),
    ("montauk",                 "8510560",  "noaa"),
    ("sandy-hook",              "8516945",  "noaa"),
    ("new-york-harbor",         "8518750",  "noaa"),
    ("the-battery",             "8518750",  "noaa"),
    ("atlantic-city",           "8534720",  "noaa"),
    ("lewes",                   "8557380",  "noaa"),
    # Mid-Atlantic
    ("ocean-city-maryland",     "8570283",  "noaa"),
    ("annapolis",               "8575512",  "noaa"),
    ("chesapeake-bay",          "8638610",  "noaa"),
    ("norfolk",                 "8638610",  "noaa"),
    ("hampton-roads",           "8638610",  "noaa"),
    # Southeast
    ("outer-banks",             "8651370",  "noaa"),
    ("duck-nc",                 "8651370",  "noaa"),
    ("beaufort-nc",             "8656483",  "noaa"),
    ("myrtle-beach",            "8661070",  "noaa"),
    ("charleston",              "8665530",  "noaa"),
    ("charleston-sc",           "8665530",  "noaa"),
    ("savannah",                "8670870",  "noaa"),
    ("jacksonville",            "8720218",  "noaa"),
    ("miami",                   "8723214",  "noaa"),
    ("miami-beach",             "8723214",  "noaa"),
    ("key-west",                "8724580",  "noaa"),
    ("fort-myers",              "8725520",  "noaa"),
    ("st-petersburg-fl",        "8726520",  "noaa"),
    ("tampa-bay",               "8726520",  "noaa"),
    ("cedar-key",               "8727520",  "noaa"),
    # Gulf Coast
    ("dauphin-island",          "8735180",  "noaa"),
    ("grand-isle",              "8761724",  "noaa"),
    ("galveston-bay",           "8771341",  "noaa"),
    ("galveston",               "8771450",  "noaa"),
    ("rockport-tx",             "8775870",  "noaa"),
    ("south-padre-island",      "8779748",  "noaa"),
    # West Coast
    ("san-diego",               "9410170",  "noaa"),
    ("la-jolla",                "9410230",  "noaa"),
    ("santa-monica",            "9410840",  "noaa"),
    ("monterey",                "9413450",  "noaa"),
    ("monterey-bay",            "9413450",  "noaa"),
    ("san-francisco-bay",       "9414290",  "noaa"),
    ("san-francisco",           "9414290",  "noaa"),
    ("point-reyes",             "9415020",  "noaa"),
    ("crescent-city",           "9419750",  "noaa"),
    ("newport-oregon",          "9435380",  "noaa"),
    ("astoria",                 "9439040",  "noaa"),
    ("port-townsend",           "9444900",  "noaa"),
    ("puget-sound",             "9447130",  "noaa"),
    ("seattle",                 "9447130",  "noaa"),
    ("friday-harbor",           "9449880",  "noaa"),
    # Alaska
    ("juneau",                  "9452210",  "noaa"),
    ("anchorage",               "9455920",  "noaa"),
    ("kodiak",                  "9461380",  "noaa"),
    # Hawaii
    ("honolulu",                "1612340",  "noaa"),
    ("oahu",                    "1612340",  "noaa"),
    ("maui",                    "1617760",  "noaa"),
    ("kahului",                 "1617760",  "noaa"),
]


# ---------------------------------------------------------------------------
# Secondary (upsell) gear — higher-ticket items paired by primary ASIN.
# Keyed on primary asin since every primary ASIN is unique across both seed
# tables. UPDATE runs after the initial INSERT so it works on existing DBs too.
# ---------------------------------------------------------------------------
# (primary_asin, secondary_asin, secondary_gear_label)
SECONDARY_GEAR = [
    ("B0891QB6G9", "B08X21YP1L", "Ugly Stik Elite Ice Spinning Combo"),
    ("B08ZMQQF8H", "B0DNDMMQWG", "KastKing Spartacus II Spinning Rod and Reel Combo"),
    ("B08W2Z6VT8", "B0DNDMMQWG", "KastKing Spartacus II Spinning Rod and Reel Combo"),
    ("B093L95KQ1", "B001IAHX6A", "Wild Water Fly Fishing Combo Starter Kit"),
    ("B0FNCZV64V", "B0GC635T1V", "KastKing Brutus Baitcasting Combo"),
    ("B09M3F2PQZ", "B0GC635T1V", "KastKing Brutus Baitcasting Combo"),
    ("B091GG71M2", "B0GC635T1V", "KastKing Brutus Baitcasting Combo"),
    ("B0FBYF917T", "B0DNDMMQWG", "KastKing Spartacus II Spinning Rod and Reel Combo"),
    ("B09R1GQPZK", "B0FYWTWVT7", "Portable Wireless Fish Finder Sonar"),
    ("B0F1CMB7DD", "B0DNDMMQWG", "KastKing Spartacus II Spinning Rod and Reel Combo"),
    ("B001E25LLQ", "B0CNKRJ3QB", "Baitium Fishing Backpack with Rod Holders and Cooler"),
    ("B09ZNQ8JTM", "B0DNDMMQWG", "KastKing Spartacus II Spinning Rod and Reel Combo"),
    ("B0CNPFJS1Z", "B0FYWTWVT7", "Portable Wireless Fish Finder Sonar"),
    ("B0F5PTZDK3", "B0FYWTWVT7", "Portable Wireless Fish Finder Sonar"),
    ("B000GAYF3M", "B07J4N9TM5", "Bootfoot Chest Wader — Waterproof Fishing and Hunting"),
    ("B07DC4GB43", "B0GC635T1V", "KastKing Brutus Baitcasting Combo"),
    ("B0D8PRTY9S", "B0DNDMMQWG", "KastKing Spartacus II Spinning Rod and Reel Combo"),
    ("B07SW7ZN9G", "B0DNDMMQWG", "KastKing Spartacus II Spinning Rod and Reel Combo"),
    ("B07RRDYN6H", "B001IAHX6A", "Wild Water Fly Fishing Combo Starter Kit"),
    ("B0CGR81YDZ", "B0GC635T1V", "KastKing Brutus Baitcasting Combo"),
]


def init():
    with open(SCHEMA_PATH, "r") as f:
        schema = f.read()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)

    # Migrate existing DBs — add columns added after initial release
    migrations = [
        "ALTER TABLE fishing_logic ADD COLUMN secondary_asin TEXT DEFAULT NULL",
        "ALTER TABLE fishing_logic ADD COLUMN secondary_gear TEXT DEFAULT NULL",
        # bait_shop_cache and api_call_log are created by executescript(schema) above
        # for new DBs; existing DBs get them on next schema run automatically.
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
        except Exception:
            pass  # column already exists

    conn.executemany(
        """INSERT OR IGNORE INTO fishing_logic
           (temp_min_f, temp_max_f, fish_behavior, recommended_gear, asin, water_type)
           VALUES (?, ?, ?, ?, ?, ?)""",
        FISHING_LOGIC_SEED,
    )

    conn.executemany(
        """INSERT OR IGNORE INTO fishing_logic
           (temp_min_f, temp_max_f, fish_behavior, recommended_gear, asin, water_type, target_species)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        SPECIES_LOGIC_SEED,
    )

    for primary_asin, secondary_asin, secondary_gear in SECONDARY_GEAR:
        conn.execute(
            """UPDATE fishing_logic
               SET secondary_asin = ?, secondary_gear = ?
               WHERE asin = ?""",
            (secondary_asin, secondary_gear, primary_asin),
        )

    conn.executemany(
        """INSERT OR IGNORE INTO site_species (site_id, species) VALUES (?, ?)""",
        SITE_SPECIES_SEED,
    )

    # INSERT OR REPLACE so NOAA entries (added last) override earlier scrape proxies
    # for coastal locations where NOAA has authoritative data.
    conn.executemany(
        """INSERT OR REPLACE INTO location_aliases (alias, site_id, source)
           VALUES (?, ?, ?)""",
        ALIAS_SEED,
    )

    noaa_count  = sum(1 for _, _, src in ALIAS_SEED if src == "noaa")
    usgs_count  = sum(1 for _, _, src in ALIAS_SEED if src == "usgs")
    scrape_count = sum(1 for _, _, src in ALIAS_SEED if src == "scrape")

    conn.commit()
    conn.close()
    print(
        f"Database initialized at {DB_PATH}\n"
        f"  {len(FISHING_LOGIC_SEED)} generic fishing-logic rows\n"
        f"  {len(SPECIES_LOGIC_SEED)} species-specific fishing-logic rows\n"
        f"  {len(SITE_SPECIES_SEED)} site-species mappings\n"
        f"  {len(ALIAS_SEED)} location aliases "
        f"({usgs_count} USGS · {noaa_count} NOAA · {scrape_count} scrape)"
    )


if __name__ == "__main__":
    init()
