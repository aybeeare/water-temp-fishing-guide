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
    # ── Walleye ───────────────────────────────────────────────────────────────
    (38, 45,
     "The walleye are experiencing winter lethargy and are holding in deep basin transitions or slow-moving river holes to conserve energy. They will not chase bait, so you need to fish vertically with a dead-stick presentation. Drop your bait right on their nose and use an agonizingly slow jigging cadence.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "freshwater", "walleye"),

    (46, 54,
     "Walleye are staging for the pre-spawn and moving toward rocky shorelines, gravel shoals, and river mouths. They feed heavily during low light periods to build energy for the spawn. Cast toward the shallows and use a slow, steady retrieve to bump the rocks.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "freshwater", "walleye"),

    (55, 64,
     "These are prime post-spawn feeding temperatures, and the walleye are aggressively hunting on shallow flats and emerging weed edges. They are highly active at dawn and dusk, chasing baitfish silhouettes near the surface. Troll or cast shallow diving baits to cover maximum water.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "freshwater", "walleye"),

    (65, 74,
     "The fish are in their summer pattern, suspending near thermoclines or dropping back to deep offshore humps to find cooler water. They feed primarily at night now to avoid the daytime heat. Troll near the bottom at a slow walking speed to trigger reaction strikes.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "freshwater", "walleye"),

    # ── Trout (Rainbow, Brown, Brook, Lake) ───────────────────────────────────
    (36, 44,
     "Trout are sluggish in this cold water and are holding close to the bottom in deep, slow-moving pools to avoid heavy current. Their metabolism is slowed, so they are primarily feeding on tiny midges drifting right to them. Drift your presentation under an indicator with split shot to keep it deep.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "freshwater", "trout"),

    (45, 54,
     "Insect hatches are beginning, and trout are moving up into feeding lanes, riffles, and the tail-outs of pools. They are actively feeding on aquatic nymphs right near the bottom. High-stick your rig through the current seams to keep a natural drift.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "freshwater", "trout"),

    (55, 64,
     "This is the optimal thermal range for trout, making them highly aggressive and willing to feed heavily on the surface. They are holding near undercut banks and current seams waiting to ambush prey. Present a dry fly dead-drifted over these feeding lanes.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "freshwater", "trout"),

    (65, 72,
     "The water is getting dangerously warm for trout, forcing them into fast riffles or deep shaded pools just to find oxygen. They are stressed and feeding mostly at first light. Use a flashy moving bait to trigger a quick territorial strike.",
     "Hard Metal Multicolor Buzzbait Spinnerbait Jigs",
     "B07DC4GB43", "freshwater", "trout"),

    # ── Salmon (Chinook, Coho, Atlantic) ──────────────────────────────────────
    (42, 50,
     "The salmon are moving upriver very slowly and holding in deep, slow-moving pools to conserve energy in the cold water. They are not actively feeding, but they will strike out of pure territorial aggression if a bait invades their space. Swing your presentation low and slow right across their face.",
     "Berkley Gulp! Floating Salmon Eggs",
     "B000GAYF3M", "freshwater", "salmon"),

    (51, 58,
     "This is the prime migration temperature, and the salmon are aggressively pushing through current seams and shallow runs. They are striking out of instinct and frustration at flashy, moving targets. Cast slightly upstream and let your bait swing through the current arc.",
     "Hard Metal Multicolor Buzzbait Spinnerbait Jigs",
     "B07DC4GB43", "freshwater", "salmon"),

    (59, 66,
     "The fish are staging in deep thermal refuges and river mouths to avoid the warming water while they wait to spawn. They are easily spooked and conserving energy, so you need to agitate them into biting. Drop your bait vertically and jig it aggressively to trigger a reaction.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "freshwater", "salmon"),

    # ── Northern Pike ─────────────────────────────────────────────────────────
    (38, 47,
     "Pike are in their ice-out pre-spawn phase, cruising the very shallow, dark-bottomed bays that warm up first in the sun. They are sluggish but hungry, looking for slow-moving prey holding in the remaining dead vegetation. Fish a weedless bait at a creeping pace with long pauses.",
     "Worm-Tube Jigs Kit for Smallmouth and Largemouth Bass",
     "B0D8PRTY9S", "freshwater", "northern_pike"),

    (48, 58,
     "The pike have finished spawning and are aggressively ambushing prey along emerging weed beds and rocky points. Their metabolism is firing, and they are willing to chase fast-moving baits. Burn your lure over the tops of the new weeds to draw violent strikes.",
     "Hard Metal Multicolor Buzzbait Spinnerbait Jigs",
     "B07DC4GB43", "freshwater", "northern_pike"),

    (59, 68,
     "This is the optimal feeding temperature for big pike, and they are actively patrolling thick cabbage weed lines and sharp drop-offs. They are hunting larger baitfish and will travel a good distance to strike. Use a twitch-and-pause retrieve to mimic a dying baitfish.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "freshwater", "northern_pike"),

    (69, 76,
     "The water is getting too warm, pushing the larger pike into deep basin transitions or heavy current areas to find cooler temperatures. They become sluggish during the day and feed primarily during low light. Troll heavy metal baits deep near the thermocline.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "freshwater", "northern_pike"),

    # ── Largemouth Bass ───────────────────────────────────────────────────────
    (45, 52,
     "The bass are physiologically sluggish in this cold water, holding tight to deep structure like river channel swings or steep bluffs. They are not chasing bait, so you have to present your lure right on the bottom with agonizingly slow movements. Use dead-stick pauses to tempt a lethargic bite.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "freshwater", "largemouth_bass"),

    (53, 62,
     "Largemouth are in their pre-spawn pattern, feeding heavily and moving up to secondary points and the edges of spawning flats. They are staging in five to ten feet of water and looking for high-protein meals like crawfish. Drag your bait slowly along the bottom, making sure to bump into rocks and wood.",
     "Ned-Rig Finesse Baits Soft Plastic Worms",
     "B09M3F2PQZ", "freshwater", "largemouth_bass"),

    (63, 72,
     "The bass are actively spawning or guarding fry in the shallowest protected coves and flats. They are locked onto beds and will aggressively attack anything that threatens their territory. Pitch your bait directly into visible beds or heavy shallow cover and shake it in place.",
     "Ned-Rig Finesse Baits Soft Plastic Worms",
     "B09M3F2PQZ", "freshwater", "largemouth_bass"),

    (73, 84,
     "This is the classic summer pattern where bass retreat to deep offshore humps, ledges, or heavily shaded dock pilings to escape the heat. They are highly active but only feeding during brief windows, often at dawn or dusk. Run your bait fast and deep to trigger reaction strikes from schooling fish.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "freshwater", "largemouth_bass"),

    # ── Smallmouth Bass ───────────────────────────────────────────────────────
    (42, 50,
     "Smallmouth are huddled tightly together in deep wintering holes, usually at the base of steep drop-offs or deep river bends. Their metabolism is crawling, and they will only eat tiny, motionless prey. Suspend a finesse bait horizontally in the water column and do not move it.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "freshwater", "smallmouth_bass"),

    (51, 60,
     "The smallmouth are pushing out of the deep water and staging on massive rocky flats and gravel points for the pre-spawn. They are extremely aggressive right now, feeding heavily on baitfish to gain weight. Use an erratic, darting retrieve with long pauses to draw violent strikes.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "freshwater", "smallmouth_bass"),

    (61, 70,
     "These are prime post-spawn temperatures, and the smallmouth are actively roaming shallow shoals and current breaks hunting for crawfish. They are highly visual feeders in this warm water. Hop your bait erratically along the rocky bottom to mimic a fleeing crawfish.",
     "Ned-Rig Finesse Baits Soft Plastic Worms",
     "B09M3F2PQZ", "freshwater", "smallmouth_bass"),

    (71, 80,
     "The heat pushes smallmouth to seek high-oxygen areas like heavy river rapids, waterfalls, or deep main-lake ledges. They are looking upward for prey and will aggressively strike topwater lures during the low light of early morning. Walk your bait side-to-side across the surface over deep water adjacent to structure.",
     "Topwater Frog Lure Bass Kit",
     "B091GG71M2", "freshwater", "smallmouth_bass"),

    # ── Catfish (Channel, Blue, Flathead) ─────────────────────────────────────
    (45, 54,
     "Catfish are largely inactive in this cold water, tightly packed into deep holes, bottom depressions, and heavy log jams. They are not expending energy to hunt, so you must rely entirely on scent to draw them in. Anchor upstream of a deep hole and let your bait sit perfectly still on the bottom.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "freshwater", "catfish"),

    (55, 66,
     "The warming water has the catfish moving out of their wintering holes and cruising adjacent mud flats and channel ledges to feed. They are aggressively hunting smaller baitfish to prepare for the spawn. Drift slowly across the flats, keeping your bait in constant contact with the bottom.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "freshwater", "catfish"),

    (67, 76,
     "Catfish are moving into their spawning phase, seeking out dark cavities like hollow logs, cutbanks, and rocky crevices in shallow water. They are highly territorial right now and will aggressively strike anything that invades their nest. Pitch pungent baits right into the heaviest cover you can find.",
     "Catfish Punch Bait",
     "B0FBYF917T", "freshwater", "catfish"),

    (77, 86,
     "In this summer heat, catfish become nocturnal predators, pushing up into incredibly shallow flats at night to hunt. During the day, they bury themselves in the deepest, most shaded river bends. At night, fan cast your baits toward the shallow banks and wait for a heavy runoff.",
     "Catfish Punch Bait",
     "B0FBYF917T", "freshwater", "catfish"),

    # ── Crappie (Black and White) ─────────────────────────────────────────────
    (42, 50,
     "The crappie are tightly schooled and suspended deep in the water column, usually holding right over massive brush piles or bridge pilings. They are moving very little, so your presentation needs to be perfectly still right above their heads. Vertically jig with almost zero rod movement.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "freshwater", "crappie"),

    (51, 60,
     "Crappie are leaving the deep water and migrating into creeks and secondary points, staging for the spawn. They are feeding actively on small minnows as they move shallow. Cast and slowly reel your bait at a steady pace right through the middle of the water column.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "freshwater", "crappie"),

    (61, 68,
     "The crappie are locked into the spawn, holding in just two to four feet of water around flooded timber, reeds, and lily pads. They are extremely aggressive and will hit anything that falls near their bed. Suspend your bait under a float and twitch it gently near visible structure.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "freshwater", "crappie"),

    (69, 78,
     "Post-spawn heat has pushed the crappie back out to deep main-lake brush, standing timber, and submerged creek channels. They are suspending in the shade to stay cool. Cast past the structure and let your bait pendulum down slowly through the branches.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "freshwater", "crappie"),

    # ── Bluegill ──────────────────────────────────────────────────────────────
    (45, 55,
     "Bluegill are hunkered down in deep water basins to survive the cold, moving very little and feeding only when a meal is right in front of them. You need to downsize your gear significantly. Drop your bait straight down and hold it completely still just off the bottom.",
     "Northland Fishing Tackle Buck-Shot Ice Fishing Rattle Spoon",
     "B0891QB6G9", "freshwater", "bluegill"),

    (56, 67,
     "As the water warms, bluegill move out of the deep basins and begin cruising the edges of developing weed lines in mid-depth water. They are actively foraging for insects and small crustaceans. Use a slow retrieval speed, popping the float slightly to attract attention.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "freshwater", "bluegill"),

    (68, 76,
     "This is prime spawning temperature for bluegill, and they are gathered by the hundreds in shallow, saucer-shaped beds on sandy or gravel bottoms. They are aggressively defending these nests. Cast past the colony and drag your bait right through the middle of the beds.",
     "Bulk Fishing Hooks Set Worm Catfish Hooks",
     "B09R1GQPZK", "freshwater", "bluegill"),

    (77, 85,
     "The peak summer heat forces large bluegill under heavy vegetation like lily pads or deep under boat docks seeking shade. They are looking upward to feed on terrestrial insects falling into the water. Cast a topwater bug right against the cover and let the rings dissipate before twitching it.",
     "Bass Fishing Topwater Popper Lures",
     "B0CGR81YDZ", "freshwater", "bluegill"),

    # ── Yellow Perch ──────────────────────────────────────────────────────────
    (35, 43,
     "Perch are schooled up tight to the bottom in deep mud basin transitions, barely moving in the freezing water. They are feeding entirely on bloodworms and tiny invertebrates in the mud. Pound your bait rhythmically into the mud to create a cloud, then pause so they can eat it.",
     "Northland Fishing Tackle Buck-Shot Ice Fishing Rattle Spoon",
     "B0891QB6G9", "freshwater", "yellow_perch"),

    (44, 53,
     "The perch are moving incredibly shallow to spawn, laying their ribbon-like egg strands over dead weeds, sunken brush, and dock pilings. They are voraciously hungry right now and traveling in massive schools. Cast a small swimming bait and retrieve it slowly near the bottom cover.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "freshwater", "yellow_perch"),

    (54, 66,
     "Post-spawn perch are actively roaming expansive sand and gravel flats looking for crayfish and small minnows. They are highly aggressive and will chase moving baits. Troll or cast a flashy rig to locate the school, keeping your presentation near the bottom.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "freshwater", "yellow_perch"),

    (67, 76,
     "Summer temperatures push the jumbo perch deeper, typically holding on sharp drop-offs or deep weed edges to find cooler water and shade. They school tightly and feed mostly in the morning. Fish vertically with a tandem rig to catch multiple fish at once.",
     "Ned-Rig Finesse Baits Soft Plastic Worms",
     "B09M3F2PQZ", "freshwater", "yellow_perch"),

    # ── Muskie ────────────────────────────────────────────────────────────────
    (45, 54,
     "Muskies are sluggish in the cold water, holding near sharp, deep drop-offs just outside of shallow bays. Their metabolism is extremely low, so they are looking for one large, easy meal rather than chasing small bait. Fish large live baits on a quick-strike rig and let them swim naturally near the bottom.",
     "Hard Metal Multicolor Buzzbait Spinnerbait Jigs",
     "B07DC4GB43", "freshwater", "muskie"),

    (55, 64,
     "The muskies are pushing shallow to cruise the newly emerging green weed edges, actively hunting spawning panfish and suckers. Their aggression is rising, and they are willing to chase fast-moving hardware. Burn your lure over the weed tops, and always execute a figure-eight at the boat.",
     "Hard Metal Multicolor Buzzbait Spinnerbait Jigs",
     "B07DC4GB43", "freshwater", "muskie"),

    (65, 73,
     "This is peak muskie metabolism, and they are roaming open water basins or stalking heavy cabbage beds, keying in on suspended schools of large baitfish. They are highly active and will aggressively strike massive profile baits. Use a fast, erratic pull-and-pause retrieve to trigger a reaction.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "freshwater", "muskie"),

    (74, 82,
     "Muskies are severely heat-stressed at these temperatures and are holding in the deepest holes they can find just to survive. Catch and release at this temperature carries a high risk of delayed mortality, so fight fish quickly and minimize handling time. If you must fish, target deep thermoclines with large trolling baits.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "freshwater", "muskie"),

    # ── Carp (Common and Grass) ───────────────────────────────────────────────
    (48, 55,
     "Carp are completely lethargic in this cold water, huddled in deep, slow-moving pools with almost zero desire to feed. They will only suck in food that is highly visible and right in front of their mouth. Use a tiny, high-visibility bait with no free offerings around it, and be patient.",
     "Bulk Fishing Hooks Set Worm Catfish Hooks",
     "B09R1GQPZK", "freshwater", "carp"),

    (56, 65,
     "As the water warms, carp begin moving onto shallow mud flats to root around for emerging aquatic insects. They are actively feeding but can be easily spooked in the clear, shallow water. Use a method feeder packed with groundbait to create a concentrated scent cloud on the bottom.",
     "Bulk Fishing Hooks Set Worm Catfish Hooks",
     "B09R1GQPZK", "freshwater", "carp"),

    (66, 76,
     "This is peak feeding temperature, and carp are violently rooting up the bottom along drop-offs and undercut muddy banks. They are consuming massive amounts of calories. Lay down a heavy bed of chum to hold the school, and fish a heavy rig that hooks them automatically when they pick up the bait.",
     "Bulk Fishing Hooks Set Worm Catfish Hooks",
     "B09R1GQPZK", "freshwater", "carp"),

    (77, 86,
     "The summer heat forces carp to seek shade under overhanging trees or thick lily pads, and they will often suspend right near the surface. They are actively feeding on insects and berries falling from the trees. Free-line a floating bait directly into the shade with no weights attached.",
     "Bulk Fishing Hooks Set Worm Catfish Hooks",
     "B09R1GQPZK", "freshwater", "carp"),

    # ── White Bass ────────────────────────────────────────────────────────────
    (46, 53,
     "White bass are holding in deep river channels or main lake basins, sluggishly waiting for the water to warm. They are tightly schooled but not actively chasing bait. Fish vertically with a flashy presentation, popping it aggressively off the bottom and letting it flutter down.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "freshwater", "white_bass"),

    (54, 62,
     "The white bass are making their massive spawning run, pushing as far up into shallow tributary creeks as they can physically swim. They are incredibly aggressive and will hit almost anything flashy. Cast upstream and reel your bait quickly across the current.",
     "Hard Metal Multicolor Buzzbait Spinnerbait Jigs",
     "B07DC4GB43", "freshwater", "white_bass"),

    (63, 72,
     "Post-spawn white bass have returned to the main lake and are actively hunting huge schools of shad in open water. They push the bait to the surface, creating massive feeding frenzies you can see from a distance. Cast directly into the boiling water and rip your bait back at top speed.",
     "Bass Fishing Topwater Popper Lures",
     "B0CGR81YDZ", "freshwater", "white_bass"),

    (73, 82,
     "The summer heat pushes the white bass schools onto deep windy points and underwater roadbeds. They are still feeding aggressively but holding much deeper. Count your bait down ten to twenty feet before starting a steady, moderate retrieve.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "freshwater", "white_bass"),

    # ── Steelhead ─────────────────────────────────────────────────────────────
    (34, 42,
     "Winter steelhead are holding in the deepest, slowest walking-speed pools of the river to conserve energy in the freezing water. Their metabolism is basically stopped, so your bait must bounce literally off their nose. Drift a subtle presentation right on the bottom with no aggressive movements.",
     "Berkley Gulp! Floating Salmon Eggs",
     "B000GAYF3M", "freshwater", "steelhead"),

    (43, 50,
     "As the water warms slightly, steelhead begin moving upriver and holding in shallower tailouts and current seams. They are more willing to move a few inches to grab a drifting meal. Use a float rig to suspend your bait naturally in the strike zone as it drifts down the seam.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "freshwater", "steelhead"),

    (51, 58,
     "This is the peak temperature for steelhead aggression; they are actively pushing through heavy rapids and striking out of pure annoyance. They will chase fast-moving, flashy baits from a long distance. Cast a heavy piece of hardware across the current and let it swing wildly on a tight line.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "freshwater", "steelhead"),

    (59, 66,
     "The water is getting dangerously warm for steelhead, and post-spawn drop-back fish are rushing back to the lake or ocean. They are stressed, tired, and holding in highly oxygenated riffles. Use a subtle, organic presentation to tempt a bite without spooking them.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "freshwater", "steelhead"),

    # ── Peacock Bass ─────────────────────────────────────────────────────────
    (76, 92,
     "Peacock bass are explosively aggressive near lily pads and submerged structure. "
     "They attack topwater lures with incredible force and sprint directly for cover when hooked. "
     "Use heavy 30-pound braid — do not give them an inch.",
     "Bass Fishing Topwater Popper Lures",
     "B0CGR81YDZ", "freshwater", "peacock_bass"),

    # ── Striped Bass ──────────────────────────────────────────────────────────
    (43, 51,
     "Striped bass are in a strict winter holdover pattern, hunkered down in deep, muddy tidal rivers and estuaries. They are virtually comatose and will not expend energy to chase bait. Use an incredibly light jig and let it drift naturally with the outgoing tide, dragging the bottom.",
     "TRUSCEND Shadtale Easy Catch Soft Fishing Lures",
     "B08W2Z6VT8", "saltwater", "striped_bass"),

    (52, 60,
     "The spring migration is on, and stripers are pushing onto shallow flats and rocky points to intercept schools of herring and bunker. They are highly aggressive during the changing tides. Work a noisy topwater bait violently across the surface at dawn or dusk.",
     "Bass Fishing Topwater Popper Lures",
     "B0CGR81YDZ", "saltwater", "striped_bass"),

    (61, 69,
     "This is peak feeding temperature, and the stripers are actively blitzing baitfish along ocean beaches, rips, and inlet mouths. They are looking for large profile meals. Cast a heavy jig into the strike zone and bounce it aggressively off the bottom.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "striped_bass"),

    (70, 78,
     "The summer heat pushes large striped bass into deep, fast-moving rips, and they become almost entirely nocturnal to avoid the sun. Daytime fishing is tough, so wait for the night tides. Drift live baits on the bottom through the deepest channels.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "striped_bass"),

    # ── Redfish (Red Drum) ────────────────────────────────────────────────────
    (52, 59,
     "Redfish are sluggish and seeking thermal refuge in deep muddy bayous and residential canals that absorb the sun's heat. They are grouped up tight and moving slowly. Fish a weedless bait with a painfully slow retrieve, letting it sit still in the mud for long pauses.",
     "Berkley Gulp! Alive! Shrimp and Peeler Crab Assortment",
     "B001E25LLQ", "saltwater", "redfish"),

    (60, 68,
     "As the water warms, the redfish move onto shallow grass flats with the incoming tide to hunt for crabs and shrimp. They are actively feeding and eager to strike natural presentations. Hop a shrimp imitation lightly along the bottom, making sure to puff up the sand.",
     "Berkley Gulp! Alive! Shrimp and Peeler Crab Assortment",
     "B001E25LLQ", "saltwater", "redfish"),

    (69, 78,
     "This is optimal redfish weather, and you will find them aggressively tailing in a foot of water or cruising oyster bars to crush baitfish. They are highly visible and feeding heavily. Cast a noisy topwater bait right over the oyster beds and walk it side to side.",
     "Bass Fishing Topwater Popper Lures",
     "B0CGR81YDZ", "saltwater", "redfish"),

    (79, 88,
     "The intense summer heat pushes the redfish under heavy mangrove overhangs or into deeper inlet channels during the middle of the day. They will not chase bait in the sun. Skip cut bait as far under the shaded mangroves as possible and let it soak on the bottom.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "redfish"),

    # ── Tarpon ────────────────────────────────────────────────────────────────
    (66, 73,
     "Tarpon are incredibly lethargic in this cool water, sulking in deep residential canals or coastal basins. They will rarely roll on the surface and refuse to chase moving baits. Suspend a lively natural bait just off the bottom and wait patiently for them to slowly suck it in.",
     "Popping Corks for Redfish and Speckled Trout",
     "B09ZNQ8JTM", "saltwater", "tarpon"),

    (74, 81,
     "The tarpon are staging near passes and inlets, feeding heavily on crabs flushing out during the strong outgoing tides. This is pre-spawn behavior, and they are feeding aggressively on the surface. Drift your bait naturally with the tide right through the middle of the pass.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "tarpon"),

    (82, 88,
     "This is peak migration temperature, and massive schools of tarpon are rolling actively along the shallow beach fronts. They are highly aggressive and willing to strike large artificial baits. Cast ahead of the rolling pod and reel a swimbait steadily across their path.",
     "TRUSCEND Shadtale Easy Catch Soft Fishing Lures",
     "B08W2Z6VT8", "saltwater", "tarpon"),

    (89, 94,
     "The extreme tropical heat pushes the tarpon into deep channels by mid-morning, making them only active during the very first light of dawn on the flats. You need to fish early and use unweighted baits so they don't sink too fast. Free-line a live bait right on the surface.",
     "Chartreuse Tarpon Saltwater Streamer Fly",
     "B07SW7ZN9G", "saltwater", "tarpon"),

    # ── Bonefish ──────────────────────────────────────────────────────────────
    (67, 73,
     "Bonefish hate the cold and are refusing to push onto the flats, choosing to hold in deeper adjacent channels waiting for the sun to bake the mud. They are moving slowly and feeding selectively. Cast your fly into the channel and let it sink completely to the bottom before stripping.",
     "Bonefish Fly Fishing Flies",
     "B07RRDYN6H", "saltwater", "bonefish"),

    (74, 81,
     "This is the perfect temperature for bonefish, and they are actively cruising the shallow flats, tailing as they root for shrimp during the incoming tide. They are highly aggressive but easily spooked. Lead the fish by three feet and strip the bait with short, sharp ticks.",
     "Bonefish Fly Fishing Flies",
     "B07RRDYN6H", "saltwater", "bonefish"),

    (82, 89,
     "The flat is getting uncomfortably hot, causing the bonefish to move incredibly fast as they cross the shallows, eventually dropping off into cooler deep edges. You must present the bait instantly when you spot them. Use a heavier fly that drops fast into their strike zone.",
     "Bonefish Fly Fishing Flies",
     "B07RRDYN6H", "saltwater", "bonefish"),

    # ── Flounder ──────────────────────────────────────────────────────────────
    (48, 56,
     "Flounder are largely inactive, holding in deep inlet channels and offshore wrecks to avoid the cold estuarine water. They are buried in the sand and extremely lethargic. You must bounce your bait repeatedly right on their nose to trigger a frustrated bite.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "flounder"),

    (57, 65,
     "The flounder are migrating back into the bays and estuaries, staging along creek mouths and dock pilings on the incoming tide. They are hungry and actively ambushing baitfish. Drag a live bait rig slowly across the bottom, making sure you maintain constant contact with the sand.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "flounder"),

    (66, 74,
     "This is peak feeding temperature, and the flounder are pushing aggressively into very shallow water along marsh edges and oyster bars to hunt finger mullet. They will actually chase moving baits right now. Cast a soft plastic and hop it aggressively off the bottom.",
     "Berkley Gulp! Alive! Shrimp and Peeler Crab Assortment",
     "B001E25LLQ", "saltwater", "flounder"),

    (75, 84,
     "The intense summer heat pushes flounder back toward the deeper, cooler water of the inlets, primarily feeding during the cooler night or early morning tides. They are holding near deep structure. Vertically jig heavy baits over the deep channel ledges.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "saltwater", "flounder"),

    # ── Yellowtail (Pacific) ──────────────────────────────────────────────────
    (58, 64,
     "Yellowtail are sluggish and holding deep over offshore reefs and rock piles, refusing to come up to the surface. Their metabolism is slow, and they won't chase fast lures. Drop heavy iron jigs straight to the bottom and reel them back up with a moderate, steady crank.",
     "Yellowtail Snapper Jigs Fishing",
     "B0CNPFJS1Z", "saltwater", "yellowtail"),

    (65, 71,
     "The yellowtail are highly active, pushing bait to the surface and aggressively feeding around kelp paddies and high spots. They are visual hunters right now and will aggressively strike surface baits. Cast a surface iron past the boiling fish and wind it as fast as you physically can.",
     "Yellowtail Snapper Jigs Fishing",
     "B0CNPFJS1Z", "saltwater", "yellowtail"),

    (72, 79,
     "In this warmer water, yellowtail are cruising the edges of offshore banks, often getting picky and refusing artificial lures entirely. They are keying in on specific live baits. Fly-line a lively baitfish perfectly with no weight so it swims naturally away from the boat.",
     "Yellowtail Snapper Jigs Fishing",
     "B0CNPFJS1Z", "saltwater", "yellowtail"),

    # ── Halibut (Pacific / Alaska) ────────────────────────────────────────────
    (43, 51,
     "Halibut are holding tight to the bottom in deep offshore structure, heavily conserving energy in the frigid water. They will not chase bait, so you need to put a high-scent meal directly on the sandy patches between the rocks. Bounce a heavy bait rigorously on the bottom.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "halibut"),

    (52, 59,
     "The halibut are pushing shallower into bays and nearshore sandy drop-offs to feed heavily on schooling baitfish. They are actively hunting and willing to rise slightly off the bottom to strike. Troll a bouncing rig slowly just off the sandy bottom to cover maximum ground.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "halibut"),

    (60, 67,
     "This is peak feeding temperature, and the halibut are sitting in shallow surf zones and sandy depressions near kelp beds, aggressively ambushing prey. They are highly active and striking hard. Cast a large swimbait into the surf zone and slowly drag it across the sand.",
     "TRUSCEND Shadtale Easy Catch Soft Fishing Lures",
     "B08W2Z6VT8", "saltwater", "halibut"),

    # ── Speckled Trout (Spotted Seatrout) ─────────────────────────────────────
    (48, 55,
     "Speckled trout are lethargic and huddled in deep holes in coastal rivers and dredged canals to escape the cold. They are not feeding aggressively, so you need a slow, sinking presentation right on their nose. Twitch a suspending bait very gently and let it sit still for several seconds.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "saltwater", "speckled_trout"),

    (56, 65,
     "The trout are moving out of the deep holes and aggressively feeding over dark mud flats that warm up quickly in the afternoon sun. They are hunting shrimp and small baitfish. Use a popping cork to make a surface commotion, and let the bait settle below it.",
     "Popping Corks for Redfish and Speckled Trout",
     "B09ZNQ8JTM", "saltwater", "speckled_trout"),

    (66, 75,
     "This is the optimal temperature for huge speckled trout, and they are aggressively feeding over shallow grass beds and oyster bars during the early morning. They are highly active and looking for a big meal. Walk a topwater bait side-to-side over the grass flats.",
     "Bass Fishing Topwater Popper Lures",
     "B0CGR81YDZ", "saltwater", "speckled_trout"),

    (76, 86,
     "The severe summer heat pushes the trout off the shallow flats into deeper inlet channels or near offshore gas rigs for cooler water. They feed exclusively at night or first light. Fish heavy jigs deep in the water column and bounce them aggressively.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "speckled_trout"),

    # ── Snook ─────────────────────────────────────────────────────────────────
    (54, 62,
     "Snook are highly sensitive to cold and are virtually comatose, hiding in deep residential canals, power plant outflows, or muddy creeks to avoid freezing. They will not chase bait and are focused purely on survival. Slowly drag a small, dark bait across the bottom with tiny twitches.",
     "TRUSCEND Shadtale Easy Catch Soft Fishing Lures",
     "B08W2Z6VT8", "saltwater", "snook"),

    (63, 71,
     "The snook are waking up and moving toward the mouths of creeks and rivers, staging around structure like dock pilings and bridge fenders. They are ambushing passing baitfish but still won't expend much energy. Free-line a live bait so it swims naturally with the tidal current past the structure.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "snook"),

    (72, 80,
     "This is prime snook weather; they are highly aggressive and staging in the passes and inlets to spawn. They are feeding heavily on the strong outgoing tides. Cast a heavy jig up-current and let it bounce naturally along the bottom through the pass.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "snook"),

    (81, 89,
     "Summer heat has the snook cruising the shallow beach troughs and mangrove shorelines, feeding aggressively at dawn, dusk, and night. They are highly visual hunters in the clear water. Burn a surface bait parallel to the shoreline to trigger violent strikes.",
     "Topwater Frog Lure Bass Kit",
     "B091GG71M2", "saltwater", "snook"),

    # ── Grouper (Red and Gag) ─────────────────────────────────────────────────
    (58, 66,
     "Grouper are pushing into remarkably shallow water, often staging on nearshore rock piles and ledges in less than 30 feet of water. They are aggressive and feeding heavily on baitfish seeking the same thermal refuge. Troll large diving plugs right over the top of the reef structure.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "saltwater", "grouper"),

    (67, 75,
     "The grouper are moving out to mid-depth offshore wrecks and limestone hard bottom, feeding actively on crabs and bottom fish. They will strike hard and instantly dive back into their caves. Drop heavy live baits straight down and lock your drag tight to pull them out of the rocks.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "grouper"),

    (76, 84,
     "The warm water pushes the biggest grouper to very deep offshore structure, often over 100 feet deep. They are lazy in the heat and prefer a large, dead bait that requires no energy to catch. Drop a massive chunk of cut bait to the bottom and leave it perfectly still.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "grouper"),

    # ── Red Snapper ───────────────────────────────────────────────────────────
    (60, 67,
     "Red snapper are holding tight to deep offshore wrecks and artificial reefs, feeding aggressively as their metabolism handles the cooler water well. They are suspended slightly above the structure. Drop heavy jigs down to the reef and bounce them gently in the strike zone.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "saltwater", "red_snapper"),

    (68, 76,
     "This is peak feeding temperature, and the snapper are highly aggressive, often rising near the surface when chummed heavily. They will compete fiercely for food. Free-line a chunk bait directly into the chum slick with no weight.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "red_snapper"),

    (77, 85,
     "The heat pushes the red snapper back down to the deepest parts of the wrecks and gas platforms, making them slightly more sluggish. They are holding very tight to the structure. Use a heavy bottom rig to punch through the surface current directly to the fish.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "red_snapper"),

    # ── Bluefish ──────────────────────────────────────────────────────────────
    (52, 59,
     "Bluefish are sluggish and staging in deep offshore waters, just beginning their coastal migration. They are not chasing fast baits and feed primarily on slow-moving prey near the bottom. Jig vertically with metal spoons, keeping the action slow and close to the sand.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "saltwater", "bluefish"),

    (60, 68,
     "The bluefish are highly aggressive and pushing into inlets and surf zones in massive schools, chopping up baitfish on the surface. They are feeding with pure frenzy behavior. Cast heavy metal baits into the boiling water and reel as fast as humanly possible.",
     "Trout Spoon Fishing Lure Set",
     "B093L95KQ1", "saltwater", "bluefish"),

    (69, 78,
     "The warm water has the bluefish cruising expansive shallow bays and estuaries, actively hunting schools of bunker. They are prone to striking surface baits out of pure aggression. Work a noisy popper across the surface with violent, splashing rips.",
     "Bass Fishing Topwater Popper Lures",
     "B0CGR81YDZ", "saltwater", "bluefish"),

    # ── Cobia ─────────────────────────────────────────────────────────────────
    (64, 71,
     "Cobia are migrating along the coastlines and are often found tightly following massive manta rays or holding on nearshore buoys. They are curious but sometimes lethargic in this cooler water. Cast a brightly colored jig past the fish and retrieve it right in front of its face with erratic jigs.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "cobia"),

    (72, 79,
     "This is optimal temperature, and the cobia are highly aggressive, cruising the surface near offshore towers, wrecks, and floating debris. They will actively swim up to inspect your boat. Pitch a live bait right to the visible fish and let it sink slightly.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "cobia"),

    (80, 87,
     "The intense heat pushes the cobia off the surface and down to deep wrecks and hard bottom ledges to find cooler water. They are less visible and feeding near the bottom. Drop a heavy jig tipped with bait straight down and bounce it loudly on the structure.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "cobia"),

    # ── King Mackerel ─────────────────────────────────────────────────────────
    (66, 73,
     "King mackerel are staging near nearshore reefs and color changes, feeding actively but refusing to chase extremely fast baits. They are keyed in on slower, struggling baitfish. Slow-troll live baits bump-trolling just enough to keep the boat moving.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "king_mackerel"),

    (74, 81,
     "This is peak feeding temperature, and the kings are sky-rocketing on massive schools of baitfish near offshore platforms and rips. They are incredibly aggressive and striking at high speed. Troll diving plugs or heavy spoons at a fast clip to trigger vicious reaction bites.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "saltwater", "king_mackerel"),

    (82, 88,
     "The summer heat pushes the king mackerel very deep, holding below the thermocline near offshore wrecks. They are feeding actively but you must get your baits down to them. Use downriggers to troll live baits perfectly in the cool water zone.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "king_mackerel"),

    # ── Pompano ───────────────────────────────────────────────────────────────
    (62, 69,
     "Pompano are moving out of the deeper passes and staging just outside the surf break in the troughs. They are feeding on small crustaceans but moving slowly in the cooler water. Cast a heavy bait rig past the sandbar and let it soak motionless on the bottom.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "pompano"),

    (70, 78,
     "This is the optimal temperature, and pompano are highly active, aggressively skipping through the shallow surf zones and inlet passes. They are visually hunting for colorful fleeing prey. Bounce a bright jig aggressively off the sandy bottom, puffing up sand to get their attention.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "pompano"),

    (79, 86,
     "The hot water pushes the pompano out of the shallow surf and into deeper inlet channels or nearshore sandbars. They are feeding primarily on moving tides to stay cool. Drift the deep channels, bouncing small, heavy jigs rapidly off the bottom.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "pompano"),

    # ── Black Drum ────────────────────────────────────────────────────────────
    (50, 58,
     "Black drum are huddled in deep dredged holes and residential canals, moving very slowly to conserve energy. They rely entirely on their barbels to find food in the cold mud. Soak a highly pungent bait dead on the bottom and wait patiently for them to stumble upon it.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "black_drum"),

    (59, 68,
     "The drum are migrating toward the inlets and bridges, schooling heavily and feeding actively on crustaceans holding on the pilings. They are hungry and aggressive. Pitch baits tight to the bridge pilings and keep a tight line to feel the subtle bite.",
     "Berkley Gulp! Alive! Shrimp and Peeler Crab Assortment",
     "B001E25LLQ", "saltwater", "black_drum"),

    (69, 78,
     "This is peak spawning temperature, and massive schools of huge black drum are roaming the shallow flats and intracoastal waterways. They are highly active and will readily take a well-placed bait. Cast a heavy jig tipped with bait directly in front of the cruising school.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "black_drum"),

    (79, 88,
     "The summer heat pushes the black drum under deep docks or into heavily shaded inlet channels. They are lethargic during the day and feed mostly at night on the incoming tide. Soak cut bait in the deepest, most shaded structure you can find.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "black_drum"),

    # ── Sheepshead ────────────────────────────────────────────────────────────
    (52, 60,
     "Sheepshead thrive in this cold water and are aggressively congregated around heavily encrusted dock pilings, bridge fenders, and seawalls. They are actively crunching barnacles and crabs. Drop a small bait vertically, scraping it directly against the piling as it falls.",
     "Bulk Fishing Hooks Set Worm Catfish Hooks",
     "B09R1GQPZK", "saltwater", "sheepshead"),

    (61, 69,
     "The sheepshead are moving out to nearshore reefs and wrecks to spawn, schooling in massive numbers around the structure. They are highly active and feeding heavily. Use a specialized jig to drop bait straight down into the rocks while maintaining maximum sensitivity.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "sheepshead"),

    (70, 80,
     "Warming water pushes the sheepshead into deep residential canals and under heavy mangrove roots where they seek shade and cooler currents. They become very picky and subtle biters in the heat. Float a small bait deep under the overhangs and watch the line carefully for any twitch.",
     "Berkley Gulp! Alive! Shrimp and Peeler Crab Assortment",
     "B001E25LLQ", "saltwater", "sheepshead"),

    # ── Mahi Mahi (Dorado) ────────────────────────────────────────────────────
    (70, 76,
     "Mahi are cruising the open ocean but are slightly lethargic in this cooler water, holding deeper below floating weed lines and debris. They aren't actively exploding on the surface. Troll natural baits heavily weighted to run below the surface chop.",
     "Yellowtail Snapper Jigs Fishing",
     "B0CNPFJS1Z", "saltwater", "mahi_mahi"),

    (77, 83,
     "This is peak temperature for mahi, and they are aggressively patrolling massive sargassum weed lines and floating debris. They are highly visual and will fiercely attack surface baits. Cast bright, noisy topwater baits right to the edges of the floating weeds and rip them back fast.",
     "Bass Fishing Topwater Popper Lures",
     "B0CGR81YDZ", "saltwater", "mahi_mahi"),

    (84, 89,
     "The intense tropical heat scatters the mahi, pushing them deeper and away from the surface debris during the middle of the day. They are feeding actively but holding deep. Troll heavy diving plugs or drop vertical jigs down past the 50-foot mark.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "saltwater", "mahi_mahi"),

    # ── Tuna (Bluefin, Yellowfin) ─────────────────────────────────────────────
    (60, 67,
     "Tuna are holding deep beneath massive bait balls, using the cooler water to regulate their body temperature. They are feeding aggressively but refusing to break the surface. Drop heavy metal jigs straight down to the marked fish and retrieve them with high-speed, frantic cranks.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "saltwater", "tuna"),

    (68, 75,
     "This is optimal feeding temperature, and the tuna are aggressively pushing baitfish to the surface, creating massive, violent boils in the open ocean. They are striking out of pure predatory instinct. Cast a heavy surface lure directly into the boil and let it sink for two seconds before ripping it.",
     "TRUSCEND Shadtale Easy Catch Soft Fishing Lures",
     "B08W2Z6VT8", "saltwater", "tuna"),

    (76, 83,
     "The warm water causes tuna to scatter and cruise the deep edges of offshore canyons or oil rigs, looking for isolated schools of flying fish. They are highly active but spread out. Troll large artificial baits at very high speeds to cover maximum water and trigger reaction strikes.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "saltwater", "tuna"),

    # ── Sea Bass (Black Sea Bass) ─────────────────────────────────────────────
    (45, 53,
     "Sea bass are holding tightly in deep offshore wrecks and rocky crevices, heavily lethargic from the cold. They are feeding minimally and will not chase a bait off the bottom. Drop heavily scented natural bait straight down and hold it completely still on the structure.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "sea_bass"),

    (54, 63,
     "The sea bass are highly active and migrating toward nearshore reefs and rubble piles. They are aggressively feeding and will eagerly attack anything that falls past their face. Drop flashy artificial jigs down to the reef and bounce them gently in the strike zone.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "saltwater", "sea_bass"),

    (64, 72,
     "In this warmer water, sea bass are aggressively defending their territory on shallow inshore wrecks and breakwaters. They are striking out of anger and hunger. Cast a jig tipped with plastic and hop it violently through the submerged rocks.",
     "Jig Heads for Bass Walleye Trout",
     "B0F5PTZDK3", "saltwater", "sea_bass"),

    # ── Amberjack ─────────────────────────────────────────────────────────────
    (64, 71,
     "Amberjack are holding deep on offshore wrecks and artificial reefs, heavily congregated but somewhat lazy in the cool water. They won't chase fast-moving baits all the way to the surface. Drop large live baits right into the wreck and lock the drag to keep them from breaking you off.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "amberjack"),

    (72, 79,
     "This is peak aggression for amberjack; they are schooling tightly over the wrecks and will furiously chase jigs from the bottom all the way to the boat. They are feeding with maximum violence. Drop a heavy vertical jig and crank it upward with a fast, erratic yo-yo motion.",
     "TRUSCEND Swim or Jig Fishing Spinner Baits",
     "B08ZMQQF8H", "saltwater", "amberjack"),

    (80, 87,
     "The intense heat pushes amberjack incredibly deep, often holding near structure over 200 feet down. They are feeding actively but conserving energy by not chasing fast prey. Send down large, slow-moving dead baits to the bottom to trigger a bite.",
     "Sinkers Circle Hooks for Catfish Flounder Drum",
     "B0F1CMB7DD", "saltwater", "amberjack"),

    # ── Wahoo ─────────────────────────────────────────────────────────────────
    (70, 77,
     "Wahoo are cruising the edges of deep offshore drop-offs and temperature breaks, feeding aggressively but staying deep in the water column. They are incredibly fast and looking for flashy, fleeing prey. High-speed troll a heavy lure well below the surface wash to intercept them.",
     "Yellowtail Snapper Jigs Fishing",
     "B0CNPFJS1Z", "saltwater", "wahoo"),

    (78, 85,
     "The wahoo are highly active, pushing closer to the surface around floating debris, weed lines, and offshore buoys. They are actively hunting smaller pelagic fish. Troll diving plugs at a very fast speed directly past the floating structure.",
     "TRUSCEND Shallow or Deep Diving Crankbait with BKK Hooks",
     "B0FNCZV64V", "saltwater", "wahoo"),
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
    ("lake-ontario",            "9052030",   "noaa"),
    ("ontario",                 "9052030",   "noaa"),
    ("lake-ontario-oswego",     "9052030",   "noaa"),

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
    ("half-moon-beach",     "half-moon-bay", "scrape"),
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
    ("revere-beach",            "8443970",  "noaa"),
    ("revere",                  "8443970",  "noaa"),
    ("winthrop",                "8443970",  "noaa"),
    ("lynn-harbor",             "8443970",  "noaa"),
    ("swampscott",              "8443970",  "noaa"),
    ("nahant",                  "8443970",  "noaa"),
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
    ("waikiki",                 "1612340",  "noaa"),
    ("maui",                    "1617760",  "noaa"),
    ("kahului",                 "1617760",  "noaa"),
    # Cape Cod — Woods Hole (8447930) is on the cape itself
    ("cape-cod",                "8447930",  "noaa"),
    ("woods-hole",              "8447930",  "noaa"),
    ("falmouth-ma",             "8447930",  "noaa"),
    ("nantucket",               "8449130",  "noaa"),
    ("marthas-vineyard",        "8449130",  "noaa"),
    # Jekyll Island — same Fort Pulaski station as Tybee Island
    ("jekyll-island",           "8670870",  "noaa"),
    ("golden-isles",            "8670870",  "noaa"),

    # -- OSM auto-generated aliases (OpenStreetMap + seatemperature.info/NOAA, max 40km) --
    ("abrahams-bay",                          "abrahams-bay",  "scrape"),  # Abrahams Bay
    ("absecon-bay",                           "absecon",  "scrape"),  # Absecon Bay
    ("absecon",                               "absecon",  "scrape"),  # Absecon Bay (seatemp canonical)
    ("addison-bay",                           "addison",  "scrape"),  # Addison Bay
    ("addison",                               "addison",  "scrape"),  # Addison Bay (seatemp canonical)
    ("addison-cove",                          "addison",  "scrape"),  # Addison Cove
    ("agate-beach",                           "agate-beach",  "scrape"),  # Agate Beach
    ("agawa-bay",                             "agawa-bay",  "scrape"),  # Agawa Bay
    ("aiea-bay",                              "aiea",  "scrape"),  # Aiea Bay
    ("aiea",                                  "aiea",  "scrape"),  # Aiea Bay (seatemp canonical)
    ("akutan-bay",                            "akutan",  "scrape"),  # Akutan Bay
    ("akutan",                                "akutan",  "scrape"),  # Akutan Bay (seatemp canonical)
    ("akutan-harbor",                         "akutan",  "scrape"),  # Akutan Harbor
    ("ala-moana-beach",                       "ala-moana",  "scrape"),  # Ala Moana Beach
    ("ala-moana",                             "ala-moana",  "scrape"),  # Ala Moana Beach (seatemp canonical)
    ("alamitos-bay",                          "alamitos-bay",  "scrape"),  # Alamitos Bay
    ("alaska-bay",                            "alaska",  "scrape"),  # Alaska Bay
    ("alaska",                                "alaska",  "scrape"),  # Alaska Bay (seatemp canonical)
    ("albany-bay",                            "albany",  "scrape"),  # Albany Bay
    ("albany",                                "albany",  "scrape"),  # Albany Bay (seatemp canonical)
    ("albany-beach",                          "albany",  "scrape"),  # Albany Beach
    ("albany-harbor",                         "albany",  "scrape"),  # Albany Harbor
    ("alcona-bay",                            "alcona",  "scrape"),  # Alcona Bay
    ("alcona",                                "alcona",  "scrape"),  # Alcona Bay (seatemp canonical)
    ("alexander-bay",                         "alexander-bay",  "scrape"),  # Alexander Bay
    ("algoma-bay",                            "algoma",  "scrape"),  # Algoma Bay
    ("algoma",                                "algoma",  "scrape"),  # Algoma Bay (seatemp canonical)
    ("allenwood-beach",                       "allenwood-beach",  "scrape"),  # Allenwood Beach
    ("alys-beach",                            "alys-beach",  "scrape"),  # Alys Beach
    ("amityville-beach",                      "amityville",  "scrape"),  # Amityville Beach
    ("amityville",                            "amityville",  "scrape"),  # Amityville Beach (seatemp canonical)
    ("anahola-bay",                           "anahola",  "scrape"),  # Anahola Bay
    ("anahola",                               "anahola",  "scrape"),  # Anahola Bay (seatemp canonical)
    ("anchor-bay",                            "anchor-bay",  "scrape"),  # Anchor Bay
    ("anchorage-bay",                         "anchorage",  "scrape"),  # Anchorage Bay
    ("anchorage-cove",                        "anchorage",  "scrape"),  # Anchorage Cove
    ("anguilla-bay",                          "anguilla",  "scrape"),  # Anguilla Bay
    ("anguilla",                              "anguilla",  "scrape"),  # Anguilla Bay (seatemp canonical)
    ("annisquam-harbor",                      "annisquam",  "scrape"),  # Annisquam Harbor
    ("annisquam",                             "annisquam",  "scrape"),  # Annisquam Harbor (seatemp canonical)
    ("anse-rouge",                            "anse-rouge",  "scrape"),  # Anse Rouge
    ("anse-bertrand",                         "anse-bertrand",  "scrape"),  # Anse à Bertrand
    ("apalachee-bay",                         "apalachee-bay",  "scrape"),  # Apalachee Bay
    ("apalachicola-bay",                      "apalachicola",  "scrape"),  # Apalachicola Bay
    ("apollo-beach",                          "apollo-beach",  "scrape"),  # Apollo Beach
    ("arcadia-beach",                         "arcadia",  "scrape"),  # Arcadia Beach
    ("arcadia",                               "arcadia",  "scrape"),  # Arcadia Beach (seatemp canonical)
    ("arizona-bay",                           "arizona",  "scrape"),  # Arizona Bay
    ("arizona",                               "arizona",  "scrape"),  # Arizona Bay (seatemp canonical)
    ("arroyo-burro-beach",                    "arroyo-burro-beach",  "scrape"),  # Arroyo Burro Beach
    ("asharoken-beach",                       "asharoken",  "scrape"),  # Asharoken Beach
    ("asharoken",                             "asharoken",  "scrape"),  # Asharoken Beach (seatemp canonical)
    ("au-train-bay",                          "au-train",  "scrape"),  # Au Train Bay
    ("au-train",                              "au-train",  "scrape"),  # Au Train Bay (seatemp canonical)
    ("avila-beach",                           "avila-beach",  "scrape"),  # Avila Beach
    ("avon-beach",                            "avon-beach",  "scrape"),  # Avon Beach
    ("baracoa",                               "baracoa",  "scrape"),  # BARACOA
    ("babes-beach",                           "babes-beach",  "scrape"),  # Babe's Beach
    ("baby-beach",                            "baby-beach",  "scrape"),  # Baby Beach
    ("babylon-cove",                          "babylon",  "scrape"),  # Babylon Cove
    ("babylon",                               "babylon",  "scrape"),  # Babylon Cove (seatemp canonical)
    ("bacon-inlet",                           "bacon",  "scrape"),  # Bacon Inlet
    ("bacon",                                 "bacon",  "scrape"),  # Bacon Inlet (seatemp canonical)
    ("bacon-river",                           "bacon",  "scrape"),  # Bacon River
    ("baffin-bay",                            "baffin-bay",  "scrape"),  # Baffin Bay
    ("bahia-beach",                           "bahia",  "scrape"),  # Bahia Beach
    ("bahia",                                 "bahia",  "scrape"),  # Bahia Beach (seatemp canonical)
    ("baie-comeau",                           "baie-comeau",  "scrape"),  # Baie Comeau
    ("baie-mahault",                          "baie-mahault",  "scrape"),  # Baie Mahault
    ("baie-verte",                            "baie-verte",  "scrape"),  # Baie Verte
    ("baileys-harbor",                        "baileys-harbor",  "scrape"),  # Baileys Harbor
    ("baker-beach",                           "baker-beach",  "scrape"),  # Baker Beach
    ("balboa-bay",                            "balboa",  "scrape"),  # Balboa Bay
    ("balboa",                                "balboa",  "scrape"),  # Balboa Bay (seatemp canonical)
    ("balboa-beach",                          "balboa",  "scrape"),  # Balboa Beach
    ("ball-bay",                              "ball-bay",  "scrape"),  # Ball Bay
    ("ballston-beach",                        "ballston-beach",  "scrape"),  # Ballston Beach
    ("balm-beach",                            "balm-beach",  "scrape"),  # Balm Beach
    ("balmy-beach",                           "balmy-beach",  "scrape"),  # Balmy Beach
    ("baltimore-bay",                         "baltimore",  "scrape"),  # Baltimore Bay
    ("baltimore",                             "baltimore",  "scrape"),  # Baltimore Bay (seatemp canonical)
    ("bank-street-beach",                     "bank-street-beach",  "scrape"),  # Bank Street Beach
    ("bar-harbor",                            "bar-harbor",  "scrape"),  # Bar Harbor
    ("barefoot-beach",                        "barefoot-beach",  "scrape"),  # Barefoot Beach
    ("barnstable-bay",                        "barnstable",  "scrape"),  # Barnstable Bay
    ("barnstable",                            "barnstable",  "scrape"),  # Barnstable Bay (seatemp canonical)
    ("barrow-bay",                            "barrow",  "scrape"),  # Barrow Bay
    ("barrow",                                "barrow",  "scrape"),  # Barrow Bay (seatemp canonical)
    ("barry-bay",                             "barry",  "scrape"),  # Barry Bay
    ("barry",                                 "barry",  "scrape"),  # Barry Bay (seatemp canonical)
    ("bass-lake-beach",                       "bass-lake",  "scrape"),  # Bass Lake Beach
    ("bass-lake",                             "bass-lake",  "scrape"),  # Bass Lake Beach (seatemp canonical)
    ("bass-river-beach",                      "bass-river",  "scrape"),  # Bass River Beach
    ("bass-river",                            "bass-river",  "scrape"),  # Bass River Beach (seatemp canonical)
    ("basseterre-bay",                        "basseterre",  "scrape"),  # Basseterre Bay
    ("basseterre",                            "basseterre",  "scrape"),  # Basseterre Bay (seatemp canonical)
    ("batchawana-bay",                        "batchawana-bay",  "scrape"),  # Batchawana Bay
    ("bay-head-harbor",                       "bay-head",  "scrape"),  # Bay Head Harbor
    ("bay-head",                              "bay-head",  "scrape"),  # Bay Head Harbor (seatemp canonical)
    ("bay-of-islands",                        "bay-of-islands",  "scrape"),  # Bay of Islands
    ("bayfield-bay",                          "bayfield",  "scrape"),  # Bayfield Bay
    ("bayfield",                              "bayfield",  "scrape"),  # Bayfield Bay (seatemp canonical)
    ("bayfield-beach",                        "bayfield",  "scrape"),  # Bayfield Beach
    ("bayfield-inlet",                        "bayfield",  "scrape"),  # Bayfield Inlet
    ("bayside-beach",                         "bayside",  "scrape"),  # Bayside Beach
    ("bayside",                               "bayside",  "scrape"),  # Bayside Beach (seatemp canonical)
    ("bayswater-beach",                       "bayswater",  "scrape"),  # Bayswater Beach
    ("bayswater",                             "bayswater",  "scrape"),  # Bayswater Beach (seatemp canonical)
    ("bayview-beach",                         "bayview",  "scrape"),  # Bayview Beach
    ("bayview",                               "bayview",  "scrape"),  # Bayview Beach (seatemp canonical)
    ("beach-meadows-beach",                   "beach-meadows",  "scrape"),  # Beach Meadows Beach
    ("beach-meadows",                         "beach-meadows",  "scrape"),  # Beach Meadows Beach (seatemp canonical)
    ("beachwood-beach",                       "beachwood",  "scrape"),  # Beachwood Beach
    ("beachwood",                             "beachwood",  "scrape"),  # Beachwood Beach (seatemp canonical)
    ("beaver-bay",                            "beaver-bay",  "scrape"),  # Beaver Bay
    ("beaver-island-beach",                   "beaver-island",  "scrape"),  # Beaver Island Beach
    ("beaver-island",                         "beaver-island",  "scrape"),  # Beaver Island Beach (seatemp canonical)
    ("belford-harbor",                        "belford",  "scrape"),  # Belford Harbor
    ("belford",                               "belford",  "scrape"),  # Belford Harbor (seatemp canonical)
    ("belhaven-beach",                        "belhaven",  "scrape"),  # Belhaven Beach
    ("belhaven",                              "belhaven",  "scrape"),  # Belhaven Beach (seatemp canonical)
    ("belle-harbor",                          "belle-harbor",  "scrape"),  # Belle Harbor
    ("belleair-beach",                        "belleair-beach",  "scrape"),  # Belleair Beach
    ("bellevue-bay",                          "bellevue",  "scrape"),  # Bellevue Bay
    ("bellevue",                              "bellevue",  "scrape"),  # Bellevue Bay (seatemp canonical)
    ("bellevue-beach",                        "bellevue",  "scrape"),  # Bellevue Beach
    ("bellport-bay",                          "bellport",  "scrape"),  # Bellport Bay
    ("bellport",                              "bellport",  "scrape"),  # Bellport Bay (seatemp canonical)
    ("belmont-beach",                         "belmont",  "scrape"),  # Belmont Beach
    ("belmont",                               "belmont",  "scrape"),  # Belmont Beach (seatemp canonical)
    ("belvedere-cove",                        "belvedere",  "scrape"),  # Belvedere Cove
    ("belvedere",                             "belvedere",  "scrape"),  # Belvedere Cove (seatemp canonical)
    ("beresford-beach",                       "beresford",  "scrape"),  # Beresford Beach
    ("beresford",                             "beresford",  "scrape"),  # Beresford Beach (seatemp canonical)
    ("bermuda-beach",                         "bermuda",  "scrape"),  # Bermuda Beach
    ("bermuda",                               "bermuda",  "scrape"),  # Bermuda Beach (seatemp canonical)
    ("beverly-beach",                         "beverly-beach",  "scrape"),  # Beverly Beach
    ("beverly-cove",                          "beverly-cove",  "scrape"),  # Beverly Cove
    ("beverly-shores-beach",                  "beverly-shores",  "scrape"),  # Beverly Shores Beach
    ("beverly-shores",                        "beverly-shores",  "scrape"),  # Beverly Shores Beach (seatemp canonical)
    ("big-bay",                               "big-bay",  "scrape"),  # Big Bay
    ("big-bay-de-noc",                        "big-bay-de-noc",  "scrape"),  # Big Bay de Noc
    ("bikini-beach",                          "bikini-beach",  "scrape"),  # Bikini Beach
    ("biloxi-bay",                            "biloxi",  "scrape"),  # Biloxi Bay
    ("bimini-bay",                            "bimini",  "scrape"),  # Bimini Bay
    ("bimini",                                "bimini",  "scrape"),  # Bimini Bay (seatemp canonical)
    ("bimini-beach",                          "bimini",  "scrape"),  # Bimini Beach
    ("birch-bay",                             "birch-bay",  "scrape"),  # Birch Bay
    ("bird-island-bay",                       "bird-island",  "scrape"),  # Bird Island Bay
    ("bird-island",                           "bird-island",  "scrape"),  # Bird Island Bay (seatemp canonical)
    ("bird-island-cove",                      "bird-island",  "scrape"),  # Bird Island Cove
    ("black-point-beach",                     "black-point",  "scrape"),  # Black Point Beach
    ("black-point",                           "black-point",  "scrape"),  # Black Point Beach (seatemp canonical)
    ("black-river-bay",                       "black-river",  "scrape"),  # Black River Bay
    ("black-river",                           "black-river",  "scrape"),  # Black River Bay (seatemp canonical)
    ("black-river-beach",                     "black-river",  "scrape"),  # Black River Beach
    ("black-rock-bay",                        "black-rock",  "scrape"),  # Black Rock Bay
    ("black-rock",                            "black-rock",  "scrape"),  # Black Rock Bay (seatemp canonical)
    ("black-rock-beach",                      "black-rock",  "scrape"),  # Black Rock Beach
    ("blacks-beach",                          "blacks-beach",  "scrape"),  # Black's Beach
    ("blacksmiths-beach",                     "blacksmiths-beach",  "scrape"),  # Blacksmiths Beach
    ("blackwater-sound",                      "blackwater-sound",  "scrape"),  # Blackwater Sound
    ("blaine-bay",                            "blaine",  "scrape"),  # Blaine Bay
    ("blaine",                                "blaine",  "scrape"),  # Blaine Bay (seatemp canonical)
    ("blind-pass-beach",                      "blind-pass-beach",  "scrape"),  # Blind Pass Beach
    ("block-island-sound",                    "block-island",  "scrape"),  # Block Island Sound
    ("blue-hill-bay",                         "blue-hill",  "scrape"),  # Blue Hill Bay
    ("blue-hill",                             "blue-hill",  "scrape"),  # Blue Hill Bay (seatemp canonical)
    ("blue-hill-harbor",                      "blue-hill",  "scrape"),  # Blue Hill Harbor
    ("bluff-cove",                            "bluff",  "scrape"),  # Bluff Cove
    ("bluff",                                 "bluff",  "scrape"),  # Bluff Cove (seatemp canonical)
    ("bluff-point-beach",                     "bluff-point-beach",  "scrape"),  # Bluff Point Beach
    ("boat-harbour",                          "boat-harbour",  "scrape"),  # Boat Harbour
    ("boca-chica-beach",                      "boca-chica-beach",  "scrape"),  # Boca Chica Beach
    ("bolinas-bay",                           "bolinas",  "scrape"),  # Bolinas Bay
    ("bolinas",                               "bolinas",  "scrape"),  # Bolinas Bay (seatemp canonical)
    ("bolinas-beach",                         "bolinas",  "scrape"),  # Bolinas Beach
    ("bombay-beach",                          "bombay-beach",  "scrape"),  # Bombay Beach
    ("bonny-bay",                             "bonny",  "scrape"),  # Bonny Bay
    ("bonny",                                 "bonny",  "scrape"),  # Bonny Bay (seatemp canonical)
    ("boothbay-harbor",                       "boothbay-harbor",  "scrape"),  # Boothbay Harbor
    ("bordeaux-bay",                          "bordeaux",  "scrape"),  # Bordeaux Bay
    ("bordeaux",                              "bordeaux",  "scrape"),  # Bordeaux Bay (seatemp canonical)
    ("bordeaux-beach",                        "bordeaux",  "scrape"),  # Bordeaux Beach
    ("boston-bay",                            "boston",  "scrape"),  # Boston Bay
    ("boston-beach",                          "boston",  "scrape"),  # Boston Beach
    ("boundary-bay",                          "boundary-bay",  "scrape"),  # Boundary Bay
    ("bourne-cove",                           "bourne",  "scrape"),  # Bourne Cove
    ("bourne",                                "bourne",  "scrape"),  # Bourne Cove (seatemp canonical)
    ("bournemouth",                           "bournemouth",  "scrape"),  # Bournemouth
    ("bowers-bay",                            "bowers",  "scrape"),  # Bowers Bay
    ("bowers",                                "bowers",  "scrape"),  # Bowers Bay (seatemp canonical)
    ("bowers-harbor",                         "bowers",  "scrape"),  # Bowers Harbor
    ("bowman-bay",                            "bowman-bay",  "scrape"),  # Bowman Bay
    ("brackley-beach",                        "brackley-beach",  "scrape"),  # Brackley Beach
    ("bradford-beach",                        "bradford-beach",  "scrape"),  # Bradford Beach
    ("bradley-beach",                         "bradley-beach",  "scrape"),  # Bradley Beach
    ("branford-cove",                         "branford",  "scrape"),  # Branford Cove
    ("branford",                              "branford",  "scrape"),  # Branford Cove (seatemp canonical)
    ("branford-harbor",                       "branford",  "scrape"),  # Branford Harbor
    ("brant-beach",                           "brant-beach",  "scrape"),  # Brant Beach
    ("bray-bay",                              "bray",  "scrape"),  # Bray Bay
    ("bray",                                  "bray",  "scrape"),  # Bray Bay (seatemp canonical)
    ("bray-beach",                            "bray",  "scrape"),  # Bray Beach
    ("bray-cove",                             "bray",  "scrape"),  # Bray Cove
    ("brazil-beach",                          "brazil",  "scrape"),  # Brazil Beach
    ("brazil",                                "brazil",  "scrape"),  # Brazil Beach (seatemp canonical)
    ("breakwater-beach",                      "breakwater-beach",  "scrape"),  # Breakwater Beach
    ("breezy-point-beach",                    "breezy-point",  "scrape"),  # Breezy Point Beach
    ("breezy-point",                          "breezy-point",  "scrape"),  # Breezy Point Beach (seatemp canonical)
    ("brest-bay",                             "brest",  "scrape"),  # Brest Bay
    ("brest",                                 "brest",  "scrape"),  # Brest Bay (seatemp canonical)
    ("brewster-beach",                        "brewster",  "scrape"),  # Brewster Beach
    ("brewster",                              "brewster",  "scrape"),  # Brewster Beach (seatemp canonical)
    ("brewster-cove",                         "brewster",  "scrape"),  # Brewster Cove
    ("brick-beach",                           "brick",  "scrape"),  # Brick Beach
    ("brick",                                 "brick",  "scrape"),  # Brick Beach (seatemp canonical)
    ("bridgeport-beach",                      "bridgeport",  "scrape"),  # Bridgeport Beach
    ("bridgeport",                            "bridgeport",  "scrape"),  # Bridgeport Beach (seatemp canonical)
    ("bridgeport-harbor",                     "bridgeport",  "scrape"),  # Bridgeport Harbor
    ("brigantine-cove",                       "brigantine",  "scrape"),  # Brigantine Cove
    ("brigantine",                            "brigantine",  "scrape"),  # Brigantine Cove (seatemp canonical)
    ("bristol-bay",                           "bristol-bay",  "scrape"),  # Bristol Bay
    ("bristol-beach",                         "bristol-beach",  "scrape"),  # Bristol Beach
    ("bristol-cove",                          "bristol",  "scrape"),  # Bristol Cove
    ("bristol",                               "bristol",  "scrape"),  # Bristol Cove (seatemp canonical)
    ("bristol-harbor",                        "bristol",  "scrape"),  # Bristol Harbor
    ("britannia-bay",                         "britannia-bay",  "scrape"),  # Britannia Bay
    ("broad-creek",                           "broad-creek",  "scrape"),  # Broad Creek
    ("broadwater-bay",                        "broadwater",  "scrape"),  # Broadwater Bay
    ("broadwater",                            "broadwater",  "scrape"),  # Broadwater Bay (seatemp canonical)
    ("broadwater-cove",                       "broadwater",  "scrape"),  # Broadwater Cove
    ("brookings-bay",                         "brookings",  "scrape"),  # Brookings Bay
    ("brooklyn-bay",                          "brooklyn",  "scrape"),  # Brooklyn Bay
    ("brooklyn",                              "brooklyn",  "scrape"),  # Brooklyn Bay (seatemp canonical)
    ("broughton-bay",                         "broughton-bay",  "scrape"),  # Broughton Bay
    ("browns-bay",                            "browns-bay",  "scrape"),  # Brown's Bay
    ("brunswick-beach",                       "brunswick",  "scrape"),  # Brunswick Beach
    ("brunswick",                             "brunswick",  "scrape"),  # Brunswick Beach (seatemp canonical)
    ("buchanan-bay",                          "buchanan",  "scrape"),  # Buchanan Bay
    ("buchanan",                              "buchanan",  "scrape"),  # Buchanan Bay (seatemp canonical)
    ("buchanan-beach",                        "buchanan",  "scrape"),  # Buchanan Beach
    ("buchanan-cove",                         "buchanan",  "scrape"),  # Buchanan Cove
    ("buff-bay",                              "buff-bay",  "scrape"),  # Buff Bay
    ("buffalo-bay",                           "buffalo",  "scrape"),  # Buffalo Bay
    ("buffalo",                               "buffalo",  "scrape"),  # Buffalo Bay (seatemp canonical)
    ("buffalo-beach",                         "buffalo",  "scrape"),  # Buffalo Beach
    ("buffalo-cove",                          "buffalo",  "scrape"),  # Buffalo Cove
    ("bunche-beach",                          "bunche-beach",  "scrape"),  # Bunche Beach
    ("byram-bay",                             "byram",  "scrape"),  # Byram Bay
    ("byram",                                 "byram",  "scrape"),  # Byram Bay (seatemp canonical)
    ("byram-cove",                            "byram",  "scrape"),  # Byram Cove
    ("byram-harbor",                          "byram",  "scrape"),  # Byram Harbor
    ("byron-bay",                             "byron-bay",  "scrape"),  # Byron Bay
    ("cable-bay",                             "cable-bay",  "scrape"),  # Cable Bay
    ("cabrillo-beach",                        "cabrillo-beach",  "scrape"),  # Cabrillo Beach
    ("cahoon-hollow-beach",                   "cahoon-hollow-beach",  "scrape"),  # Cahoon Hollow Beach
    ("california-bay",                        "california",  "scrape"),  # California Bay
    ("california",                            "california",  "scrape"),  # California Bay (seatemp canonical)
    ("california-cove",                       "california",  "scrape"),  # California Cove
    ("calumet-beach",                         "calumet",  "scrape"),  # Calumet Beach
    ("calumet",                               "calumet",  "scrape"),  # Calumet Beach (seatemp canonical)
    ("calumet-harbor",                        "calumet",  "scrape"),  # Calumet Harbor
    ("camden-harbor",                         "camden",  "scrape"),  # Camden Harbor
    ("camden",                                "camden",  "scrape"),  # Camden Harbor (seatemp canonical)
    ("cameron-bay",                           "cameron",  "scrape"),  # Cameron Bay
    ("cameron",                               "cameron",  "scrape"),  # Cameron Bay (seatemp canonical)
    ("cameron-beach",                         "cameron",  "scrape"),  # Cameron Beach
    ("cameron-cove",                          "cameron",  "scrape"),  # Cameron Cove
    ("camp-cove",                             "camp-cove",  "scrape"),  # Camp Cove
    ("campground-beach",                      "campground-beach",  "scrape"),  # Campground Beach
    ("camps-bay",                             "camps-bay",  "scrape"),  # Camps Bay
    ("canatara-beach",                        "canatara-beach",  "scrape"),  # Canatara Beach
    ("canoe-cove",                            "canoe-cove",  "scrape"),  # Canoe Cove
    ("cape-charles-harbor",                   "cape-charles",  "scrape"),  # Cape Charles Harbor
    ("cape-charles",                          "cape-charles",  "scrape"),  # Cape Charles Harbor (seatemp canonical)
    ("cape-cod-bay",                          "cape-cod-bay",  "scrape"),  # Cape Cod Bay
    ("cape-horn-bay",                         "cape-horn",  "scrape"),  # Cape Horn Bay
    ("cape-horn",                             "cape-horn",  "scrape"),  # Cape Horn Bay (seatemp canonical)
    ("cape-may-harbor",                       "cape-may",  "scrape"),  # Cape May Harbor
    ("capitola-beach",                        "capitola",  "scrape"),  # Capitola Beach
    ("caribou-bay",                           "caribou",  "scrape"),  # Caribou Bay
    ("caribou",                               "caribou",  "scrape"),  # Caribou Bay (seatemp canonical)
    ("caribou-cove",                          "caribou",  "scrape"),  # Caribou Cove
    ("carlton-bay",                           "carlton",  "scrape"),  # Carlton Bay
    ("carlton",                               "carlton",  "scrape"),  # Carlton Bay (seatemp canonical)
    ("carlton-beach",                         "carlton",  "scrape"),  # Carlton Beach
    ("carrabelle-harbor",                     "carrabelle",  "scrape"),  # Carrabelle Harbor
    ("carrabelle",                            "carrabelle",  "scrape"),  # Carrabelle Harbor (seatemp canonical)
    ("carson-bay",                            "carson",  "scrape"),  # Carson Bay
    ("carson",                                "carson",  "scrape"),  # Carson Bay (seatemp canonical)
    ("carson-beach",                          "carson-beach",  "scrape"),  # Carson Beach
    ("carters-beach",                         "carters-beach",  "scrape"),  # Carters Beach
    ("cascade-bay",                           "cascade",  "scrape"),  # Cascade Bay
    ("cascade",                               "cascade",  "scrape"),  # Cascade Bay (seatemp canonical)
    ("cascade-inlet",                         "cascade",  "scrape"),  # Cascade Inlet
    ("casco-bay",                             "casco-bay",  "scrape"),  # Casco Bay
    ("caspersen-beach",                       "caspersen-beach",  "scrape"),  # Caspersen Beach
    ("castine-harbor",                        "castine",  "scrape"),  # Castine Harbor
    ("castine",                               "castine",  "scrape"),  # Castine Harbor (seatemp canonical)
    ("caswell-beach",                         "caswell-beach",  "scrape"),  # Caswell Beach
    ("catalina-harbor",                       "catalina",  "scrape"),  # Catalina Harbor
    ("catalina",                              "catalina",  "scrape"),  # Catalina Harbor (seatemp canonical)
    ("cathedral-cove",                        "cathedral-cove",  "scrape"),  # Cathedral Cove
    ("cato-cove",                             "cato",  "scrape"),  # Cato Cove
    ("cato",                                  "cato",  "scrape"),  # Cato Cove (seatemp canonical)
    ("cedar-beach",                           "cedar-beach",  "scrape"),  # Cedar Beach
    ("cedar-beach-harbor",                    "cedar-beach",  "scrape"),  # Cedar Beach Harbor
    ("cedar-grove-beach",                     "cedar-grove-beach",  "scrape"),  # Cedar Grove Beach
    ("cedar-island",                          "cedar-island",  "scrape"),  # Cedar Island
    ("cedar-island-bay",                      "cedar-island",  "scrape"),  # Cedar Island Bay
    ("cedar-island-beach",                    "cedar-island",  "scrape"),  # Cedar Island Beach
    ("cedar-island-cove",                     "cedar-island",  "scrape"),  # Cedar Island Cove
    ("cedar-point-beach",                     "cedar-point",  "scrape"),  # Cedar Point Beach
    ("cedar-point",                           "cedar-point",  "scrape"),  # Cedar Point Beach (seatemp canonical)
    ("cedarville-bay",                        "cedarville",  "scrape"),  # Cedarville Bay
    ("cedarville",                            "cedarville",  "scrape"),  # Cedarville Bay (seatemp canonical)
    ("centennial-beach",                      "centennial-beach",  "scrape"),  # Centennial Beach
    ("centerport-beach",                      "centerport",  "scrape"),  # Centerport Beach
    ("centerport",                            "centerport",  "scrape"),  # Centerport Beach (seatemp canonical)
    ("centerport-harbor",                     "centerport",  "scrape"),  # Centerport Harbor
    ("centerville-beach",                     "centerville",  "scrape"),  # Centerville Beach
    ("centerville",                           "centerville",  "scrape"),  # Centerville Beach (seatemp canonical)
    ("centerville-harbor",                    "centerville",  "scrape"),  # Centerville Harbor
    ("centre-island-beach",                   "centre-island-beach",  "scrape"),  # Centre Island Beach
    ("cerritos-beach",                        "cerritos-beach",  "scrape"),  # Cerritos Beach
    ("chadwick-beach",                        "chadwick-beach",  "scrape"),  # Chadwick Beach
    ("chandler-bay",                          "chandler",  "scrape"),  # Chandler Bay
    ("chandler",                              "chandler",  "scrape"),  # Chandler Bay (seatemp canonical)
    ("chandler-cove",                         "chandler",  "scrape"),  # Chandler Cove
    ("charleston-harbor",                     "charleston",  "scrape"),  # Charleston Harbor
    ("charlotte-harbor",                      "charlotte-harbor",  "scrape"),  # Charlotte Harbor
    ("chatham-harbor",                        "chatham",  "scrape"),  # Chatham Harbor
    ("chelsea-river",                         "chelsea",  "scrape"),  # Chelsea River
    ("chelsea",                               "chelsea",  "scrape"),  # Chelsea River (seatemp canonical)
    ("chelton-beach",                         "chelton-beach",  "scrape"),  # Chelton Beach
    ("cherry-beach",                          "cherry-beach",  "scrape"),  # Cherry Beach
    ("cherry-grove-beach",                    "cherry-grove-beach",  "scrape"),  # Cherry Grove Beach
    ("cherry-hill-bay",                       "cherry-hill",  "scrape"),  # Cherry Hill Bay
    ("cherry-hill",                           "cherry-hill",  "scrape"),  # Cherry Hill Bay (seatemp canonical)
    ("cherry-hill-beach",                     "cherry-hill",  "scrape"),  # Cherry Hill Beach
    ("chicago-bay",                           "chicago",  "scrape"),  # Chicago Bay
    ("chicago",                               "chicago",  "scrape"),  # Chicago Bay (seatemp canonical)
    ("chicago-harbor",                        "chicago",  "scrape"),  # Chicago Harbor
    ("china-bay",                             "china",  "scrape"),  # China Bay
    ("china",                                 "china",  "scrape"),  # China Bay (seatemp canonical)
    ("china-beach",                           "china-beach",  "scrape"),  # China Beach
    ("china-cove",                            "china",  "scrape"),  # China Cove
    ("china-harbor",                          "china",  "scrape"),  # China Harbor
    ("chincoteague-bay",                      "chincoteague",  "scrape"),  # Chincoteague Bay
    ("chincoteague",                          "chincoteague",  "scrape"),  # Chincoteague Bay (seatemp canonical)
    ("choctawhatchee-bay",                    "choctawhatchee-bay",  "scrape"),  # Choctawhatchee Bay
    ("chokoloskee-bay",                       "chokoloskee",  "scrape"),  # Chokoloskee Bay
    ("chokoloskee",                           "chokoloskee",  "scrape"),  # Chokoloskee Bay (seatemp canonical)
    ("christiansted-harbor",                  "christiansted",  "scrape"),  # Christiansted Harbor
    ("christiansted",                         "christiansted",  "scrape"),  # Christiansted Harbor (seatemp canonical)
    ("christies-beach",                       "christies-beach",  "scrape"),  # Christies Beach
    ("christmas-bay",                         "christmas",  "scrape"),  # Christmas Bay
    ("christmas",                             "christmas",  "scrape"),  # Christmas Bay (seatemp canonical)
    ("christmas-cove",                        "christmas-cove",  "scrape"),  # Christmas Cove
    ("christmas-cove-beach",                  "christmas-cove",  "scrape"),  # Christmas Cove Beach
    ("churchill-beach",                       "churchill",  "scrape"),  # Churchill Beach
    ("churchill",                             "churchill",  "scrape"),  # Churchill Beach (seatemp canonical)
    ("cinnamon-bay",                          "cinnamon-bay",  "scrape"),  # Cinnamon Bay
    ("cinnamon-bay-beach",                    "cinnamon-bay",  "scrape"),  # Cinnamon Bay Beach
    ("cisco-beach",                           "cisco-beach",  "scrape"),  # Cisco Beach
    ("city-beach",                            "city-beach",  "scrape"),  # City Beach
    ("clam-harbour-beach",                    "clam-harbour",  "scrape"),  # Clam Harbour Beach
    ("clam-harbour",                          "clam-harbour",  "scrape"),  # Clam Harbour Beach (seatemp canonical)
    ("clam-pass-beach",                       "clam-pass-beach",  "scrape"),  # Clam Pass Beach
    ("clear-lake",                            "clear-lake",  "scrape"),  # Clear Lake
    ("clearwater-bay",                        "clearwater-bay",  "scrape"),  # Clearwater Bay
    ("clearwater-harbor",                     "clearwater",  "scrape"),  # Clearwater Harbor
    ("clearwater",                            "clearwater",  "scrape"),  # Clearwater Harbor (seatemp canonical)
    ("cleveland-beach",                       "cleveland-beach",  "scrape"),  # Cleveland Beach
    ("cliffwood-beach",                       "cliffwood-beach",  "scrape"),  # Cliffwood Beach
    ("clifton-beach",                         "clifton-beach",  "scrape"),  # Clifton Beach
    ("coast-guard-beach",                     "coast-guard-beach",  "scrape"),  # Coast Guard Beach
    ("coatzacoalcos",                         "coatzacoalcos",  "scrape"),  # Coatzacoalcos
    ("cobourg-beach",                         "cobourg",  "scrape"),  # Cobourg Beach
    ("cobourg",                               "cobourg",  "scrape"),  # Cobourg Beach (seatemp canonical)
    ("coco-plum-beach",                       "coco-plum-beach",  "scrape"),  # Coco Plum Beach
    ("cocoa-bay",                             "cocoa",  "scrape"),  # Cocoa Bay
    ("cocoa",                                 "cocoa",  "scrape"),  # Cocoa Bay (seatemp canonical)
    ("coffins-beach",                         "coffins-beach",  "scrape"),  # Coffins Beach
    ("cohasset-cove",                         "cohasset",  "scrape"),  # Cohasset Cove
    ("cohasset",                              "cohasset",  "scrape"),  # Cohasset Cove (seatemp canonical)
    ("cohasset-harbor",                       "cohasset",  "scrape"),  # Cohasset Harbor
    ("colchester-beach",                      "colchester",  "scrape"),  # Colchester Beach
    ("colchester",                            "colchester",  "scrape"),  # Colchester Beach (seatemp canonical)
    ("cold-spring-harbor",                    "cold-spring-harbor",  "scrape"),  # Cold Spring Harbor
    ("coles-bay",                             "coles-bay",  "scrape"),  # Coles Bay
    ("collingwood-bay",                       "collingwood",  "scrape"),  # Collingwood Bay
    ("collingwood",                           "collingwood",  "scrape"),  # Collingwood Bay (seatemp canonical)
    ("colonial-beach",                        "colonial-beach",  "scrape"),  # Colonial Beach
    ("colpoys-bay",                           "colpoys-bay",  "scrape"),  # Colpoy's Bay
    ("columbia-bay",                          "columbia",  "scrape"),  # Columbia Bay
    ("columbia",                              "columbia",  "scrape"),  # Columbia Bay (seatemp canonical)
    ("columbia-beach",                        "columbia",  "scrape"),  # Columbia Beach
    ("columbia-cove",                         "columbia",  "scrape"),  # Columbia Cove
    ("compo-beach",                           "compo-beach",  "scrape"),  # Compo Beach
    ("coney-island-beach",                    "coney-island",  "scrape"),  # Coney Island Beach
    ("conneaut-beach",                        "conneaut",  "scrape"),  # Conneaut Beach
    ("conneaut",                              "conneaut",  "scrape"),  # Conneaut Beach (seatemp canonical)
    ("conneaut-harbor",                       "conneaut",  "scrape"),  # Conneaut Harbor
    ("constance-bay",                         "constance",  "scrape"),  # Constance Bay
    ("constance",                             "constance",  "scrape"),  # Constance Bay (seatemp canonical)
    ("constantine-bay",                       "constantine-bay",  "scrape"),  # Constantine Bay
    ("cooks-bay",                             "cooks-bay",  "scrape"),  # Cook's Bay
    ("cooks-beach",                           "cooks-beach",  "scrape"),  # Cooks Beach
    ("cooks-brook-beach",                     "cooks-brook-beach",  "scrape"),  # Cooks Brook Beach
    ("copenhagen-bay",                        "copenhagen",  "scrape"),  # Copenhagen Bay
    ("copenhagen",                            "copenhagen",  "scrape"),  # Copenhagen Bay (seatemp canonical)
    ("copper-harbor",                         "copper-harbor",  "scrape"),  # Copper Harbor
    ("coquina-beach",                         "coquina-beach",  "scrape"),  # Coquina Beach
    ("cordova-bay",                           "cordova-bay",  "scrape"),  # Cordova Bay
    ("cordova-bay-beach",                     "cordova-bay",  "scrape"),  # Cordova Bay Beach
    ("cork-cove",                             "cork",  "scrape"),  # Cork Cove
    ("cork",                                  "cork",  "scrape"),  # Cork Cove (seatemp canonical)
    ("cornwall-beach",                        "cornwall",  "scrape"),  # Cornwall Beach
    ("cornwall",                              "cornwall",  "scrape"),  # Cornwall Beach (seatemp canonical)
    ("corpus-christi-bay",                    "corpus-christi",  "scrape"),  # Corpus Christi Bay
    ("cos-cob-harbor",                        "cos-cob",  "scrape"),  # Cos Cob Harbor
    ("cos-cob",                               "cos-cob",  "scrape"),  # Cos Cob Harbor (seatemp canonical)
    ("coskata-beach",                         "coskata-beach",  "scrape"),  # Coskata Beach
    ("costa-blanca",                          "costa-blanca",  "scrape"),  # Costa Blanca
    ("cotuit-bay",                            "cotuit",  "scrape"),  # Cotuit Bay
    ("cotuit",                                "cotuit",  "scrape"),  # Cotuit Bay (seatemp canonical)
    ("county-line-beach",                     "county-line-beach",  "scrape"),  # County Line Beach
    ("cow-bay",                               "cow-bay",  "scrape"),  # Cow Bay
    ("cowell-beach",                          "cowell",  "scrape"),  # Cowell Beach
    ("cowell",                                "cowell",  "scrape"),  # Cowell Beach (seatemp canonical)
    ("coyote-point-beach",                    "coyote-point",  "scrape"),  # Coyote Point Beach
    ("coyote-point",                          "coyote-point",  "scrape"),  # Coyote Point Beach (seatemp canonical)
    ("craig-cove",                            "craig",  "scrape"),  # Craig Cove
    ("craig",                                 "craig",  "scrape"),  # Craig Cove (seatemp canonical)
    ("craig-harbor",                          "craig",  "scrape"),  # Craig Harbor
    ("craigville-beach",                      "craigville-beach",  "scrape"),  # Craigville Beach
    ("crane-beach",                           "crane-beach",  "scrape"),  # Crane Beach
    ("crescent-bay",                          "crescent-bay",  "scrape"),  # Crescent Bay
    ("crescent-beach",                        "crescent-beach",  "scrape"),  # Crescent Beach
    ("croatan-sound",                         "croatan-sound",  "scrape"),  # Croatan Sound
    ("crocus-bay-beach",                      "crocus-bay-beach",  "scrape"),  # Crocus Bay Beach
    ("crosby-landing-beach",                  "crosby-landing-beach",  "scrape"),  # Crosby Landing Beach
    ("cruz-bay",                              "cruz-bay",  "scrape"),  # Cruz Bay
    ("cruz-bay-beach",                        "cruz-bay",  "scrape"),  # Cruz Bay Beach
    ("crystal-bay",                           "crystal-bay",  "scrape"),  # Crystal Bay
    ("crystal-cove",                          "crystal-cove",  "scrape"),  # Crystal Cove
    ("crystal-lake",                          "crystal-lake",  "scrape"),  # Crystal Lake
    ("crystal-lake-beach",                    "crystal-lake",  "scrape"),  # Crystal Lake Beach
    ("cul-de-sac",                            "cul-de-sac",  "scrape"),  # Cul de Sac
    ("currituck-bay",                         "currituck",  "scrape"),  # Currituck Bay
    ("currituck",                             "currituck",  "scrape"),  # Currituck Bay (seatemp canonical)
    ("currituck-beach",                       "currituck",  "scrape"),  # Currituck Beach
    ("cutler-cove",                           "cutler",  "scrape"),  # Cutler Cove
    ("cutler",                                "cutler",  "scrape"),  # Cutler Cove (seatemp canonical)
    ("cypremort-point-beach",                 "cypremort-point",  "scrape"),  # Cypremort Point Beach
    ("cypremort-point",                       "cypremort-point",  "scrape"),  # Cypremort Point Beach (seatemp canonical)
    ("dabob-bay",                             "dabob-bay",  "scrape"),  # Dabob Bay
    ("dallas-bay",                            "dallas",  "scrape"),  # Dallas Bay
    ("dallas",                                "dallas",  "scrape"),  # Dallas Bay (seatemp canonical)
    ("dampier-cove",                          "dampier",  "scrape"),  # Dampier Cove
    ("dampier",                               "dampier",  "scrape"),  # Dampier Cove (seatemp canonical)
    ("dauphin-island-bay",                    "dauphin-island",  "scrape"),  # Dauphin Island Bay
    ("davenport-bay",                         "davenport",  "scrape"),  # Davenport Bay
    ("davenport",                             "davenport",  "scrape"),  # Davenport Bay (seatemp canonical)
    ("davenport-cove",                        "davenport",  "scrape"),  # Davenport Cove
    ("david-bay",                             "david",  "scrape"),  # David Bay
    ("david",                                 "david",  "scrape"),  # David Bay (seatemp canonical)
    ("davis-bay",                             "davis-bay",  "scrape"),  # Davis Bay
    ("davis-beach",                           "davis",  "scrape"),  # Davis Beach
    ("davis",                                 "davis",  "scrape"),  # Davis Beach (seatemp canonical)
    ("davis-cove",                            "davis",  "scrape"),  # Davis Cove
    ("deception-bay",                         "deception-bay",  "scrape"),  # Deception Bay
    ("deep-cove",                             "deep-cove",  "scrape"),  # Deep Cove
    ("deer-island-bay",                       "deer-island",  "scrape"),  # Deer Island Bay
    ("deer-island",                           "deer-island",  "scrape"),  # Deer Island Bay (seatemp canonical)
    ("del-mar-cove",                          "del-mar",  "scrape"),  # Del Mar Cove
    ("del-mar",                               "del-mar",  "scrape"),  # Del Mar Cove (seatemp canonical)
    ("del-monte-beach",                       "del-monte-beach",  "scrape"),  # Del Monte Beach
    ("denmark-cove",                          "denmark",  "scrape"),  # Denmark Cove
    ("denmark",                               "denmark",  "scrape"),  # Denmark Cove (seatemp canonical)
    ("dennis-bay",                            "dennis",  "scrape"),  # Dennis Bay
    ("dennis-beach",                          "dennis",  "scrape"),  # Dennis Beach
    ("depoe-bay-harbor",                      "depoe-bay",  "scrape"),  # Depoe Bay Harbor
    ("des-moines-beach",                      "des-moines",  "scrape"),  # Des Moines Beach
    ("des-moines",                            "des-moines",  "scrape"),  # Des Moines Beach (seatemp canonical)
    ("destin-harbor",                         "destin",  "scrape"),  # Destin Harbor
    ("detroit-harbor",                        "detroit",  "scrape"),  # Detroit Harbor
    ("detroit",                               "detroit",  "scrape"),  # Detroit Harbor (seatemp canonical)
    ("devereux-beach",                        "devereux-beach",  "scrape"),  # Devereux Beach
    ("diamond-beach",                         "diamond-beach",  "scrape"),  # Diamond Beach
    ("dieppe-bay",                            "dieppe",  "scrape"),  # Dieppe Bay
    ("dieppe",                                "dieppe",  "scrape"),  # Dieppe Bay (seatemp canonical)
    ("dionis-beach",                          "dionis-beach",  "scrape"),  # Dionis Beach
    ("discovery-bay",                         "discovery-bay",  "scrape"),  # Discovery Bay
    ("divers-cove",                           "divers-cove",  "scrape"),  # Divers Cove
    ("dominion-bay",                          "dominion",  "scrape"),  # Dominion Bay
    ("dominion",                              "dominion",  "scrape"),  # Dominion Bay (seatemp canonical)
    ("dominion-beach",                        "dominion",  "scrape"),  # Dominion Beach
    ("donegal-bay",                           "donegal",  "scrape"),  # Donegal Bay
    ("donegal",                               "donegal",  "scrape"),  # Donegal Bay (seatemp canonical)
    ("double-bay",                            "double-bay",  "scrape"),  # Double Bay
    ("douglas-bay",                           "douglas",  "scrape"),  # Douglas Bay
    ("douglas",                               "douglas",  "scrape"),  # Douglas Bay (seatemp canonical)
    ("douglas-beach",                         "douglas",  "scrape"),  # Douglas Beach
    ("douglas-cove",                          "douglas",  "scrape"),  # Douglas Cove
    ("dover-inlet",                           "dover",  "scrape"),  # Dover Inlet
    ("dover",                                 "dover",  "scrape"),  # Dover Inlet (seatemp canonical)
    ("dowses-beach",                          "dowses-beach",  "scrape"),  # Dowses Beach
    ("drakes-bay",                            "drakes-bay",  "scrape"),  # Drakes Bay
    ("drakes-beach",                          "drakes-beach",  "scrape"),  # Drakes Beach
    ("drakes-island-beach",                   "drakes-island-beach",  "scrape"),  # Drakes Island Beach
    ("driftwood-beach",                       "driftwood-beach",  "scrape"),  # Driftwood Beach
    ("drum-point-beach",                      "drum-point",  "scrape"),  # Drum Point Beach
    ("drum-point",                            "drum-point",  "scrape"),  # Drum Point Beach (seatemp canonical)
    ("drum-point-cove",                       "drum-point",  "scrape"),  # Drum Point Cove
    ("drummond-cove",                         "drummond",  "scrape"),  # Drummond Cove
    ("drummond",                              "drummond",  "scrape"),  # Drummond Cove (seatemp canonical)
    ("drummore-bay",                          "drummore",  "scrape"),  # Drummore Bay
    ("drummore",                              "drummore",  "scrape"),  # Drummore Bay (seatemp canonical)
    ("dublin-bay",                            "dublin",  "scrape"),  # Dublin Bay
    ("dublin",                                "dublin",  "scrape"),  # Dublin Bay (seatemp canonical)
    ("duck-bay",                              "duck",  "scrape"),  # Duck Bay
    ("duck",                                  "duck",  "scrape"),  # Duck Bay (seatemp canonical)
    ("duck-cove",                             "duck",  "scrape"),  # Duck Cove
    ("duck-harbor",                           "duck",  "scrape"),  # Duck Harbor
    ("duck-lake",                             "duck",  "scrape"),  # Duck Lake
    ("dunbar-beach",                          "dunbar",  "scrape"),  # Dunbar Beach
    ("dunbar",                                "dunbar",  "scrape"),  # Dunbar Beach (seatemp canonical)
    ("dune-acres-beach",                      "dune-acres",  "scrape"),  # Dune Acres Beach
    ("dune-acres",                            "dune-acres",  "scrape"),  # Dune Acres Beach (seatemp canonical)
    ("dunes-beach",                           "dunes-beach",  "scrape"),  # Dunes Beach
    ("dutch-harbor",                          "dutch-harbor",  "scrape"),  # Dutch Harbor
    ("duxbury-bay",                           "duxbury",  "scrape"),  # Duxbury Bay
    ("duxbury",                               "duxbury",  "scrape"),  # Duxbury Bay (seatemp canonical)
    ("dyers-bay",                             "dyers-bay",  "scrape"),  # Dyer's Bay
    ("eagle-bay",                             "eagle-bay",  "scrape"),  # Eagle Bay
    ("eagle-beach",                           "eagle-beach",  "scrape"),  # Eagle Beach
    ("eagle-harbor",                          "eagle-harbor",  "scrape"),  # Eagle Harbor
    ("eagle-river-beach",                     "eagle-river",  "scrape"),  # Eagle River Beach
    ("eagle-river",                           "eagle-river",  "scrape"),  # Eagle River Beach (seatemp canonical)
    ("east-bay",                              "east-bay",  "scrape"),  # East Bay
    ("east-beach",                            "east-beach",  "scrape"),  # East Beach
    ("eastern-beach",                         "eastern-beach",  "scrape"),  # Eastern Beach
    ("eastport-beach",                        "eastport",  "scrape"),  # Eastport Beach
    ("eastport",                              "eastport",  "scrape"),  # Eastport Beach (seatemp canonical)
    ("eden-beach",                            "eden",  "scrape"),  # Eden Beach
    ("eden",                                  "eden",  "scrape"),  # Eden Beach (seatemp canonical)
    ("eden-harbor",                           "eden",  "scrape"),  # Eden Harbor
    ("edgartown-beach",                       "edgartown",  "scrape"),  # Edgartown Beach
    ("edgartown-harbor",                      "edgartown",  "scrape"),  # Edgartown Harbor
    ("edgewood-beach",                        "edgewood-beach",  "scrape"),  # Edgewood Beach
    ("edmonds-cove",                          "edmonds",  "scrape"),  # Edmonds Cove
    ("egg-harbor",                            "egg-harbor",  "scrape"),  # Egg Harbor
    ("egg-harbor-beach",                      "egg-harbor",  "scrape"),  # Egg Harbor Beach
    ("egypt-bay",                             "egypt",  "scrape"),  # Egypt Bay
    ("egypt",                                 "egypt",  "scrape"),  # Egypt Bay (seatemp canonical)
    ("egypt-beach",                           "egypt",  "scrape"),  # Egypt Beach
    ("egypt-cove",                            "egypt",  "scrape"),  # Egypt Cove
    ("el-granada-beach",                      "el-granada",  "scrape"),  # El Granada Beach
    ("el-granada",                            "el-granada",  "scrape"),  # El Granada Beach (seatemp canonical)
    ("el-sargento",                           "el-sargento",  "scrape"),  # El Sargento
    ("el-segundo-beach",                      "el-segundo",  "scrape"),  # El Segundo Beach
    ("el-segundo",                            "el-segundo",  "scrape"),  # El Segundo Beach (seatemp canonical)
    ("elbow-beach",                           "elbow-beach",  "scrape"),  # Elbow Beach
    ("ellis-landing-beach",                   "ellis-landing-beach",  "scrape"),  # Ellis Landing Beach
    ("ellison-bay",                           "ellison-bay",  "scrape"),  # Ellison Bay
    ("emerald-bay",                           "emerald-bay",  "scrape"),  # Emerald Bay
    ("emerald-beach",                         "emerald-beach",  "scrape"),  # Emerald Beach
    ("empire-cove",                           "empire",  "scrape"),  # Empire Cove
    ("empire",                                "empire",  "scrape"),  # Empire Cove (seatemp canonical)
    ("englewood",                             "englewood",  "scrape"),  # Englewood Beach (seatemp canonical)
    ("english-bay",                           "english-bay",  "scrape"),  # English Bay
    ("english-bay-beach",                     "english-bay",  "scrape"),  # English Bay Beach
    ("english-harbour",                       "english-harbour",  "scrape"),  # English Harbour
    ("epoufette-bay",                         "epoufette",  "scrape"),  # Epoufette Bay
    ("epoufette",                             "epoufette",  "scrape"),  # Epoufette Bay (seatemp canonical)
    ("erie-beach",                            "erie",  "scrape"),  # Erie Beach
    ("essex-bay",                             "essex",  "scrape"),  # Essex Bay
    ("essex",                                 "essex",  "scrape"),  # Essex Bay (seatemp canonical)
    ("essex-cove",                            "essex",  "scrape"),  # Essex Cove
    ("estero-bay",                            "estero-bay",  "scrape"),  # Estero Bay
    ("euclid-beach",                          "euclid",  "scrape"),  # Euclid Beach
    ("euclid",                                "euclid",  "scrape"),  # Euclid Beach (seatemp canonical)
    ("europe-bay",                            "europe",  "scrape"),  # Europe Bay
    ("europe",                                "europe",  "scrape"),  # Europe Bay (seatemp canonical)
    ("evans-bay",                             "evans-bay",  "scrape"),  # Evans Bay
    ("everett-bay",                           "everett",  "scrape"),  # Everett Bay
    ("everett",                               "everett",  "scrape"),  # Everett Bay (seatemp canonical)
    ("everett-cove",                          "everett",  "scrape"),  # Everett Cove
    ("fairbanks-bay",                         "fairbanks",  "scrape"),  # Fairbanks Bay
    ("fairbanks",                             "fairbanks",  "scrape"),  # Fairbanks Bay (seatemp canonical)
    ("fairfield-bay",                         "fairfield",  "scrape"),  # Fairfield Bay
    ("fairfield",                             "fairfield",  "scrape"),  # Fairfield Bay (seatemp canonical)
    ("fairfield-beach",                       "fairfield",  "scrape"),  # Fairfield Beach
    ("false-bay",                             "false-bay",  "scrape"),  # False Bay
    ("fareham-bay",                           "fareham",  "scrape"),  # Fareham Bay
    ("fareham",                               "fareham",  "scrape"),  # Fareham Bay (seatemp canonical)
    ("faria-beach",                           "faria-beach",  "scrape"),  # Faria Beach
    ("fig-tree-bay",                          "fig-tree-bay",  "scrape"),  # Fig Tree Bay
    ("fire-island-inlet",                     "fire-island",  "scrape"),  # Fire Island Inlet
    ("first-beach",                           "first-beach",  "scrape"),  # First Beach
    ("first-encounter-beach",                 "first-encounter-beach",  "scrape"),  # First Encounter Beach
    ("fish-creek-bay",                        "fish-creek",  "scrape"),  # Fish Creek Bay
    ("fish-creek",                            "fish-creek",  "scrape"),  # Fish Creek Bay (seatemp canonical)
    ("fish-creek-harbor",                     "fish-creek",  "scrape"),  # Fish Creek Harbor
    ("fishers-island-sound",                  "fishers-island",  "scrape"),  # Fishers Island Sound
    ("fishers-island",                        "fishers-island",  "scrape"),  # Fishers Island Sound (seatemp canonical)
    ("flamingo",                              "flamingo",  "scrape"),  # Flamingo
    ("flamingo-bay",                          "flamingo",  "scrape"),  # Flamingo Bay
    ("flamingo-cove",                         "flamingo",  "scrape"),  # Flamingo Cove
    ("flanders-bay",                          "flanders",  "scrape"),  # Flanders Bay
    ("flanders",                              "flanders",  "scrape"),  # Flanders Bay (seatemp canonical)
    ("fleming-beach",                         "fleming-beach",  "scrape"),  # Fleming Beach
    ("florida",                               "florida",  "scrape"),  # Florida Bay (seatemp canonical)
    ("forest-beach",                          "forest-beach",  "scrape"),  # Forest Beach
    ("fort-island-beach",                     "fort-island-beach",  "scrape"),  # Fort Island Beach
    ("fort-lauderdale",                       "fort-lauderdale",  "scrape"),  # Fort Lauderdale Beach (seatemp canonical)
    ("fort-tilden-beach",                     "fort-tilden",  "scrape"),  # Fort Tilden Beach
    ("fort-tilden",                           "fort-tilden",  "scrape"),  # Fort Tilden Beach (seatemp canonical)
    ("fox-bay",                               "fox-bay",  "scrape"),  # Fox Bay
    ("fox-island-beach",                      "fox-island",  "scrape"),  # Fox Island Beach
    ("fox-island",                            "fox-island",  "scrape"),  # Fox Island Beach (seatemp canonical)
    ("fox-point-beach",                       "fox-point-beach",  "scrape"),  # Fox Point Beach
    ("frankfort-bay",                         "frankfort",  "scrape"),  # Frankfort Bay
    ("frankfort",                             "frankfort",  "scrape"),  # Frankfort Bay (seatemp canonical)
    ("frankfort-beach",                       "frankfort",  "scrape"),  # Frankfort Beach
    ("frankfort-harbor",                      "frankfort",  "scrape"),  # Frankfort Harbor
    ("franklin-beach",                        "franklin",  "scrape"),  # Franklin Beach
    ("franklin",                              "franklin",  "scrape"),  # Franklin Beach (seatemp canonical)
    ("fraser-bay",                            "fraser",  "scrape"),  # Fraser Bay
    ("fraser",                                "fraser",  "scrape"),  # Fraser Bay (seatemp canonical)
    ("frederiksted-beach",                    "frederiksted",  "scrape"),  # Frederiksted Beach
    ("frederiksted",                          "frederiksted",  "scrape"),  # Frederiksted Beach (seatemp canonical)
    ("fremont-beach",                         "fremont",  "scrape"),  # Fremont Beach
    ("fremont",                               "fremont",  "scrape"),  # Fremont Beach (seatemp canonical)
    ("freshwater-bay",                        "freshwater",  "scrape"),  # Freshwater Bay
    ("freshwater",                            "freshwater",  "scrape"),  # Freshwater Bay (seatemp canonical)
    ("freshwater-cove",                       "freshwater",  "scrape"),  # Freshwater Cove
    ("friendship-beach",                      "friendship",  "scrape"),  # Friendship Beach
    ("friendship",                            "friendship",  "scrape"),  # Friendship Beach (seatemp canonical)
    ("friendship-cove",                       "friendship",  "scrape"),  # Friendship Cove
    ("friendship-harbor",                     "friendship",  "scrape"),  # Friendship Harbor
    ("fripp-island-beach",                    "fripp-island",  "scrape"),  # Fripp Island beach
    ("fripp-island",                          "fripp-island",  "scrape"),  # Fripp Island beach (seatemp canonical)
    ("frisco-bay",                            "frisco",  "scrape"),  # Frisco Bay
    ("frisco",                                "frisco",  "scrape"),  # Frisco Bay (seatemp canonical)
    ("galley-bay",                            "galley-bay",  "scrape"),  # Galley Bay
    ("galley-bay-beach",                      "galley-bay",  "scrape"),  # Galley Bay Beach
    ("galveston-beach",                       "galveston",  "scrape"),  # Galveston Beach
    ("galway-bay",                            "galway",  "scrape"),  # Galway Bay
    ("galway",                                "galway",  "scrape"),  # Galway Bay (seatemp canonical)
    ("gander-bay",                            "gander-bay",  "scrape"),  # Gander Bay
    ("garden-bay",                            "garden",  "scrape"),  # Garden Bay
    ("garden",                                "garden",  "scrape"),  # Garden Bay (seatemp canonical)
    ("garden-city-beach",                     "garden-city",  "scrape"),  # Garden City Beach
    ("garden-city",                           "garden-city",  "scrape"),  # Garden City Beach (seatemp canonical)
    ("garden-cove",                           "garden",  "scrape"),  # Garden Cove
    ("garden-island-bay",                     "garden-island",  "scrape"),  # Garden Island Bay
    ("garden-island",                         "garden-island",  "scrape"),  # Garden Island Bay (seatemp canonical)
    ("garden-island-harbor",                  "garden-island",  "scrape"),  # Garden Island Harbor
    ("gardiners-bay",                         "gardiners-bay",  "scrape"),  # Gardiners Bay
    ("gary-harbor",                           "gary",  "scrape"),  # Gary Harbor
    ("gary",                                  "gary",  "scrape"),  # Gary Harbor (seatemp canonical)
    ("geneva-bay",                            "geneva",  "scrape"),  # Geneva Bay
    ("geneva",                                "geneva",  "scrape"),  # Geneva Bay (seatemp canonical)
    ("geneva-beach",                          "geneva",  "scrape"),  # Geneva Beach
    ("george-inlet",                          "george",  "scrape"),  # George Inlet
    ("george",                                "george",  "scrape"),  # George Inlet (seatemp canonical)
    ("georgia-beach",                         "georgia",  "scrape"),  # Georgia Beach
    ("georgia",                               "georgia",  "scrape"),  # Georgia Beach (seatemp canonical)
    ("germany-bay",                           "germany",  "scrape"),  # Germany Bay
    ("germany",                               "germany",  "scrape"),  # Germany Bay (seatemp canonical)
    ("gibson-island-beach",                   "gibson-island",  "scrape"),  # Gibson Island Beach
    ("gibson-island",                         "gibson-island",  "scrape"),  # Gibson Island Beach (seatemp canonical)
    ("gibsons-bay",                           "gibsons",  "scrape"),  # Gibsons Bay
    ("gibsons",                               "gibsons",  "scrape"),  # Gibsons Bay (seatemp canonical)
    ("gibsons-beach",                         "gibsons",  "scrape"),  # Gibsons Beach
    ("gilgo-beach",                           "gilgo-beach",  "scrape"),  # Gilgo Beach
    ("gillson-beach",                         "gillson-beach",  "scrape"),  # Gillson Beach
    ("gimli-beach",                           "gimli",  "scrape"),  # Gimli Beach
    ("gimli",                                 "gimli",  "scrape"),  # Gimli Beach (seatemp canonical)
    ("glacier-bay",                           "glacier-bay",  "scrape"),  # Glacier Bay
    ("glass-beach",                           "glass-beach",  "scrape"),  # Glass Beach
    ("glen-cove",                             "glen-cove",  "scrape"),  # Glen Cove
    ("glen-cove-beach",                       "glen-cove",  "scrape"),  # Glen Cove Beach
    ("glencoe-beach",                         "glencoe",  "scrape"),  # Glencoe Beach
    ("glencoe",                               "glencoe",  "scrape"),  # Glencoe Beach (seatemp canonical)
    ("glenn-bay",                             "glenn",  "scrape"),  # Glenn Bay
    ("glenn",                                 "glenn",  "scrape"),  # Glenn Bay (seatemp canonical)
    ("glenn-cove",                            "glenn",  "scrape"),  # Glenn Cove
    ("gloucester-harbor",                     "gloucester",  "scrape"),  # Gloucester Harbor
    ("gloucester",                            "gloucester",  "scrape"),  # Gloucester Harbor (seatemp canonical)
    ("goleta-cove",                           "goleta",  "scrape"),  # Goleta Cove
    ("goleta",                                "goleta",  "scrape"),  # Goleta Cove (seatemp canonical)
    ("good-harbor-bay",                       "good-harbor-bay",  "scrape"),  # Good Harbor Bay
    ("good-harbor-beach",                     "good-harbor-beach",  "scrape"),  # Good Harbor Beach
    ("goodland-bay",                          "goodland",  "scrape"),  # Goodland Bay
    ("goodland",                              "goodland",  "scrape"),  # Goodland Bay (seatemp canonical)
    ("goose-bay",                             "goose-bay",  "scrape"),  # Goose Bay
    ("gooseberry-beach",                      "gooseberry-beach",  "scrape"),  # Gooseberry Beach
    ("gordons-bay",                           "gordons-bay",  "scrape"),  # Gordons Bay
    ("gore-bay",                              "gore-bay",  "scrape"),  # Gore Bay
    ("gosport-harbor",                        "gosport",  "scrape"),  # Gosport Harbor
    ("gosport",                               "gosport",  "scrape"),  # Gosport Harbor (seatemp canonical)
    ("governors-beach",                       "governors-beach",  "scrape"),  # Governor's Beach
    ("grace-bay",                             "grace-bay",  "scrape"),  # Grace Bay
    ("grace-bay-beach",                       "grace-bay",  "scrape"),  # Grace Bay Beach
    ("grand-beach",                           "grand-beach",  "scrape"),  # Grand Beach
    ("grand-isle-beach",                      "grand-isle",  "scrape"),  # Grand Isle Beach
    ("grand-traverse-bay",                    "grand-traverse-bay",  "scrape"),  # Grand Traverse Bay
    ("grande-anse",                           "grande-anse",  "scrape"),  # Grande Anse
    ("grandview-beach",                       "grandview-beach",  "scrape"),  # Grandview Beach
    ("gray-whale-cove-state-beach",           "gray-whale-cove-state-beach",  "scrape"),  # Gray Whale Cove State Beach
    ("grays-bay",                             "grays",  "scrape"),  # Grays Bay
    ("grays",                                 "grays",  "scrape"),  # Grays Bay (seatemp canonical)
    ("grays-beach",                           "grays-beach",  "scrape"),  # Grays Beach
    ("grays-cove",                            "grays",  "scrape"),  # Grays Cove
    ("great-bay",                             "great-bay",  "scrape"),  # Great Bay
    ("great-bay-beach",                       "great-bay",  "scrape"),  # Great Bay Beach
    ("great-egg-harbor-bay",                  "great-egg-harbor-bay",  "scrape"),  # Great Egg Harbor Bay
    ("great-river",                           "great-river",  "scrape"),  # Great River
    ("great-river-bay",                       "great-river",  "scrape"),  # Great River Bay
    ("great-south-bay",                       "great-south-bay",  "scrape"),  # Great South Bay
    ("green-harbor",                          "green-harbor",  "scrape"),  # Green Harbor
    ("green-harbor-beach",                    "green-harbor",  "scrape"),  # Green Harbor Beach
    ("green-hill-cove",                       "green-hill",  "scrape"),  # Green Hill Cove
    ("green-hill",                            "green-hill",  "scrape"),  # Green Hill Cove (seatemp canonical)
    ("green-island-bay",                      "green-island",  "scrape"),  # Green Island Bay
    ("green-island",                          "green-island",  "scrape"),  # Green Island Bay (seatemp canonical)
    ("green-island-sound",                    "green-island",  "scrape"),  # Green Island Sound
    ("greenland-cove",                        "greenland",  "scrape"),  # Greenland Cove
    ("greenland",                             "greenland",  "scrape"),  # Greenland Cove (seatemp canonical)
    ("greenport-harbor",                      "greenport",  "scrape"),  # Greenport Harbor
    ("greenville-sound",                      "greenville",  "scrape"),  # Greenville Sound
    ("greenville",                            "greenville",  "scrape"),  # Greenville Sound (seatemp canonical)
    ("groton-beach",                          "groton",  "scrape"),  # Groton Beach
    ("groton",                                "groton",  "scrape"),  # Groton Beach (seatemp canonical)
    ("grotto-bay",                            "grotto-bay",  "scrape"),  # Grotto Bay
    ("grotto-beach",                          "grotto-beach",  "scrape"),  # Grotto Beach
    ("guadalupe-bay",                         "guadalupe",  "scrape"),  # Guadalupe Bay
    ("guadalupe",                             "guadalupe",  "scrape"),  # Guadalupe Bay (seatemp canonical)
    ("guilford-harbor",                       "guilford",  "scrape"),  # Guilford Harbor
    ("guilford",                              "guilford",  "scrape"),  # Guilford Harbor (seatemp canonical)
    ("haena-beach",                           "haena-beach",  "scrape"),  # Ha'ena Beach
    ("haleiwa-beach",                         "haleiwa",  "scrape"),  # Haleʻiwa Beach
    ("haleiwa",                               "haleiwa",  "scrape"),  # Haleʻiwa Beach (seatemp canonical)
    ("half-moon-bay-beach",                   "half-moon-bay-beach",  "scrape"),  # Half Moon Bay Beach
    ("halfmoon-bay",                          "halfmoon-bay",  "scrape"),  # Halfmoon Bay
    ("hamburg-cove",                          "hamburg",  "scrape"),  # Hamburg Cove
    ("hamburg",                               "hamburg",  "scrape"),  # Hamburg Cove (seatemp canonical)
    ("hamlin-beach",                          "hamlin-beach",  "scrape"),  # Hamlin Beach
    ("hammonasset-beach",                     "hammonasset-beach",  "scrape"),  # Hammonasset Beach
    ("hammond-bay",                           "hammond-bay",  "scrape"),  # Hammond Bay
    ("hammond-cove",                          "hammond",  "scrape"),  # Hammond Cove
    ("hammond",                               "hammond",  "scrape"),  # Hammond Cove (seatemp canonical)
    ("hamoa-beach",                           "hamoa-beach",  "scrape"),  # Hamoa beach
    ("hampstead-bay",                         "hampstead",  "scrape"),  # Hampstead Bay
    ("hampstead",                             "hampstead",  "scrape"),  # Hampstead Bay (seatemp canonical)
    ("hanalei",                               "hanalei",  "scrape"),  # Hanalei Bay (seatemp canonical)
    ("hanapepe-bay",                          "hanapepe",  "scrape"),  # Hanapepe Bay
    ("hanapepe",                              "hanapepe",  "scrape"),  # Hanapepe Bay (seatemp canonical)
    ("hancock-beach",                         "hancock",  "scrape"),  # Hancock Beach
    ("hancock",                               "hancock",  "scrape"),  # Hancock Beach (seatemp canonical)
    ("hapuna-beach",                          "hapuna-beach",  "scrape"),  # Hapuna Beach
    ("harbor-beach",                          "harbor-beach",  "scrape"),  # Harbor Beach
    ("harbor-isle-beach",                     "harbor-isle",  "scrape"),  # Harbor Isle Beach
    ("harbor-isle",                           "harbor-isle",  "scrape"),  # Harbor Isle Beach (seatemp canonical)
    ("harbor-view-beach",                     "harbor-view",  "scrape"),  # Harbor View Beach
    ("harbor-view",                           "harbor-view",  "scrape"),  # Harbor View Beach (seatemp canonical)
    ("harbour-island-cove",                   "harbour-island",  "scrape"),  # Harbour Island Cove
    ("harbour-island",                        "harbour-island",  "scrape"),  # Harbour Island Cove (seatemp canonical)
    ("hardings-beach",                        "hardings-beach",  "scrape"),  # Hardings Beach
    ("harper-cove",                           "harper",  "scrape"),  # Harper Cove
    ("harper",                                "harper",  "scrape"),  # Harper Cove (seatemp canonical)
    ("harrington-bay",                        "harrington",  "scrape"),  # Harrington Bay
    ("harrington",                            "harrington",  "scrape"),  # Harrington Bay (seatemp canonical)
    ("harrington-cove",                       "harrington",  "scrape"),  # Harrington Cove
    ("haskells-beach",                        "haskells-beach",  "scrape"),  # Haskell's Beach
    ("hastings-cove",                         "hastings",  "scrape"),  # Hastings Cove
    ("hastings",                              "hastings",  "scrape"),  # Hastings Cove (seatemp canonical)
    ("hawaii",                                "hawaii",  "scrape"),  # Hawai'i
    ("heather-beach",                         "heather-beach",  "scrape"),  # Heather Beach
    ("hempstead-harbor",                      "hempstead-harbor",  "scrape"),  # Hempstead Harbor
    ("henderson-harbor",                      "henderson-harbor",  "scrape"),  # Henderson Harbor
    ("hernando-beach",                        "hernando-beach",  "scrape"),  # Hernando Beach
    ("herring-cove",                          "herring-cove",  "scrape"),  # Herring Cove
    ("herring-cove-beach",                    "herring-cove-beach",  "scrape"),  # Herring Cove Beach
    ("hessel-bay",                            "hessel",  "scrape"),  # Hessel Bay
    ("hessel",                                "hessel",  "scrape"),  # Hessel Bay (seatemp canonical)
    ("heeia-bay",                             "heeia",  "scrape"),  # Heʻeia Bay
    ("heeia",                                 "heeia",  "scrape"),  # Heʻeia Bay (seatemp canonical)
    ("hideaway-beach",                        "hideaway-beach",  "scrape"),  # Hideaway Beach
    ("higgins-beach",                         "higgins-beach",  "scrape"),  # Higgins Beach
    ("higgs-beach",                           "higgs-beach",  "scrape"),  # Higgs Beach
    ("high-rock-bay",                         "high-rock",  "scrape"),  # High Rock Bay
    ("high-rock",                             "high-rock",  "scrape"),  # High Rock Bay (seatemp canonical)
    ("highland-beach",                        "highland-beach",  "scrape"),  # Highland Beach
    ("highlands-bay",                         "highlands",  "scrape"),  # Highlands Bay
    ("highlands",                             "highlands",  "scrape"),  # Highlands Bay (seatemp canonical)
    ("highlands-beach",                       "highlands",  "scrape"),  # Highlands Beach
    ("hilo-bay",                              "hilo",  "scrape"),  # Hilo Bay
    ("hingham-bay",                           "hingham",  "scrape"),  # Hingham Bay
    ("hingham",                               "hingham",  "scrape"),  # Hingham Bay (seatemp canonical)
    ("hirtles-beach",                         "hirtles-beach",  "scrape"),  # Hirtle's Beach
    ("hobart-bay",                            "hobart",  "scrape"),  # Hobart Bay
    ("hobart",                                "hobart",  "scrape"),  # Hobart Bay (seatemp canonical)
    ("hobe-sound",                            "hobe-sound",  "scrape"),  # Hobe Sound
    ("hog-bay",                               "hog-bay",  "scrape"),  # Hog Bay
    ("holden-beach",                          "holden-beach",  "scrape"),  # Holden Beach
    ("holkham-bay",                           "holkham",  "scrape"),  # Holkham Bay
    ("holkham",                               "holkham",  "scrape"),  # Holkham Bay (seatemp canonical)
    ("holland-bay",                           "holland",  "scrape"),  # Holland Bay
    ("holland",                               "holland",  "scrape"),  # Holland Bay (seatemp canonical)
    ("holland-beach",                         "holland",  "scrape"),  # Holland Beach
    ("holland-cove",                          "holland",  "scrape"),  # Holland Cove
    ("holly-beach",                           "holly-beach",  "scrape"),  # Holly Beach
    ("hollywood-harbor",                      "hollywood",  "scrape"),  # Hollywood Harbor
    ("hollywood",                             "hollywood",  "scrape"),  # Hollywood Harbor (seatemp canonical)
    ("homestead-bay",                         "homestead",  "scrape"),  # Homestead Bay
    ("homestead",                             "homestead",  "scrape"),  # Homestead Bay (seatemp canonical)
    ("homosassa-bay",                         "homosassa",  "scrape"),  # Homosassa Bay
    ("honey-harbour",                         "honey-harbour",  "scrape"),  # Honey Harbour
    ("honolua-bay",                           "honolua-bay",  "scrape"),  # Honolua Bay
    ("honolulu-harbor",                       "honolulu",  "scrape"),  # Honolulu Harbor
    ("hope-bay",                              "hope-bay",  "scrape"),  # Hope Bay
    ("hopkins-bay",                           "hopkins",  "scrape"),  # Hopkins Bay
    ("hopkins",                               "hopkins",  "scrape"),  # Hopkins Bay (seatemp canonical)
    ("hopkins-cove",                          "hopkins",  "scrape"),  # Hopkins Cove
    ("hopkins-harbor",                        "hopkins",  "scrape"),  # Hopkins Harbor
    ("horseneck-beach",                       "horseneck-beach",  "scrape"),  # Horseneck Beach
    ("horseshoe-bay",                         "horseshoe-bay",  "scrape"),  # Horseshoe Bay
    ("horseshoe-bay-beach",                   "horseshoe-bay",  "scrape"),  # Horseshoe Bay Beach
    ("houston-beach",                         "houston",  "scrape"),  # Houston Beach
    ("houston",                               "houston",  "scrape"),  # Houston Beach (seatemp canonical)
    ("howdenvale-bay",                        "howdenvale",  "scrape"),  # Howdenvale Bay
    ("howdenvale",                            "howdenvale",  "scrape"),  # Howdenvale Bay (seatemp canonical)
    ("hubbards-beach",                        "hubbards-beach",  "scrape"),  # Hubbard's Beach
    ("humber-bay",                            "humber-bay",  "scrape"),  # Humber Bay
    ("humboldt-beach",                        "humboldt-beach",  "scrape"),  # Humboldt Beach
    ("huntington-bay",                        "huntington-bay",  "scrape"),  # Huntington Bay
    ("huron-bay",                             "huron",  "scrape"),  # Huron Bay
    ("idaho-inlet",                           "idaho",  "scrape"),  # Idaho Inlet
    ("idaho",                                 "idaho",  "scrape"),  # Idaho Inlet (seatemp canonical)
    ("ideal-beach",                           "ideal-beach",  "scrape"),  # Ideal Beach
    ("illinois",                              "illinois",  "scrape"),  # Illinois
    ("illinois-beach-state-park",             "illinois-beach-state-park",  "scrape"),  # Illinois Beach State Park
    ("incline-village-beach",                 "incline-village",  "scrape"),  # Incline Village Beach
    ("incline-village",                       "incline-village",  "scrape"),  # Incline Village Beach (seatemp canonical)
    ("indian-beach",                          "indian-beach",  "scrape"),  # Indian Beach
    ("indian-river-inlet",                    "indian-river-inlet",  "scrape"),  # Indian River Inlet
    ("indiana-beach",                         "indiana",  "scrape"),  # Indiana Beach
    ("indiana",                               "indiana",  "scrape"),  # Indiana Beach (seatemp canonical)
    ("indiana-harbor",                        "indiana",  "scrape"),  # Indiana Harbor
    ("indianola-beach",                       "indianola",  "scrape"),  # Indianola Beach
    ("indianola",                             "indianola",  "scrape"),  # Indianola Beach (seatemp canonical)
    ("ingonish-beach",                        "ingonish-beach",  "scrape"),  # Ingonish Beach
    ("inverhuron-bay",                        "inverhuron",  "scrape"),  # Inverhuron Bay
    ("inverhuron",                            "inverhuron",  "scrape"),  # Inverhuron Bay (seatemp canonical)
    ("iona-beach",                            "iona",  "scrape"),  # Iona Beach
    ("iona",                                  "iona",  "scrape"),  # Iona Beach (seatemp canonical)
    ("iona-cove",                             "iona",  "scrape"),  # Iona Cove
    ("ipperwash-beach",                       "ipperwash-beach",  "scrape"),  # Ipperwash Beach
    ("ireland-bay",                           "ireland",  "scrape"),  # Ireland Bay
    ("ireland",                               "ireland",  "scrape"),  # Ireland Bay (seatemp canonical)
    ("irvine-bay",                            "irvine",  "scrape"),  # Irvine Bay
    ("irvine",                                "irvine",  "scrape"),  # Irvine Bay (seatemp canonical)
    ("isla-blanca-beach",                     "isla-blanca",  "scrape"),  # Isla Blanca Beach
    ("isla-blanca",                           "isla-blanca",  "scrape"),  # Isla Blanca Beach (seatemp canonical)
    ("isla-vista-beach",                      "isla-vista",  "scrape"),  # Isla Vista Beach
    ("isla-vista",                            "isla-vista",  "scrape"),  # Isla Vista Beach (seatemp canonical)
    ("island-bay",                            "island-bay",  "scrape"),  # Island Bay
    ("island-park-beach",                     "island-park",  "scrape"),  # Island Park Beach
    ("island-park",                           "island-park",  "scrape"),  # Island Park Beach (seatemp canonical)
    ("island-park-harbor",                    "island-park",  "scrape"),  # Island Park Harbor
    ("islesboro-harbor",                      "islesboro",  "scrape"),  # Islesboro Harbor
    ("islesboro",                             "islesboro",  "scrape"),  # Islesboro Harbor (seatemp canonical)
    ("jackson-bay",                           "jackson-bay",  "scrape"),  # Jackson Bay
    ("jacksons-bay",                          "jacksons-bay",  "scrape"),  # Jacksons Bay
    ("jamaica-bay",                           "jamaica",  "scrape"),  # Jamaica Bay
    ("jamaica",                               "jamaica",  "scrape"),  # Jamaica Bay (seatemp canonical)
    ("jamaica-beach",                         "jamaica-beach",  "scrape"),  # Jamaica Beach
    ("jamaica-cove",                          "jamaica",  "scrape"),  # Jamaica Cove
    ("james-bay",                             "james-bay",  "scrape"),  # James Bay
    ("jaws-bay",                              "jaws",  "scrape"),  # Jaws Bay
    ("jaws",                                  "jaws",  "scrape"),  # Jaws Bay (seatemp canonical)
    ("jenner-bay",                            "jenner",  "scrape"),  # Jenner Bay
    ("jenner",                                "jenner",  "scrape"),  # Jenner Bay (seatemp canonical)
    ("jenner-beach",                          "jenner",  "scrape"),  # Jenner Beach
    ("jenness-beach",                         "jenness-beach",  "scrape"),  # Jenness Beach
    ("jennings-beach",                        "jennings-beach",  "scrape"),  # Jennings Beach
    ("jericho-beach",                         "jericho-beach",  "scrape"),  # Jericho Beach
    ("jersey-bay",                            "jersey",  "scrape"),  # Jersey Bay
    ("jersey",                                "jersey",  "scrape"),  # Jersey Bay (seatemp canonical)
    ("jetties-beach",                         "jetties-beach",  "scrape"),  # Jetties Beach
    ("jobos",                                 "jobos",  "scrape"),  # Jobos
    ("jordan-bay",                            "jordan",  "scrape"),  # Jordan Bay
    ("jordan",                                "jordan",  "scrape"),  # Jordan Bay (seatemp canonical)
    ("jordan-beach",                          "jordan",  "scrape"),  # Jordan Beach
    ("jordan-cove",                           "jordan",  "scrape"),  # Jordan Cove
    ("jordan-harbor",                         "jordan",  "scrape"),  # Jordan Harbor
    ("june-lake-beach",                       "june-lake",  "scrape"),  # June Lake Beach
    ("june-lake",                             "june-lake",  "scrape"),  # June Lake Beach (seatemp canonical)
    ("juneau-bay",                            "juneau",  "scrape"),  # Juneau Bay
    ("juno-beach",                            "juno-beach",  "scrape"),  # Juno Beach
    ("jupiter-sound",                         "jupiter",  "scrape"),  # Jupiter Sound
    ("jupiter",                               "jupiter",  "scrape"),  # Jupiter Sound (seatemp canonical)
    ("kaanapali",                             "kaanapali",  "scrape"),  # Ka'anapali Beach (seatemp canonical)
    ("kahakuloa-beach",                       "kahakuloa",  "scrape"),  # Kahakuloa Beach
    ("kahakuloa",                             "kahakuloa",  "scrape"),  # Kahakuloa Beach (seatemp canonical)
    ("kahala-beach",                          "kahala-beach",  "scrape"),  # Kahala Beach
    ("kahaluu-bay",                           "kahaluu",  "scrape"),  # Kahaluu Bay
    ("kahaluu",                               "kahaluu",  "scrape"),  # Kahaluu Bay (seatemp canonical)
    ("kahana-bay",                            "kahana",  "scrape"),  # Kahana Bay
    ("kahana",                                "kahana",  "scrape"),  # Kahana Bay (seatemp canonical)
    ("kahuku-beach",                          "kahuku",  "scrape"),  # Kahuku Beach
    ("kahuku",                                "kahuku",  "scrape"),  # Kahuku Beach (seatemp canonical)
    ("kahului-bay",                           "kahului",  "scrape"),  # Kahului Bay
    ("kailua",                                "kailua",  "scrape"),  # Kailua
    ("kailua-bay",                            "kailua",  "scrape"),  # Kailua Bay
    ("kaimana-beach",                         "kaimana-beach",  "scrape"),  # Kaimana beach
    ("kamal-harbor",                          "kamal",  "scrape"),  # Kamalō Harbor
    ("kamal",                                 "kamal",  "scrape"),  # Kamalō Harbor (seatemp canonical)
    ("kapaa-beach",                           "kapaa",  "scrape"),  # Kapa'a Beach
    ("kapaa",                                 "kapaa",  "scrape"),  # Kapa'a Beach (seatemp canonical)
    ("kapalua-bay",                           "kapalua",  "scrape"),  # Kapalua Bay
    ("kapalua",                               "kapalua",  "scrape"),  # Kapalua Bay (seatemp canonical)
    ("kapalua-beach",                         "kapalua",  "scrape"),  # Kapalua Beach
    ("kaunakakai-harbor",                     "kaunakakai",  "scrape"),  # Kaunakakai Harbor
    ("kaunakakai",                            "kaunakakai",  "scrape"),  # Kaunakakai Harbor (seatemp canonical)
    ("kawaihae-bay",                          "kawaihae",  "scrape"),  # Kawaihae Bay
    ("kawaihae",                              "kawaihae",  "scrape"),  # Kawaihae Bay (seatemp canonical)
    ("kawaihae-harbor",                       "kawaihae",  "scrape"),  # Kawaihae Harbor
    ("kawela-bay",                            "kawela-bay",  "scrape"),  # Kawela Bay
    ("kaaawa-beach",                          "kaaawa",  "scrape"),  # Kaʻaʻawa Beach
    ("kaaawa",                                "kaaawa",  "scrape"),  # Kaʻaʻawa Beach (seatemp canonical)
    ("kealakekua-bay",                        "kealakekua-bay",  "scrape"),  # Kealakekua Bay
    ("keaton-beach",                          "keaton-beach",  "scrape"),  # Keaton Beach
    ("kelly-beach",                           "kelly-beach",  "scrape"),  # Kelly Beach
    ("kellys-beach",                          "kellys-beach",  "scrape"),  # Kellys Beach
    ("kempenfelt-bay",                        "kempenfelt-bay",  "scrape"),  # Kempenfelt Bay
    ("kennebunkport-harbor",                  "kennebunkport",  "scrape"),  # Kennebunkport Harbor
    ("kennebunkport",                         "kennebunkport",  "scrape"),  # Kennebunkport Harbor (seatemp canonical)
    ("kenora-bay",                            "kenora",  "scrape"),  # Kenora Bay
    ("kenora",                                "kenora",  "scrape"),  # Kenora Bay (seatemp canonical)
    ("kent-cove",                             "kent",  "scrape"),  # Kent Cove
    ("kent",                                  "kent",  "scrape"),  # Kent Cove (seatemp canonical)
    ("kew-beach",                             "kew-beach",  "scrape"),  # Kew Beach
    ("keweenaw-bay",                          "keweenaw-bay",  "scrape"),  # Keweenaw Bay
    ("keyport-harbor",                        "keyport",  "scrape"),  # Keyport Harbor
    ("keyport",                               "keyport",  "scrape"),  # Keyport Harbor (seatemp canonical)
    ("kee-beach",                             "kee-beach",  "scrape"),  # Keʻe Beach
    ("kiahuna-beach",                         "kiahuna",  "scrape"),  # Kiahuna Beach
    ("kiahuna",                               "kiahuna",  "scrape"),  # Kiahuna Beach (seatemp canonical)
    ("killarney-bay",                         "killarney",  "scrape"),  # Killarney Bay
    ("killarney",                             "killarney",  "scrape"),  # Killarney Bay (seatemp canonical)
    ("king-salmon-bay",                       "king-salmon",  "scrape"),  # King Salmon Bay
    ("king-salmon",                           "king-salmon",  "scrape"),  # King Salmon Bay (seatemp canonical)
    ("kings-bay",                             "kings-bay",  "scrape"),  # King's Bay
    ("kings-beach",                           "kings-beach",  "scrape"),  # Kings Beach
    ("kingsport-beach",                       "kingsport",  "scrape"),  # Kingsport Beach
    ("kingsport",                             "kingsport",  "scrape"),  # Kingsport Beach (seatemp canonical)
    ("kite-beach",                            "kite-beach",  "scrape"),  # Kite beach
    ("kitsilano-beach",                       "kitsilano",  "scrape"),  # Kitsilano Beach
    ("kitsilano",                             "kitsilano",  "scrape"),  # Kitsilano Beach (seatemp canonical)
    ("kitty-hawk-bay",                        "kitty-hawk",  "scrape"),  # Kitty Hawk Bay
    ("knife-river-beach",                     "knife-river",  "scrape"),  # Knife River Beach
    ("knife-river",                           "knife-river",  "scrape"),  # Knife River Beach (seatemp canonical)
    ("ko-olina",                              "ko-olina",  "scrape"),  # Ko Olina
    ("kodiak-harbor",                         "kodiak",  "scrape"),  # Kodiak Harbor
    ("kotzebue-sound",                        "kotzebue",  "scrape"),  # Kotzebue Sound
    ("kotzebue",                              "kotzebue",  "scrape"),  # Kotzebue Sound (seatemp canonical)
    ("kua-bay",                               "kua-bay",  "scrape"),  # Kua Bay
    ("kua-bay-beach",                         "kua-bay",  "scrape"),  # Kua Bay Beach
    ("kuilima-cove",                          "kuilima-cove",  "scrape"),  # Kuilima Cove
    ("kukio-bay",                             "kukio",  "scrape"),  # Kukio Bay
    ("kukio",                                 "kukio",  "scrape"),  # Kukio Bay (seatemp canonical)
    ("kure-beach",                            "kure-beach",  "scrape"),  # Kure Beach
    ("lanse",                                 "lanse",  "scrape"),  # L'Anse
    ("lanse-bay",                             "lanse",  "scrape"),  # L'Anse Bay
    ("la-boquilla",                           "la-boquilla",  "scrape"),  # La Boquilla
    ("la-jolla-bay",                          "la-jolla",  "scrape"),  # La Jolla Bay
    ("la-jolla-beach",                        "la-jolla",  "scrape"),  # La Jolla Beach
    ("la-jolla-shores-beach",                 "la-jolla-shores",  "scrape"),  # La Jolla Shores Beach
    ("la-manga",                              "la-manga",  "scrape"),  # La Manga
    ("la-perouse-bay",                        "la-perouse-bay",  "scrape"),  # La Perouse Bay
    ("la-punta",                              "la-punta",  "scrape"),  # La Punta
    ("la-puntilla",                           "la-puntilla",  "scrape"),  # La Puntilla
    ("ladies-beach",                          "ladies-beach",  "scrape"),  # Ladies Beach
    ("laguna-harbor",                         "laguna",  "scrape"),  # Laguna Harbor
    ("laguna",                                "laguna",  "scrape"),  # Laguna Harbor (seatemp canonical)
    ("laguna-vista-cove",                     "laguna-vista",  "scrape"),  # Laguna Vista Cove
    ("laguna-vista",                          "laguna-vista",  "scrape"),  # Laguna Vista Cove (seatemp canonical)
    ("lake-louise-beach",                     "lake-louise",  "scrape"),  # Lake Louise Beach
    ("lake-louise",                           "lake-louise",  "scrape"),  # Lake Louise Beach (seatemp canonical)
    ("lake-lucerne-beach",                    "lake-lucerne",  "scrape"),  # Lake Lucerne Beach
    ("lake-lucerne",                          "lake-lucerne",  "scrape"),  # Lake Lucerne Beach (seatemp canonical)
    ("lake-michigan-beach",                   "lake-michigan",  "scrape"),  # Lake Michigan Beach
    ("lake-placid",                           "lake-placid",  "scrape"),  # Lake Placid
    ("lakeside-beach",                        "lakeside-beach",  "scrape"),  # Lakeside Beach
    ("lamberts-cove",                         "lamberts-cove",  "scrape"),  # Lamberts Cove
    ("lamberts-cove-beach",                   "lamberts-cove",  "scrape"),  # Lamberts Cove Beach
    ("lamoine-beach",                         "lamoine",  "scrape"),  # Lamoine Beach
    ("lamoine",                               "lamoine",  "scrape"),  # Lamoine Beach (seatemp canonical)
    ("lane-cove",                             "lane-cove",  "scrape"),  # Lane Cove
    ("langley-bay",                           "langley",  "scrape"),  # Langley Bay
    ("langley",                               "langley",  "scrape"),  # Langley Bay (seatemp canonical)
    ("langley-beach",                         "langley",  "scrape"),  # Langley Beach
    ("lanikai",                               "lanikai",  "scrape"),  # Lanikai Beach (seatemp canonical)
    ("larchmont-harbor",                      "larchmont",  "scrape"),  # Larchmont Harbor
    ("larchmont",                             "larchmont",  "scrape"),  # Larchmont Harbor (seatemp canonical)
    ("las-vegas-bay",                         "las-vegas",  "scrape"),  # Las Vegas Bay
    ("las-vegas",                             "las-vegas",  "scrape"),  # Las Vegas Bay (seatemp canonical)
    ("laurel-beach",                          "laurel",  "scrape"),  # Laurel Beach
    ("laurel",                                "laurel",  "scrape"),  # Laurel Beach (seatemp canonical)
    ("laurence-harbor-beach",                 "laurence-harbor",  "scrape"),  # Laurence Harbor Beach
    ("laurence-harbor",                       "laurence-harbor",  "scrape"),  # Laurence Harbor Beach (seatemp canonical)
    ("law-street-beach",                      "law-street-beach",  "scrape"),  # Law Street Beach
    ("lawai-beach",                           "lawai-beach",  "scrape"),  # Lawai Beach
    ("lawrencetown-beach",                    "lawrencetown-beach",  "scrape"),  # Lawrencetown Beach
    ("leadbetter-beach",                      "leadbetter-beach",  "scrape"),  # Leadbetter Beach
    ("lecount-hollow-beach",                  "lecount-hollow-beach",  "scrape"),  # Lecount Hollow Beach
    ("leonardo-harbor",                       "leonardo",  "scrape"),  # Leonardo Harbor
    ("leonardo",                              "leonardo",  "scrape"),  # Leonardo Harbor (seatemp canonical)
    ("lewis-bay",                             "lewis-bay",  "scrape"),  # Lewis Bay
    ("liberty-cove",                          "liberty",  "scrape"),  # Liberty Cove
    ("liberty",                               "liberty",  "scrape"),  # Liberty Cove (seatemp canonical)
    ("lido-beach",                            "lido-beach",  "scrape"),  # Lido Beach
    ("lighthouse-beach",                      "lighthouse-beach",  "scrape"),  # Lighthouse Beach
    ("lighthouse-point-cove",                 "lighthouse-point",  "scrape"),  # Lighthouse Point Cove
    ("lighthouse-point",                      "lighthouse-point",  "scrape"),  # Lighthouse Point Cove (seatemp canonical)
    ("lincoln-beach",                         "lincoln-beach",  "scrape"),  # Lincoln Beach
    ("lincolnville-beach",                    "lincolnville",  "scrape"),  # Lincolnville Beach
    ("lincolnville",                          "lincolnville",  "scrape"),  # Lincolnville Beach (seatemp canonical)
    ("linwood-bay",                           "linwood",  "scrape"),  # Linwood Bay
    ("linwood",                               "linwood",  "scrape"),  # Linwood Bay (seatemp canonical)
    ("linwood-beach",                         "linwood",  "scrape"),  # Linwood Beach
    ("lions-bay-beach",                       "lions-bay",  "scrape"),  # Lions Bay Beach
    ("lions-bay",                             "lions-bay",  "scrape"),  # Lions Bay Beach (seatemp canonical)
    ("lisbon-beach",                          "lisbon",  "scrape"),  # Lisbon Beach
    ("lisbon",                                "lisbon",  "scrape"),  # Lisbon Beach (seatemp canonical)
    ("litchfield-beach",                      "litchfield-beach",  "scrape"),  # Litchfield Beach
    ("little-bay",                            "little-bay",  "scrape"),  # Little Bay
    ("little-bay-beach",                      "little-bay",  "scrape"),  # Little Bay Beach
    ("little-bay-de-noc",                     "little-bay-de-noc",  "scrape"),  # Little Bay de Noc
    ("little-harbor-beach",                   "little-harbor-beach",  "scrape"),  # Little Harbor Beach
    ("little-neck-bay",                       "little-neck-bay",  "scrape"),  # Little Neck Bay
    ("little-sturgeon-bay",                   "little-sturgeon-bay",  "scrape"),  # Little Sturgeon Bay
    ("little-traverse-bay",                   "little-traverse-bay",  "scrape"),  # Little Traverse Bay
    ("livingston-bay",                        "livingston",  "scrape"),  # Livingston Bay
    ("livingston",                            "livingston",  "scrape"),  # Livingston Bay (seatemp canonical)
    ("lloyd-harbor",                          "lloyd-harbor",  "scrape"),  # Lloyd Harbor
    ("locarno-beach",                         "locarno-beach",  "scrape"),  # Locarno Beach
    ("long-bay-beach",                        "long-bay-beach",  "scrape"),  # Long Bay Beach
    ("long-neck-cove",                        "long-neck",  "scrape"),  # Long Neck Cove
    ("long-neck",                             "long-neck",  "scrape"),  # Long Neck Cove (seatemp canonical)
    ("long-point-bay",                        "long-point",  "scrape"),  # Long Point Bay
    ("long-point",                            "long-point",  "scrape"),  # Long Point Bay (seatemp canonical)
    ("long-point-beach",                      "long-point-beach",  "scrape"),  # Long Point Beach
    ("longnook-beach",                        "longnook-beach",  "scrape"),  # Longnook Beach
    ("loon-bay",                              "loon",  "scrape"),  # Loon Bay
    ("loon",                                  "loon",  "scrape"),  # Loon Bay (seatemp canonical)
    ("loon-cove",                             "loon",  "scrape"),  # Loon Cove
    ("loon-lake",                             "loon",  "scrape"),  # Loon Lake
    ("lorne-beach",                           "lorne",  "scrape"),  # Lorne Beach
    ("lorne",                                 "lorne",  "scrape"),  # Lorne Beach (seatemp canonical)
    ("los-angeles-harbor",                    "los-angeles",  "scrape"),  # Los Angeles Harbor
    ("los-angeles",                           "los-angeles",  "scrape"),  # Los Angeles Harbor (seatemp canonical)
    ("lowdermilk-beach",                      "lowdermilk-beach",  "scrape"),  # Lowdermilk Beach
    ("loyola-beach",                          "loyola-beach",  "scrape"),  # Loyola Beach
    ("lucky-bay",                             "lucky-bay",  "scrape"),  # Lucky Bay
    ("lynn-beach",                            "lynn",  "scrape"),  # Lynn Beach
    ("lynn",                                  "lynn",  "scrape"),  # Lynn Beach (seatemp canonical)
    ("lyon-cove",                             "lyon",  "scrape"),  # Lyon Cove
    ("lyon",                                  "lyon",  "scrape"),  # Lyon Cove (seatemp canonical)
    ("maalaea-bay",                           "maalaea",  "scrape"),  # Maalaea Bay
    ("maalaea",                               "maalaea",  "scrape"),  # Maalaea Bay (seatemp canonical)
    ("macatawa-bay",                          "macatawa",  "scrape"),  # Macatawa Bay
    ("macatawa",                              "macatawa",  "scrape"),  # Macatawa Bay (seatemp canonical)
    ("madeira-bay",                           "madeira",  "scrape"),  # Madeira Bay
    ("madeira",                               "madeira",  "scrape"),  # Madeira Bay (seatemp canonical)
    ("madison-bay",                           "madison",  "scrape"),  # Madison Bay
    ("madison",                               "madison",  "scrape"),  # Madison Bay (seatemp canonical)
    ("madison-cove",                          "madison",  "scrape"),  # Madison Cove
    ("magens-bay-beach",                      "magens-bay-beach",  "scrape"),  # Magen's Bay Beach
    ("magic-sands-beach",                     "magic-sands",  "scrape"),  # Magic Sands Beach
    ("magic-sands",                           "magic-sands",  "scrape"),  # Magic Sands Beach (seatemp canonical)
    ("maho-bay",                              "maho-bay",  "scrape"),  # Maho Bay
    ("maho-bay-beach",                        "maho-bay",  "scrape"),  # Maho Bay Beach
    ("maho-beach",                            "maho-beach",  "scrape"),  # Maho Beach
    ("mahogany-bay",                          "mahogany-bay",  "scrape"),  # Mahogany Bay
    ("main-beach",                            "main-beach",  "scrape"),  # Main Beach
    ("makalawena-beach",                      "makalawena-beach",  "scrape"),  # Makalawena Beach
    ("malaga-cove",                           "malaga-cove",  "scrape"),  # Malaga Cove
    ("malaquite-beach",                       "malaquite-beach",  "scrape"),  # Malaquite Beach
    ("malmo-bay",                             "malmo",  "scrape"),  # Malmo Bay
    ("malmo",                                 "malmo",  "scrape"),  # Malmo Bay (seatemp canonical)
    ("maluaka-beach",                         "maluaka-beach",  "scrape"),  # Maluaka Beach
    ("mamaroneck-harbor",                     "mamaroneck",  "scrape"),  # Mamaroneck Harbor
    ("mamaroneck",                            "mamaroneck",  "scrape"),  # Mamaroneck Harbor (seatemp canonical)
    ("manatee-bay",                           "manatee-bay",  "scrape"),  # Manatee Bay
    ("manchester-bay",                        "manchester",  "scrape"),  # Manchester Bay
    ("manchester",                            "manchester",  "scrape"),  # Manchester Bay (seatemp canonical)
    ("manchester-beach",                      "manchester",  "scrape"),  # Manchester Beach
    ("manhasset-bay",                         "manhasset-bay",  "scrape"),  # Manhasset Bay
    ("manila-bay",                            "manila",  "scrape"),  # Manila Bay
    ("manila",                                "manila",  "scrape"),  # Manila Bay (seatemp canonical)
    ("manitoba-bay",                          "manitoba",  "scrape"),  # Manitoba Bay
    ("manitoba",                              "manitoba",  "scrape"),  # Manitoba Bay (seatemp canonical)
    ("manitou-beach",                         "manitou-beach",  "scrape"),  # Manitou Beach
    ("manitowaning-bay",                      "manitowaning",  "scrape"),  # Manitowaning Bay
    ("manitowaning",                          "manitowaning",  "scrape"),  # Manitowaning Bay (seatemp canonical)
    ("manning-bay",                           "manning",  "scrape"),  # Manning Bay
    ("manning",                               "manning",  "scrape"),  # Manning Bay (seatemp canonical)
    ("manns-harbor",                          "manns-harbor",  "scrape"),  # Manns Harbor
    ("manzanita-bay",                         "manzanita",  "scrape"),  # Manzanita Bay
    ("manzanita",                             "manzanita",  "scrape"),  # Manzanita Bay (seatemp canonical)
    ("maple-bay",                             "maple-bay",  "scrape"),  # Maple Bay
    ("maple-bay-beach",                       "maple-bay",  "scrape"),  # Maple Bay Beach
    ("mar-chiquita",                          "mar-chiquita",  "scrape"),  # Mar Chiquita
    ("marconi-beach",                         "marconi-beach",  "scrape"),  # Marconi Beach
    ("maria-bay",                             "maria",  "scrape"),  # Maria Bay
    ("maria",                                 "maria",  "scrape"),  # Maria Bay (seatemp canonical)
    ("marina-bay",                            "marina-bay",  "scrape"),  # Marina Bay
    ("marina-beach",                          "marina",  "scrape"),  # Marina Beach
    ("marina",                                "marina",  "scrape"),  # Marina Beach (seatemp canonical)
    ("marina-cove",                           "marina",  "scrape"),  # Marina Cove
    ("marina-lake",                           "marina",  "scrape"),  # Marina Lake
    ("marina-state-beach",                    "marina-state-beach",  "scrape"),  # Marina State Beach
    ("marion-bay",                            "marion-bay",  "scrape"),  # Marion Bay
    ("marka-bay",                             "marka",  "scrape"),  # Marka Bay
    ("marka",                                 "marka",  "scrape"),  # Marka Bay (seatemp canonical)
    ("marquette-bay",                         "marquette",  "scrape"),  # Marquette Bay
    ("marquette",                             "marquette",  "scrape"),  # Marquette Bay (seatemp canonical)
    ("marquette-beach",                       "marquette-beach",  "scrape"),  # Marquette Beach
    ("marshalls-beach",                       "marshalls-beach",  "scrape"),  # Marshall's Beach
    ("maryland-beach",                        "maryland",  "scrape"),  # Maryland Beach
    ("maryland",                              "maryland",  "scrape"),  # Maryland Beach (seatemp canonical)
    ("mashes-sands-beach",                    "mashes-sands-beach",  "scrape"),  # Mashes Sands Beach
    ("masonboro-inlet",                       "masonboro",  "scrape"),  # Masonboro Inlet
    ("masonboro",                             "masonboro",  "scrape"),  # Masonboro Inlet (seatemp canonical)
    ("masonboro-sound",                       "masonboro",  "scrape"),  # Masonboro Sound
    ("massachusetts-bay",                     "massachusetts",  "scrape"),  # Massachusetts Bay
    ("massachusetts",                         "massachusetts",  "scrape"),  # Massachusetts Bay (seatemp canonical)
    ("matagorda-beach",                       "matagorda",  "scrape"),  # Matagorda Beach
    ("matagorda",                             "matagorda",  "scrape"),  # Matagorda Beach (seatemp canonical)
    ("mattapoisett-harbor",                   "mattapoisett",  "scrape"),  # Mattapoisett Harbor
    ("mattapoisett",                          "mattapoisett",  "scrape"),  # Mattapoisett Harbor (seatemp canonical)
    ("mauna-kea-beach",                       "mauna-kea-beach",  "scrape"),  # Mauna Kea Beach
    ("mauna-lani-beach",                      "mauna-lani",  "scrape"),  # Mauna Lani Beach
    ("mauna-lani",                            "mauna-lani",  "scrape"),  # Mauna Lani Beach (seatemp canonical)
    ("mavericks-beach",                       "mavericks-beach",  "scrape"),  # Mavericks Beach
    ("maya-beach",                            "maya",  "scrape"),  # Maya Beach
    ("maya",                                  "maya",  "scrape"),  # Maya Beach (seatemp canonical)
    ("mayflower-beach",                       "mayflower-beach",  "scrape"),  # Mayflower Beach
    ("mcgregor-bay",                          "mcgregor",  "scrape"),  # McGregor Bay
    ("mcgregor",                              "mcgregor",  "scrape"),  # McGregor Bay (seatemp canonical)
    ("mckinley-beach",                        "mckinley",  "scrape"),  # McKinley Beach
    ("mckinley",                              "mckinley",  "scrape"),  # McKinley Beach (seatemp canonical)
    ("meads-bay-beach",                       "meads-bay-beach",  "scrape"),  # Meads Bay Beach
    ("meeks-bay",                             "meeks-bay",  "scrape"),  # Meeks Bay
    ("meldrum-bay",                           "meldrum-bay",  "scrape"),  # Meldrum Bay
    ("melmerby-beach",                        "melmerby-beach",  "scrape"),  # Melmerby Beach
    ("melville-bay",                          "melville",  "scrape"),  # Melville Bay
    ("melville",                              "melville",  "scrape"),  # Melville Bay (seatemp canonical)
    ("melville-sound",                        "melville",  "scrape"),  # Melville Sound
    ("menauhant-beach",                       "menauhant-beach",  "scrape"),  # Menauhant Beach
    ("mendocino-bay",                         "mendocino",  "scrape"),  # Mendocino Bay
    ("mendocino",                             "mendocino",  "scrape"),  # Mendocino Bay (seatemp canonical)
    ("menemsha-beach",                        "menemsha",  "scrape"),  # Menemsha Beach
    ("menemsha",                              "menemsha",  "scrape"),  # Menemsha Beach (seatemp canonical)
    ("mermaid-beach",                         "mermaid-beach",  "scrape"),  # Mermaid Beach
    ("mexico-bay",                            "mexico",  "scrape"),  # Mexico Bay
    ("mexico",                                "mexico",  "scrape"),  # Mexico Bay (seatemp canonical)
    ("miami-cove",                            "miami",  "scrape"),  # Miami Cove
    ("michigan-bay",                          "michigan",  "scrape"),  # Michigan Bay
    ("michigan-beach",                        "michigan",  "scrape"),  # Michigan Beach
    ("mid-beach",                             "mid-beach",  "scrape"),  # Mid Beach
    ("midland-bay",                           "midland",  "scrape"),  # Midland Bay
    ("midland",                               "midland",  "scrape"),  # Midland Bay (seatemp canonical)
    ("midland-beach",                         "midland-beach",  "scrape"),  # Midland Beach
    ("milford-bay",                           "milford",  "scrape"),  # Milford Bay
    ("milford",                               "milford",  "scrape"),  # Milford Bay (seatemp canonical)
    ("milford-beach",                         "milford",  "scrape"),  # Milford Beach
    ("milford-harbor",                        "milford",  "scrape"),  # Milford Harbor
    ("milford-haven",                         "milford-haven",  "scrape"),  # Milford Haven
    ("mill-bay",                              "mill-bay",  "scrape"),  # Mill Bay
    ("mill-cove",                             "mill-cove",  "scrape"),  # Mill Cove
    ("miller-place-beach",                    "miller-place",  "scrape"),  # Miller Place Beach
    ("miller-place",                          "miller-place",  "scrape"),  # Miller Place Beach (seatemp canonical)
    ("milwaukee-bay",                         "milwaukee",  "scrape"),  # Milwaukee Bay
    ("milwaukee",                             "milwaukee",  "scrape"),  # Milwaukee Bay (seatemp canonical)
    ("minneapolis-beach",                     "minneapolis",  "scrape"),  # Minneapolis Beach
    ("minneapolis",                           "minneapolis",  "scrape"),  # Minneapolis Beach (seatemp canonical)
    ("minnesota-bay",                         "minnesota",  "scrape"),  # Minnesota Bay
    ("minnesota",                             "minnesota",  "scrape"),  # Minnesota Bay (seatemp canonical)
    ("miramar-beach",                         "miramar-beach",  "scrape"),  # Miramar Beach
    ("mismaloya",                             "mismaloya",  "scrape"),  # Mismaloya
    ("mississippi-sound",                     "mississippi",  "scrape"),  # Mississippi Sound
    ("mississippi",                           "mississippi",  "scrape"),  # Mississippi Sound (seatemp canonical)
    ("mitchells-bay",                         "mitchells-bay",  "scrape"),  # Mitchell's Bay
    ("mobile-bay",                            "mobile",  "scrape"),  # Mobile Bay
    ("mobile",                                "mobile",  "scrape"),  # Mobile Bay (seatemp canonical)
    ("mobjack-bay",                           "mobjack-bay",  "scrape"),  # Mobjack Bay
    ("monhegan-harbor",                       "monhegan",  "scrape"),  # Monhegan Harbor
    ("monhegan",                              "monhegan",  "scrape"),  # Monhegan Harbor (seatemp canonical)
    ("monroe-bay",                            "monroe",  "scrape"),  # Monroe Bay
    ("monroe",                                "monroe",  "scrape"),  # Monroe Bay (seatemp canonical)
    ("monroe-cove",                           "monroe",  "scrape"),  # Monroe Cove
    ("monroe-inlet",                          "monroe",  "scrape"),  # Monroe Inlet
    ("montauk-harbor",                        "montauk",  "scrape"),  # Montauk Harbor
    ("montego-bay",                           "montego-bay",  "scrape"),  # Montego Bay
    ("montezuma-bay",                         "montezuma",  "scrape"),  # Montezuma Bay
    ("montezuma",                             "montezuma",  "scrape"),  # Montezuma Bay (seatemp canonical)
    ("montgomery-bay",                        "montgomery",  "scrape"),  # Montgomery Bay
    ("montgomery",                            "montgomery",  "scrape"),  # Montgomery Bay (seatemp canonical)
    ("montreal-bay",                          "montreal",  "scrape"),  # Montreal Bay
    ("montreal",                              "montreal",  "scrape"),  # Montreal Bay (seatemp canonical)
    ("monument-beach",                        "monument-beach",  "scrape"),  # Monument Beach
    ("moonlight-bay",                         "moonlight-bay",  "scrape"),  # Moonlight Bay
    ("moonstone-beach",                       "moonstone-beach",  "scrape"),  # Moonstone Beach
    ("moorings-bay",                          "moorings",  "scrape"),  # Moorings Bay
    ("moorings",                              "moorings",  "scrape"),  # Moorings Bay (seatemp canonical)
    ("morant-bay",                            "morant-bay",  "scrape"),  # Morant Bay
    ("more-mesa-beach",                       "more-mesa-beach",  "scrape"),  # More Mesa Beach
    ("moriches-bay",                          "moriches-bay",  "scrape"),  # Moriches Bay
    ("mosman-inlet",                          "mosman",  "scrape"),  # Mosman Inlet
    ("mosman",                                "mosman",  "scrape"),  # Mosman Inlet (seatemp canonical)
    ("moss-bay",                              "moss",  "scrape"),  # Moss Bay
    ("moss",                                  "moss",  "scrape"),  # Moss Bay (seatemp canonical)
    ("moss-cove",                             "moss",  "scrape"),  # Moss Cove
    ("moss-landing-harbor",                   "moss-landing",  "scrape"),  # Moss Landing Harbor
    ("moss-landing",                          "moss-landing",  "scrape"),  # Moss Landing Harbor (seatemp canonical)
    ("moss-beach",                            "moss-beach",  "scrape"),  # Moss' Beach
    ("mount-sinai-harbor",                    "mount-sinai",  "scrape"),  # Mount Sinai Harbor
    ("mount-sinai",                           "mount-sinai",  "scrape"),  # Mount Sinai Harbor (seatemp canonical)
    ("muir-beach",                            "muir-beach",  "scrape"),  # Muir Beach
    ("mullet-bay",                            "mullet-bay",  "scrape"),  # Mullet Bay
    ("murray-beach",                          "murray-beach",  "scrape"),  # Murray Beach
    ("murrells-inlet",                        "murrells-inlet",  "scrape"),  # Murrells Inlet
    ("mystic-harbor",                         "mystic",  "scrape"),  # Mystic Harbor
    ("naha-bay",                              "naha",  "scrape"),  # Naha Bay
    ("naha",                                  "naha",  "scrape"),  # Naha Bay (seatemp canonical)
    ("nahant-bay",                            "nahant",  "scrape"),  # Nahant Bay
    ("nahant-beach",                          "nahant-beach",  "scrape"),  # Nahant Beach
    ("nahant-harbor",                         "nahant",  "scrape"),  # Nahant Harbor
    ("nairn-bay",                             "nairn",  "scrape"),  # Nairn Bay
    ("nairn",                                 "nairn",  "scrape"),  # Nairn Bay (seatemp canonical)
    ("nantucket-harbor",                      "nantucket",  "scrape"),  # Nantucket Harbor
    ("nantucket-sound",                       "nantucket",  "scrape"),  # Nantucket Sound
    ("napeague-bay",                          "napeague",  "scrape"),  # Napeague Bay
    ("napeague",                              "napeague",  "scrape"),  # Napeague Bay (seatemp canonical)
    ("napeague-beach",                        "napeague",  "scrape"),  # Napeague Beach
    ("napeague-harbor",                       "napeague",  "scrape"),  # Napeague Harbor
    ("napili-bay",                            "napili-bay",  "scrape"),  # Napili Bay
    ("narragansett-bay",                      "narragansett-bay",  "scrape"),  # Narragansett Bay
    ("nassau-bay",                            "nassau",  "scrape"),  # Nassau Bay
    ("nassau",                                "nassau",  "scrape"),  # Nassau Bay (seatemp canonical)
    ("nassau-sound",                          "nassau",  "scrape"),  # Nassau Sound
    ("nauset-beach",                          "nauset-beach",  "scrape"),  # Nauset Beach
    ("nauset-light-beach",                    "nauset-light-beach",  "scrape"),  # Nauset Light Beach
    ("navarre",                               "navarre",  "scrape"),  # Navarre Beach (seatemp canonical)
    ("nebraska-bay",                          "nebraska",  "scrape"),  # Nebraska Bay
    ("nebraska",                              "nebraska",  "scrape"),  # Nebraska Bay (seatemp canonical)
    ("nelson-bay",                            "nelson-bay",  "scrape"),  # Nelson Bay
    ("nelson-cove",                           "nelson",  "scrape"),  # Nelson Cove
    ("nelson",                                "nelson",  "scrape"),  # Nelson Cove (seatemp canonical)
    ("neptune-beach",                         "neptune-beach",  "scrape"),  # Neptune Beach
    ("neskowin-beach",                        "neskowin",  "scrape"),  # Neskowin Beach
    ("neskowin",                              "neskowin",  "scrape"),  # Neskowin Beach (seatemp canonical)
    ("netarts-bay",                           "netarts",  "scrape"),  # Netarts Bay
    ("netarts",                               "netarts",  "scrape"),  # Netarts Bay (seatemp canonical)
    ("nevada-bay",                            "nevada",  "scrape"),  # Nevada Bay
    ("nevada",                                "nevada",  "scrape"),  # Nevada Bay (seatemp canonical)
    ("nevada-beach",                          "nevada",  "scrape"),  # Nevada Beach
    ("new-haven-beach",                       "new-haven",  "scrape"),  # New Haven Beach
    ("new-haven",                             "new-haven",  "scrape"),  # New Haven Beach (seatemp canonical)
    ("new-haven-harbor",                      "new-haven",  "scrape"),  # New Haven Harbor
    ("new-london-harbor",                     "new-london",  "scrape"),  # New London Harbor
    ("new-river-beach",                       "new-river-beach",  "scrape"),  # New River Beach
    ("new-york-bay",                          "new-york",  "scrape"),  # New York Bay
    ("new-york",                              "new-york",  "scrape"),  # New York Bay (seatemp canonical)
    ("newburgh-bay",                          "newburgh",  "scrape"),  # Newburgh Bay
    ("newburgh",                              "newburgh",  "scrape"),  # Newburgh Bay (seatemp canonical)
    ("newcastle-bay",                         "newcastle",  "scrape"),  # Newcastle Bay
    ("newcastle",                             "newcastle",  "scrape"),  # Newcastle Bay (seatemp canonical)
    ("newcastle-beach",                       "newcastle",  "scrape"),  # Newcastle Beach
    ("niantic-bay",                           "niantic",  "scrape"),  # Niantic Bay
    ("nickel-beach",                          "nickel-beach",  "scrape"),  # Nickel Beach
    ("nicolet-bay",                           "nicolet-bay",  "scrape"),  # Nicolet Bay
    ("nicolet-bay-beach",                     "nicolet-bay",  "scrape"),  # Nicolet Bay Beach
    ("nobska-beach",                          "nobska-beach",  "scrape"),  # Nobska Beach
    ("norfolk-bay",                           "norfolk",  "scrape"),  # Norfolk Bay
    ("normandy-beach",                        "normandy-beach",  "scrape"),  # Normandy Beach
    ("normandy-harbor",                       "normandy",  "scrape"),  # Normandy Harbor
    ("normandy",                              "normandy",  "scrape"),  # Normandy Harbor (seatemp canonical)
    ("north-bay",                             "north-bay",  "scrape"),  # North Bay
    ("north-bay-beach",                       "north-bay",  "scrape"),  # North Bay Beach
    ("north-beach",                           "north-beach",  "scrape"),  # North Beach
    ("north-beach-bay",                       "north-beach",  "scrape"),  # North Beach Bay
    ("north-east-bay",                        "north-east",  "scrape"),  # North East Bay
    ("north-east",                            "north-east",  "scrape"),  # North East Bay (seatemp canonical)
    ("north-hampton-beach",                   "north-hampton",  "scrape"),  # North Hampton Beach
    ("north-hampton",                         "north-hampton",  "scrape"),  # North Hampton Beach (seatemp canonical)
    ("north-island-beach",                    "north-island",  "scrape"),  # North Island Beach
    ("north-island",                          "north-island",  "scrape"),  # North Island Beach (seatemp canonical)
    ("north-rustico-beach",                   "north-rustico",  "scrape"),  # North Rustico Beach
    ("north-rustico",                         "north-rustico",  "scrape"),  # North Rustico Beach (seatemp canonical)
    ("north-sea-harbor",                      "north-sea",  "scrape"),  # North Sea Harbor
    ("north-shore-beach",                     "north-shore-beach",  "scrape"),  # North Shore Beach
    ("northport-bay",                         "northport",  "scrape"),  # Northport Bay
    ("northport",                             "northport",  "scrape"),  # Northport Bay (seatemp canonical)
    ("northport-beach",                       "northport",  "scrape"),  # Northport Beach
    ("northport-harbor",                      "northport",  "scrape"),  # Northport Harbor
    ("norwalk-harbor",                        "norwalk",  "scrape"),  # Norwalk Harbor
    ("norwalk",                               "norwalk",  "scrape"),  # Norwalk Harbor (seatemp canonical)
    ("noyack-bay",                            "noyack",  "scrape"),  # Noyack Bay
    ("noyack",                                "noyack",  "scrape"),  # Noyack Bay (seatemp canonical)
    ("oak-bay",                               "oak-bay",  "scrape"),  # Oak Bay
    ("oak-beach",                             "oak-beach",  "scrape"),  # Oak Beach
    ("oak-creek",                             "oak-creek",  "scrape"),  # Oak Creek
    ("oak-street-beach",                      "oak-street-beach",  "scrape"),  # Oak Street Beach
    ("oakland-beach",                         "oakland-beach",  "scrape"),  # Oakland Beach
    ("oakland-cove",                          "oakland",  "scrape"),  # Oakland Cove
    ("oakland",                               "oakland",  "scrape"),  # Oakland Cove (seatemp canonical)
    ("oakwood-beach",                         "oakwood-beach",  "scrape"),  # Oakwood Beach
    ("ocean-isle-beach",                      "ocean-isle-beach",  "scrape"),  # Ocean Isle Beach
    ("ochlockonee-bay",                       "ochlockonee-bay",  "scrape"),  # Ochlockonee Bay
    ("ocho-rios-bay",                         "ocho-rios",  "scrape"),  # Ocho Rios Bay
    ("ocho-rios",                             "ocho-rios",  "scrape"),  # Ocho Rios Bay (seatemp canonical)
    ("ogden-bay",                             "ogden",  "scrape"),  # Ogden Bay
    ("ogden",                                 "ogden",  "scrape"),  # Ogden Bay (seatemp canonical)
    ("ogden-dunes-beach",                     "ogden-dunes",  "scrape"),  # Ogden Dunes Beach
    ("ogden-dunes",                           "ogden-dunes",  "scrape"),  # Ogden Dunes Beach (seatemp canonical)
    ("ogunquit-beach",                        "ogunquit",  "scrape"),  # Ogunquit Beach
    ("ohio-street-beach",                     "ohio-street-beach",  "scrape"),  # Ohio Street Beach
    ("olcott-harbor",                         "olcott",  "scrape"),  # Olcott Harbor
    ("olcott",                                "olcott",  "scrape"),  # Olcott Harbor (seatemp canonical)
    ("old-beach",                             "old-beach",  "scrape"),  # Old Beach
    ("old-harbour-bay",                       "old-harbour-bay",  "scrape"),  # Old Harbour Bay
    ("omaha-beach",                           "omaha-beach",  "scrape"),  # Omaha Beach
    ("oneloa-bay",                            "oneloa-bay",  "scrape"),  # Oneloa Bay
    ("onset-bay",                             "onset",  "scrape"),  # Onset Bay
    ("onset",                                 "onset",  "scrape"),  # Onset Bay (seatemp canonical)
    ("ontario-bay",                           "ontario",  "scrape"),  # Ontario Bay
    ("ontario-beach",                         "ontario",  "scrape"),  # Ontario Beach
    ("opal-beach",                            "opal-beach",  "scrape"),  # Opal Beach
    ("oracabessa-bay",                        "oracabessa",  "scrape"),  # Oracabessa Bay
    ("oracabessa",                            "oracabessa",  "scrape"),  # Oracabessa Bay (seatemp canonical)
    ("orange-bay",                            "orange-bay",  "scrape"),  # Orange Bay
    ("orchard-beach",                         "orchard-beach",  "scrape"),  # Orchard Beach
    ("orchid-bay",                            "orchid-bay",  "scrape"),  # Orchid Bay
    ("oregon-beach",                          "oregon",  "scrape"),  # Oregon Beach
    ("oregon",                                "oregon",  "scrape"),  # Oregon Beach (seatemp canonical)
    ("orient-beach",                          "orient-beach",  "scrape"),  # Orient Beach
    ("orkney-bay",                            "orkney",  "scrape"),  # Orkney Bay
    ("orkney",                                "orkney",  "scrape"),  # Orkney Bay (seatemp canonical)
    ("orleans-beach",                         "orleans",  "scrape"),  # Orleans Beach
    ("orleans",                               "orleans",  "scrape"),  # Orleans Beach (seatemp canonical)
    ("ormond-beach",                          "ormond-beach",  "scrape"),  # Ormond Beach
    ("osprey-bay",                            "osprey",  "scrape"),  # Osprey Bay
    ("osprey",                                "osprey",  "scrape"),  # Osprey Bay (seatemp canonical)
    ("osprey-beach",                          "osprey",  "scrape"),  # Osprey Beach
    ("osprey-cove",                           "osprey",  "scrape"),  # Osprey Cove
    ("ottawa-beach",                          "ottawa-beach",  "scrape"),  # Ottawa Beach
    ("outlook-beach",                         "outlook-beach",  "scrape"),  # Outlook Beach
    ("owls-head-bay",                         "owls-head",  "scrape"),  # Owls Head Bay
    ("owls-head",                             "owls-head",  "scrape"),  # Owls Head Bay (seatemp canonical)
    ("owls-head-harbor",                      "owls-head",  "scrape"),  # Owls Head Harbor
    ("oxnard-beach",                          "oxnard",  "scrape"),  # Oxnard Beach
    ("oxnard",                                "oxnard",  "scrape"),  # Oxnard Beach (seatemp canonical)
    ("oyama-beach",                           "oyama",  "scrape"),  # Oyama Beach
    ("oyama",                                 "oyama",  "scrape"),  # Oyama Beach (seatemp canonical)
    ("oyster-bay",                            "oyster-bay",  "scrape"),  # Oyster Bay
    ("oyster-bay-harbor",                     "oyster-bay",  "scrape"),  # Oyster Bay Harbor
    ("oyster-cove",                           "oyster",  "scrape"),  # Oyster Cove
    ("oyster",                                "oyster",  "scrape"),  # Oyster Cove (seatemp canonical)
    ("pacifica-state-beach",                  "pacifica-state-beach",  "scrape"),  # Pacifica State Beach
    ("paignton-beach",                        "paignton",  "scrape"),  # Paignton Beach
    ("paignton",                              "paignton",  "scrape"),  # Paignton Beach (seatemp canonical)
    ("palisades-beach",                       "palisades-beach",  "scrape"),  # Palisades Beach
    ("palm-bay",                              "palm-bay",  "scrape"),  # Palm Bay
    ("palmetto-bay",                          "palmetto-bay",  "scrape"),  # Palmetto Bay
    ("palomino",                              "palomino",  "scrape"),  # Palomino
    ("pancake-bay",                           "pancake-bay",  "scrape"),  # Pancake Bay
    ("paradise-bay",                          "paradise-bay",  "scrape"),  # Paradise Bay
    ("paradise-beach",                        "paradise-beach",  "scrape"),  # Paradise Beach
    ("paradise-cove",                         "paradise",  "scrape"),  # Paradise Cove
    ("paradise",                              "paradise",  "scrape"),  # Paradise Cove (seatemp canonical)
    ("park-shore-beach",                      "park-shore",  "scrape"),  # Park Shore Beach
    ("park-shore",                            "park-shore",  "scrape"),  # Park Shore Beach (seatemp canonical)
    ("park-beach",                            "park-beach",  "scrape"),  # Park beach
    ("parker-bay",                            "parker",  "scrape"),  # Parker Bay
    ("parker",                                "parker",  "scrape"),  # Parker Bay (seatemp canonical)
    ("parker-beach",                          "parker",  "scrape"),  # Parker Beach
    ("parker-cove",                           "parker",  "scrape"),  # Parker Cove
    ("parksville-beach",                      "parksville",  "scrape"),  # Parksville Beach
    ("parksville",                            "parksville",  "scrape"),  # Parksville Beach (seatemp canonical)
    ("parlee-beach",                          "parlee-beach",  "scrape"),  # Parlee Beach
    ("parry-sound",                           "parry-sound",  "scrape"),  # Parry Sound
    ("pascagoula-bay",                        "pascagoula",  "scrape"),  # Pascagoula Bay
    ("pascagoula",                            "pascagoula",  "scrape"),  # Pascagoula Bay (seatemp canonical)
    ("pass-a-grille-beach",                   "pass-a-grille",  "scrape"),  # Pass-a-Grille Beach
    ("pass-a-grille",                         "pass-a-grille",  "scrape"),  # Pass-a-Grille Beach (seatemp canonical)
    ("passage-key-inlet",                     "passage-key",  "scrape"),  # Passage Key Inlet
    ("passage-key",                           "passage-key",  "scrape"),  # Passage Key Inlet (seatemp canonical)
    ("pawleys-island-beach",                  "pawleys-island",  "scrape"),  # Pawleys Island Beach
    ("pea-island-bay",                        "pea-island",  "scrape"),  # Pea Island Bay
    ("pea-island",                            "pea-island",  "scrape"),  # Pea Island Bay (seatemp canonical)
    ("pebble-beach",                          "pebble-beach",  "scrape"),  # Pebble Beach
    ("pebbles-beach",                         "pebbles-beach",  "scrape"),  # Pebbles Beach
    ("pelican-bay",                           "pelican-bay",  "scrape"),  # Pelican Bay
    ("pemaquid-harbor",                       "pemaquid",  "scrape"),  # Pemaquid Harbor
    ("pemaquid",                              "pemaquid",  "scrape"),  # Pemaquid Harbor (seatemp canonical)
    ("penobscot-bay",                         "penobscot-bay",  "scrape"),  # Penobscot Bay
    ("pensacola-bay",                         "pensacola",  "scrape"),  # Pensacola Bay
    ("pensacola",                             "pensacola",  "scrape"),  # Pensacola Bay (seatemp canonical)
    ("perez-cove",                            "perez",  "scrape"),  # Perez Cove
    ("perez",                                 "perez",  "scrape"),  # Perez Cove (seatemp canonical)
    ("pescadero-beach",                       "pescadero",  "scrape"),  # Pescadero Beach
    ("pescadero",                             "pescadero",  "scrape"),  # Pescadero Beach (seatemp canonical)
    ("pfeiffer-beach",                        "pfeiffer-beach",  "scrape"),  # Pfeiffer Beach
    ("philipsburg-bay",                       "philipsburg",  "scrape"),  # Philipsburg Bay
    ("philipsburg",                           "philipsburg",  "scrape"),  # Philipsburg Bay (seatemp canonical)
    ("phillips-beach",                        "phillips-beach",  "scrape"),  # Phillips Beach
    ("phoenix-bay",                           "phoenix",  "scrape"),  # Phoenix Bay
    ("phoenix",                               "phoenix",  "scrape"),  # Phoenix Bay (seatemp canonical)
    ("pickering-beach",                       "pickering",  "scrape"),  # Pickering Beach
    ("pickering",                             "pickering",  "scrape"),  # Pickering Beach (seatemp canonical)
    ("pickering-cove",                        "pickering",  "scrape"),  # Pickering Cove
    ("pierre-bay",                            "pierre",  "scrape"),  # Pierre Bay
    ("pierre",                                "pierre",  "scrape"),  # Pierre Bay (seatemp canonical)
    ("pike-bay",                              "pike-bay",  "scrape"),  # Pike Bay
    ("pine-knoll-shores",                     "pine-knoll-shores",  "scrape"),  # Pine Knoll Shores
    ("pine-point-beach",                      "pine-point",  "scrape"),  # Pine Point Beach
    ("pine-point",                            "pine-point",  "scrape"),  # Pine Point Beach (seatemp canonical)
    ("placer-cove",                           "placer",  "scrape"),  # Placer Cove
    ("placer",                                "placer",  "scrape"),  # Placer Cove (seatemp canonical)
    ("placida-harbor",                        "placida",  "scrape"),  # Placida Harbor
    ("placida",                               "placida",  "scrape"),  # Placida Harbor (seatemp canonical)
    ("playa-azul",                            "playa-azul",  "scrape"),  # Playa Azul
    ("playa-brava",                           "playa-brava",  "scrape"),  # Playa Brava
    ("playa-dorada",                          "playa-dorada",  "scrape"),  # Playa Dorada
    ("playa-esmeralda",                       "playa-esmeralda",  "scrape"),  # Playa Esmeralda
    ("playa-fortuna",                         "playa-fortuna",  "scrape"),  # Playa Fortuna
    ("playa-hermosa",                         "playa-hermosa",  "scrape"),  # Playa Hermosa
    ("playa-jibacoa",                         "playa-jibacoa",  "scrape"),  # Playa Jibacoa
    ("playa-la-lancha",                       "playa-la-lancha",  "scrape"),  # Playa La Lancha
    ("playa-langosta",                        "playa-langosta",  "scrape"),  # Playa Langosta
    ("playa-larga",                           "playa-larga",  "scrape"),  # Playa Larga
    ("playa-miramar",                         "playa-miramar",  "scrape"),  # Playa Miramar
    ("playa-norte",                           "playa-norte",  "scrape"),  # Playa Norte
    ("playa-pesquero",                        "playa-pesquero",  "scrape"),  # Playa Pesquero
    ("playa-san-francisco",                   "playa-san-francisco",  "scrape"),  # Playa San Francisco
    ("playa-santa-lucia",                     "playa-santa-lucia",  "scrape"),  # Playa Santa Lucia
    ("playa-sucia",                           "playa-sucia",  "scrape"),  # Playa Sucia
    ("playa-ventanas",                        "playa-ventanas",  "scrape"),  # Playa Ventanas
    ("playa-del-rey",                         "playa-del-rey",  "scrape"),  # Playa del Rey
    ("playalinda-beach",                      "playalinda-beach",  "scrape"),  # Playalinda Beach
    ("pleasant-bay",                          "pleasant-bay",  "scrape"),  # Pleasant Bay
    ("pleasant-bay-beach",                    "pleasant-bay",  "scrape"),  # Pleasant Bay Beach
    ("pleasantville-cove",                    "pleasantville",  "scrape"),  # Pleasantville Cove
    ("pleasantville",                         "pleasantville",  "scrape"),  # Pleasantville Cove (seatemp canonical)
    ("pleasure-bay",                          "pleasure-bay",  "scrape"),  # Pleasure Bay
    ("pleasure-bay-beach",                    "pleasure-bay",  "scrape"),  # Pleasure Bay Beach
    ("pleasure-point",                        "pleasure-point",  "scrape"),  # Pleasure Point
    ("plum-island-beach",                     "plum-island",  "scrape"),  # Plum Island Beach
    ("point-clark-beach",                     "point-clark",  "scrape"),  # Point Clark Beach
    ("point-clark",                           "point-clark",  "scrape"),  # Point Clark Beach (seatemp canonical)
    ("point-michaud-beach",                   "point-michaud",  "scrape"),  # Point Michaud Beach
    ("point-michaud",                         "point-michaud",  "scrape"),  # Point Michaud Beach (seatemp canonical)
    ("point-reyes-beach",                     "point-reyes",  "scrape"),  # Point Reyes Beach
    ("ponce-harbor",                          "ponce",  "scrape"),  # Ponce Harbor
    ("ponce",                                 "ponce",  "scrape"),  # Ponce Harbor (seatemp canonical)
    ("poole-bay",                             "poole",  "scrape"),  # Poole Bay
    ("poole",                                 "poole",  "scrape"),  # Poole Bay (seatemp canonical)
    ("popham-beach",                          "popham-beach",  "scrape"),  # Popham Beach
    ("poplar-beach",                          "poplar-beach",  "scrape"),  # Poplar Beach
    ("popponesset-bay",                       "popponesset",  "scrape"),  # Popponesset Bay
    ("popponesset",                           "popponesset",  "scrape"),  # Popponesset Bay (seatemp canonical)
    ("port-chalmers",                         "port-chalmers",  "scrape"),  # Port Chalmers
    ("port-chester",                          "port-chester",  "scrape"),  # Port Chester
    ("port-chester-harbor",                   "port-chester",  "scrape"),  # Port Chester Harbor
    ("port-crescent-beach",                   "port-crescent",  "scrape"),  # Port Crescent Beach
    ("port-crescent",                         "port-crescent",  "scrape"),  # Port Crescent Beach (seatemp canonical)
    ("port-darlington",                       "port-darlington",  "scrape"),  # Port Darlington
    ("port-dover-beach",                      "port-dover",  "scrape"),  # Port Dover Beach
    ("port-dover",                            "port-dover",  "scrape"),  # Port Dover Beach (seatemp canonical)
    ("port-glasgow-beach",                    "port-glasgow",  "scrape"),  # Port Glasgow Beach
    ("port-glasgow",                          "port-glasgow",  "scrape"),  # Port Glasgow Beach (seatemp canonical)
    ("port-hueneme",                          "port-hueneme",  "scrape"),  # Port Hueneme
    ("port-hueneme-beach",                    "port-hueneme",  "scrape"),  # Port Hueneme Beach
    ("port-jefferson-harbor",                 "port-jefferson",  "scrape"),  # Port Jefferson Harbor
    ("port-jefferson",                        "port-jefferson",  "scrape"),  # Port Jefferson Harbor (seatemp canonical)
    ("port-maitland-beach",                   "port-maitland",  "scrape"),  # Port Maitland Beach
    ("port-maitland",                         "port-maitland",  "scrape"),  # Port Maitland Beach (seatemp canonical)
    ("port-maria-bay",                        "port-maria",  "scrape"),  # Port Maria Bay
    ("port-maria",                            "port-maria",  "scrape"),  # Port Maria Bay (seatemp canonical)
    ("port-orford-harbor",                    "port-orford",  "scrape"),  # Port Orford Harbor
    ("port-orford",                           "port-orford",  "scrape"),  # Port Orford Harbor (seatemp canonical)
    ("port-royal-cove",                       "port-royal",  "scrape"),  # Port Royal Cove
    ("port-royal",                            "port-royal",  "scrape"),  # Port Royal Cove (seatemp canonical)
    ("port-royal-sound",                      "port-royal",  "scrape"),  # Port Royal Sound
    ("portage-bay",                           "portage",  "scrape"),  # Portage Bay
    ("portage",                               "portage",  "scrape"),  # Portage Bay (seatemp canonical)
    ("portage-beach",                         "portage",  "scrape"),  # Portage Beach
    ("portage-cove",                          "portage",  "scrape"),  # Portage Cove
    ("portage-inlet",                         "portage",  "scrape"),  # Portage Inlet
    ("porteau-cove",                          "porteau-cove",  "scrape"),  # Porteau Cove
    ("porter-beach",                          "porter-beach",  "scrape"),  # Porter Beach
    ("portland-harbour",                      "portland-harbour",  "scrape"),  # Portland Harbour
    ("portobello-cove",                       "portobello",  "scrape"),  # Portobello Cove
    ("portobello",                            "portobello",  "scrape"),  # Portobello Cove (seatemp canonical)
    ("presque-isle-bay",                      "presque-isle-bay",  "scrape"),  # Presque Isle Bay
    ("presque-isle-harbor",                   "presque-isle-harbor",  "scrape"),  # Presque Isle Harbor
    ("pretty-bayou",                          "pretty-bayou",  "scrape"),  # Pretty Bayou
    ("prince-william-sound",                  "prince-william-sound",  "scrape"),  # Prince William Sound
    ("princess-bay",                          "princess-bay",  "scrape"),  # Princess Bay
    ("providence-bay",                        "providence-bay",  "scrape"),  # Providence Bay
    ("providence-cove",                       "providence",  "scrape"),  # Providence Cove
    ("providence",                            "providence",  "scrape"),  # Providence Cove (seatemp canonical)
    ("providence-harbor",                     "providence",  "scrape"),  # Providence Harbor
    ("provincetown-harbor",                   "provincetown",  "scrape"),  # Provincetown Harbor
    ("provo-bay",                             "provo",  "scrape"),  # Provo Bay
    ("provo",                                 "provo",  "scrape"),  # Provo Bay (seatemp canonical)
    ("prudhoe-bay",                           "prudhoe-bay",  "scrape"),  # Prudhoe Bay
    ("puako-bay",                             "puako",  "scrape"),  # Puako Bay
    ("puako",                                 "puako",  "scrape"),  # Puako Bay (seatemp canonical)
    ("puerto-escondido",                      "puerto-escondido",  "scrape"),  # Puerto Escondido
    ("puerto-nuevo",                          "puerto-nuevo",  "scrape"),  # Puerto Nuevo
    ("puerto-rico-cove",                      "puerto-rico",  "scrape"),  # Puerto Rico Cove
    ("puerto-rico",                           "puerto-rico",  "scrape"),  # Puerto Rico Cove (seatemp canonical)
    ("punaluu-bay",                           "punaluu",  "scrape"),  # Punaluʻu Bay
    ("punaluu",                               "punaluu",  "scrape"),  # Punaluʻu Bay (seatemp canonical)
    ("punta-blanca-bay",                      "punta-blanca",  "scrape"),  # Punta Blanca Bay
    ("punta-blanca",                          "punta-blanca",  "scrape"),  # Punta Blanca Bay (seatemp canonical)
    ("punta-rassa-cove",                      "punta-rassa",  "scrape"),  # Punta Rassa Cove
    ("punta-rassa",                           "punta-rassa",  "scrape"),  # Punta Rassa Cove (seatemp canonical)
    ("pyramid-lake-beach",                    "pyramid-lake",  "scrape"),  # Pyramid Lake Beach
    ("pyramid-lake",                          "pyramid-lake",  "scrape"),  # Pyramid Lake Beach (seatemp canonical)
    ("qualicum-beach",                        "qualicum-beach",  "scrape"),  # Qualicum Beach
    ("quebec-bay",                            "quebec",  "scrape"),  # Quebec Bay
    ("quebec",                                "quebec",  "scrape"),  # Quebec Bay (seatemp canonical)
    ("queensland-beach",                      "queensland-beach",  "scrape"),  # Queensland Beach
    ("quincy-bay",                            "quincy",  "scrape"),  # Quincy Bay
    ("quincy",                                "quincy",  "scrape"),  # Quincy Bay (seatemp canonical)
    ("quissett-beach",                        "quissett-beach",  "scrape"),  # Quissett Beach
    ("rabbit-island-beach",                   "rabbit-island",  "scrape"),  # Rabbit Island Beach
    ("rabbit-island",                         "rabbit-island",  "scrape"),  # Rabbit Island Beach (seatemp canonical)
    ("race-point-beach",                      "race-point-beach",  "scrape"),  # Race Point Beach
    ("ragged-point-beach",                    "ragged-point",  "scrape"),  # Ragged Point Beach
    ("ragged-point",                          "ragged-point",  "scrape"),  # Ragged Point Beach (seatemp canonical)
    ("ragged-point-cove",                     "ragged-point",  "scrape"),  # Ragged Point Cove
    ("rainbow-bay",                           "rainbow-bay",  "scrape"),  # Rainbow Bay
    ("rainbow-beach",                         "rainbow-beach",  "scrape"),  # Rainbow Beach
    ("rainbow-haven-beach",                   "rainbow-haven-beach",  "scrape"),  # Rainbow Haven Beach
    ("raleigh-bay",                           "raleigh",  "scrape"),  # Raleigh Bay
    ("raleigh",                               "raleigh",  "scrape"),  # Raleigh Bay (seatemp canonical)
    ("ramsey-bay",                            "ramsey",  "scrape"),  # Ramsey Bay
    ("ramsey",                                "ramsey",  "scrape"),  # Ramsey Bay (seatemp canonical)
    ("rankin-inlet",                          "rankin-inlet",  "scrape"),  # Rankin Inlet
    ("raritan-bay",                           "raritan-bay",  "scrape"),  # Raritan Bay
    ("red-bay",                               "red-bay",  "scrape"),  # Red Bay
    ("red-beach",                             "red-beach",  "scrape"),  # Red Beach
    ("red-beach-cove",                        "red-beach",  "scrape"),  # Red Beach Cove
    ("red-river-beach",                       "red-river-beach",  "scrape"),  # Red River Beach
    ("rehoboth-bay",                          "rehoboth-bay",  "scrape"),  # Rehoboth Bay
    ("rendezvous-bay",                        "rendezvous-bay",  "scrape"),  # Rendezvous Bay
    ("rendezvous-bay-beach",                  "rendezvous-bay",  "scrape"),  # Rendezvous Bay Beach
    ("resolute-cove",                         "resolute",  "scrape"),  # Resolute Cove
    ("resolute",                              "resolute",  "scrape"),  # Resolute Cove (seatemp canonical)
    ("reunion-bay",                           "reunion",  "scrape"),  # Reunion Bay
    ("reunion",                               "reunion",  "scrape"),  # Reunion Bay (seatemp canonical)
    ("rhode-island-sound",                    "rhode-island",  "scrape"),  # Rhode Island Sound
    ("rhode-island",                          "rhode-island",  "scrape"),  # Rhode Island Sound (seatemp canonical)
    ("rhodes-cove",                           "rhodes",  "scrape"),  # Rhodes Cove
    ("rhodes",                                "rhodes",  "scrape"),  # Rhodes Cove (seatemp canonical)
    ("rice-lake",                             "rice-lake",  "scrape"),  # Rice Lake
    ("richards-bay",                          "richards-bay",  "scrape"),  # Richards Bay
    ("richardson-bay",                        "richardson-bay",  "scrape"),  # Richardson Bay
    ("rincon-beach",                          "rincon-beach",  "scrape"),  # Rincon Beach
    ("rio-del-mar-beach",                     "rio-del-mar",  "scrape"),  # Rio Del Mar Beach
    ("rio-del-mar",                           "rio-del-mar",  "scrape"),  # Rio Del Mar Beach (seatemp canonical)
    ("riverton-cove",                         "riverton",  "scrape"),  # Riverton Cove
    ("riverton",                              "riverton",  "scrape"),  # Riverton Cove (seatemp canonical)
    ("riviera-bay",                           "riviera-bay",  "scrape"),  # Riviera Bay
    ("riviera-beach",                         "riviera-beach",  "scrape"),  # Riviera Beach
    ("rochester-bay",                         "rochester",  "scrape"),  # Rochester Bay
    ("rochester",                             "rochester",  "scrape"),  # Rochester Bay (seatemp canonical)
    ("rock-harbor-beach",                     "rock-harbor-beach",  "scrape"),  # Rock Harbor Beach
    ("rock-river-bay",                        "rock-river",  "scrape"),  # Rock River Bay
    ("rock-river",                            "rock-river",  "scrape"),  # Rock River Bay (seatemp canonical)
    ("rockland-harbor",                       "rockland",  "scrape"),  # Rockland Harbor
    ("rockland",                              "rockland",  "scrape"),  # Rockland Harbor (seatemp canonical)
    ("rocky-neck-beach",                      "rocky-neck",  "scrape"),  # Rocky Neck Beach
    ("rocky-neck",                            "rocky-neck",  "scrape"),  # Rocky Neck Beach (seatemp canonical)
    ("rodeo-beach",                           "rodeo-beach",  "scrape"),  # Rodeo Beach
    ("rodeo-cove",                            "rodeo",  "scrape"),  # Rodeo Cove
    ("rodeo",                                 "rodeo",  "scrape"),  # Rodeo Cove (seatemp canonical)
    ("rogers-park-beach",                     "rogers-park",  "scrape"),  # Rogers Park Beach
    ("rogers-park",                           "rogers-park",  "scrape"),  # Rogers Park Beach (seatemp canonical)
    ("rondeau-bay",                           "rondeau",  "scrape"),  # Rondeau Bay
    ("rondeau",                               "rondeau",  "scrape"),  # Rondeau Bay (seatemp canonical)
    ("rosario-beach",                         "rosario",  "scrape"),  # Rosario Beach
    ("rosario",                               "rosario",  "scrape"),  # Rosario Beach (seatemp canonical)
    ("rose-bay",                              "rose",  "scrape"),  # Rose Bay
    ("rose",                                  "rose",  "scrape"),  # Rose Bay (seatemp canonical)
    ("rose-beach",                            "rose",  "scrape"),  # Rose Beach
    ("rose-cove",                             "rose",  "scrape"),  # Rose Cove
    ("rose-inlet",                            "rose",  "scrape"),  # Rose Inlet
    ("rowleys-bay",                           "rowleys-bay",  "scrape"),  # Rowleys Bay
    ("runaway-bay",                           "runaway-bay",  "scrape"),  # Runaway Bay
    ("rush-bay",                              "rush",  "scrape"),  # Rush Bay
    ("rush",                                  "rush",  "scrape"),  # Rush Bay (seatemp canonical)
    ("rush-cove",                             "rush",  "scrape"),  # Rush Cove
    ("russell-bay",                           "russell",  "scrape"),  # Russell Bay
    ("russell",                               "russell",  "scrape"),  # Russell Bay (seatemp canonical)
    ("russell-cove",                          "russell",  "scrape"),  # Russell Cove
    ("sandy-beach",                           "sandy-beach",  "scrape"),  # SANDY BEACH
    ("sackets-harbor",                        "sackets-harbor",  "scrape"),  # Sackets Harbor
    ("saco-bay",                              "saco",  "scrape"),  # Saco Bay
    ("saco",                                  "saco",  "scrape"),  # Saco Bay (seatemp canonical)
    ("safety-bay",                            "safety-bay",  "scrape"),  # Safety Bay
    ("safety-harbor",                         "safety-harbor",  "scrape"),  # Safety Harbor
    ("sag-harbor-bay",                        "sag-harbor",  "scrape"),  # Sag Harbor Bay
    ("sag-harbor",                            "sag-harbor",  "scrape"),  # Sag Harbor Bay (seatemp canonical)
    ("sag-harbor-cove",                       "sag-harbor",  "scrape"),  # Sag Harbor Cove
    ("sagamore-beach",                        "sagamore-beach",  "scrape"),  # Sagamore Beach
    ("saginaw-bay",                           "saginaw-bay",  "scrape"),  # Saginaw Bay
    ("saint-helena-bay",                      "saint-helena",  "scrape"),  # Saint Helena Bay
    ("saint-helena",                          "saint-helena",  "scrape"),  # Saint Helena Bay (seatemp canonical)
    ("saint-helena-sound",                    "saint-helena",  "scrape"),  # Saint Helena Sound
    ("saint-james-bay",                       "saint-james",  "scrape"),  # Saint James Bay
    ("saint-james",                           "saint-james",  "scrape"),  # Saint James Bay (seatemp canonical)
    ("saint-james-harbor",                    "saint-james",  "scrape"),  # Saint James Harbor
    ("saint-johns-beach",                     "saint-johns",  "scrape"),  # Saint John's Beach
    ("saint-johns",                           "saint-johns",  "scrape"),  # Saint John's Beach (seatemp canonical)
    ("saint-louis-bay",                       "saint-louis",  "scrape"),  # Saint Louis Bay
    ("saint-louis",                           "saint-louis",  "scrape"),  # Saint Louis Bay (seatemp canonical)
    ("saint-malo-beach",                      "saint-malo",  "scrape"),  # Saint Malo Beach
    ("saint-malo",                            "saint-malo",  "scrape"),  # Saint Malo Beach (seatemp canonical)
    ("saint-martin-bay",                      "saint-martin",  "scrape"),  # Saint Martin Bay
    ("saint-martin",                          "saint-martin",  "scrape"),  # Saint Martin Bay (seatemp canonical)
    ("saint-paul-harbor",                     "saint-paul",  "scrape"),  # Saint Paul Harbor
    ("saint-paul",                            "saint-paul",  "scrape"),  # Saint Paul Harbor (seatemp canonical)
    ("saint-thomas-bay",                      "saint-thomas",  "scrape"),  # Saint Thomas Bay
    ("saint-thomas",                          "saint-thomas",  "scrape"),  # Saint Thomas Bay (seatemp canonical)
    ("saint-thomas-harbor",                   "saint-thomas",  "scrape"),  # Saint Thomas Harbor
    ("salem-cove",                            "salem",  "scrape"),  # Salem Cove
    ("salem",                                 "salem",  "scrape"),  # Salem Cove (seatemp canonical)
    ("salem-harbor",                          "salem",  "scrape"),  # Salem Harbor
    ("salem-sound",                           "salem",  "scrape"),  # Salem Sound
    ("salt-pond-beach",                       "salt-pond-beach",  "scrape"),  # Salt Pond Beach
    ("san-carlos-bay",                        "san-carlos",  "scrape"),  # San Carlos Bay
    ("san-carlos",                            "san-carlos",  "scrape"),  # San Carlos Bay (seatemp canonical)
    ("san-carlos-beach",                      "san-carlos",  "scrape"),  # San Carlos Beach
    ("san-leandro-bay",                       "san-leandro",  "scrape"),  # San Leandro Bay
    ("san-leandro",                           "san-leandro",  "scrape"),  # San Leandro Bay (seatemp canonical)
    ("san-luis-bay",                          "san-luis",  "scrape"),  # San Luis Bay
    ("san-luis",                              "san-luis",  "scrape"),  # San Luis Bay (seatemp canonical)
    ("san-luis-beach",                        "san-luis",  "scrape"),  # San Luis Beach
    ("san-luis-obispo-bay",                   "san-luis-obispo",  "scrape"),  # San Luis Obispo Bay
    ("san-luis-obispo",                       "san-luis-obispo",  "scrape"),  # San Luis Obispo Bay (seatemp canonical)
    ("san-pablo-bay",                         "san-pablo-bay",  "scrape"),  # San Pablo Bay
    ("san-pedro-bay",                         "san-pedro",  "scrape"),  # San Pedro Bay
    ("san-pedro",                             "san-pedro",  "scrape"),  # San Pedro Bay (seatemp canonical)
    ("san-pedro-beach",                       "san-pedro",  "scrape"),  # San Pedro Beach
    ("san-rafael",                            "san-rafael",  "scrape"),  # San Rafael
    ("san-salvador-beach",                    "san-salvador",  "scrape"),  # San Salvador Beach
    ("san-salvador",                          "san-salvador",  "scrape"),  # San Salvador Beach (seatemp canonical)
    ("san-simeon-bay",                        "san-simeon",  "scrape"),  # San Simeon Bay
    ("san-simeon",                            "san-simeon",  "scrape"),  # San Simeon Bay (seatemp canonical)
    ("sand-beach",                            "sand-beach",  "scrape"),  # Sand Beach
    ("sand-dollar-beach",                     "sand-dollar-beach",  "scrape"),  # Sand Dollar Beach
    ("sand-harbor",                           "sand-harbor",  "scrape"),  # Sand Harbor
    ("sand-harbor-beach",                     "sand-harbor",  "scrape"),  # Sand Harbor Beach
    ("sand-point-bay",                        "sand-point",  "scrape"),  # Sand Point Bay
    ("sand-point",                            "sand-point",  "scrape"),  # Sand Point Bay (seatemp canonical)
    ("sand-point-beach",                      "sand-point",  "scrape"),  # Sand Point Beach
    ("sandbridge-beach",                      "sandbridge",  "scrape"),  # Sandbridge Beach
    ("sandbridge",                            "sandbridge",  "scrape"),  # Sandbridge Beach (seatemp canonical)
    ("sands-point-harbor",                    "sands-point",  "scrape"),  # Sands Point Harbor
    ("sands-point",                           "sands-point",  "scrape"),  # Sands Point Harbor (seatemp canonical)
    ("sandusky-bay",                          "sandusky",  "scrape"),  # Sandusky Bay
    ("sandusky",                              "sandusky",  "scrape"),  # Sandusky Bay (seatemp canonical)
    ("sandwich-bay",                          "sandwich-bay",  "scrape"),  # Sandwich Bay
    ("sandwich-beach",                        "sandwich",  "scrape"),  # Sandwich Beach
    ("sandwich",                              "sandwich",  "scrape"),  # Sandwich Beach (seatemp canonical)
    ("sandwich-cove",                         "sandwich",  "scrape"),  # Sandwich Cove
    ("sandy-beach-bay",                       "sandy-beach",  "scrape"),  # Sandy Beach Bay
    ("sandy-beach-cove",                      "sandy-beach",  "scrape"),  # Sandy Beach Cove
    ("sandy-cove",                            "sandy-cove",  "scrape"),  # Sandy Cove
    ("sandy-cove-beach",                      "sandy-cove",  "scrape"),  # Sandy Cove Beach
    ("sandy-hook-bay",                        "sandy-hook",  "scrape"),  # Sandy Hook Bay
    ("sandy-neck-beach",                      "sandy-neck-beach",  "scrape"),  # Sandy Neck Beach
    ("sandy-point",                           "sandy-point",  "scrape"),  # Sandy Point
    ("sandy-point-bay",                       "sandy-point",  "scrape"),  # Sandy Point Bay
    ("sandy-point-beach",                     "sandy-point-beach",  "scrape"),  # Sandy Point Beach
    ("sandy-point-cove",                      "sandy-point",  "scrape"),  # Sandy Point Cove
    ("santa-barbara-cove",                    "santa-barbara",  "scrape"),  # Santa Barbara Cove
    ("santa-claus-beach",                     "santa-claus-beach",  "scrape"),  # Santa Claus Beach
    ("santa-fe-beach",                        "santa-fe",  "scrape"),  # Santa Fe Beach
    ("santa-fe",                              "santa-fe",  "scrape"),  # Santa Fe Beach (seatemp canonical)
    ("santos-bay",                            "santos",  "scrape"),  # Santos Bay
    ("santos",                                "santos",  "scrape"),  # Santos Bay (seatemp canonical)
    ("sapphire-beach",                        "sapphire-beach",  "scrape"),  # Sapphire Beach
    ("sarasota-bay",                          "sarasota",  "scrape"),  # Sarasota Bay
    ("sarasota-beach",                        "sarasota",  "scrape"),  # Sarasota Beach
    ("sarnia-bay",                            "sarnia",  "scrape"),  # Sarnia Bay
    ("sarnia",                                "sarnia",  "scrape"),  # Sarnia Bay (seatemp canonical)
    ("savannah-bay",                          "savannah",  "scrape"),  # Savannah Bay
    ("sawyer-bay",                            "sawyer",  "scrape"),  # Sawyer Bay
    ("sawyer",                                "sawyer",  "scrape"),  # Sawyer Bay (seatemp canonical)
    ("sawyer-cove",                           "sawyer",  "scrape"),  # Sawyer Cove
    ("sawyer-harbor",                         "sawyer",  "scrape"),  # Sawyer Harbor
    ("scituate-harbor",                       "scituate",  "scrape"),  # Scituate Harbor
    ("scusset-beach",                         "scusset-beach",  "scrape"),  # Scusset Beach
    ("sea-cliff-beach",                       "sea-cliff",  "scrape"),  # Sea Cliff Beach
    ("sea-cliff",                             "sea-cliff",  "scrape"),  # Sea Cliff Beach (seatemp canonical)
    ("sea-island-beach",                      "sea-island",  "scrape"),  # Sea Island Beach
    ("sea-island",                            "sea-island",  "scrape"),  # Sea Island Beach (seatemp canonical)
    ("sea-street-beach",                      "sea-street-beach",  "scrape"),  # Sea Street Beach
    ("seabright-beach",                       "seabright-beach",  "scrape"),  # Seabright Beach
    ("seabrook-beach",                        "seabrook",  "scrape"),  # Seabrook Beach
    ("seabrook",                              "seabrook",  "scrape"),  # Seabrook Beach (seatemp canonical)
    ("seacrest-beach",                        "seacrest",  "scrape"),  # Seacrest Beach
    ("seacrest",                              "seacrest",  "scrape"),  # Seacrest Beach (seatemp canonical)
    ("seaforth-beach",                        "seaforth",  "scrape"),  # Seaforth Beach
    ("seaforth",                              "seaforth",  "scrape"),  # Seaforth Beach (seatemp canonical)
    ("seagull-beach",                         "seagull-beach",  "scrape"),  # Seagull Beach
    ("seapoint-beach",                        "seapoint",  "scrape"),  # Seapoint Beach
    ("seapoint",                              "seapoint",  "scrape"),  # Seapoint Beach (seatemp canonical)
    ("searose-beach",                         "searose-beach",  "scrape"),  # Searose Beach
    ("searsport-harbor",                      "searsport",  "scrape"),  # Searsport Harbor
    ("searsport",                             "searsport",  "scrape"),  # Searsport Harbor (seatemp canonical)
    ("seaview-beach",                         "seaview",  "scrape"),  # Seaview Beach
    ("seaview",                               "seaview",  "scrape"),  # Seaview Beach (seatemp canonical)
    ("seaview-harbor",                        "seaview",  "scrape"),  # Seaview Harbor
    ("seawall-beach",                         "seawall",  "scrape"),  # Seawall Beach
    ("seawall",                               "seawall",  "scrape"),  # Seawall Beach (seatemp canonical)
    ("second-beach",                          "second-beach",  "scrape"),  # Second Beach
    ("secret-beach",                          "secret-beach",  "scrape"),  # Secret Beach
    ("secret-cove",                           "secret-cove",  "scrape"),  # Secret Cove
    ("secret-cove-beach",                     "secret-cove",  "scrape"),  # Secret Cove Beach
    ("seminole-beach",                        "seminole",  "scrape"),  # Seminole Beach
    ("seminole",                              "seminole",  "scrape"),  # Seminole Beach (seatemp canonical)
    ("severn-beach",                          "severn-beach",  "scrape"),  # Severn Beach
    ("shannon-bay",                           "shannon",  "scrape"),  # Shannon Bay
    ("shannon",                               "shannon",  "scrape"),  # Shannon Bay (seatemp canonical)
    ("shark-bay",                             "shark-bay",  "scrape"),  # Shark Bay
    ("shaws-cove",                            "shaws-cove",  "scrape"),  # Shaws Cove
    ("sheboygan-bay",                         "sheboygan",  "scrape"),  # Sheboygan Bay
    ("sheboygan",                             "sheboygan",  "scrape"),  # Sheboygan Bay (seatemp canonical)
    ("shell-bay",                             "shell-bay",  "scrape"),  # Shell Bay
    ("shell-beach",                           "shell-beach",  "scrape"),  # Shell Beach
    ("shell-key-bay",                         "shell-key",  "scrape"),  # Shell Key Bay
    ("shell-key",                             "shell-key",  "scrape"),  # Shell Key Bay (seatemp canonical)
    ("shell-point-beach",                     "shell-point-beach",  "scrape"),  # Shell Point Beach
    ("shelly-bay-beach",                      "shelly-bay-beach",  "scrape"),  # Shelly Bay Beach
    ("shelter-cove",                          "shelter-cove",  "scrape"),  # Shelter Cove
    ("ship-island-harbor",                    "ship-island",  "scrape"),  # Ship Island Harbor
    ("ship-island",                           "ship-island",  "scrape"),  # Ship Island Harbor (seatemp canonical)
    ("shoal-bay",                             "shoal-bay",  "scrape"),  # Shoal Bay
    ("shoreacres-beach",                      "shoreacres",  "scrape"),  # Shoreacres Beach
    ("shoreacres",                            "shoreacres",  "scrape"),  # Shoreacres Beach (seatemp canonical)
    ("shoreham-beach",                        "shoreham",  "scrape"),  # Shoreham Beach
    ("shoreham",                              "shoreham",  "scrape"),  # Shoreham Beach (seatemp canonical)
    ("shorewood-beach",                       "shorewood",  "scrape"),  # Shorewood Beach
    ("shorewood",                             "shorewood",  "scrape"),  # Shorewood Beach (seatemp canonical)
    ("short-beach",                           "short-beach",  "scrape"),  # Short Beach
    ("short-sand-beach",                      "short-sand-beach",  "scrape"),  # Short Sand Beach
    ("short-sands-beach",                     "short-sands-beach",  "scrape"),  # Short Sands Beach
    ("siasconset-beach",                      "siasconset",  "scrape"),  # Siasconset Beach
    ("siasconset",                            "siasconset",  "scrape"),  # Siasconset Beach (seatemp canonical)
    ("siesta-key-beach",                      "siesta-key",  "scrape"),  # Siesta Key Beach
    ("siesta-key",                            "siesta-key",  "scrape"),  # Siesta Key Beach (seatemp canonical)
    ("sile-bay",                              "sile",  "scrape"),  # Sile Bay
    ("sile",                                  "sile",  "scrape"),  # Sile Bay (seatemp canonical)
    ("silo-cove",                             "silo",  "scrape"),  # Silo Cove
    ("silo",                                  "silo",  "scrape"),  # Silo Cove (seatemp canonical)
    ("silver-bay",                            "silver-bay",  "scrape"),  # Silver Bay
    ("silver-bay-beach",                      "silver-bay",  "scrape"),  # Silver Bay Beach
    ("silver-beach",                          "silver-beach",  "scrape"),  # Silver Beach
    ("silver-creek-bay",                      "silver-creek",  "scrape"),  # Silver Creek Bay
    ("silver-creek",                          "silver-creek",  "scrape"),  # Silver Creek Bay (seatemp canonical)
    ("silver-lake-beach",                     "silver-lake",  "scrape"),  # Silver Lake Beach
    ("silver-lake",                           "silver-lake",  "scrape"),  # Silver Lake Beach (seatemp canonical)
    ("silver-sands",                          "silver-sands",  "scrape"),  # Silver Sands
    ("silver-sands-beach",                    "silver-sands-beach",  "scrape"),  # Silver Sands Beach
    ("simmons-island-beach",                  "simmons-island-beach",  "scrape"),  # Simmons Island Beach
    ("simpson-bay",                           "simpson-bay",  "scrape"),  # Simpson Bay
    ("simpson-bay-beach",                     "simpson-bay",  "scrape"),  # Simpson Bay Beach
    ("simpson-bay-lagoon",                    "simpson-bay-lagoon",  "scrape"),  # Simpson Bay Lagoon
    ("singing-beach",                         "singing-beach",  "scrape"),  # Singing Beach
    ("sister-bay",                            "sister-bay",  "scrape"),  # Sister Bay
    ("sister-bay-beach",                      "sister-bay",  "scrape"),  # Sister Bay beach
    ("sitka-sound",                           "sitka",  "scrape"),  # Sitka Sound
    ("skaha-lake-beach",                      "skaha-lake",  "scrape"),  # Skaha Lake Beach
    ("skaha-lake",                            "skaha-lake",  "scrape"),  # Skaha Lake Beach (seatemp canonical)
    ("skaket-beach",                          "skaket-beach",  "scrape"),  # Skaket Beach
    ("skeleton-bay",                          "skeleton-bay",  "scrape"),  # Skeleton Bay
    ("slaughter-beach",                       "slaughter-beach",  "scrape"),  # Slaughter Beach
    ("sleeping-bear-bay",                     "sleeping-bear",  "scrape"),  # Sleeping Bear Bay
    ("sleeping-bear",                         "sleeping-bear",  "scrape"),  # Sleeping Bear Bay (seatemp canonical)
    ("smathers-beach",                        "smathers-beach",  "scrape"),  # Smathers Beach
    ("smith-island-bay",                      "smith-island",  "scrape"),  # Smith Island Bay
    ("smith-island",                          "smith-island",  "scrape"),  # Smith Island Bay (seatemp canonical)
    ("smith-island-beach",                    "smith-island",  "scrape"),  # Smith Island Beach
    ("smith-island-inlet",                    "smith-island",  "scrape"),  # Smith Island Inlet
    ("smithtown-bay",                         "smithtown",  "scrape"),  # Smithtown Bay
    ("smithtown",                             "smithtown",  "scrape"),  # Smithtown Bay (seatemp canonical)
    ("smugglers-beach",                       "smugglers-beach",  "scrape"),  # Smugglers Beach
    ("snug-cove",                             "snug",  "scrape"),  # Snug Cove
    ("snug",                                  "snug",  "scrape"),  # Snug Cove (seatemp canonical)
    ("snug-harbor",                           "snug",  "scrape"),  # Snug Harbor
    ("solomons-bay",                          "solomons",  "scrape"),  # Solomons Bay
    ("solomons",                              "solomons",  "scrape"),  # Solomons Bay (seatemp canonical)
    ("sombrero-beach",                        "sombrero-beach",  "scrape"),  # Sombrero Beach
    ("south-arm",                             "south-arm",  "scrape"),  # South Arm
    ("south-baymouth-beach",                  "south-baymouth",  "scrape"),  # South Baymouth Beach
    ("south-baymouth",                        "south-baymouth",  "scrape"),  # South Baymouth Beach (seatemp canonical)
    ("south-cape-beach",                      "south-cape-beach",  "scrape"),  # South Cape Beach
    ("south-haven-harbor",                    "south-haven",  "scrape"),  # South Haven Harbor
    ("south-haven",                           "south-haven",  "scrape"),  # South Haven Harbor (seatemp canonical)
    ("south-shore-beach",                     "south-shore-beach",  "scrape"),  # South Shore Beach
    ("south-venice-beach",                    "south-venice",  "scrape"),  # South Venice Beach
    ("south-venice",                          "south-venice",  "scrape"),  # South Venice Beach (seatemp canonical)
    ("southold-bay",                          "southold",  "scrape"),  # Southold Bay
    ("southold",                              "southold",  "scrape"),  # Southold Bay (seatemp canonical)
    ("southwest-harbor",                      "southwest-harbor",  "scrape"),  # Southwest Harbor
    ("southwick-beach",                       "southwick-beach",  "scrape"),  # Southwick Beach
    ("spain-cove",                            "spain",  "scrape"),  # Spain Cove
    ("spain",                                 "spain",  "scrape"),  # Spain Cove (seatemp canonical)
    ("spanish-banks-beach",                   "spanish-banks",  "scrape"),  # Spanish Banks Beach
    ("spanish-banks",                         "spanish-banks",  "scrape"),  # Spanish Banks Beach (seatemp canonical)
    ("spencer-beach",                         "spencer-beach",  "scrape"),  # Spencer Beach
    ("spring-lake",                           "spring-lake",  "scrape"),  # Spring Lake
    ("spring-lake-beach",                     "spring-lake",  "scrape"),  # Spring Lake Beach
    ("springhill-beach",                      "springhill-beach",  "scrape"),  # Springhill Beach
    ("st-margarets-bay",                      "st-margarets-bay",  "scrape"),  # St Margaret's Bay
    ("st-ives-bay",                           "st-ives",  "scrape"),  # St. Ives Bay
    ("st-ives",                               "st-ives",  "scrape"),  # St. Ives Bay (seatemp canonical)
    ("st-johns",                              "st-johns",  "scrape"),  # St. John's
    ("st-johns-bay",                          "st-johns",  "scrape"),  # St. Johns Bay
    ("st-marys-bay",                          "st-marys",  "scrape"),  # St. Mary's Bay
    ("st-marys",                              "st-marys",  "scrape"),  # St. Mary's Bay (seatemp canonical)
    ("st-thomas-bay",                         "st-thomas-bay",  "scrape"),  # St. Thomas Bay
    ("stamford-harbor",                       "stamford",  "scrape"),  # Stamford Harbor
    ("stamford",                              "stamford",  "scrape"),  # Stamford Harbor (seatemp canonical)
    ("stanley-bay",                           "stanley",  "scrape"),  # Stanley Bay
    ("stanley",                               "stanley",  "scrape"),  # Stanley Bay (seatemp canonical)
    ("stanley-beach",                         "stanley",  "scrape"),  # Stanley Beach
    ("stanley-cove",                          "stanley",  "scrape"),  # Stanley Cove
    ("steuben-harbor",                        "steuben",  "scrape"),  # Steuben Harbor
    ("steuben",                               "steuben",  "scrape"),  # Steuben Harbor (seatemp canonical)
    ("stockholm-bay",                         "stockholm",  "scrape"),  # Stockholm Bay
    ("stockholm",                             "stockholm",  "scrape"),  # Stockholm Bay (seatemp canonical)
    ("stockton-harbor",                       "stockton",  "scrape"),  # Stockton Harbor
    ("stockton",                              "stockton",  "scrape"),  # Stockton Harbor (seatemp canonical)
    ("stokes-bay",                            "stokes-bay",  "scrape"),  # Stokes Bay
    ("stone-harbor",                          "stone-harbor",  "scrape"),  # Stone Harbor
    ("stony-brook-harbor",                    "stony-brook",  "scrape"),  # Stony Brook Harbor
    ("stony-brook",                           "stony-brook",  "scrape"),  # Stony Brook Harbor (seatemp canonical)
    ("stony-point-bay",                       "stony-point",  "scrape"),  # Stony Point Bay
    ("stony-point",                           "stony-point",  "scrape"),  # Stony Point Bay (seatemp canonical)
    ("stony-point-beach",                     "stony-point",  "scrape"),  # Stony Point Beach
    ("strathmere-bay",                        "strathmere",  "scrape"),  # Strathmere Bay
    ("strathmere",                            "strathmere",  "scrape"),  # Strathmere Bay (seatemp canonical)
    ("strawberry-bay",                        "strawberry",  "scrape"),  # Strawberry Bay
    ("strawberry",                            "strawberry",  "scrape"),  # Strawberry Bay (seatemp canonical)
    ("strawberry-beach",                      "strawberry",  "scrape"),  # Strawberry Beach
    ("strawberry-harbor",                     "strawberry",  "scrape"),  # Strawberry Harbor
    ("strawberry-inlet",                      "strawberry",  "scrape"),  # Strawberry Inlet
    ("stuart-cove",                           "stuart",  "scrape"),  # Stuart Cove
    ("stuart",                                "stuart",  "scrape"),  # Stuart Cove (seatemp canonical)
    ("sturgeon-bay",                          "sturgeon-bay",  "scrape"),  # Sturgeon Bay
    ("sullivan-bay",                          "sullivan",  "scrape"),  # Sullivan Bay
    ("sullivan",                              "sullivan",  "scrape"),  # Sullivan Bay (seatemp canonical)
    ("sullivan-cove",                         "sullivan",  "scrape"),  # Sullivan Cove
    ("sullivan-harbor",                       "sullivan",  "scrape"),  # Sullivan Harbor
    ("summerland-beach",                      "summerland",  "scrape"),  # Summerland Beach
    ("summerland",                            "summerland",  "scrape"),  # Summerland Beach (seatemp canonical)
    ("summerville-beach",                     "summerville-beach",  "scrape"),  # Summerville Beach
    ("sunken-meadow-beach",                   "sunken-meadow",  "scrape"),  # Sunken Meadow Beach
    ("sunken-meadow",                         "sunken-meadow",  "scrape"),  # Sunken Meadow Beach (seatemp canonical)
    ("sunny-beach",                           "sunny-beach",  "scrape"),  # Sunny Beach
    ("sunnyside-beach",                       "sunnyside-beach",  "scrape"),  # Sunnyside Beach
    ("sunrise-beach",                         "sunrise-beach",  "scrape"),  # Sunrise Beach
    ("sunshine-beach",                        "sunshine-beach",  "scrape"),  # Sunshine Beach
    ("surf-drive-beach",                      "surf-drive-beach",  "scrape"),  # Surf Drive Beach
    ("surfside-beach",                        "surfside",  "scrape"),  # Surfside Beach
    ("surfside",                              "surfside",  "scrape"),  # Surfside Beach (seatemp canonical)
    ("suttons-bay",                           "suttons-bay",  "scrape"),  # Suttons Bay
    ("suwannee-sound",                        "suwannee",  "scrape"),  # Suwannee Sound
    ("suwannee",                              "suwannee",  "scrape"),  # Suwannee Sound (seatemp canonical)
    ("swanquarter-bay",                       "swanquarter",  "scrape"),  # Swanquarter Bay
    ("swanquarter",                           "swanquarter",  "scrape"),  # Swanquarter Bay (seatemp canonical)
    ("sylvan-beach",                          "sylvan-beach",  "scrape"),  # Sylvan Beach
    ("sylvan-lake-beach",                     "sylvan-lake",  "scrape"),  # Sylvan Lake Beach
    ("sylvan-lake",                           "sylvan-lake",  "scrape"),  # Sylvan Lake Beach (seatemp canonical)
    ("t-street-beach",                        "t-street-beach",  "scrape"),  # T Street Beach
    ("taft-bay",                              "taft",  "scrape"),  # Taft Bay
    ("taft",                                  "taft",  "scrape"),  # Taft Bay (seatemp canonical)
    ("tahiti-beach",                          "tahiti-beach",  "scrape"),  # Tahiti Beach
    ("tangier-sound",                         "tangier",  "scrape"),  # Tangier Sound
    ("tangier",                               "tangier",  "scrape"),  # Tangier Sound (seatemp canonical)
    ("tango-bay",                             "tango",  "scrape"),  # Tango Bay
    ("tango",                                 "tango",  "scrape"),  # Tango Bay (seatemp canonical)
    ("tavernier-harbor",                      "tavernier",  "scrape"),  # Tavernier Harbor
    ("ten-bay-beach",                         "ten-bay-beach",  "scrape"),  # Ten Bay Beach
    ("tenby-bay",                             "tenby",  "scrape"),  # Tenby Bay
    ("tenby",                                 "tenby",  "scrape"),  # Tenby Bay (seatemp canonical)
    ("terrace-bay",                           "terrace-bay",  "scrape"),  # Terrace Bay
    ("terrace-bay-beach",                     "terrace-bay",  "scrape"),  # Terrace Bay Beach
    ("third-beach",                           "third-beach",  "scrape"),  # Third Beach
    ("thomas-point-beach",                    "thomas-point",  "scrape"),  # Thomas Point Beach
    ("thomas-point",                          "thomas-point",  "scrape"),  # Thomas Point Beach (seatemp canonical)
    ("thompson-bay",                          "thompson",  "scrape"),  # Thompson Bay
    ("thompson",                              "thompson",  "scrape"),  # Thompson Bay (seatemp canonical)
    ("thompson-beach",                        "thompson",  "scrape"),  # Thompson Beach
    ("thompson-cove",                         "thompson",  "scrape"),  # Thompson Cove
    ("three-tables",                          "three-tables",  "scrape"),  # Three Tables
    ("thule-cove",                            "thule",  "scrape"),  # Thule Cove
    ("thule",                                 "thule",  "scrape"),  # Thule Cove (seatemp canonical)
    ("thumpertown-beach",                     "thumpertown-beach",  "scrape"),  # Thumpertown Beach
    ("thunder-bay",                           "thunder-bay",  "scrape"),  # Thunder Bay
    ("thurso-bay",                            "thurso",  "scrape"),  # Thurso Bay
    ("thurso",                                "thurso",  "scrape"),  # Thurso Bay (seatemp canonical)
    ("tigre-bay",                             "tigre",  "scrape"),  # Tigre Bay
    ("tigre",                                 "tigre",  "scrape"),  # Tigre Bay (seatemp canonical)
    ("tillamook",                             "tillamook",  "scrape"),  # Tillamook Bay (seatemp canonical)
    ("timber-cove",                           "timber-cove",  "scrape"),  # Timber Cove
    ("tin-can-bay",                           "tin-can-bay",  "scrape"),  # Tin Can Bay
    ("tiny-beach",                            "tiny-beach",  "scrape"),  # Tiny Beach
    ("titusville-beach",                      "titusville",  "scrape"),  # Titusville Beach
    ("titusville",                            "titusville",  "scrape"),  # Titusville Beach (seatemp canonical)
    ("tobay-beach",                           "tobay-beach",  "scrape"),  # Tobay Beach
    ("tofte-cove",                            "tofte",  "scrape"),  # Tofte Cove
    ("tofte",                                 "tofte",  "scrape"),  # Tofte Cove (seatemp canonical)
    ("togiak-bay",                            "togiak",  "scrape"),  # Togiak Bay
    ("togiak",                                "togiak",  "scrape"),  # Togiak Bay (seatemp canonical)
    ("tokyo-bay",                             "tokyo",  "scrape"),  # Tokyo Bay
    ("tokyo",                                 "tokyo",  "scrape"),  # Tokyo Bay (seatemp canonical)
    ("tomales-bay",                           "tomales-bay",  "scrape"),  # Tomales Bay
    ("toronto-bay",                           "toronto",  "scrape"),  # Toronto Bay
    ("toronto",                               "toronto",  "scrape"),  # Toronto Bay (seatemp canonical)
    ("torrance-bay",                          "torrance",  "scrape"),  # Torrance Bay
    ("torrance",                              "torrance",  "scrape"),  # Torrance Bay (seatemp canonical)
    ("tortuguero",                            "tortuguero",  "scrape"),  # Tortuguero
    ("tourmaline-beach",                      "tourmaline-beach",  "scrape"),  # Tourmaline Beach
    ("tower-road-beach",                      "tower-road-beach",  "scrape"),  # Tower Road Beach
    ("town-neck-beach",                       "town-neck-beach",  "scrape"),  # Town Neck Beach
    ("treasure-island-beach",                 "treasure-island-beach",  "scrape"),  # Treasure Island Beach
    ("trinidad-bay",                          "trinidad",  "scrape"),  # Trinidad Bay
    ("trinidad",                              "trinidad",  "scrape"),  # Trinidad Bay (seatemp canonical)
    ("trinidad-harbor",                       "trinidad",  "scrape"),  # Trinidad Harbor
    ("trinity-bay",                           "trinity-bay",  "scrape"),  # Trinity Bay
    ("trunk-bay",                             "trunk-bay",  "scrape"),  # Trunk Bay
    ("trunk-river-beach",                     "trunk-river-beach",  "scrape"),  # Trunk River Beach
    ("tuckers-town-bay",                      "tuckers-town",  "scrape"),  # Tucker's Town Bay
    ("tuckers-town",                          "tuckers-town",  "scrape"),  # Tucker's Town Bay (seatemp canonical)
    ("tunnels-beach",                         "tunnels-beach",  "scrape"),  # Tunnels Beach
    ("turkey-bay",                            "turkey",  "scrape"),  # Turkey Bay
    ("turkey",                                "turkey",  "scrape"),  # Turkey Bay (seatemp canonical)
    ("turkey-cove",                           "turkey",  "scrape"),  # Turkey Cove
    ("turkey-point-beach",                    "turkey-point",  "scrape"),  # Turkey Point Beach
    ("turkey-point",                          "turkey-point",  "scrape"),  # Turkey Point Beach (seatemp canonical)
    ("turquoise-bay",                         "turquoise-bay",  "scrape"),  # Turquoise Bay
    ("turtle-bay",                            "turtle-bay",  "scrape"),  # Turtle Bay
    ("turtle-bay-beach",                      "turtle-bay",  "scrape"),  # Turtle Bay Beach
    ("turtle-beach",                          "turtle-beach",  "scrape"),  # Turtle Beach
    ("twin-lakes",                            "twin-lakes",  "scrape"),  # Twin Lakes
    ("twin-lakes-beach",                      "twin-lakes",  "scrape"),  # Twin Lakes Beach
    ("ulua-beach",                            "ulua-beach",  "scrape"),  # Ulua Beach
    ("unalaska-bay",                          "unalaska",  "scrape"),  # Unalaska Bay
    ("unalaska",                              "unalaska",  "scrape"),  # Unalaska Bay (seatemp canonical)
    ("union-bay",                             "union-bay",  "scrape"),  # Union Bay
    ("union-river-bay",                       "union-river-bay",  "scrape"),  # Union River Bay
    ("upper-bay",                             "upper-bay",  "scrape"),  # Upper Bay
    ("uummannaq",                             "uummannaq",  "scrape"),  # Uummannaq
    ("varadero",                              "varadero",  "scrape"),  # VARADERO
    ("vallejo-beach",                         "vallejo-beach",  "scrape"),  # Vallejo Beach
    ("vanderbilt-beach",                      "vanderbilt-beach",  "scrape"),  # Vanderbilt Beach
    ("venice",                                "venice",  "scrape"),  # Venice Beach (seatemp canonical)
    ("vera-bay",                              "vera",  "scrape"),  # Vera Bay
    ("vera",                                  "vera",  "scrape"),  # Vera Bay (seatemp canonical)
    ("vermilion-bay",                         "vermilion",  "scrape"),  # Vermilion Bay
    ("vermilion",                             "vermilion",  "scrape"),  # Vermilion Bay (seatemp canonical)
    ("victoria-bay",                          "victoria-bay",  "scrape"),  # Victoria Bay
    ("victoria-beach",                        "victoria-beach",  "scrape"),  # Victoria Beach
    ("viking-bay",                            "viking-bay",  "scrape"),  # Viking Bay
    ("vineyard-haven-harbor",                 "vineyard-haven",  "scrape"),  # Vineyard Haven Harbor
    ("vineyard-haven",                        "vineyard-haven",  "scrape"),  # Vineyard Haven Harbor (seatemp canonical)
    ("wabasso-beach",                         "wabasso-beach",  "scrape"),  # Wabasso Beach
    ("waialea-beach",                         "waialea-beach",  "scrape"),  # Waialea Beach
    ("waialua-bay",                           "waialua",  "scrape"),  # Waialua Bay
    ("waialua",                               "waialua",  "scrape"),  # Waialua Bay (seatemp canonical)
    ("wailea-bay",                            "wailea",  "scrape"),  # Wailea Bay
    ("wailea",                                "wailea",  "scrape"),  # Wailea Bay (seatemp canonical)
    ("wailua-bay",                            "wailua",  "scrape"),  # Wailua Bay
    ("wailua",                                "wailua",  "scrape"),  # Wailua Bay (seatemp canonical)
    ("wailua-cove",                           "wailua",  "scrape"),  # Wailua Cove
    ("waimanalo-beach",                       "waimanalo-beach",  "scrape"),  # Waimanalo Beach
    ("waimea-bay",                            "waimea-bay",  "scrape"),  # Waimea Bay
    ("wainscott-beach",                       "wainscott",  "scrape"),  # Wainscott Beach
    ("wainscott",                             "wainscott",  "scrape"),  # Wainscott Beach (seatemp canonical)
    ("wales-beach",                           "wales",  "scrape"),  # Wales Beach
    ("wales",                                 "wales",  "scrape"),  # Wales Beach (seatemp canonical)
    ("wallis-sands-beach",                    "wallis-sands-beach",  "scrape"),  # Wallis Sands Beach
    ("walnut-beach",                          "walnut-beach",  "scrape"),  # Walnut Beach
    ("warren-bay",                            "warren",  "scrape"),  # Warren Bay
    ("warren",                                "warren",  "scrape"),  # Warren Bay (seatemp canonical)
    ("warren-cove",                           "warren",  "scrape"),  # Warren Cove
    ("warwick-cove",                          "warwick",  "scrape"),  # Warwick Cove
    ("warwick",                               "warwick",  "scrape"),  # Warwick Cove (seatemp canonical)
    ("washburn-beach",                        "washburn",  "scrape"),  # Washburn Beach
    ("washburn",                              "washburn",  "scrape"),  # Washburn Beach (seatemp canonical)
    ("washburn-cove",                         "washburn",  "scrape"),  # Washburn Cove
    ("washington-bay",                        "washington",  "scrape"),  # Washington Bay
    ("washington",                            "washington",  "scrape"),  # Washington Bay (seatemp canonical)
    ("washington-cove",                       "washington",  "scrape"),  # Washington Cove
    ("washington-harbor",                     "washington",  "scrape"),  # Washington Harbor
    ("washington-park-beach",                 "washington-park-beach",  "scrape"),  # Washington Park Beach
    ("watch-hill-cove",                       "watch-hill",  "scrape"),  # Watch Hill Cove
    ("waterside-beach",                       "waterside-beach",  "scrape"),  # Waterside Beach
    ("waukegan-beach",                        "waukegan",  "scrape"),  # Waukegan Beach
    ("waukegan",                              "waukegan",  "scrape"),  # Waukegan Beach (seatemp canonical)
    ("waukegan-harbor",                       "waukegan",  "scrape"),  # Waukegan Harbor
    ("waves-beach",                           "waves",  "scrape"),  # Waves Beach
    ("waves",                                 "waves",  "scrape"),  # Waves Beach (seatemp canonical)
    ("wayzata-bay",                           "wayzata",  "scrape"),  # Wayzata Bay
    ("wayzata",                               "wayzata",  "scrape"),  # Wayzata Bay (seatemp canonical)
    ("weehawken-cove",                        "weehawken",  "scrape"),  # Weehawken Cove
    ("weehawken",                             "weehawken",  "scrape"),  # Weehawken Cove (seatemp canonical)
    ("weko-beach",                            "weko-beach",  "scrape"),  # Weko Beach
    ("wellfleet-harbor",                      "wellfleet",  "scrape"),  # Wellfleet Harbor
    ("wells-bay",                             "wells",  "scrape"),  # Wells Bay
    ("wells",                                 "wells",  "scrape"),  # Wells Bay (seatemp canonical)
    ("wells-cove",                            "wells",  "scrape"),  # Wells Cove
    ("west-beach",                            "west-beach",  "scrape"),  # West Beach
    ("west-beach-cove",                       "west-beach",  "scrape"),  # West Beach Cove
    ("west-meadow-beach",                     "west-meadow-beach",  "scrape"),  # West Meadow Beach
    ("westbrook-harbor",                      "westbrook",  "scrape"),  # Westbrook Harbor
    ("westbrook",                             "westbrook",  "scrape"),  # Westbrook Harbor (seatemp canonical)
    ("whale-beach",                           "whale-beach",  "scrape"),  # Whale Beach
    ("white-beach",                           "white-beach",  "scrape"),  # White Beach
    ("white-crest-beach",                     "white-crest-beach",  "scrape"),  # White Crest Beach
    ("white-house",                           "white-house",  "scrape"),  # White House
    ("white-house-bay",                       "white-house",  "scrape"),  # White House Bay
    ("white-house-cove",                      "white-house",  "scrape"),  # White House Cove
    ("white-point",                           "white-point",  "scrape"),  # White Point
    ("white-point-beach",                     "white-point-beach",  "scrape"),  # White Point Beach
    ("white-rock-bay",                        "white-rock",  "scrape"),  # White Rock Bay
    ("white-rock",                            "white-rock",  "scrape"),  # White Rock Bay (seatemp canonical)
    ("white-rock-beach",                      "white-rock",  "scrape"),  # White Rock Beach
    ("white-rock-cove",                       "white-rock",  "scrape"),  # White Rock Cove
    ("whitefish-bay",                         "whitefish-bay",  "scrape"),  # Whitefish Bay
    ("whiting-cove",                          "whiting",  "scrape"),  # Whiting Cove
    ("whiting",                               "whiting",  "scrape"),  # Whiting Cove (seatemp canonical)
    ("whiting-harbor",                        "whiting",  "scrape"),  # Whiting Harbor
    ("wickford-harbor",                       "wickford",  "scrape"),  # Wickford Harbor
    ("wickford",                              "wickford",  "scrape"),  # Wickford Harbor (seatemp canonical)
    ("wilderness",                            "wilderness",  "scrape"),  # Wilderness
    ("wilderness-bay",                        "wilderness",  "scrape"),  # Wilderness Bay
    ("wildwood-beach",                        "wildwood",  "scrape"),  # Wildwood Beach
    ("wildwood-cove",                         "wildwood",  "scrape"),  # Wildwood Cove
    ("willoughby-bay",                        "willoughby",  "scrape"),  # Willoughby Bay
    ("willoughby",                            "willoughby",  "scrape"),  # Willoughby Bay (seatemp canonical)
    ("willoughby-beach",                      "willoughby",  "scrape"),  # Willoughby Beach
    ("willoughby-cove",                       "willoughby",  "scrape"),  # Willoughby Cove
    ("wilson-bay",                            "wilson",  "scrape"),  # Wilson Bay
    ("wilson",                                "wilson",  "scrape"),  # Wilson Bay (seatemp canonical)
    ("wilson-beach",                          "wilson",  "scrape"),  # Wilson Beach
    ("wilson-cove",                           "wilson",  "scrape"),  # Wilson Cove
    ("wilson-harbor",                         "wilson",  "scrape"),  # Wilson Harbor
    ("windansea-beach",                       "windansea-beach",  "scrape"),  # Windansea Beach
    ("windmill-beach",                        "windmill-beach",  "scrape"),  # Windmill Beach
    ("windsor-beach",                         "windsor",  "scrape"),  # Windsor Beach
    ("windsor",                               "windsor",  "scrape"),  # Windsor Beach (seatemp canonical)
    ("wingaersheek-beach",                    "wingaersheek-beach",  "scrape"),  # Wingaersheek Beach
    ("winnipeg-beach",                        "winnipeg-beach",  "scrape"),  # Winnipeg Beach
    ("winter-harbor",                         "winter-harbor",  "scrape"),  # Winter Harbor
    ("winter-harbor-cove",                    "winter-harbor",  "scrape"),  # Winter Harbor Cove
    ("winthrop-cove",                         "winthrop",  "scrape"),  # Winthrop Cove
    ("wisconsin-bay",                         "wisconsin",  "scrape"),  # Wisconsin Bay
    ("wisconsin",                             "wisconsin",  "scrape"),  # Wisconsin Bay (seatemp canonical)
    ("wollaston-beach",                       "wollaston-beach",  "scrape"),  # Wollaston Beach
    ("woodbine-beach",                        "woodbine-beach",  "scrape"),  # Woodbine Beach
    ("woodbridge-bay",                        "woodbridge",  "scrape"),  # Woodbridge Bay
    ("woodbridge",                            "woodbridge",  "scrape"),  # Woodbridge Bay (seatemp canonical)
    ("woodland-beach",                        "woodland-beach",  "scrape"),  # Woodland Beach
    ("wreck-beach",                           "wreck-beach",  "scrape"),  # Wreck Beach
    ("yakutat-bay",                           "yakutat",  "scrape"),  # Yakutat Bay
    ("yakutat",                               "yakutat",  "scrape"),  # Yakutat Bay (seatemp canonical)
    ("yallahs-bay",                           "yallahs",  "scrape"),  # Yallahs Bay
    ("yallahs",                               "yallahs",  "scrape"),  # Yallahs Bay (seatemp canonical)
    ("yellowknife-bay",                       "yellowknife",  "scrape"),  # Yellowknife Bay
    ("yellowknife",                           "yellowknife",  "scrape"),  # Yellowknife Bay (seatemp canonical)
    ("yokohama-bay",                          "yokohama",  "scrape"),  # Yokohama Bay
    ("yokohama",                              "yokohama",  "scrape"),  # Yokohama Bay (seatemp canonical)
    ("york-harbor",                           "york-harbor",  "scrape"),  # York Harbor
    ("yorktown-beach",                        "yorktown",  "scrape"),  # Yorktown Beach
    ("yorktown",                              "yorktown",  "scrape"),  # Yorktown Beach (seatemp canonical)
    ("yukon-harbor",                          "yukon",  "scrape"),  # Yukon Harbor
    ("yukon",                                 "yukon",  "scrape"),  # Yukon Harbor (seatemp canonical)
    ("los-alamos-beach",                      "los-alamos",  "scrape"),  # los  alamos beach
    ("los-alamos",                            "los-alamos",  "scrape"),  # los  alamos beach (seatemp canonical)
    ("playa-colorado",                        "playa-colorado",  "scrape"),  # playa Colorado
    ("dinghy-beach",                          "8447930",  "noaa"),   # "Dinghy" Beach (1km to station)
    ("10th-street-beach-access",              "8735180",  "noaa"),   # 10th Street Beach Access (35km to station)
    ("13th-st-beach-access",                  "8735180",  "noaa"),   # 13th St Beach Access (33km to station)
    ("14th-street-beach",                     "8723214",  "noaa"),   # 14th Street Beach (7km to station)
    ("1st-beach",                             "8467150",  "noaa"),   # 1st Beach (40km to station)
    ("2222-beach",                            "9413450",  "noaa"),   # 2222 Beach (40km to station)
    ("2nd-beach",                             "8467150",  "noaa"),   # 2nd Beach (40km to station)
    ("3rd-beach",                             "8467150",  "noaa"),   # 3rd Beach (39km to station)
    ("49-black-sand-beach",                   "1617433",  "noaa"),   # 49 Black Sand Beach (13km to station)
    ("5-graves-beach",                        "1615680",  "noaa"),   # 5 Graves Beach (27km to station)
    ("6th-street-beach-access",               "8735180",  "noaa"),   # 6th Street Beach Access (36km to station)
    ("8th-avenue-south-street-end",           "9446484",  "noaa"),   # 8th Avenue South Street End (31km to station)
    ("beach-harbor-resort",                   "9087088",  "noaa"),   # @Beach Harbor Resort (31km to station)
    ("aardvark-beach",                        "9414523",  "noaa"),   # Aardvark Beach (14km to station)
    ("abalone-cove",                          "9410840",  "noaa"),   # Abalone Cove (32km to station)
    ("abbott-cove",                           "8573364",  "noaa"),   # Abbott Cove (23km to station)
    ("aberdeen-creek",                        "8575512",  "noaa"),   # Aberdeen Creek (6km to station)
    ("abino-bay",                             "9063020",  "noaa"),   # Abino Bay (16km to station)
    ("abraham-bay",                           "8656483",  "noaa"),   # Abraham Bay (35km to station)
    ("absecon-channel",                       "8534720",  "noaa"),   # Absecon Channel (3km to station)
    ("acabonack-harbor",                      "8510560",  "noaa"),   # Acabonack Harbor (15km to station)
    ("accretion-beach",                       "9014070",  "noaa"),   # Accretion Beach (38km to station)
    ("acheredin-bay",                         "9459450",  "noaa"),   # Acheredin Bay (22km to station)
    ("achilles-bay",                          "2695535",  "noaa"),   # Achilles Bay (3km to station)
    ("achilles-bay-beach",                    "2695535",  "noaa"),   # Achilles Bay Beach (3km to station)
    ("acre-creek",                            "8571421",  "noaa"),   # Acre Creek (27km to station)
    ("active-cove",                           "9449880",  "noaa"),   # Active Cove (27km to station)
    ("acton-cove",                            "8575512",  "noaa"),   # Acton Cove (2km to station)
    ("adams-anchorage",                       "9452210",  "noaa"),   # Adams Anchorage (25km to station)
    ("adams-point-beach",                     "8518979",  "noaa"),   # Adams Point Beach (32km to station)
    ("addies-creek",                          "8410140",  "noaa"),   # Addies Creek (23km to station)
    ("admiralty-cove",                        "9452210",  "noaa"),   # Admiralty Cove (16km to station)
    ("agamgik-bay",                           "9462620",  "noaa"),   # Agamgik Bay (13km to station)
    ("ahduck-bay",                            "9453220",  "noaa"),   # Ahduck Bay (7km to station)
    ("ahihi-bay",                             "1615680",  "noaa"),   # Ahihi Bay (30km to station)
    ("ahup-bay",                              "1615680",  "noaa"),   # Ahupū Bay (40km to station)
    ("ahup-iki-bay",                          "1615680",  "noaa"),   # Ahupū Iki Bay (40km to station)
    ("akahu-kaimu",                           "1617433",  "noaa"),   # Akahu Kaimu (17km to station)
    ("akhiok-bay",                            "9457804",  "noaa"),   # Akhiok Bay (7km to station)
    ("alabama-point-beach",                   "8729840",  "noaa"),   # Alabama Point Beach (36km to station)
    ("alan-davis-beach",                      "1612480",  "noaa"),   # Alan Davis Beach (20km to station)
    ("alan-sieroty-beach",                    "9415020",  "noaa"),   # Alan Sieroty Beach (17km to station)
    ("alava-bay",                             "9450460",  "noaa"),   # Alava Bay (33km to station)
    ("alazan-bay",                            "8776604",  "noaa"),   # Alazan Bay (12km to station)
    ("alberts-pond",                          "8760721",  "noaa"),   # Alberts Pond (3km to station)
    ("albion-cove",                           "9416841",  "noaa"),   # Albion Cove (35km to station)
    ("aldens-beach",                          "9099090",  "noaa"),   # Alden's Beach (25km to station)
    ("alder-cove",                            "8551910",  "noaa"),   # Alder Cove (16km to station)
    ("aldermans-cove",                        "8658120",  "noaa"),   # Aldermans Cove (28km to station)
    ("aleck-pond",                            "8570283",  "noaa"),   # Aleck Pond (4km to station)
    ("aleutkina-bay",                         "9451600",  "noaa"),   # Aleutkina Bay (6km to station)
    ("alewife-cove",                          "8461490",  "noaa"),   # Alewife Cove (6km to station)
    ("alewife-drain",                         "8510560",  "noaa"),   # Alewife Drain (40km to station)
    ("alexander-beach",                       "9449880",  "noaa"),   # Alexander Beach (27km to station)
    ("alexis-bay",                            "8760721",  "noaa"),   # Alexis Bay (18km to station)
    ("alhambra-beach",                        "8516945",  "noaa"),   # Alhambra Beach (30km to station)
    ("alice-cove",                            "9454050",  "noaa"),   # Alice Cove (14km to station)
    ("aliomanu-bay",                          "1611400",  "noaa"),   # Aliomanu Bay (24km to station)
    ("alitak-bay",                            "9457804",  "noaa"),   # Alitak Bay (8km to station)
    ("all-tides-cove",                        "8728690",  "noaa"),   # All Tides Cove (10km to station)
    ("allen-cove",                            "8413320",  "noaa"),   # Allen Cove (29km to station)
    ("allen-harbor",                          "8452944",  "noaa"),   # Allen Harbor (12km to station)
    ("allen-slough",                          "8656483",  "noaa"),   # Allen Slough (5km to station)
    ("allenhurst-beach-club",                 "8531680",  "noaa"),   # Allenhurst Beach Club (26km to station)
    ("allens-cove",                           "9063085",  "noaa"),   # Allens Cove (15km to station)
    ("allens-fresh-run",                      "8635027",  "noaa"),   # Allens Fresh Run (13km to station)
    ("alley-bay",                             "8411060",  "noaa"),   # Alley Bay (34km to station)
    ("alligator-bay",                         "8767816",  "noaa"),   # Alligator Bay (10km to station)
    ("alligator-bayou",                       "8729108",  "noaa"),   # Alligator Bayou (9km to station)
    ("alligator-bend",                        "8761305",  "noaa"),   # Alligator Bend (21km to station)
    ("alligator-creek",                       "8720219",  "noaa"),   # Alligator Creek (3km to station)
    ("allison-hagerup-beach",                 "8725520",  "noaa"),   # Allison Hagerup Beach (35km to station)
    ("allyns-bight",                          "8774770",  "noaa"),   # Allyns Bight (8km to station)
    ("allyns-lake",                           "8774770",  "noaa"),   # Allyns Lake (8km to station)
    ("almshouse-creek",                       "8575512",  "noaa"),   # Almshouse Creek (7km to station)
    ("alpine-cove",                           "9457804",  "noaa"),   # Alpine Cove (40km to station)
    ("alsea-bay",                             "9435380",  "noaa"),   # Alsea Bay (21km to station)
    ("altona-lagoon",                         "9751364",  "noaa"),   # Altona Lagoon (1km to station)
    ("altona-lagoon-beach",                   "9751364",  "noaa"),   # Altona Lagoon Beach (1km to station)
    ("alvord-beach",                          "8467150",  "noaa"),   # Alvord Beach (14km to station)
    ("amalga-harbor",                         "9452210",  "noaa"),   # Amalga Harbor (31km to station)
    ("amarada-cut",                           "8771972",  "noaa"),   # Amarada Cut (12km to station)
    ("amarillo-beach",                        "9410840",  "noaa"),   # Amarillo Beach (19km to station)
    ("amen-corner",                           "8571421",  "noaa"),   # Amen Corner (33km to station)
    ("american-bay",                          "8761305",  "noaa"),   # American Bay (35km to station)
    ("americas-cup-harbor",                   "9410170",  "noaa"),   # Americas Cup Harbor (5km to station)
    ("amherst-bay",                           "9052000",  "noaa"),   # Amherst Bay (32km to station)
    ("amityville-cut",                        "8516945",  "noaa"),   # Amityville Cut (36km to station)
    ("amtrak-beach",                          "8461490",  "noaa"),   # Amtrak Beach (9km to station)
    ("amugul-bay",                            "9462620",  "noaa"),   # Amugul Bay (18km to station)
    ("anaco-beach",                           "9449880",  "noaa"),   # Anaco Beach (26km to station)
    ("anaehoomalu-bay",                       "1617433",  "noaa"),   # Anaehoomalu Bay (15km to station)
    ("anaehoomalu-beach",                     "1617433",  "noaa"),   # Anaehoomalu Beach (15km to station)
    ("anapuka",                               "1617760",  "noaa"),   # Anapuka (6km to station)
    ("anchor-beach",                          "8465705",  "noaa"),   # Anchor Beach (10km to station)
    ("anchor-cove",                           "9457804",  "noaa"),   # Anchor Cove (25km to station)
    ("anclaje-isabela",                       "9759938",  "noaa"),   # Anclaje Isabela (1km to station)
    ("anclaje-sardinera",                     "9759938",  "noaa"),   # Anclaje Sardinera (0km to station)
    ("anclote-anchorage",                     "8726724",  "noaa"),   # Anclote Anchorage (24km to station)
    ("anderson-bay",                          "8760721",  "noaa"),   # Anderson Bay (39km to station)
    ("anderson-bayou",                        "8729108",  "noaa"),   # Anderson Bayou (11km to station)
    ("anderson-creek",                        "8571421",  "noaa"),   # Anderson Creek (25km to station)
    ("anderson-point-park-beach",             "9446484",  "noaa"),   # Anderson Point Park Beach (21km to station)
    ("andres-pond",                           "8760721",  "noaa"),   # Andres Pond (7km to station)
    ("andrews-beach",                         "8418150",  "noaa"),   # Andrews Beach (8km to station)
    ("andy-rosse-lane-beach",                 "8725520",  "noaa"),   # Andy Rosse Lane Beach (35km to station)
    ("angeline-cove",                         "8447386",  "noaa"),   # Angeline Cove (18km to station)
    ("angle-beach",                           "2695540",  "noaa"),   # Angle Beach (17km to station)
    ("anglin-bay",                            "9052000",  "noaa"),   # Anglin Bay (17km to station)
    ("anianik-cove",                          "1612340",  "noaa"),   # Anianikū Cove (28km to station)
    ("annaberg-beach",                        "9751381",  "noaa"),   # Annaberg Beach (5km to station)
    ("annadale-beach",                        "8531680",  "noaa"),   # Annadale Beach (15km to station)
    ("annaly-bay",                            "9751401",  "noaa"),   # Annaly Bay (13km to station)
    ("annes-beach",                           "8723970",  "noaa"),   # Anne's Beach (40km to station)
    ("annette-bay",                           "9450460",  "noaa"),   # Annette Bay (9km to station)
    ("annies-bay",                            "2695535",  "noaa"),   # Annie's Bay (4km to station)
    ("anns-cove",                             "8447930",  "noaa"),   # Anns Cove (18km to station)
    ("anza-lagoon",                           "9414523",  "noaa"),   # Anza Lagoon (15km to station)
    ("apache-beach",                          "8661070",  "noaa"),   # Apache Beach (17km to station)
    ("ape-hole-creek",                        "8571421",  "noaa"),   # Ape Hole Creek (35km to station)
    ("applegate-cove",                        "9459881",  "noaa"),   # Applegate Cove (38km to station)
    ("applegate-slough",                      "9459881",  "noaa"),   # Applegate Slough (37km to station)
    ("apponagansett-bay",                     "8447930",  "noaa"),   # Apponagansett Bay (23km to station)
    ("aquatic-cove",                          "9414290",  "noaa"),   # Aquatic Cove (4km to station)
    ("aransas-bay",                           "8774770",  "noaa"),   # Aransas Bay (6km to station)
    ("aransas-channel",                       "8775237",  "noaa"),   # Aransas Channel (2km to station)
    ("arcata-bay",                            "9418767",  "noaa"),   # Arcata Bay (10km to station)
    ("arena-cove",                            "9416841",  "noaa"),   # Arena Cove (0km to station)
    ("arey-cove",                             "8413320",  "noaa"),   # Arey Cove (14km to station)
    ("armstrong-bay",                         "8571892",  "noaa"),   # Armstrong Bay (18km to station)
    ("army-hole",                             "8773701",  "noaa"),   # Army Hole (16km to station)
    ("arroyo-de-los-frijoles-beach",          "9414523",  "noaa"),   # Arroyo De Los Frijoles Beach (36km to station)
    ("arthur-bay",                            "9087088",  "noaa"),   # Arthur Bay (28km to station)
    ("arthur-cove",                           "8635750",  "noaa"),   # Arthur Cove (35km to station)
    ("arundel-beach",                         "8419870",  "noaa"),   # Arundel Beach (37km to station)
    ("ash-point-cove",                        "8418150",  "noaa"),   # Ash Point Cove (20km to station)
    ("ashbee-harbor",                         "8652587",  "noaa"),   # Ashbee Harbor (14km to station)
    ("ashlar-pond",                           "8575512",  "noaa"),   # Ashlar Pond (16km to station)
    ("ashley-cove",                           "8635750",  "noaa"),   # Ashley Cove (39km to station)
    ("ashmun-bay",                            "9076070",  "noaa"),   # Ashmun Bay (1km to station)
    ("asilomar-state-beach",                  "9413450",  "noaa"),   # Asilomar State Beach (5km to station)
    ("asquith-creek",                         "8575512",  "noaa"),   # Asquith Creek (7km to station)
    ("assawoman-inlet",                       "8631044",  "noaa"),   # Assawoman Inlet (29km to station)
    ("assonet-bay",                           "8447386",  "noaa"),   # Assonet Bay (12km to station)
    ("astrolabe-bay",                         "9452634",  "noaa"),   # Astrolabe Bay (38km to station)
    ("atchafalaya-bay",                       "8764227",  "noaa"),   # Atchafalaya Bay (6km to station)
    ("atkins-bay",                            "8418150",  "noaa"),   # Atkins Bay (38km to station)
    ("atlantic-beach",                        "8516945",  "noaa"),   # Atlantic Beach (25km to station)
    ("atlantic-highlands-yacht-harbor",       "8531680",  "noaa"),   # Atlantic Highlands Yacht Harbor (6km to station)
    ("attawan-beach",                         "8461490",  "noaa"),   # Attawan Beach (12km to station)
    ("atwells-cove",                          "8571892",  "noaa"),   # Atwells Cove (12km to station)
    ("aucoot-cove",                           "8447930",  "noaa"),   # Aucoot Cove (18km to station)
    ("auke-bay",                              "9452210",  "noaa"),   # Auke Bay (17km to station)
    ("auke-nu-cove",                          "9452210",  "noaa"),   # Auke Nu Cove (19km to station)
    ("aunt-janes-bay",                        "8311062",  "noaa"),   # Aunt Janes Bay (15km to station)
    ("aunt-lydias-cove",                      "8447435",  "noaa"),   # Aunt Lydias Cove (0km to station)
    ("aurora-19-public-beach-access",         "8779748",  "noaa"),   # Aurora 19 Public Beach Access (6km to station)
    ("austin-hollow",                         "8452660",  "noaa"),   # Austin Hollow (7km to station)
    ("austrailia-beach",                      "8461490",  "noaa"),   # Austrailia Beach (11km to station)
    ("avery-point-beach",                     "8461490",  "noaa"),   # Avery Point Beach (6km to station)
    ("awakee-bay",                            "1617433",  "noaa"),   # Awakee Bay (33km to station)
    ("ayres-bay",                             "8774230",  "noaa"),   # Ayres Bay (5km to station)
    ("babcock-cove",                          "8461490",  "noaa"),   # Babcock Cove (23km to station)
    ("back-bay",                              "9076070",  "noaa"),   # Back Bay (19km to station)
    ("back-bay-of-biloxi",                    "8741533",  "noaa"),   # Back Bay of Biloxi (33km to station)
    ("back-beach",                            "8410140",  "noaa"),   # Back Beach (26km to station)
    ("back-cove",                             "8631044",  "noaa"),   # Back Cove (33km to station)
    ("back-creek",                            "8571421",  "noaa"),   # Back Creek (20km to station)
    ("back-river-beach",                      "8670870",  "noaa"),   # Back River Beach (7km to station)
    ("back-sound",                            "8656483",  "noaa"),   # Back Sound (10km to station)
    ("back-oth-sound",                        "8536110",  "noaa"),   # Back o'th' Sound (22km to station)
    ("backefall-bay",                         "9752235",  "noaa"),   # Backefall Bay (31km to station)
    ("bagwell-cove",                          "8631044",  "noaa"),   # Bagwell Cove (26km to station)
    ("bahama-beach",                          "8726520",  "noaa"),   # Bahama Beach (5km to station)
    ("baha-algodones",                        "9753216",  "noaa"),   # Bahía Algodones (18km to station)
    ("baha-bramadero",                        "9759394",  "noaa"),   # Bahía Bramadero (8km to station)
    ("baha-corcho",                           "9752695",  "noaa"),   # Bahía Corcho (6km to station)
    ("baha-demajagua",                        "9753216",  "noaa"),   # Bahía Demajagua (5km to station)
    ("baha-fanduca",                          "9752695",  "noaa"),   # Bahía Fanduca (14km to station)
    ("baha-flamenco",                         "9752235",  "noaa"),   # Bahía Flamenco (4km to station)
    ("baha-fosforescnte",                     "9759110",  "noaa"),   # Bahía Fosforescénte (3km to station)
    ("baha-guayanilla",                       "9759110",  "noaa"),   # Bahía Guayanilla (29km to station)
    ("baha-icacos",                           "9752235",  "noaa"),   # Bahía Icacos (18km to station)
    ("baha-jalova",                           "9752695",  "noaa"),   # Bahía Jalova (15km to station)
    ("baha-lima",                             "9753216",  "noaa"),   # Bahía Lima (18km to station)
    ("baha-linda",                            "9752235",  "noaa"),   # Bahía Linda (0km to station)
    ("baha-montalva",                         "9759110",  "noaa"),   # Bahía Montalva (6km to station)
    ("baha-mosquito",                         "9752235",  "noaa"),   # Bahía Mosquito (4km to station)
    ("baha-noroeste",                         "9759110",  "noaa"),   # Bahía Noroeste (13km to station)
    ("baha-playa-blanca",                     "9752235",  "noaa"),   # Bahía Playa Blanca (18km to station)
    ("baha-salina-del-sur",                   "9752695",  "noaa"),   # Bahía Salina del Sur (18km to station)
    ("baha-salinas",                          "9752235",  "noaa"),   # Bahía Salinas (17km to station)
    ("baha-sucia",                            "9759110",  "noaa"),   # Bahía Sucia (14km to station)
    ("baha-tallaboa",                         "9759110",  "noaa"),   # Bahía Tallaboa (33km to station)
    ("baha-tamarindo",                        "9752235",  "noaa"),   # Bahía Tamarindo (3km to station)
    ("baha-tapn",                             "9752695",  "noaa"),   # Bahía Tapón (7km to station)
    ("baha-tarja",                            "9752235",  "noaa"),   # Bahía Tarja (1km to station)
    ("baha-yoye",                             "9752695",  "noaa"),   # Bahía Yoye (14km to station)
    ("baha-de-aguadilla",                     "9759394",  "noaa"),   # Bahía de Aguadilla (24km to station)
    ("baha-de-almodvar",                      "9752235",  "noaa"),   # Bahía de Almodóvar (5km to station)
    ("baha-de-aasco",                         "9759394",  "noaa"),   # Bahía de Añasco (8km to station)
    ("baha-de-boquern",                       "9759110",  "noaa"),   # Bahía de Boquerón (16km to station)
    ("baha-de-fajardo",                       "9753216",  "noaa"),   # Bahía de Fajardo (1km to station)
    ("baha-de-gunica",                        "9759110",  "noaa"),   # Bahía de Guánica (18km to station)
    ("baha-de-marejada",                      "9752235",  "noaa"),   # Bahía de Marejada (4km to station)
    ("baha-de-mulas",                         "9752695",  "noaa"),   # Bahía de Mulas (7km to station)
    ("baha-de-oleaje",                        "9752235",  "noaa"),   # Bahía de Oleaje (4km to station)
    ("baha-de-puerca",                        "9753216",  "noaa"),   # Bahía de Puerca (13km to station)
    ("baha-de-puerto-nuevo",                  "9755371",  "noaa"),   # Bahía de Puerto Nuevo (3km to station)
    ("baha-de-san-juan",                      "9755371",  "noaa"),   # Bahía de San Juan (2km to station)
    ("baha-de-sardinas",                      "9752235",  "noaa"),   # Bahía de Sardinas (0km to station)
    ("baha-de-toa",                           "9755371",  "noaa"),   # Bahía de Toa (8km to station)
    ("baha-de-la-ballena",                    "9759110",  "noaa"),   # Bahía de la Ballena (20km to station)
    ("baha-de-la-chiva",                      "9752695",  "noaa"),   # Bahía de la Chiva (9km to station)
    ("baha-las-cabezas",                      "9753216",  "noaa"),   # Bahía las Cabezas (5km to station)
    ("baie-chevreuil",                        "8762482",  "noaa"),   # Baie Chevreuil (21km to station)
    ("baie-des-deux-chenes",                  "8762482",  "noaa"),   # Baie Des Deux Chenes (14km to station)
    ("baie-a-carlin",                         "8762482",  "noaa"),   # Baie a Carlin (26km to station)
    ("baie-den-haut",                         "8762482",  "noaa"),   # Baie d'en Haut (25km to station)
    ("baie-de-wasai",                         "9076033",  "noaa"),   # Baie de Wasai (5km to station)
    ("bailey-beach",                          "8452660",  "noaa"),   # Bailey Beach (5km to station)
    ("baileys-bay",                           "2695540",  "noaa"),   # Bailey's Bay (3km to station)
    ("baileys-lower-cove",                    "8454000",  "noaa"),   # Baileys Lower Cove (4km to station)
    ("baileys-upper-cove",                    "8454000",  "noaa"),   # Baileys Upper Cove (4km to station)
    ("bairs-cove",                            "8721604",  "noaa"),   # Bairs Cove (39km to station)
    ("bajo-snapper",                          "9752235",  "noaa"),   # Bajo Snapper (4km to station)
    ("baker-cove",                            "8461490",  "noaa"),   # Baker Cove (6km to station)
    ("bald-beach",                            "8654467",  "noaa"),   # Bald Beach (30km to station)
    ("bald-head-cove",                        "8418150",  "noaa"),   # Bald Head Cove (33km to station)
    ("bald-headed-cove",                      "9450460",  "noaa"),   # Bald Headed Cove (2km to station)
    ("bald-hill-bay",                         "8656483",  "noaa"),   # Bald Hill Bay (10km to station)
    ("baldwin-bay",                           "8516945",  "noaa"),   # Baldwin Bay (25km to station)
    ("baldwin-beach",                         "1615680",  "noaa"),   # Baldwin Beach (8km to station)
    ("baldwin-town-beach",                    "8418150",  "noaa"),   # Baldwin Town Beach (39km to station)
    ("ballast-bay",                           "8651370",  "noaa"),   # Ballast Bay (10km to station)
    ("ballast-island-ledge",                  "8411060",  "noaa"),   # Ballast Island Ledge (29km to station)
    ("ballena-bay",                           "9414750",  "noaa"),   # Ballena Bay (2km to station)
    ("balls-cove",                            "8452660",  "noaa"),   # Balls Cove (38km to station)
    ("balls-creek",                           "8571892",  "noaa"),   # Balls Creek (25km to station)
    ("ballys-legends-vip-beach",              "8534720",  "noaa"),   # Bally's Legend’s VIP Beach (1km to station)
    ("balneario-caa-gorda",                   "9759110",  "noaa"),   # Balneario Caña Gorda (17km to station)
    ("balneario-cerro-gordo",                 "9755371",  "noaa"),   # Balneario Cerro Gordo (24km to station)
    ("balneario-crash-boat",                  "9759394",  "noaa"),   # Balneario Crash Boat (27km to station)
    ("balneario-el-escambrn",                 "9755371",  "noaa"),   # Balneario El Escambrón (3km to station)
    ("balneario-el-escambrn-ii",              "9755371",  "noaa"),   # Balneario El Escambrón II (3km to station)
    ("balneario-la-monseratte",               "9753216",  "noaa"),   # Balneario La Monseratte (12km to station)
    ("balneario-pico-de-piedra",              "9759394",  "noaa"),   # Balneario Pico de Piedra (19km to station)
    ("balneario-puerto-nuevo",                "9755371",  "noaa"),   # Balneario Puerto Nuevo (30km to station)
    ("balneario-punta-santiago",              "9753216",  "noaa"),   # Balneario Punta Santiago (24km to station)
    ("balneario-seven-seas",                  "9753216",  "noaa"),   # Balneario Seven Seas (4km to station)
    ("balneario-sunbay",                      "9752695",  "noaa"),   # Balneario Sunbay (1km to station)
    ("balneario-tres-hermanos",               "9759394",  "noaa"),   # Balneario Tres Hermanos (9km to station)
    ("balneario-de-boquern",                  "9759110",  "noaa"),   # Balneario de Boquerón (14km to station)
    ("balneario-de-carolina",                 "9755371",  "noaa"),   # Balneario de Carolina (12km to station)
    ("balneario-de-rincn",                    "9759394",  "noaa"),   # Balneario de Rincón (17km to station)
    ("bamageseck-bay",                        "9076024",  "noaa"),   # Bamageseck Bay (18km to station)
    ("banana-bay",                            "9751381",  "noaa"),   # Banana Bay (23km to station)
    ("banjo-cove",                            "8418150",  "noaa"),   # Banjo Cove (26km to station)
    ("bankhead-cove",                         "8635027",  "noaa"),   # Bankhead Cove (20km to station)
    ("bannister-bay",                         "8516945",  "noaa"),   # Bannister Bay (23km to station)
    ("bar-channel",                           "9414750",  "noaa"),   # Bar Channel (6km to station)
    ("baralof-bay",                           "9459450",  "noaa"),   # Baralof Bay (11km to station)
    ("barataria-bay",                         "8761724",  "noaa"),   # Barataria Bay (12km to station)
    ("barbadoes-basin",                       "8518750",  "noaa"),   # Barbadoes Basin (21km to station)
    ("barbara-road-beach",                    "8454000",  "noaa"),   # Barbara Road Beach (19km to station)
    ("barbers-basin",                         "8551910",  "noaa"),   # Barber's Basin (8km to station)
    ("barcelona-bay",                         "8735180",  "noaa"),   # Barcelona Bay (2km to station)
    ("bare-cove",                             "8411060",  "noaa"),   # Bare Cove (18km to station)
    ("bare-neck-shore",                       "8575512",  "noaa"),   # Bare Neck Shore (15km to station)
    ("bare-sand-beach",                       "8656483",  "noaa"),   # Bare Sand Beach (18km to station)
    ("baremore-quarters",                     "8534720",  "noaa"),   # Baremore Quarters (7km to station)
    ("barents-bay",                           "9752235",  "noaa"),   # Barents Bay (29km to station)
    ("barges-beach",                          "8447930",  "noaa"),   # Barges Beach (23km to station)
    ("barker-cove",                           "8447386",  "noaa"),   # Barker Cove (26km to station)
    ("barleyfield-cove",                      "8461490",  "noaa"),   # Barleyfield Cove (16km to station)
    ("barlow-cove",                           "9452210",  "noaa"),   # Barlow Cove (29km to station)
    ("barlows-landing-beach",                 "8447930",  "noaa"),   # Barlow's Landing Beach (19km to station)
    ("barn-cove",                             "8635027",  "noaa"),   # Barn Cove (16km to station)
    ("barnes-cove",                           "8577330",  "noaa"),   # Barnes Cove (18km to station)
    ("barnetts-cove",                         "9063079",  "noaa"),   # Barnett's Cove (16km to station)
    ("barrs-bay",                             "2695540",  "noaa"),   # Barr's Bay (12km to station)
    ("barren-island-gap",                     "8577330",  "noaa"),   # Barren Island Gap (17km to station)
    ("barren-island-thorofare",               "8577330",  "noaa"),   # Barren Island Thorofare (17km to station)
    ("barrett-bay",                           "9052000",  "noaa"),   # Barrett Bay (11km to station)
    ("barretto-cove",                         "8516945",  "noaa"),   # Barretto Cove (10km to station)
    ("barretts-bay",                          "9052000",  "noaa"),   # Barretts Bay (33km to station)
    ("barries-bay",                           "9415020",  "noaa"),   # Barries Bay (6km to station)
    ("barrow-slough",                         "8770808",  "noaa"),   # Barrow Slough (33km to station)
    ("bartlett-cove",                         "9452634",  "noaa"),   # Bartlett Cove (39km to station)
    ("bartletts-cove",                        "8419870",  "noaa"),   # Bartlett's Cove (31km to station)
    ("basin-cove",                            "8418150",  "noaa"),   # Basin Cove (21km to station)
    ("basin-harbor",                          "9052000",  "noaa"),   # Basin Harbor (9km to station)
    ("bass-cove",                             "8447930",  "noaa"),   # Bass Cove (22km to station)
    ("bass-creek",                            "8447930",  "noaa"),   # Bass Creek (22km to station)
    ("bass-harbor",                           "8534720",  "noaa"),   # Bass Harbor (15km to station)
    ("bass-hole-cove",                        "8729840",  "noaa"),   # Bass Hole Cove (20km to station)
    ("bassa-bassa-bay",                       "8761724",  "noaa"),   # Bassa Bassa Bay (11km to station)
    ("basses-bay",                            "8534720",  "noaa"),   # Basses Bay (22km to station)
    ("bastendorff-beach",                     "9432780",  "noaa"),   # Bastendorff Beach (2km to station)
    ("bastian-bay",                           "8761724",  "noaa"),   # Bastian Bay (30km to station)
    ("bastian-lake",                          "8760721",  "noaa"),   # Bastian Lake (10km to station)
    ("bastrop-bay",                           "8771972",  "noaa"),   # Bastrop Bay (6km to station)
    ("bathing-beach",                         "8418150",  "noaa"),   # Bathing Beach (4km to station)
    ("bathing-beach-park",                    "9075014",  "noaa"),   # Bathing Beach Park (1km to station)
    ("battersea-bay",                         "9052000",  "noaa"),   # Battersea Bay (35km to station)
    ("battle-beach",                          "8410140",  "noaa"),   # Battle Beach (37km to station)
    ("battle-ground-bay",                     "8761305",  "noaa"),   # Battle Ground Bay (32km to station)
    ("battleship-cove",                       "8447386",  "noaa"),   # Battleship Cove (0km to station)
    ("baum-bay",                              "8651370",  "noaa"),   # Baum Bay (20km to station)
    ("baxter-estates-village-beach",          "8516945",  "noaa"),   # Baxter Estates Village Beach (6km to station)
    ("bay-banan",                             "8764314",  "noaa"),   # Bay Banan (39km to station)
    ("bay-batiste",                           "8761724",  "noaa"),   # Bay Batiste (24km to station)
    ("bay-beach",                             "9063020",  "noaa"),   # Bay Beach (16km to station)
    ("bay-boudreau",                          "8761305",  "noaa"),   # Bay Boudreau (33km to station)
    ("bay-carrion-crow",                      "8760721",  "noaa"),   # Bay Carrion Crow (21km to station)
    ("bay-castagnier",                        "8764314",  "noaa"),   # Bay Castagnier (26km to station)
    ("bay-chaland",                           "8761724",  "noaa"),   # Bay Chaland (22km to station)
    ("bay-chalon",                            "8760721",  "noaa"),   # Bay Chalon (9km to station)
    ("bay-cheniere-ronquille",                "8761724",  "noaa"),   # Bay Cheniere Ronquille (14km to station)
    ("bay-cheri",                             "8761724",  "noaa"),   # Bay Cheri (35km to station)
    ("bay-colony-dog-beach",                  "8639348",  "noaa"),   # Bay Colony Dog Beach (28km to station)
    ("bay-coquette",                          "8760721",  "noaa"),   # Bay Coquette (25km to station)
    ("bay-crabe",                             "8761305",  "noaa"),   # Bay Crabe (35km to station)
    ("bay-crapaud",                           "8760721",  "noaa"),   # Bay Crapaud (30km to station)
    ("bay-creek",                             "8570283",  "noaa"),   # Bay Creek (32km to station)
    ("bay-des-ilettes",                       "8761724",  "noaa"),   # Bay Des Ilettes (5km to station)
    ("bay-desespere",                         "8761724",  "noaa"),   # Bay Desespere (13km to station)
    ("bay-dispute",                           "8761724",  "noaa"),   # Bay Dispute (10km to station)
    ("bay-gardene",                           "8761305",  "noaa"),   # Bay Gardene (31km to station)
    ("bay-grass",                             "8737048",  "noaa"),   # Bay Grass (4km to station)
    ("bay-heron",                             "8764044",  "noaa"),   # Bay Heron (25km to station)
    ("bay-jaune",                             "8761305",  "noaa"),   # Bay Jaune (30km to station)
    ("bay-jimmy",                             "8761724",  "noaa"),   # Bay Jimmy (22km to station)
    ("bay-john",                              "8737048",  "noaa"),   # Bay John (10km to station)
    ("bay-joyeux",                            "8761724",  "noaa"),   # Bay Joyeux (8km to station)
    ("bay-junop",                             "8764314",  "noaa"),   # Bay Junop (36km to station)
    ("bay-la-fourche",                        "8761305",  "noaa"),   # Bay La Fourche (28km to station)
    ("bay-la-mer",                            "8761724",  "noaa"),   # Bay La Mer (18km to station)
    ("bay-laurent",                           "8762482",  "noaa"),   # Bay Laurent (8km to station)
    ("bay-law",                               "8761305",  "noaa"),   # Bay Law (34km to station)
    ("bay-lizette",                           "8761724",  "noaa"),   # Bay Lizette (14km to station)
    ("bay-long",                              "8761724",  "noaa"),   # Bay Long (16km to station)
    ("bay-macoin",                            "8760721",  "noaa"),   # Bay Macoin (12km to station)
    ("bay-marcalite",                         "8764044",  "noaa"),   # Bay Marcalite (26km to station)
    ("bay-marchand",                          "8761724",  "noaa"),   # Bay Marchand (31km to station)
    ("bay-melville",                          "8761724",  "noaa"),   # Bay Melville (8km to station)
    ("bay-minette",                           "8737048",  "noaa"),   # Bay Minette (12km to station)
    ("bay-natchez",                           "8764044",  "noaa"),   # Bay Natchez (38km to station)
    ("bay-pomme-dor",                         "8760721",  "noaa"),   # Bay Pomme d'or (34km to station)
    ("bay-ridge-beach",                       "8575512",  "noaa"),   # Bay Ridge Beach (5km to station)
    ("bay-rondo",                             "8760721",  "noaa"),   # Bay Rondo (7km to station)
    ("bay-ronfleur",                          "8760721",  "noaa"),   # Bay Ronfleur (13km to station)
    ("bay-ronquille",                         "8761724",  "noaa"),   # Bay Ronquille (13km to station)
    ("bay-saint-honore",                      "8760721",  "noaa"),   # Bay Saint Honore (11km to station)
    ("bay-san-blas",                          "8728690",  "noaa"),   # Bay San Blas (31km to station)
    ("bay-sherman",                           "8764044",  "noaa"),   # Bay Sherman (20km to station)
    ("bay-street-end",                        "9446484",  "noaa"),   # Bay Street End (39km to station)
    ("bay-sylvester",                         "8764044",  "noaa"),   # Bay Sylvester (26km to station)
    ("bay-tambour",                           "8761724",  "noaa"),   # Bay Tambour (10km to station)
    ("bay-vasier",                            "8761724",  "noaa"),   # Bay Vasier (16km to station)
    ("bay-view-street-beach",                 "8447435",  "noaa"),   # Bay View Street Beach (27km to station)
    ("bay-wallace",                           "8764044",  "noaa"),   # Bay Wallace (24km to station)
    ("bay-of-river-aux-chenes",               "8761305",  "noaa"),   # Bay of River Aux Chenes (26km to station)
    ("bayboro-harbor",                        "8726520",  "noaa"),   # Bayboro Harbor (0km to station)
    ("baye-de-grigri",                        "9751381",  "noaa"),   # Baye de Grigri (24km to station)
    ("bayley-beach",                          "8467150",  "noaa"),   # Bayley Beach (25km to station)
    ("bayou-aloe",                            "8735180",  "noaa"),   # Bayou Aloe (5km to station)
    ("bayou-bubie",                           "8741533",  "noaa"),   # Bayou Bubie (20km to station)
    ("bayou-caddy",                           "8741533",  "noaa"),   # Bayou Caddy (22km to station)
    ("bayou-garcon",                          "8729840",  "noaa"),   # Bayou Garcon (23km to station)
    ("bayou-george",                          "8729108",  "noaa"),   # Bayou George (19km to station)
    ("bayou-grande",                          "8729840",  "noaa"),   # Bayou Grande (9km to station)
    ("bayou-jack-bend",                       "8760721",  "noaa"),   # Bayou Jack Bend (40km to station)
    ("bayou-la-fourche-bay",                  "8741533",  "noaa"),   # Bayou La Fourche Bay (19km to station)
    ("bayou-lasseigne",                       "8762482",  "noaa"),   # Bayou Lasseigne (25km to station)
    ("bayou-marcus",                          "8729840",  "noaa"),   # Bayou Marcus (12km to station)
    ("bayou-sale-bay",                        "8764227",  "noaa"),   # Bayou Sale Bay (22km to station)
    ("bayou-second",                          "8735180",  "noaa"),   # Bayou Second (6km to station)
    ("bayville-gut",                          "8570283",  "noaa"),   # Bayville Gut (17km to station)
    ("bazzard-bay",                           "8637689",  "noaa"),   # Bazzard Bay (34km to station)
    ("beach-3",                               "9442396",  "noaa"),   # Beach 3 (36km to station)
    ("beach-potawatomi-state-park",           "9087088",  "noaa"),   # Beach @ Potawatomi State Park (29km to station)
    ("beach-area",                            "8725520",  "noaa"),   # Beach Area (19km to station)
    ("beach-b",                               "8531680",  "noaa"),   # Beach B (7km to station)
    ("beach-c",                               "8531680",  "noaa"),   # Beach C (6km to station)
    ("beach-cove",                            "8557380",  "noaa"),   # Beach Cove (22km to station)
    ("beach-creek",                           "8651370",  "noaa"),   # Beach Creek (7km to station)
    ("beach-d",                               "8531680",  "noaa"),   # Beach D (5km to station)
    ("beach-e",                               "8531680",  "noaa"),   # Beach E (5km to station)
    ("beach-haven-west-bay-beach",            "8534720",  "noaa"),   # Beach Haven West Bay Beach (38km to station)
    ("beachkayak-launch-ramp",                "8518750",  "noaa"),   # Beach/Kayak launch ramp (2km to station)
    ("beacon-bay",                            "8573364",  "noaa"),   # Beacon Bay (12km to station)
    ("beacon-hill-residences-beach",          "8516945",  "noaa"),   # Beacon Hill Residences Beach (9km to station)
    ("beadon-cove",                           "8537121",  "noaa"),   # Beadon Cove (18km to station)
    ("beals-cove",                            "8418150",  "noaa"),   # Beals Cove (24km to station)
    ("beals-harbor",                          "8411060",  "noaa"),   # Beals Harbor (31km to station)
    ("bean-hollow-state-beach",               "9414523",  "noaa"),   # Bean Hollow State Beach (34km to station)
    ("bear-bay",                              "9459881",  "noaa"),   # Bear Bay (24km to station)
    ("bear-cove",                             "9451600",  "noaa"),   # Bear Cove (12km to station)
    ("bear-creek",                            "8574680",  "noaa"),   # Bear Creek (9km to station)
    ("bear-harbor",                           "9451054",  "noaa"),   # Bear Harbor (33km to station)
    ("bear-neck-creek",                       "8575512",  "noaa"),   # Bear Neck Creek (10km to station)
    ("beards-creek",                          "8575512",  "noaa"),   # Beards Creek (9km to station)
    ("bearinda-cove",                         "9415102",  "noaa"),   # Bearinda Cove (13km to station)
    ("beartrap-bay",                          "9454050",  "noaa"),   # Beartrap Bay (27km to station)
    ("beasley-bay",                           "8631044",  "noaa"),   # Beasley Bay (29km to station)
    ("beatty-bayou",                          "8729108",  "noaa"),   # Beatty Bayou (12km to station)
    ("beaumont-reserve-fleet",                "8770475",  "noaa"),   # Beaumont Reserve Fleet (18km to station)
    ("beaumont-reserve-fleet-small-craft-basin", "8770475",  "noaa"),   # Beaumont Reserve Fleet Small Craft Basin (20km to station)
    ("beauregard-bay",                        "9751364",  "noaa"),   # Beauregard Bay (2km to station)
    ("beaver-beach",                          "9455920",  "noaa"),   # Beaver Beach (30km to station)
    ("beaver-cove",                           "9446484",  "noaa"),   # Beaver Cove (18km to station)
    ("beaver-hole",                           "8570283",  "noaa"),   # Beaver Hole (25km to station)
    ("beaver-inlet",                          "9462620",  "noaa"),   # Beaver Inlet (16km to station)
    ("beaver-landing",                        "8594900",  "noaa"),   # Beaver Landing (40km to station)
    ("beaver-tail-bay",                       "9075099",  "noaa"),   # Beaver Tail Bay (21km to station)
    ("bebe-beach",                            "9075065",  "noaa"),   # Bebe Beach (15km to station)
    ("beckwith-creek",                        "8571892",  "noaa"),   # Beckwith Creek (12km to station)
    ("beebe-cove",                            "8461490",  "noaa"),   # Beebe Cove (10km to station)
    ("beehive-cove",                          "8574680",  "noaa"),   # Beehive Cove (13km to station)
    ("beekman-beach",                         "8516945",  "noaa"),   # Beekman Beach (20km to station)
    ("beer-can-beach",                        "9413450",  "noaa"),   # Beer Can Beach (38km to station)
    ("beesleys-point-beach",                  "8534720",  "noaa"),   # Beesley's Point Beach (20km to station)
    ("bel-pass-bay",                          "8761305",  "noaa"),   # Bel Pass Bay (38km to station)
    ("belcamp-beach",                         "8573364",  "noaa"),   # Belcamp Beach (28km to station)
    ("belcher-cove",                          "8452944",  "noaa"),   # Belcher Cove (6km to station)
    ("belkofski-bay",                         "9459881",  "noaa"),   # Belkofski Bay (13km to station)
    ("bell-pond",                             "8760721",  "noaa"),   # Bell Pond (11km to station)
    ("bella-vista-bay",                       "8722956",  "noaa"),   # Bella Vista Bay (17km to station)
    ("bells-cove",                            "8574680",  "noaa"),   # Bells Cove (10km to station)
    ("bells-creek",                           "8635750",  "noaa"),   # Bells Creek (31km to station)
    ("bells-oyster-gut",                      "8638610",  "noaa"),   # Bells Oyster Gut (19km to station)
    ("bellville-bay",                         "8729840",  "noaa"),   # Bellville Bay (29km to station)
    ("belvedero-beach",                       "8531680",  "noaa"),   # Belvedero Beach (11km to station)
    ("belvidere-bay",                         "9014070",  "noaa"),   # Belvidere Bay (22km to station)
    ("ben-green-bight",                       "9459450",  "noaa"),   # Ben Green Bight (6km to station)
    ("benedict-outside-pond",                 "8760721",  "noaa"),   # Benedict Outside Pond (12km to station)
    ("benner-bay",                            "9751381",  "noaa"),   # Benner Bay (15km to station)
    ("bennet-cove",                           "8413320",  "noaa"),   # Bennet Cove (20km to station)
    ("bennett-beach",                         "9063020",  "noaa"),   # Bennett Beach (28km to station)
    ("benneys-bay",                           "8760721",  "noaa"),   # Benneys Bay (14km to station)
    ("bennie-pond",                           "8760721",  "noaa"),   # Bennie Pond (4km to station)
    ("bennies-pond",                          "8760721",  "noaa"),   # Bennies Pond (12km to station)
    ("bent-cove",                             "9459881",  "noaa"),   # Bent Cove (21km to station)
    ("bentley-cove",                          "8571421",  "noaa"),   # Bentley Cove (14km to station)
    ("berean-park-beach",                     "8518962",  "noaa"),   # Berean Park Beach (33km to station)
    ("bergen-basin",                          "8518750",  "noaa"),   # Bergen Basin (17km to station)
    ("berkeley-yacht-harbor",                 "9414863",  "noaa"),   # Berkeley Yacht Harbor (10km to station)
    ("berry-bay",                             "8767816",  "noaa"),   # Berry Bay (10km to station)
    ("berry-cove",                            "8413320",  "noaa"),   # Berry Cove (12km to station)
    ("bertie-bay",                            "9063020",  "noaa"),   # Bertie Bay (6km to station)
    ("berwick-bay",                           "8764044",  "noaa"),   # Berwick Bay (4km to station)
    ("beshta-bay",                            "9455760",  "noaa"),   # Beshta Bay (39km to station)
    ("bessemer-beach",                        "9410170",  "noaa"),   # Bessemer Beach (5km to station)
    ("betterton-beach",                       "8573364",  "noaa"),   # Betterton Beach (24km to station)
    ("betty-hole-cove",                       "8658120",  "noaa"),   # Betty Hole Cove (31km to station)
    ("bettys-cove",                           "8577330",  "noaa"),   # Bettys Cove (14km to station)
    ("beulah-park-beach",                     "9063063",  "noaa"),   # Beulah Park Beach (7km to station)
    ("biemillers-cove",                       "9063079",  "noaa"),   # Biemiller's Cove (9km to station)
    ("bienvenue-inside-pond",                 "8760721",  "noaa"),   # Bienvenue Inside Pond (14km to station)
    ("bienvenue-outside-pond",                "8760721",  "noaa"),   # Bienvenue Outside Pond (16km to station)
    ("bienville-beach",                       "8735180",  "noaa"),   # Bienville Beach (5km to station)
    ("big-bass-bay",                          "8311062",  "noaa"),   # Big Bass Bay (19km to station)
    ("big-bateau-bay",                        "8737048",  "noaa"),   # Big Bateau Bay (9km to station)
    ("big-bayou",                             "8726520",  "noaa"),   # Big Bayou (2km to station)
    ("big-beach",                             "8413320",  "noaa"),   # Big Beach (34km to station)
    ("big-bend",                              "8639348",  "noaa"),   # Big Bend (32km to station)
    ("big-branch-bay",                        "9451054",  "noaa"),   # Big Branch Bay (16km to station)
    ("big-break",                             "9415144",  "noaa"),   # Big Break (29km to station)
    ("big-burley-cove",                       "8574680",  "noaa"),   # Big Burley Cove (13km to station)
    ("big-carlos-bay",                        "8725520",  "noaa"),   # Big Carlos Bay (28km to station)
    ("big-cleaninghole",                      "9751381",  "noaa"),   # Big Cleaninghole (22km to station)
    ("big-cove",                              "8557380",  "noaa"),   # Big Cove (24km to station)
    ("big-creek-arm",                         "9432780",  "noaa"),   # Big Creek Arm (32km to station)
    ("big-dome-cove",                         "9413450",  "noaa"),   # Big Dome Cove (11km to station)
    ("big-eddy",                              "8729840",  "noaa"),   # Big Eddy (36km to station)
    ("big-eddy-hole",                         "9455760",  "noaa"),   # Big Eddy Hole (26km to station)
    ("big-elmgrove-bayou",                    "8771341",  "noaa"),   # Big Elmgrove Bayou (13km to station)
    ("big-gut",                               "8656483",  "noaa"),   # Big Gut (34km to station)
    ("big-hickory-bay",                       "8725520",  "noaa"),   # Big Hickory Bay (32km to station)
    ("big-holly-cove",                        "8411060",  "noaa"),   # Big Holly Cove (6km to station)
    ("big-lake",                              "8747437",  "noaa"),   # Big Lake (34km to station)
    ("big-muscamoot-bay",                     "9014070",  "noaa"),   # Big Muscamoot Bay (13km to station)
    ("big-pocket",                            "8773701",  "noaa"),   # Big Pocket (10km to station)
    ("big-pond",                              "8760721",  "noaa"),   # Big Pond (6km to station)
    ("big-port-walter",                       "9451054",  "noaa"),   # Big Port Walter (16km to station)
    ("big-rock-beach",                        "9410840",  "noaa"),   # Big Rock Beach (12km to station)
    ("big-sand-bay",                          "9063085",  "noaa"),   # Big Sand Bay (26km to station)
    ("big-sandy-bay",                         "9052000",  "noaa"),   # Big Sandy Bay (10km to station)
    ("big-shoal-beach",                       "9075099",  "noaa"),   # Big Shoal Beach (24km to station)
    ("big-shoal-cove",                        "9075099",  "noaa"),   # Big Shoal Cove (23km to station)
    ("big-stone-bay",                         "9075080",  "noaa"),   # Big Stone Bay (14km to station)
    ("big-trunk-bay",                         "9751381",  "noaa"),   # Big Trunk Bay (32km to station)
    ("big-water",                             "8311062",  "noaa"),   # Big Water (23km to station)
    ("bigelow-beach",                         "9751381",  "noaa"),   # Bigelow Beach (24km to station)
    ("billet-bay",                            "8761724",  "noaa"),   # Billet Bay (22km to station)
    ("billings-cove",                         "8413320",  "noaa"),   # Billings Cove (39km to station)
    ("billington-cove",                       "8452660",  "noaa"),   # Billington Cove (17km to station)
    ("bilston-bar",                           "9444090",  "noaa"),   # Bilston Bar (30km to station)
    ("bingham-cove",                          "9452634",  "noaa"),   # Bingham Cove (17km to station)
    ("birch-harbor",                          "8413320",  "noaa"),   # Birch Harbor (14km to station)
    ("birch-island-cove",                     "8413320",  "noaa"),   # Birch Island Cove (19km to station)
    ("birchhead-shore",                       "8413320",  "noaa"),   # Birchhead Shore (30km to station)
    ("birdsall-bay",                          "9459881",  "noaa"),   # Birdsall Bay (40km to station)
    ("birdsnest-bay",                         "9451600",  "noaa"),   # Birdsnest Bay (7km to station)
    ("birdsong-bay",                          "9075065",  "noaa"),   # Birdsong Bay (7km to station)
    ("bishop-cove",                           "8454000",  "noaa"),   # Bishop Cove (6km to station)
    ("bishop-harbor",                         "8726384",  "noaa"),   # Bishop Harbor (4km to station)
    ("bishops-beach",                         "9455500",  "noaa"),   # Bishop's Beach (24km to station)
    ("bivalve-harbor",                        "8571421",  "noaa"),   # Bivalve Harbor (16km to station)
    ("black-bass-bay",                        "9075065",  "noaa"),   # Black Bass Bay (30km to station)
    ("black-bay",                             "8761305",  "noaa"),   # Black Bay (29km to station)
    ("black-bay-beach",                       "2695540",  "noaa"),   # Black Bay Beach (15km to station)
    ("black-beach",                           "8447930",  "noaa"),   # Black Beach (8km to station)
    ("black-cove",                            "8413320",  "noaa"),   # Black Cove (30km to station)
    ("black-duck-bay",                        "8770613",  "noaa"),   # Black Duck Bay (5km to station)
    ("black-duck-cove",                       "8631044",  "noaa"),   # Black Duck Cove (15km to station)
    ("black-point-creek",                     "8721604",  "noaa"),   # Black Point Creek (35km to station)
    ("black-sand-beach",                      "1617760",  "noaa"),   # Black Sand Beach (38km to station)
    ("black-sand-cove",                       "9450460",  "noaa"),   # Black Sand Cove (5km to station)
    ("black-sands-beach",                     "9414290",  "noaa"),   # Black Sands Beach (4km to station)
    ("blacks-beachlincoln-beach",             "9413450",  "noaa"),   # Black's Beach/Lincoln Beach (40km to station)
    ("blackbeards-creek",                     "8632200",  "noaa"),   # Blackbeards Creek (8km to station)
    ("blackberry-bay",                        "8531680",  "noaa"),   # Blackberry Bay (16km to station)
    ("blackhole-creek",                       "8575512",  "noaa"),   # Blackhole Creek (11km to station)
    ("blacks-arm",                            "9432780",  "noaa"),   # Blacks Arm (32km to station)
    ("blackstone-bay",                        "8311030",  "noaa"),   # Blackstone Bay (26km to station)
    ("blackwalnut-cove",                      "8571892",  "noaa"),   # Blackwalnut Cove (27km to station)
    ("blackwalnut-creek",                     "8575512",  "noaa"),   # Blackwalnut Creek (6km to station)
    ("blackwater-bay",                        "8729840",  "noaa"),   # Blackwater Bay (24km to station)
    ("blakes-cove",                           "8571892",  "noaa"),   # Blakes Cove (28km to station)
    ("blank-inlet",                           "9450460",  "noaa"),   # Blank Inlet (6km to station)
    ("blankinship-cove",                      "8447930",  "noaa"),   # Blankinship Cove (21km to station)
    ("blind-alligator-bayou",                 "8729108",  "noaa"),   # Blind Alligator Bayou (20km to station)
    ("blind-bay",                             "8761724",  "noaa"),   # Blind Bay (10km to station)
    ("blind-bayou",                           "8770475",  "noaa"),   # Blind Bayou (12km to station)
    ("blind-breaker",                         "9459450",  "noaa"),   # Blind Breaker (18km to station)
    ("blinds-hammock-bay",                    "8656483",  "noaa"),   # Blinds Hammock Bay (15km to station)
    ("blinn-bay",                             "9412110",  "noaa"),   # Blinn Bay (30km to station)
    ("bloody-cove",                           "8465705",  "noaa"),   # Bloody Cove (18km to station)
    ("bloody-point-creek",                    "8575512",  "noaa"),   # Bloody Point Creek (18km to station)
    ("bloomer-beach",                         "8516945",  "noaa"),   # Bloomer Beach (17km to station)
    ("blossom-cove",                          "8531680",  "noaa"),   # Blossom Cove (13km to station)
    ("blount-bay",                            "8651370",  "noaa"),   # Blount Bay (19km to station)
    ("blounts-bay",                           "8728690",  "noaa"),   # Blounts Bay (8km to station)
    ("blue-bay",                              "8635027",  "noaa"),   # Blue Bay (25km to station)
    ("blue-bill-hole",                        "8447435",  "noaa"),   # Blue Bill Hole (7km to station)
    ("blue-church-bay",                       "8311030",  "noaa"),   # Blue Church Bay (6km to station)
    ("blue-cobblestone-beach",                "9751381",  "noaa"),   # Blue Cobblestone Beach (3km to station)
    ("blue-hole",                             "2695540",  "noaa"),   # Blue Hole (12km to station)
    ("bluebeard-beach",                       "9751381",  "noaa"),   # Bluebeard Beach (12km to station)
    ("blueberry-bay",                         "9462620",  "noaa"),   # Blueberry Bay (40km to station)
    ("bluefish-cove",                         "8570283",  "noaa"),   # Bluefish Cove (3km to station)
    ("bluewater-bay",                         "9076070",  "noaa"),   # Bluewater Bay (36km to station)
    ("bluewing-pond",                         "8760721",  "noaa"),   # Bluewing Pond (13km to station)
    ("bluff-hill-cove",                       "8452660",  "noaa"),   # Bluff Hill Cove (20km to station)
    ("bluff-point-cove",                      "8635027",  "noaa"),   # Bluff Point Cove (14km to station)
    ("boat-bay",                              "8652587",  "noaa"),   # Boat Bay (34km to station)
    ("boat-bayou",                            "8726724",  "noaa"),   # Boat Bayou (19km to station)
    ("boat-cove",                             "8411060",  "noaa"),   # Boat Cove (34km to station)
    ("boathouse-cove",                        "8573364",  "noaa"),   # Boathouse Cove (17km to station)
    ("boathouse-creek",                       "8575512",  "noaa"),   # Boathouse Creek (13km to station)
    ("boating-side",                          "8465705",  "noaa"),   # Boating Side (40km to station)
    ("boatman-point-beach",                   "9751381",  "noaa"),   # Boatman Point Beach (5km to station)
    ("bob-taylors-pond",                      "8760721",  "noaa"),   # Bob Taylors Pond (10km to station)
    ("bobs-cove",                             "8411060",  "noaa"),   # Bobs Cove (28km to station)
    ("bobs-lakes",                            "8761305",  "noaa"),   # Bobs Lakes (24km to station)
    ("boby-owl-cove",                         "8571892",  "noaa"),   # Boby Owl Cove (26km to station)
    ("boca-chica-nude-beach",                 "8724580",  "noaa"),   # Boca Chica Nude Beach (13km to station)
    ("boca-ciega-bay",                        "8726520",  "noaa"),   # Boca Ciega Bay (16km to station)
    ("boca-de-alava",                         "9443090",  "noaa"),   # Boca De Alava (22km to station)
    ("boca-prieta",                           "9759110",  "noaa"),   # Boca Prieta (18km to station)
    ("boca-del-cibuco",                       "9755371",  "noaa"),   # Boca del Cibuco (28km to station)
    ("bodega-harbor",                         "9415020",  "noaa"),   # Bodega Harbor (37km to station)
    ("boedne-bay",                            "9075080",  "noaa"),   # Boedne Bay (33km to station)
    ("bogans-cove",                           "8534720",  "noaa"),   # Bogans Cove (21km to station)
    ("boggess-hole",                          "8725520",  "noaa"),   # Boggess Hole (39km to station)
    ("boggy-bay",                             "8726724",  "noaa"),   # Boggy Bay (35km to station)
    ("boggy-bayou",                           "8726724",  "noaa"),   # Boggy Bayou (15km to station)
    ("bogle-cove",                            "8573364",  "noaa"),   # Bogle Cove (20km to station)
    ("bogues-bay",                            "8631044",  "noaa"),   # Bogues Bay (34km to station)
    ("boiler-bay",                            "9751364",  "noaa"),   # Boiler Bay (13km to station)
    ("boiling-hole",                          "2695540",  "noaa"),   # Boiling Hole (19km to station)
    ("boiling-lot-cove",                      "8452660",  "noaa"),   # Boiling Lot Cove (17km to station)
    ("bolinas-lagoon",                        "9414290",  "noaa"),   # Bolinas Lagoon (23km to station)
    ("bolivar-beach",                         "8771341",  "noaa"),   # Bolivar Beach (7km to station)
    ("bolongo-bay",                           "9751381",  "noaa"),   # Bolongo Bay (18km to station)
    ("bolster-bayou",                         "8726384",  "noaa"),   # Bolster Bayou (13km to station)
    ("bomways-bay",                           "9087096",  "noaa"),   # Bomways Bay (31km to station)
    ("bon-secour-bay",                        "8735180",  "noaa"),   # Bon Secour Bay (21km to station)
    ("bond-bay",                              "9450460",  "noaa"),   # Bond Bay (30km to station)
    ("bone-yard-beach",                       "8720218",  "noaa"),   # Bone Yard Beach (12km to station)
    ("bonita-cove",                           "9414290",  "noaa"),   # Bonita Cove (5km to station)
    ("bonito-channel",                        "8656483",  "noaa"),   # Bonito Channel (36km to station)
    ("bonney-cove",                           "8639348",  "noaa"),   # Bonney Cove (34km to station)
    ("bonnies-bay",                           "8760721",  "noaa"),   # Bonnies Bay (38km to station)
    ("boomer-beach",                          "9410230",  "noaa"),   # Boomer Beach (2km to station)
    ("boomer-cove",                           "9052000",  "noaa"),   # Boomer Cove (32km to station)
    ("boot-cove-beach",                       "8410140",  "noaa"),   # Boot Cove Beach (15km to station)
    ("boot-key-harbor",                       "8723970",  "noaa"),   # Boot Key Harbor (2km to station)
    ("bootlegger-cove",                       "9455920",  "noaa"),   # Bootlegger Cove (4km to station)
    ("borck-creek",                           "9751381",  "noaa"),   # Borck Creek (5km to station)
    ("bordenstake-bay",                       "8631044",  "noaa"),   # Bordenstake Bay (13km to station)
    ("borinquen-beach",                       "9759394",  "noaa"),   # Borinquen Beach (30km to station)
    ("bosss-cove",                            "2695540",  "noaa"),   # Boss's Cove (13km to station)
    ("bostwick-bay",                          "8510560",  "noaa"),   # Bostwick Bay (16km to station)
    ("bostwick-inlet",                        "9450460",  "noaa"),   # Bostwick Inlet (13km to station)
    ("boswell-bay",                           "9454050",  "noaa"),   # Boswell Bay (27km to station)
    ("botany-bay",                            "9752235",  "noaa"),   # Botany Bay (29km to station)
    ("bottle-bayou-pond",                     "8760721",  "noaa"),   # Bottle Bayou Pond (3km to station)
    ("bottle-pond",                           "8760721",  "noaa"),   # Bottle Pond (6km to station)
    ("boulder-bay",                           "9454240",  "noaa"),   # Boulder Bay (32km to station)
    ("boulder-beach",                         "8413320",  "noaa"),   # Boulder Beach (9km to station)
    ("bournes-pond",                          "8447930",  "noaa"),   # Bournes Pond (11km to station)
    ("boussole-bay",                          "9452634",  "noaa"),   # Boussole Bay (40km to station)
    ("bouvier-bay",                           "9014070",  "noaa"),   # Bouvier Bay (10km to station)
    ("bovoni-bay",                            "9751381",  "noaa"),   # Bovoni Bay (18km to station)
    ("bowery-bay",                            "8516945",  "noaa"),   # Bowery Bay (11km to station)
    ("bowling-ball-beach",                    "9416841",  "noaa"),   # Bowling Ball Beach (7km to station)
    ("boxam-cove",                            "8413320",  "noaa"),   # Boxam Cove (40km to station)
    ("boy-scout-camp-cove",                   "9415102",  "noaa"),   # Boy Scout Camp Cove (13km to station)
    ("bracy-cove",                            "8413320",  "noaa"),   # Bracy Cove (12km to station)
    ("bradley-cove",                          "8571892",  "noaa"),   # Bradley Cove (3km to station)
    ("brady-bay",                             "8767816",  "noaa"),   # Brady Bay (11km to station)
    ("brakey-bay",                            "9052000",  "noaa"),   # Brakey Bay (14km to station)
    ("bramble-beach",                         "9414863",  "noaa"),   # Bramble Beach (8km to station)
    ("branch-bay",                            "9451054",  "noaa"),   # Branch Bay (14km to station)
    ("branch-gut-cove",                       "8570283",  "noaa"),   # Branch Gut Cove (20km to station)
    ("brandywine-bay-beach",                  "9751381",  "noaa"),   # Brandywine Bay Beach (18km to station)
    ("brannock-bay",                          "8571892",  "noaa"),   # Brannock Bay (18km to station)
    ("branson-cove",                          "8635750",  "noaa"),   # Branson Cove (22km to station)
    ("brant-hole",                            "8571421",  "noaa"),   # Brant Hole (14km to station)
    ("brant-island-cove",                     "8447930",  "noaa"),   # Brant Island Cove (17km to station)
    ("brant-island-pond",                     "8651370",  "noaa"),   # Brant Island Pond (18km to station)
    ("brayton-point-beach",                   "8447386",  "noaa"),   # Brayton Point Beach (2km to station)
    ("brazos-harbor",                         "8772471",  "noaa"),   # Brazos Harbor (4km to station)
    ("breach-inlet",                          "8665530",  "noaa"),   # Breach Inlet (10km to station)
    ("bread-and-cheese-creek",                "8574680",  "noaa"),   # Bread and Cheese Creek (9km to station)
    ("breakers-beach",                        "9410170",  "noaa"),   # Breakers Beach (5km to station)
    ("breakwater-harbor",                     "8557380",  "noaa"),   # Breakwater Harbor (1km to station)
    ("brecknock-bay",                         "8635027",  "noaa"),   # Brecknock Bay (40km to station)
    ("breeds-cove",                           "8447386",  "noaa"),   # Breeds Cove (4km to station)
    ("breids-bay",                            "9751401",  "noaa"),   # Breids Bay (8km to station)
    ("brennan-bay",                           "9450460",  "noaa"),   # Brennan Bay (36km to station)
    ("brenton-cove",                          "8452660",  "noaa"),   # Brenton Cove (3km to station)
    ("breton-bay",                            "8577330",  "noaa"),   # Breton Bay (19km to station)
    ("breton-sound",                          "8760721",  "noaa"),   # Breton Sound (36km to station)
    ("brewer-cove",                           "8418150",  "noaa"),   # Brewer Cove (28km to station)
    ("brewer-creek",                          "8575512",  "noaa"),   # Brewer Creek (8km to station)
    ("brewer-marine-south-freeport",          "8418150",  "noaa"),   # Brewer Marine South Freeport (21km to station)
    ("brewer-pond",                           "8575512",  "noaa"),   # Brewer Pond (8km to station)
    ("brewers-bay",                           "9751381",  "noaa"),   # Brewer's Bay (16km to station)
    ("brewers-bay-beach",                     "9751381",  "noaa"),   # Brewers Bay Beach (27km to station)
    ("briarcliffe-beach",                     "8661070",  "noaa"),   # Briarcliffe Beach (22km to station)
    ("briary-cove",                           "8575512",  "noaa"),   # Briary Cove (28km to station)
    ("brickhouse-creek",                      "8575512",  "noaa"),   # Brickhouse Creek (8km to station)
    ("brickyard-bay",                         "9076024",  "noaa"),   # Brickyard Bay (27km to station)
    ("brickyard-cove",                        "8418150",  "noaa"),   # Brickyard Cove (24km to station)
    ("bridge-cove",                           "8635750",  "noaa"),   # Bridge Cove (38km to station)
    ("bridge-creek",                          "8571421",  "noaa"),   # Bridge Creek (21km to station)
    ("brig-cove",                             "8418150",  "noaa"),   # Brig Cove (25km to station)
    ("briggs-cove",                           "8447930",  "noaa"),   # Briggs Cove (23km to station)
    ("brighams-cove",                         "8418150",  "noaa"),   # Brighams Cove (38km to station)
    ("brim-cove",                             "8411060",  "noaa"),   # Brim Cove (33km to station)
    ("bristol-town-beach",                    "8452944",  "noaa"),   # Bristol Town Beach (5km to station)
    ("british-bay",                           "8735180",  "noaa"),   # British Bay (2km to station)
    ("britton-bay",                           "8311062",  "noaa"),   # Britton Bay (19km to station)
    ("broad-bay",                             "9462620",  "noaa"),   # Broad Bay (8km to station)
    ("broad-cove",                            "8419870",  "noaa"),   # Broad Cove (9km to station)
    ("broad-sound",                           "8418150",  "noaa"),   # Broad Sound (16km to station)
    ("broadkill-sound",                       "8557380",  "noaa"),   # Broadkill Sound (8km to station)
    ("broads-bay",                            "8311062",  "noaa"),   # Broads Bay (30km to station)
    ("broadwater-creek",                      "8575512",  "noaa"),   # Broadwater Creek (22km to station)
    ("brock-creek",                           "8721604",  "noaa"),   # Brock Creek (28km to station)
    ("brockatonorton-bay",                    "8570283",  "noaa"),   # Brockatonorton Bay (33km to station)
    ("brockenberry-bay",                      "8632200",  "noaa"),   # Brockenberry Bay (17km to station)
    ("broken-cove",                           "8418150",  "noaa"),   # Broken Cove (15km to station)
    ("broken-oar-cove",                       "9453220",  "noaa"),   # Broken Oar Cove (5km to station)
    ("bromwell-cove",                         "8571892",  "noaa"),   # Bromwell Cove (26km to station)
    ("brooker-creek",                         "8726724",  "noaa"),   # Brooker Creek (11km to station)
    ("brooklyn-basin",                        "9414750",  "noaa"),   # Brooklyn Basin (4km to station)
    ("brooks-cove",                           "8410140",  "noaa"),   # Brooks Cove (24km to station)
    ("brooks-creek",                          "8571892",  "noaa"),   # Brooks Creek (18km to station)
    ("brosewere-bay",                         "8516945",  "noaa"),   # Brosewere Bay (23km to station)
    ("broward-creek",                         "8720218",  "noaa"),   # Broward Creek (7km to station)
    ("brown-bay",                             "9751381",  "noaa"),   # Brown Bay (5km to station)
    ("brown-bay-beach",                       "9751381",  "noaa"),   # Brown Bay Beach (5km to station)
    ("brown-cove",                            "8639348",  "noaa"),   # Brown Cove (24km to station)
    ("browns-beach",                          "9412110",  "noaa"),   # Brown's Beach (33km to station)
    ("brownies-beach",                        "8575512",  "noaa"),   # Brownie's Beach (34km to station)
    ("browns-cove",                           "8635750",  "noaa"),   # Browns Cove (27km to station)
    ("browns-creek",                          "8720219",  "noaa"),   # Browns Creek (5km to station)
    ("bruce-bay",                             "9076024",  "noaa"),   # Bruce Bay (31km to station)
    ("bruce-bight-beach",                     "9449880",  "noaa"),   # Bruce Bight Beach (26km to station)
    ("brule-bay",                             "9099090",  "noaa"),   # Brule Bay (29km to station)
    ("brush-valley",                          "8447435",  "noaa"),   # Brush Valley (34km to station)
    ("brushy-bend-bayou",                     "8770808",  "noaa"),   # Brushy Bend Bayou (6km to station)
    ("bryan-beach",                           "8772471",  "noaa"),   # Bryan Beach (7km to station)
    ("bryans-cove",                           "8575512",  "noaa"),   # Bryans Cove (19km to station)
    ("bryant-bay",                            "8637689",  "noaa"),   # Bryant Bay (11km to station)
    ("bryant-cove",                           "8447930",  "noaa"),   # Bryant Cove (20km to station)
    ("buccaneer-beach",                       "9751364",  "noaa"),   # Buccaneer Beach (2km to station)
    ("buck-bay",                              "8311062",  "noaa"),   # Buck Bay (19km to station)
    ("buck-cove",                             "8413320",  "noaa"),   # Buck Cove (13km to station)
    ("buck-island-bay",                       "8651370",  "noaa"),   # Buck Island Bay (40km to station)
    ("bucket-bend",                           "8760721",  "noaa"),   # Bucket Bend (14km to station)
    ("buckhorn-cove",                         "9416841",  "noaa"),   # Buckhorn Cove (39km to station)
    ("buckinghams-cove",                      "8575512",  "noaa"),   # Buckinghams Cove (10km to station)
    ("buckle-island-harbor",                  "8413320",  "noaa"),   # Buckle Island Harbor (32km to station)
    ("buckmans-creek",                        "8410140",  "noaa"),   # Buckmans Creek (29km to station)
    ("bucks-bay",                             "8760721",  "noaa"),   # Bucks Bay (38km to station)
    ("bucks-harbor",                          "8411060",  "noaa"),   # Bucks Harbor (13km to station)
    ("budds-creek",                           "8635027",  "noaa"),   # Budds Creek (20km to station)
    ("buffalo-outer-harbor",                  "9063020",  "noaa"),   # Buffalo Outer Harbor (3km to station)
    ("buffalo-wallow",                        "8311062",  "noaa"),   # Buffalo Wallow (13km to station)
    ("bugsy-beach",                           "8651370",  "noaa"),   # Bugsy Beach (35km to station)
    ("building-bay",                          "2695535",  "noaa"),   # Building Bay (3km to station)
    ("building-bay-beach",                    "2695535",  "noaa"),   # Building Bay Beach (3km to station)
    ("bulkhead-cove",                         "8770613",  "noaa"),   # Bulkhead Cove (28km to station)
    ("bull-bay",                              "8760721",  "noaa"),   # Bull Bay (14km to station)
    ("bull-cove",                             "8631044",  "noaa"),   # Bull Cove (21km to station)
    ("bull-creek",                            "8656483",  "noaa"),   # Bull Creek (36km to station)
    ("bull-dog-beach",                        "8410140",  "noaa"),   # Bull Dog Beach (7km to station)
    ("bull-harbor",                           "8665530",  "noaa"),   # Bull Harbor (35km to station)
    ("bullhead-bay",                          "9075080",  "noaa"),   # Bullhead Bay (34km to station)
    ("bullock-cove",                          "8452944",  "noaa"),   # Bullock Cove (4km to station)
    ("bulls-bay",                             "8665530",  "noaa"),   # Bulls Bay (40km to station)
    ("bunker-cove",                           "8411060",  "noaa"),   # Bunker Cove (26km to station)
    ("bunker-hole",                           "8411060",  "noaa"),   # Bunker Hole (26km to station)
    ("bunkers-cove",                          "8413320",  "noaa"),   # Bunkers Cove (8km to station)
    ("bunkers-harbor",                        "8413320",  "noaa"),   # Bunkers Harbor (14km to station)
    ("buoy-pond",                             "8760721",  "noaa"),   # Buoy Pond (11km to station)
    ("buras-pond",                            "8760721",  "noaa"),   # Buras Pond (10km to station)
    ("burchall-cove",                         "2695540",  "noaa"),   # Burchall Cove (5km to station)
    ("burges-cove",                           "8454000",  "noaa"),   # Burges Cove (0km to station)
    ("burgundy-beach",                        "9063079",  "noaa"),   # Burgundy Beach (18km to station)
    ("burkhart-cove",                         "8773146",  "noaa"),   # Burkhart Cove (8km to station)
    ("burley-creek",                          "8575512",  "noaa"),   # Burley Creek (3km to station)
    ("burlingame-state-park-beach",           "8461490",  "noaa"),   # Burlingame State Park Beach (33km to station)
    ("burns-bay",                             "9075099",  "noaa"),   # Burn's Bay (37km to station)
    ("burnell-cove",                          "8418150",  "noaa"),   # Burnell Cove (35km to station)
    ("burnet-bay",                            "8770613",  "noaa"),   # Burnet Bay (12km to station)
    ("burnett-bay",                           "8767816",  "noaa"),   # Burnett Bay (11km to station)
    ("burnett-creek",                         "8510560",  "noaa"),   # Burnett Creek (37km to station)
    ("burnt-coat-harbor",                     "8413320",  "noaa"),   # Burnt Coat Harbor (34km to station)
    ("burnt-house-cove",                      "8635027",  "noaa"),   # Burnt House Cove (13km to station)
    ("burr-creek",                            "8467150",  "noaa"),   # Burr Creek (3km to station)
    ("burritt-cove",                          "8467150",  "noaa"),   # Burritt Cove (17km to station)
    ("burton-bay",                            "2695540",  "noaa"),   # Burton Bay (12km to station)
    ("burtons-bay",                           "8631044",  "noaa"),   # Burtons Bay (4km to station)
    ("burwell-bay",                           "8637689",  "noaa"),   # Burwell Bay (23km to station)
    ("burwells-beach",                        "8465705",  "noaa"),   # Burwells Beach (10km to station)
    ("burying-hill-beach",                    "8467150",  "noaa"),   # Burying Hill Beach (13km to station)
    ("buschalaugh-cove",                      "9410170",  "noaa"),   # Buschalaugh Cove (26km to station)
    ("bush-bay",                              "9075099",  "noaa"),   # Bush Bay (29km to station)
    ("bush-island-cove",                      "8639348",  "noaa"),   # Bush Island Cove (36km to station)
    ("bush-river",                            "8573364",  "noaa"),   # Bush River (21km to station)
    ("bushwick-inlet",                        "8518750",  "noaa"),   # Bushwick Inlet (5km to station)
    ("bushwood-cove",                         "8635027",  "noaa"),   # Bushwood Cove (20km to station)
    ("bushy-point-beach",                     "8461490",  "noaa"),   # Bushy Point Beach (7km to station)
    ("butcherpen-cove",                       "8729840",  "noaa"),   # Butcherpen Cove (7km to station)
    ("butler-bay",                            "9751401",  "noaa"),   # Butler Bay (16km to station)
    ("butler-cove",                           "8447930",  "noaa"),   # Butler Cove (25km to station)
    ("butler-creek",                          "8637689",  "noaa"),   # Butler Creek (10km to station)
    ("butler-hole",                           "8726520",  "noaa"),   # Butler Hole (15km to station)
    ("butter-bean-beach",                     "8670870",  "noaa"),   # Butter Bean Beach (18km to station)
    ("butterfish-cove",                       "8570283",  "noaa"),   # Butterfish Cove (2km to station)
    ("buttermilk-bay",                        "8447930",  "noaa"),   # Buttermilk Bay (27km to station)
    ("buttermilk-cove",                       "8418150",  "noaa"),   # Buttermilk Cove (35km to station)
    ("butterowe-bayou",                       "8771486",  "noaa"),   # Butterowe Bayou (13km to station)
    ("button-bay",                            "9052000",  "noaa"),   # Button Bay (4km to station)
    ("buttonwood-harbor",                     "8726384",  "noaa"),   # Buttonwood Harbor (29km to station)
    ("buttonwoods-beach",                     "8452944",  "noaa"),   # Buttonwoods Beach (7km to station)
    ("buttrocker-cove",                       "9446484",  "noaa"),   # Buttrocker Cove (17km to station)
    ("buzzard-bay",                           "8637689",  "noaa"),   # Buzzard Bay (34km to station)
    ("cabin-cove",                            "8632200",  "noaa"),   # Cabin Cove (8km to station)
    ("cabin-creek",                           "8575512",  "noaa"),   # Cabin Creek (24km to station)
    ("cabrita-point-beach",                   "9751381",  "noaa"),   # Cabrita Point Beach (12km to station)
    ("cadle-creek",                           "8575512",  "noaa"),   # Cadle Creek (12km to station)
    ("cadman-cove",                           "8447386",  "noaa"),   # Cadman Cove (18km to station)
    ("caesars-beach",                         "8534720",  "noaa"),   # Caesars Beach (2km to station)
    ("cains-pond",                            "8449130",  "noaa"),   # Cains Pond (9km to station)
    ("caleta-parguera",                       "9759110",  "noaa"),   # Caleta Parguera (2km to station)
    ("caleta-salinas",                        "9759110",  "noaa"),   # Caleta Salinas (10km to station)
    ("calf-pasture-beach",                    "8467150",  "noaa"),   # Calf Pasture Beach (20km to station)
    ("calf-pasture-cove",                     "8635750",  "noaa"),   # Calf Pasture Cove (36km to station)
    ("calf-pasture-point-beach",              "8452944",  "noaa"),   # Calf Pasture Point Beach (11km to station)
    ("calfpasture-cove",                      "8573364",  "noaa"),   # Calfpasture Cove (19km to station)
    ("calico-bay",                            "8656483",  "noaa"),   # Calico Bay (4km to station)
    ("calico-creek",                          "8656483",  "noaa"),   # Calico Creek (5km to station)
    ("california-bayou",                      "8729108",  "noaa"),   # California Bayou (18km to station)
    ("california-hole",                       "8775237",  "noaa"),   # California Hole (8km to station)
    ("calkins-point",                         "9446484",  "noaa"),   # Calkins Point (39km to station)
    ("callaghan-bay",                         "2695540",  "noaa"),   # Callaghan Bay (18km to station)
    ("callahans-beach",                       "8467150",  "noaa"),   # Callahans Beach (30km to station)
    ("callaway-bayou",                        "8729108",  "noaa"),   # Callaway Bayou (10km to station)
    ("cals-hammock",                          "8631044",  "noaa"),   # Cals Hammock (25km to station)
    ("calusa-beach",                          "8723970",  "noaa"),   # Calusa Beach (19km to station)
    ("calusa-point",                          "8725520",  "noaa"),   # Calusa Point (25km to station)
    ("calvert-bay",                           "8635750",  "noaa"),   # Calvert Bay (13km to station)
    ("caminada-bay",                          "8761724",  "noaa"),   # Caminada Bay (10km to station)
    ("camp-burgess-waterfront",               "8447930",  "noaa"),   # Camp Burgess Waterfront (26km to station)
    ("camp-coogan-bay",                       "9451600",  "noaa"),   # Camp Coogan Bay (8km to station)
    ("camp-ellis-reach",                      "8418150",  "noaa"),   # Camp Ellis Reach (24km to station)
    ("camp-fuller-waterfront",                "8452660",  "noaa"),   # Camp Fuller Waterfront (19km to station)
    ("campau-bay",                            "9014070",  "noaa"),   # Campau Bay (21km to station)
    ("campbell-bayou",                        "8771486",  "noaa"),   # Campbell Bayou (4km to station)
    ("campbell-cove",                         "9415020",  "noaa"),   # Campbell Cove (35km to station)
    ("campers-delight",                       "8418150",  "noaa"),   # Campers Delight (4km to station)
    ("camps-pond",                            "8760721",  "noaa"),   # Camps Pond (12km to station)
    ("canadian-hole",                         "8654467",  "noaa"),   # Canadian Hole (20km to station)
    ("canal-beach",                           "8410140",  "noaa"),   # Canal Beach (32km to station)
    ("canarsie-beach",                        "8518750",  "noaa"),   # Canarsie Beach (13km to station)
    ("canary-cove",                           "8413320",  "noaa"),   # Canary Cove (29km to station)
    ("canaveral-bight",                       "8721604",  "noaa"),   # Canaveral Bight (4km to station)
    ("cane-bay",                              "9751401",  "noaa"),   # Cane Bay (11km to station)
    ("cane-bay-beach",                        "9751401",  "noaa"),   # Cane Bay Beach (11km to station)
    ("cane-garden-bay",                       "9751381",  "noaa"),   # Cane Garden Bay (14km to station)
    ("cane-pond",                             "8760721",  "noaa"),   # Cane Pond (10km to station)
    ("caneel-bay",                            "9751381",  "noaa"),   # Caneel Bay (7km to station)
    ("caneel-hawksnest-beach",                "9751381",  "noaa"),   # Caneel Hawksnest Beach (7km to station)
    ("canegarden-bay",                        "9751401",  "noaa"),   # Canegarden Bay (2km to station)
    ("canes-cove",                            "8413320",  "noaa"),   # Canes Cove (20km to station)
    ("cannery-bay",                           "9462620",  "noaa"),   # Cannery Bay (26km to station)
    ("cannery-cove",                          "9457804",  "noaa"),   # Cannery Cove (29km to station)
    ("cannery-slough",                        "9440910",  "noaa"),   # Cannery Slough (5km to station)
    ("cannonball-bay",                        "9099090",  "noaa"),   # Cannonball Bay (40km to station)
    ("canoe-bay",                             "9075099",  "noaa"),   # Canoe Bay (17km to station)
    ("canoe-beach",                           "8516945",  "noaa"),   # Canoe Beach (17km to station)
    ("canton-bay",                            "2695535",  "noaa"),   # Canton Bay (6km to station)
    ("cape-coral-yacht-club-beach",           "8725520",  "noaa"),   # Cape Coral Yacht club beach (14km to station)
    ("cape-cove",                             "8411060",  "noaa"),   # Cape Cove (35km to station)
    ("cape-haze-bay",                         "8725520",  "noaa"),   # Cape Haze Bay (32km to station)
    ("cape-lookout-shoals",                   "8656483",  "noaa"),   # Cape Lookout Shoals (21km to station)
    ("cape-neddick-beach",                    "8419870",  "noaa"),   # Cape Neddick Beach (17km to station)
    ("cape-neddick-harbor",                   "8419870",  "noaa"),   # Cape Neddick Harbor (16km to station)
    ("cape-poge-bay",                         "8447930",  "noaa"),   # Cape Poge Bay (22km to station)
    ("cape-porpoise-harbor",                  "8418150",  "noaa"),   # Cape Porpoise Harbor (36km to station)
    ("cape-small-harbor",                     "8418150",  "noaa"),   # Cape Small Harbor (33km to station)
    ("cape-split-harbor",                     "8413320",  "noaa"),   # Cape Split Harbor (40km to station)
    ("cape-windsor",                          "8570283",  "noaa"),   # Cape Windsor (14km to station)
    ("capella-bay",                           "9751381",  "noaa"),   # Capella Bay (18km to station)
    ("capelli-cove",                          "8637689",  "noaa"),   # Capelli Cove (22km to station)
    ("capers-inlet",                          "8665530",  "noaa"),   # Capers Inlet (22km to station)
    ("capers-island-boneyard",                "8665530",  "noaa"),   # Capers Island Boneyard (23km to station)
    ("captain-harbor",                        "8516945",  "noaa"),   # Captain Harbor (24km to station)
    ("captain-williams-bay",                  "2695540",  "noaa"),   # Captain Williams Bay (9km to station)
    ("captains-bay",                          "9462620",  "noaa"),   # Captains Bay (3km to station)
    ("cara-cove",                             "8573927",  "noaa"),   # Cara Cove (14km to station)
    ("carabelle-beach",                       "8728690",  "noaa"),   # Carabelle Beach (31km to station)
    ("carancahua-cove",                       "8771486",  "noaa"),   # Carancahua Cove (13km to station)
    ("carbon---la-costa-beach",               "9410840",  "noaa"),   # Carbon - La Costa Beach (14km to station)
    ("carbon-beach",                          "9410840",  "noaa"),   # Carbon Beach (15km to station)
    ("card-cove",                             "8418150",  "noaa"),   # Card Cove (29km to station)
    ("carden-bay",                            "9751364",  "noaa"),   # Carden Bay (6km to station)
    ("careening-cove",                        "9751381",  "noaa"),   # Careening Cove (22km to station)
    ("carencro-bay",                          "8760721",  "noaa"),   # Carencro Bay (21km to station)
    ("caret-bay",                             "9751381",  "noaa"),   # Caret Bay (28km to station)
    ("carland-beach",                         "9063085",  "noaa"),   # Carland Beach (4km to station)
    ("carlos-bay",                            "8774513",  "noaa"),   # Carlos Bay (13km to station)
    ("carlson-arm",                           "9432780",  "noaa"),   # Carlson Arm (34km to station)
    ("carmel-bay",                            "9413450",  "noaa"),   # Carmel Bay (9km to station)
    ("carnegie-bay",                          "8311062",  "noaa"),   # Carnegie Bay (3km to station)
    ("carnival-bay",                          "8536110",  "noaa"),   # Carnival Bay (19km to station)
    ("carnival-bayou",                        "8534720",  "noaa"),   # Carnival Bayou (18km to station)
    ("carot-bay-beach",                       "9751381",  "noaa"),   # Carot Bay Beach (20km to station)
    ("carquinez-bay",                         "9415102",  "noaa"),   # Carquinez Bay (12km to station)
    ("carr-creek",                            "8575512",  "noaa"),   # Carr Creek (2km to station)
    ("carrs-beach",                           "8575512",  "noaa"),   # Carr's Beach (3km to station)
    ("carrier-bay",                           "8311062",  "noaa"),   # Carrier Bay (14km to station)
    ("carrin-bayou",                          "8728690",  "noaa"),   # Carrin Bayou (15km to station)
    ("carroll-inlet",                         "9450460",  "noaa"),   # Carroll Inlet (25km to station)
    ("carrs-creek",                           "8575512",  "noaa"),   # Carrs Creek (22km to station)
    ("carrying-place",                        "8413320",  "noaa"),   # Carrying Place (22km to station)
    ("carrying-place-beach",                  "8413320",  "noaa"),   # Carrying Place Beach (22km to station)
    ("carrying-place-cove",                   "8413320",  "noaa"),   # Carrying Place Cove (37km to station)
    ("carrying-place-inlet",                  "8413320",  "noaa"),   # Carrying Place Inlet (17km to station)
    ("carter-cove",                           "8635750",  "noaa"),   # Carter Cove (38km to station)
    ("carters-cut",                           "8721604",  "noaa"),   # Carters Cut (29km to station)
    ("casey-bay",                             "8654467",  "noaa"),   # Casey Bay (37km to station)
    ("cash-bayou",                            "8728690",  "noaa"),   # Cash Bayou (15km to station)
    ("cassidys-bay",                          "9052000",  "noaa"),   # Cassidys Bay (14km to station)
    ("castle-hill-beach",                     "8452660",  "noaa"),   # Castle Hill Beach (6km to station)
    ("castle-hill-cove",                      "8452660",  "noaa"),   # Castle Hill Cove (5km to station)
    ("castle-rock-beach",                     "9410840",  "noaa"),   # Castle Rock Beach (7km to station)
    ("caswell-basin",                         "8658120",  "noaa"),   # Caswell Basin (37km to station)
    ("cat-bay",                               "8761724",  "noaa"),   # Cat Bay (12km to station)
    ("cat-cove",                              "8571421",  "noaa"),   # Cat Cove (16km to station)
    ("cat-rock-cove",                         "8510560",  "noaa"),   # Cat Rock Cove (37km to station)
    ("catahoula-bay",                         "8762482",  "noaa"),   # Catahoula Bay (19km to station)
    ("cataraqui-bay",                         "9052000",  "noaa"),   # Cataraqui Bay (19km to station)
    ("catelins-cove",                         "8575512",  "noaa"),   # Catelins Cove (2km to station)
    ("catfish-basin",                         "8729840",  "noaa"),   # Catfish Basin (25km to station)
    ("catfish-creek",                         "8721604",  "noaa"),   # Catfish Creek (9km to station)
    ("cathys-fancy-beach",                    "9751364",  "noaa"),   # Cathys Fancy Beach (3km to station)
    ("caton-cove",                            "9459450",  "noaa"),   # Caton Cove (37km to station)
    ("cators-cove",                           "8577330",  "noaa"),   # Cators Cove (23km to station)
    ("cattail-creek",                         "8575512",  "noaa"),   # Cattail Creek (12km to station)
    ("caucus-bay",                            "8637689",  "noaa"),   # Caucus Bay (13km to station)
    ("causeway-beach",                        "8413320",  "noaa"),   # Causeway Beach (40km to station)
    ("cave-cove",                             "9751381",  "noaa"),   # Cave Cove (28km to station)
    ("cavello-bay",                           "2695540",  "noaa"),   # Cavello Bay (17km to station)
    ("caven-point-beach",                     "8518750",  "noaa"),   # Caven Point Beach (5km to station)
    ("cay-bay",                               "9751381",  "noaa"),   # Cay Bay (23km to station)
    ("cay-beach",                             "9751364",  "noaa"),   # Cay Beach (0km to station)
    ("cayo-luis-pena",                        "9752235",  "noaa"),   # Cayo Luis Pena (3km to station)
    ("cayo-de-hinoso",                        "8776604",  "noaa"),   # Cayo de Hinoso (18km to station)
    ("cayo-del-grullo",                       "8776604",  "noaa"),   # Cayo del Grullo (27km to station)
    ("cayo-del-infiernillo",                  "8776604",  "noaa"),   # Cayo del Infiernillo (18km to station)
    ("cayo-del-mazon",                        "8776604",  "noaa"),   # Cayo del Mazon (21km to station)
    ("cayucos-state-beach",                   "9412110",  "noaa"),   # Cayucos State Beach (34km to station)
    ("cecil-bay",                             "9075080",  "noaa"),   # Cecil Bay (10km to station)
    ("cedar-bay",                             "8656483",  "noaa"),   # Cedar Bay (38km to station)
    ("cedar-beach-creek",                     "8510560",  "noaa"),   # Cedar Beach Creek (36km to station)
    ("cedar-bush-bay",                        "8652587",  "noaa"),   # Cedar Bush Bay (11km to station)
    ("cedar-cove",                            "8631044",  "noaa"),   # Cedar Cove (26km to station)
    ("cedar-creek",                           "8571421",  "noaa"),   # Cedar Creek (34km to station)
    ("cedar-island-creek",                    "8571421",  "noaa"),   # Cedar Island Creek (36km to station)
    ("cedar-lake",                            "8774230",  "noaa"),   # Cedar Lake (13km to station)
    ("center-beach",                          "8465705",  "noaa"),   # Center Beach (9km to station)
    ("center-harbor",                         "8413320",  "noaa"),   # Center Harbor (33km to station)
    ("central-beach",                         "9410170",  "noaa"),   # Central Beach (4km to station)
    ("chacaloochee-bay",                      "8737048",  "noaa"),   # Chacaloochee Bay (6km to station)
    ("chadwick-bayou",                        "8725520",  "noaa"),   # Chadwick Bayou (34km to station)
    ("chain-lake-beach",                      "9075080",  "noaa"),   # Chain Lake Beach (11km to station)
    ("chalk-cove",                            "8410140",  "noaa"),   # Chalk Cove (32km to station)
    ("chalker-beach",                         "8461490",  "noaa"),   # Chalker Beach (28km to station)
    ("champlain-bayou",                       "8726384",  "noaa"),   # Champlain Bayou (12km to station)
    ("chandler-cove-beach",                   "8418150",  "noaa"),   # Chandler Cove Beach (12km to station)
    ("changs-beach",                          "1615680",  "noaa"),   # Chang's Beach (26km to station)
    ("channel-beach",                         "8447930",  "noaa"),   # Channel Beach (23km to station)
    ("channel-cove",                          "8534720",  "noaa"),   # Channel Cove (33km to station)
    ("chapel-cove",                           "8571892",  "noaa"),   # Chapel Cove (24km to station)
    ("chapin-memorial-beach",                 "8447435",  "noaa"),   # Chapin Memorial Beach (24km to station)
    ("chaplin-bay",                           "2695540",  "noaa"),   # Chaplin Bay (17km to station)
    ("chaplin-bay-beach",                     "2695540",  "noaa"),   # Chaplin Bay Beach (17km to station)
    ("chapman-beach",                         "8461490",  "noaa"),   # Chapman Beach (29km to station)
    ("chappaquiddick-beach",                  "8447930",  "noaa"),   # Chappaquiddick Beach (21km to station)
    ("chappaquoit-beach",                     "8447930",  "noaa"),   # Chappaquoit Beach (9km to station)
    ("chaptico-bay",                          "8635027",  "noaa"),   # Chaptico Bay (19km to station)
    ("charles-creek",                         "8467150",  "noaa"),   # Charles Creek (20km to station)
    ("charles-e-ransom-beach",                "8516945",  "noaa"),   # Charles E. Ransom Beach (19km to station)
    ("charleys-cove",                         "8413320",  "noaa"),   # Charleys Cove (5km to station)
    ("chase-cove",                            "8447386",  "noaa"),   # Chase Cove (6km to station)
    ("chase-creek",                           "8575512",  "noaa"),   # Chase Creek (5km to station)
    ("chases-cove",                           "8635750",  "noaa"),   # Chases Cove (37km to station)
    ("chaska-beach",                          "9063079",  "noaa"),   # Chaska Beach (23km to station)
    ("chenay-bay",                            "9751364",  "noaa"),   # Chenay Bay (4km to station)
    ("cherry-harbor",                         "8510560",  "noaa"),   # Cherry Harbor (14km to station)
    ("cherrystone-inlet",                     "8632200",  "noaa"),   # Cherrystone Inlet (15km to station)
    ("cherrytree-cove",                       "8575512",  "noaa"),   # Cherrytree Cove (7km to station)
    ("cheston-creek",                         "8575512",  "noaa"),   # Cheston Creek (14km to station)
    ("chetco-cove",                           "9419750",  "noaa"),   # Chetco Cove (34km to station)
    ("chichagof-bay",                         "9459450",  "noaa"),   # Chichagof Bay (40km to station)
    ("chicken-ranch-beach",                   "9415020",  "noaa"),   # Chicken Ranch Beach (16km to station)
    ("chickering-cove",                       "8419870",  "noaa"),   # Chickering Cove (3km to station)
    ("chicopit-bay",                          "8720218",  "noaa"),   # Chicopit Bay (4km to station)
    ("childrens-beach",                       "8449130",  "noaa"),   # Childrens Beach (0km to station)
    ("childrens-cove",                        "8452660",  "noaa"),   # Childrens Cove (30km to station)
    ("chilkat-inlet",                         "9452400",  "noaa"),   # Chilkat Inlet (33km to station)
    ("chilkoot-inlet",                        "9452400",  "noaa"),   # Chilkoot Inlet (25km to station)
    ("chilson-beach",                         "8454000",  "noaa"),   # Chilson Beach (31km to station)
    ("chimney-cove",                          "8729840",  "noaa"),   # Chimney Cove (27km to station)
    ("chin-chin-tse-tung",                    "9449880",  "noaa"),   # Chin-Chin-Tse-Tung (15km to station)
    ("china-basin",                           "9414750",  "noaa"),   # China Basin (8km to station)
    ("china-poot-bay",                        "9455500",  "noaa"),   # China Poot Bay (28km to station)
    ("chinaman-bayou",                        "8761724",  "noaa"),   # Chinaman Bayou (37km to station)
    ("chinese-cut",                           "9415144",  "noaa"),   # Chinese Cut (28km to station)
    ("chink-creek",                           "8574680",  "noaa"),   # Chink Creek (8km to station)
    ("chino-bay",                             "8747437",  "noaa"),   # Chino Bay (35km to station)
    ("chip-cove",                             "9457804",  "noaa"),   # Chip Cove (16km to station)
    ("chippewa-bay",                          "8311062",  "noaa"),   # Chippewa Bay (18km to station)
    ("chivericks-cove",                       "8418150",  "noaa"),   # Chivericks Cove (10km to station)
    ("chix-beach",                            "8638610",  "noaa"),   # Chix Beach (18km to station)
    ("chocolate-bay",                         "8771972",  "noaa"),   # Chocolate Bay (11km to station)
    ("chocolate-hole",                        "9751381",  "noaa"),   # Chocolate Hole (6km to station)
    ("chocomount-beach",                      "8461490",  "noaa"),   # Chocomount Beach (15km to station)
    ("chocomount-cove",                       "8461490",  "noaa"),   # Chocomount Cove (14km to station)
    ("cholmondeley-sound",                    "9450460",  "noaa"),   # Cholmondeley Sound (33km to station)
    ("christensen-bay",                       "9075080",  "noaa"),   # Christensen Bay (26km to station)
    ("christian-bay",                         "2695540",  "noaa"),   # Christian Bay (19km to station)
    ("christian-camp-meeting-beach",          "8447930",  "noaa"),   # Christian Camp Meeting Beach (30km to station)
    ("christian-cove",                        "9751381",  "noaa"),   # Christian Cove (8km to station)
    ("christian-sound",                       "9451054",  "noaa"),   # Christian Sound (38km to station)
    ("christie-pond",                         "8760721",  "noaa"),   # Christie Pond (13km to station)
    ("christmas-tree-cove",                   "9410840",  "noaa"),   # Christmas Tree Cove (28km to station)
    ("chub-cove",                             "8410140",  "noaa"),   # Chub Cove (36km to station)
    ("chuckfee-bay",                          "8737048",  "noaa"),   # Chuckfee Bay (11km to station)
    ("chugach-bay",                           "9455500",  "noaa"),   # Chugach Bay (29km to station)
    ("chuns-reef-beach",                      "1612480",  "noaa"),   # Chuns Reef Beach (37km to station)
    ("church-bay",                            "2695540",  "noaa"),   # Church Bay (19km to station)
    ("church-cove",                           "8452660",  "noaa"),   # Church Cove (11km to station)
    ("church-creek",                          "8575512",  "noaa"),   # Church Creek (6km to station)
    ("churchs-beach",                         "8447930",  "noaa"),   # Church's Beach (24km to station)
    ("churn-bay",                             "8761724",  "noaa"),   # Churn Bay (14km to station)
    ("cinnamon-bay-campground-beach",         "9751381",  "noaa"),   # Cinnamon Bay Campground Beach (5km to station)
    ("circle-beach",                          "8465705",  "noaa"),   # Circle Beach (22km to station)
    ("civic-center-bay",                      "9414523",  "noaa"),   # Civic Center Bay (22km to station)
    ("claiborne-cove",                        "9410170",  "noaa"),   # Claiborne Cove (8km to station)
    ("clam-bayou",                            "8726520",  "noaa"),   # Clam Bayou (7km to station)
    ("clam-beach",                            "9418767",  "noaa"),   # Clam Beach (27km to station)
    ("clam-cove",                             "8418150",  "noaa"),   # Clam Cove (13km to station)
    ("clambar-bay",                           "8726384",  "noaa"),   # Clambar Bay (4km to station)
    ("clambar-bayou",                         "8726384",  "noaa"),   # Clambar Bayou (12km to station)
    ("clamshell-cove",                        "8411060",  "noaa"),   # Clamshell Cove (12km to station)
    ("clarence-cove",                         "2695540",  "noaa"),   # Clarence Cove (12km to station)
    ("clarence-cove-beach",                   "2695540",  "noaa"),   # Clarence Cove Beach (12km to station)
    ("clark-cove",                            "8418150",  "noaa"),   # Clark Cove (26km to station)
    ("clark-sound",                           "8665530",  "noaa"),   # Clark Sound (7km to station)
    ("clarks-bay",                            "8652587",  "noaa"),   # Clarks Bay (30km to station)
    ("clarks-cove",                           "8447930",  "noaa"),   # Clarks Cove (22km to station)
    ("clay-cove",                             "8413320",  "noaa"),   # Clay Cove (25km to station)
    ("clay-island-creek",                     "8571421",  "noaa"),   # Clay Island Creek (8km to station)
    ("claybank-bay",                          "8311030",  "noaa"),   # Claybank Bay (10km to station)
    ("clean-shore",                           "8449130",  "noaa"),   # Clean Shore (1km to station)
    ("cleaves-cove",                          "8418150",  "noaa"),   # Cleaves Cove (38km to station)
    ("clement-cove",                          "8574680",  "noaa"),   # Clement Cove (7km to station)
    ("clements-creek",                        "8575512",  "noaa"),   # Clements Creek (6km to station)
    ("clermont-harbor-beach",                 "8747437",  "noaa"),   # Clermont Harbor Beach (12km to station)
    ("cliff-beach",                           "8449130",  "noaa"),   # Cliff Beach (2km to station)
    ("cliff-house-beach",                     "8418150",  "noaa"),   # Cliff House Beach (3km to station)
    ("cliff-metcalf-memorial-beach",          "8447435",  "noaa"),   # Cliff Metcalf Memorial Beach (14km to station)
    ("cliffs-bight",                          "8573364",  "noaa"),   # Cliffs Bight (14km to station)
    ("clinton-beach",                         "8465705",  "noaa"),   # Clinton Beach (34km to station)
    ("clinton-harbor",                        "8465705",  "noaa"),   # Clinton Harbor (32km to station)
    ("clinton-town-beach",                    "8465705",  "noaa"),   # Clinton Town Beach (32km to station)
    ("clipper-cove",                          "9414750",  "noaa"),   # Clipper Cove (8km to station)
    ("clissolds-beach",                       "1612480",  "noaa"),   # Clissolds Beach (27km to station)
    ("close-bay",                             "9451054",  "noaa"),   # Close Bay (39km to station)
    ("closson-cove",                          "8413320",  "noaa"),   # Closson Cove (25km to station)
    ("cloudman-bay",                          "9454240",  "noaa"),   # Cloudman Bay (37km to station)
    ("clover-bay",                            "9450460",  "noaa"),   # Clover Bay (33km to station)
    ("club-cove",                             "8574680",  "noaa"),   # Club Cove (9km to station)
    ("club-pond",                             "8760721",  "noaa"),   # Club Pond (4km to station)
    ("clubhouse-cove",                        "8418150",  "noaa"),   # Clubhouse Cove (26km to station)
    ("clubhouse-lagoon",                      "8534720",  "noaa"),   # Clubhouse Lagoon (20km to station)
    ("coakley-bay",                           "9751364",  "noaa"),   # Coakley Bay (6km to station)
    ("coal-bay",                              "9455500",  "noaa"),   # Coal Bay (25km to station)
    ("coal-cove",                             "9455500",  "noaa"),   # Coal Cove (11km to station)
    ("coal-tar-bay",                          "8761724",  "noaa"),   # Coal Tar Bay (34km to station)
    ("coalbin-rock",                          "8724580",  "noaa"),   # Coalbin Rock (30km to station)
    ("coast-guard-basin",                     "9099064",  "noaa"),   # Coast Guard Basin (0km to station)
    ("coast-guard-mooring-basin",             "8771450",  "noaa"),   # Coast Guard Mooring Basin (3km to station)
    ("coasters-harbor",                       "8452660",  "noaa"),   # Coasters Harbor (1km to station)
    ("coatue-beach",                          "8449130",  "noaa"),   # Coatue Beach (4km to station)
    ("cobb-bay",                              "8632200",  "noaa"),   # Cobb Bay (22km to station)
    ("cobble-beach",                          "8413320",  "noaa"),   # Cobble Beach (21km to station)
    ("cobble-stone-cove",                     "8418150",  "noaa"),   # Cobble Stone Cove (40km to station)
    ("cobbs-cove",                            "9455760",  "noaa"),   # Cobbs Cove (37km to station)
    ("cobham-bay",                            "8637689",  "noaa"),   # Cobham Bay (24km to station)
    ("coca-plum-beach",                       "8723970",  "noaa"),   # Coca Plum Beach (11km to station)
    ("cockenoe-bay",                          "8467150",  "noaa"),   # Cockenoe Bay (18km to station)
    ("cockenoe-harbor",                       "8467150",  "noaa"),   # Cockenoe Harbor (19km to station)
    ("cockey-creek",                          "8575512",  "noaa"),   # Cockey Creek (13km to station)
    ("cockle-cove",                           "8447435",  "noaa"),   # Cockle Cove (5km to station)
    ("cockler-bay",                           "8760721",  "noaa"),   # Cockler Bay (15km to station)
    ("cockroach-bay",                         "8726384",  "noaa"),   # Cockroach Bay (7km to station)
    ("cocktail-cove",                         "8418150",  "noaa"),   # Cocktail Cove (13km to station)
    ("cocoloba-beach",                        "9751381",  "noaa"),   # Cocoloba Beach (4km to station)
    ("coconut-bayou",                         "8726384",  "noaa"),   # Coconut Bayou (38km to station)
    ("coconut-beach",                         "9752695",  "noaa"),   # Coconut Beach (1km to station)
    ("coculus-bay",                           "9751381",  "noaa"),   # Coculus Bay (19km to station)
    ("cod-harbor",                            "8631044",  "noaa"),   # Cod Harbor (35km to station)
    ("coddington-cove",                       "8452660",  "noaa"),   # Coddington Cove (2km to station)
    ("codfish-cove",                          "9451054",  "noaa"),   # Codfish Cove (20km to station)
    ("coecles-harbor",                        "8510560",  "noaa"),   # Coecles Harbor (29km to station)
    ("coffee-ground-cove",                    "8770475",  "noaa"),   # Coffee Ground Cove (20km to station)
    ("coffin-pond",                           "8418150",  "noaa"),   # Coffin Pond (36km to station)
    ("coggeshall-cove",                       "8452944",  "noaa"),   # Coggeshall Cove (7km to station)
    ("cohansey-cove",                         "8537121",  "noaa"),   # Cohansey Cove (5km to station)
    ("coho-cove",                             "9450460",  "noaa"),   # Coho Cove (18km to station)
    ("coits-cove",                            "8461490",  "noaa"),   # Coits Cove (3km to station)
    ("coki-bay",                              "9751381",  "noaa"),   # Coki Bay (15km to station)
    ("coki-point-beach",                      "9751381",  "noaa"),   # Coki Point Beach (15km to station)
    ("cold-spring-beach",                     "8516945",  "noaa"),   # Cold Spring Beach (26km to station)
    ("cold-spring-cove",                      "8575512",  "noaa"),   # Cold Spring Cove (12km to station)
    ("cole-bay",                              "8311062",  "noaa"),   # Cole Bay (27km to station)
    ("coleman-arm",                           "9432780",  "noaa"),   # Coleman Arm (29km to station)
    ("coleman-cove",                          "8418150",  "noaa"),   # Coleman Cove (12km to station)
    ("college-cove",                          "9418767",  "noaa"),   # College Cove (34km to station)
    ("college-cove-north",                    "9418767",  "noaa"),   # College Cove North (34km to station)
    ("college-cove-south",                    "9418767",  "noaa"),   # College Cove South (34km to station)
    ("college-creek",                         "8575512",  "noaa"),   # College Creek (1km to station)
    ("collins-bay",                           "9052000",  "noaa"),   # Collins Bay (25km to station)
    ("collins-beach",                         "9440422",  "noaa"),   # Collins Beach (37km to station)
    ("collins-branch",                        "8411060",  "noaa"),   # Collins Branch (17km to station)
    ("collins-cove",                          "8461490",  "noaa"),   # Collins Cove (15km to station)
    ("colonel-willie-cove",                   "8461490",  "noaa"),   # Colonel Willie Cove (22km to station)
    ("colony-beach",                          "8419870",  "noaa"),   # Colony Beach (37km to station)
    ("colony-cove",                           "8735180",  "noaa"),   # Colony Cove (1km to station)
    ("colton-bay",                            "9075099",  "noaa"),   # Colton Bay (26km to station)
    ("colvins-cove",                          "8658120",  "noaa"),   # Colvins Cove (34km to station)
    ("comegys-bight",                         "8573364",  "noaa"),   # Comegys Bight (15km to station)
    ("comfort-cove",                          "9454050",  "noaa"),   # Comfort Cove (25km to station)
    ("commodore-beach",                       "8467150",  "noaa"),   # Commodore Beach (29km to station)
    ("compass-harbor",                        "8413320",  "noaa"),   # Compass Harbor (2km to station)
    ("compass-rose-beach",                    "8452660",  "noaa"),   # Compass Rose Beach (12km to station)
    ("compo-cove",                            "8467150",  "noaa"),   # Compo Cove (15km to station)
    ("comstock-bay",                          "9075065",  "noaa"),   # Comstock Bay (30km to station)
    ("conary-cove",                           "8413320",  "noaa"),   # Conary Cove (37km to station)
    ("conaumet-cove",                         "8447930",  "noaa"),   # Conaumet Cove (23km to station)
    ("concord-gulf-cove",                     "8452660",  "noaa"),   # Concord Gulf Cove (5km to station)
    ("cone-bay",                              "9099090",  "noaa"),   # Cone Bay (35km to station)
    ("confederate-pass",                      "8735180",  "noaa"),   # Confederate Pass (2km to station)
    ("congdon-cove",                          "8452660",  "noaa"),   # Congdon Cove (18km to station)
    ("congdons-creek",                        "8510560",  "noaa"),   # Congdons Creek (30km to station)
    ("conger-bay",                            "8311062",  "noaa"),   # Conger Bay (28km to station)
    ("connolly-cove",                         "8571892",  "noaa"),   # Connolly Cove (9km to station)
    ("conquest-beach",                        "8573364",  "noaa"),   # Conquest Beach (16km to station)
    ("conrad-creek",                          "8721604",  "noaa"),   # Conrad Creek (18km to station)
    ("conscience-bay",                        "8467150",  "noaa"),   # Conscience Bay (25km to station)
    ("constantine-cove",                      "9452634",  "noaa"),   # Constantine Cove (39km to station)
    ("contee-lake",                           "8773037",  "noaa"),   # Contee Lake (19km to station)
    ("contention-cove",                       "8413320",  "noaa"),   # Contention Cove (24km to station)
    ("convict-bay",                           "2695535",  "noaa"),   # Convict Bay (2km to station)
    ("cony-beach",                            "8410140",  "noaa"),   # Cony Beach (2km to station)
    ("conyers-bay",                           "2695540",  "noaa"),   # Conyers Bay (20km to station)
    ("cook-cove",                             "8410140",  "noaa"),   # Cook Cove (28km to station)
    ("cook-point-cove",                       "8571892",  "noaa"),   # Cook Point Cove (19km to station)
    ("cooks-chasm",                           "9435380",  "noaa"),   # Cooks Chasm (39km to station)
    ("cool-spring-cove",                      "8575512",  "noaa"),   # Cool Spring Cove (9km to station)
    ("coon-cove",                             "9450460",  "noaa"),   # Coon Cove (17km to station)
    ("coon-outside-pond",                     "8760721",  "noaa"),   # Coon Outside Pond (11km to station)
    ("cooper-bayou",                          "8726724",  "noaa"),   # Cooper Bayou (13km to station)
    ("coot-cove",                             "9452210",  "noaa"),   # Coot Cove (29km to station)
    ("coot-pond",                             "2695535",  "noaa"),   # Coot Pond (3km to station)
    ("copahee-sound",                         "8665530",  "noaa"),   # Copahee Sound (19km to station)
    ("copiague-beach",                        "8516945",  "noaa"),   # Copiague Beach (35km to station)
    ("copps-cave",                            "8454000",  "noaa"),   # Copps Cave (4km to station)
    ("copps-cove",                            "8454000",  "noaa"),   # Copps Cove (3km to station)
    ("coral-bay",                             "9751381",  "noaa"),   # Coral Bay (4km to station)
    ("coral-harbor",                          "9751381",  "noaa"),   # Coral Harbor (3km to station)
    ("corallina-cove",                        "9412110",  "noaa"),   # Corallina Cove (17km to station)
    ("cordreys-beach",                        "8635750",  "noaa"),   # Cordreys Beach (9km to station)
    ("corea-harbor",                          "8413320",  "noaa"),   # Corea Harbor (19km to station)
    ("corey-cove",                            "8773037",  "noaa"),   # Corey Cove (18km to station)
    ("corey-creek",                           "8510560",  "noaa"),   # Corey Creek (39km to station)
    ("corliss-cove",                          "8454000",  "noaa"),   # Corliss Cove (1km to station)
    ("cormorant-beach",                       "9751364",  "noaa"),   # Cormorant Beach (6km to station)
    ("cormorant-beach-club",                  "9751364",  "noaa"),   # Cormorant Beach Club (6km to station)
    ("corn-cove",                             "8510560",  "noaa"),   # Corn Cove (36km to station)
    ("cornfield-creek",                       "8575512",  "noaa"),   # Cornfield Creek (13km to station)
    ("cornfield-harbor",                      "8635750",  "noaa"),   # Cornfield Harbor (13km to station)
    ("coronado-cove",                         "8735180",  "noaa"),   # Coronado Cove (3km to station)
    ("coronado-shores-beach",                 "9410170",  "noaa"),   # Coronado Shores Beach (4km to station)
    ("corps-of-engineers-slip",               "8770475",  "noaa"),   # Corps of Engineers Slip (0km to station)
    ("corpus-christi-channel",                "8775237",  "noaa"),   # Corpus Christi Channel (2km to station)
    ("corpus-christi-north-beach",            "8775296",  "noaa"),   # Corpus Christi North Beach (1km to station)
    ("corrotoman-river",                      "8635750",  "noaa"),   # Corrotoman River (35km to station)
    ("corson-inlet",                          "8534720",  "noaa"),   # Corson Inlet (26km to station)
    ("corson-sound",                          "8534720",  "noaa"),   # Corson Sound (26km to station)
    ("cosmos-cove",                           "9451600",  "noaa"),   # Cosmos Cove (36km to station)
    ("coster-cove",                           "8577330",  "noaa"),   # Coster Cove (4km to station)
    ("cottage-beach",                         "8661070",  "noaa"),   # Cottage Beach (17km to station)
    ("cottage-cove",                          "8411060",  "noaa"),   # Cottage Cove (12km to station)
    ("cotter-cove",                           "8570283",  "noaa"),   # Cotter Cove (24km to station)
    ("cottongarden-bay",                      "9751364",  "noaa"),   # Cottongarden Bay (12km to station)
    ("cottongarden-bay-beach",                "9751364",  "noaa"),   # Cottongarden Bay Beach (12km to station)
    ("cottonwood-beach",                      "9440422",  "noaa"),   # Cottonwood Beach (5km to station)
    ("cottonwood-cove",                       "9449880",  "noaa"),   # Cottonwood Cove (18km to station)
    ("coule-pond",                            "8760721",  "noaa"),   # Coule Pond (4km to station)
    ("coults-hole",                           "8461490",  "noaa"),   # Coults Hole (22km to station)
    ("coupon-bight",                          "8723970",  "noaa"),   # Coupon Bight (26km to station)
    ("court-of-the-duke",                     "8311062",  "noaa"),   # Court of the Duke (31km to station)
    ("cove-1",                                "9446484",  "noaa"),   # Cove 1 (36km to station)
    ("cove-2",                                "9446484",  "noaa"),   # Cove 2 (36km to station)
    ("cove-3",                                "9446484",  "noaa"),   # Cove 3 (36km to station)
    ("cove-harbor",                           "8467150",  "noaa"),   # Cove Harbor (30km to station)
    ("cove-island-bay",                       "9459881",  "noaa"),   # Cove Island Bay (39km to station)
    ("cove-number-two",                       "8557380",  "noaa"),   # Cove Number Two (23km to station)
    ("cove-point-beach",                      "8577330",  "noaa"),   # Cove Point Beach (9km to station)
    ("cove-point-hollow",                     "8577330",  "noaa"),   # Cove Point Hollow (9km to station)
    ("cove-slough",                           "9459881",  "noaa"),   # Cove Slough (38km to station)
    ("cove-of-cork",                          "8575512",  "noaa"),   # Cove of Cork (3km to station)
    ("covey-creek",                           "8571892",  "noaa"),   # Covey Creek (18km to station)
    ("covington-cove",                        "8575512",  "noaa"),   # Covington Cove (31km to station)
    ("cow-cove",                              "8452660",  "noaa"),   # Cow Cove (37km to station)
    ("cow-creek",                             "8651370",  "noaa"),   # Cow Creek (24km to station)
    ("cow-gap-creek",                         "8571421",  "noaa"),   # Cow Gap Creek (37km to station)
    ("cow-pen-creek",                         "8721604",  "noaa"),   # Cow Pen Creek (34km to station)
    ("cow-point-creek",                       "8571421",  "noaa"),   # Cow Point Creek (34km to station)
    ("cowell-ranch-beach",                    "9414523",  "noaa"),   # Cowell Ranch Beach (22km to station)
    ("cowpet-bay",                            "9751381",  "noaa"),   # Cowpet Bay (12km to station)
    ("cox-bay",                               "8773259",  "noaa"),   # Cox Bay (9km to station)
    ("cox-creek",                             "8575512",  "noaa"),   # Cox Creek (16km to station)
    ("coxs-bay",                              "2695540",  "noaa"),   # Cox's Bay (10km to station)
    ("crab-bay",                              "9451600",  "noaa"),   # Crab Bay (16km to station)
    ("crab-cove",                             "8447930",  "noaa"),   # Crab Cove (25km to station)
    ("crab-creek",                            "8575512",  "noaa"),   # Crab Creek (5km to station)
    ("crab-meadow-beach",                     "8467150",  "noaa"),   # Crab Meadow Beach (30km to station)
    ("crab-point-bay",                        "8656483",  "noaa"),   # Crab Point Bay (5km to station)
    ("crab-point-cove",                       "8571421",  "noaa"),   # Crab Point Cove (7km to station)
    ("cramer-park-beach",                     "9751364",  "noaa"),   # Cramer Park Beach (12km to station)
    ("cranberry-cove",                        "8411060",  "noaa"),   # Cranberry Cove (35km to station)
    ("cranberry-harbor",                      "8413320",  "noaa"),   # Cranberry Harbor (16km to station)
    ("cranberry-slough",                      "9468333",  "noaa"),   # Cranberry Slough (1km to station)
    ("crandon-beach",                         "8723214",  "noaa"),   # Crandon Beach (3km to station)
    ("crandon-park-beach",                    "8723214",  "noaa"),   # Crandon Park Beach (4km to station)
    ("crane-bayou",                           "8770475",  "noaa"),   # Crane Bayou (13km to station)
    ("crane-cove",                            "8571421",  "noaa"),   # Crane Cove (27km to station)
    ("cranetown-bay",                         "8747437",  "noaa"),   # Cranetown Bay (39km to station)
    ("cranston-cove",                         "8452660",  "noaa"),   # Cranston Cove (5km to station)
    ("crawfish-inlet",                        "9451600",  "noaa"),   # Crawfish Inlet (33km to station)
    ("creamery-bay",                          "9415020",  "noaa"),   # Creamery Bay (8km to station)
    ("creasy-cove",                           "8413320",  "noaa"),   # Creasy Cove (20km to station)
    ("creek-club-beach",                      "8516945",  "noaa"),   # Creek Club Beach (18km to station)
    ("cremona-creek",                         "8577330",  "noaa"),   # Cremona Creek (23km to station)
    ("creole-bay",                            "8761724",  "noaa"),   # Creole Bay (13km to station)
    ("crescent-harbor",                       "9419750",  "noaa"),   # Crescent Harbor (1km to station)
    ("crescent-sail-club-beach-private",      "9014070",  "noaa"),   # Crescent Sail Club Beach (Private) (38km to station)
    ("crescent-surf",                         "8419870",  "noaa"),   # Crescent Surf (33km to station)
    ("critical-bayou",                        "8726384",  "noaa"),   # Critical Bayou (9km to station)
    ("croaker-hole",                          "8775283",  "noaa"),   # Croaker Hole (10km to station)
    ("cromwell-cove",                         "8413320",  "noaa"),   # Cromwell Cove (2km to station)
    ("cromwells-beach",                       "1612340",  "noaa"),   # Cromwell's Beach (9km to station)
    ("crooked-thorofare-cove",                "8536110",  "noaa"),   # Crooked Thorofare Cove (17km to station)
    ("crooks-bay",                            "9751381",  "noaa"),   # Crooks Bay (33km to station)
    ("cross-bay",                             "2695540",  "noaa"),   # Cross Bay (18km to station)
    ("cross-bayou",                           "8726520",  "noaa"),   # Cross Bayou (15km to station)
    ("cross-cove",                            "8411060",  "noaa"),   # Cross Cove (34km to station)
    ("cross-sound",                           "9452634",  "noaa"),   # Cross Sound (10km to station)
    ("crossmon-bay",                          "8311062",  "noaa"),   # Crossmon Bay (2km to station)
    ("crow-bay",                              "8632200",  "noaa"),   # Crow Bay (20km to station)
    ("crow-beach",                            "9446484",  "noaa"),   # Crow Beach (17km to station)
    ("crowes-pasture",                        "8447435",  "noaa"),   # Crowe's Pasture (17km to station)
    ("crowley-bight",                         "9451054",  "noaa"),   # Crowley Bight (30km to station)
    ("crown-bay",                             "9751381",  "noaa"),   # Crown Bay (24km to station)
    ("crown-cove",                            "9410170",  "noaa"),   # Crown Cove (9km to station)
    ("crown-point-shores",                    "9410170",  "noaa"),   # Crown Point Shores (9km to station)
    ("crystal-beach",                         "8770971",  "noaa"),   # Crystal Beach (13km to station)
    ("cub-cove",                              "8418150",  "noaa"),   # Cub Cove (38km to station)
    ("cuckold-creek",                         "8577330",  "noaa"),   # Cuckold Creek (6km to station)
    ("cudjoe-basin",                          "8724580",  "noaa"),   # Cudjoe Basin (33km to station)
    ("cudjoe-bay",                            "8724580",  "noaa"),   # Cudjoe Bay (34km to station)
    ("cueva-de-la-julia",                     "9759110",  "noaa"),   # Cueva de la Julia (13km to station)
    ("cuffeys-cove",                          "9416841",  "noaa"),   # Cuffeys Cove (25km to station)
    ("cuffeys-inlet",                         "9416841",  "noaa"),   # Cuffeys Inlet (25km to station)
    ("culbreath-bayou",                       "8726607",  "noaa"),   # Culbreath Bayou (9km to station)
    ("cumberland-sound",                      "8720218",  "noaa"),   # Cumberland Sound (36km to station)
    ("cummings-creek",                        "8575512",  "noaa"),   # Cummings Creek (28km to station)
    ("cummings-park-beach",                   "8467150",  "noaa"),   # Cummings Park Beach (32km to station)
    ("cummings-point",                        "8665530",  "noaa"),   # Cummings Point (7km to station)
    ("cundy-harbor",                          "8418150",  "noaa"),   # Cundy Harbor (32km to station)
    ("cunningham-bay",                        "8311062",  "noaa"),   # Cunningham Bay (39km to station)
    ("cunninghill-cove",                      "8573364",  "noaa"),   # Cunninghill Cove (18km to station)
    ("curlew-bay",                            "8631044",  "noaa"),   # Curlew Bay (3km to station)
    ("curlew-ledge",                          "9452210",  "noaa"),   # Curlew Ledge (30km to station)
    ("currell-cove",                          "8635750",  "noaa"),   # Currell Cove (38km to station)
    ("curriers-cove",                         "8419870",  "noaa"),   # Curriers Cove (2km to station)
    ("currioman-bay",                         "8635750",  "noaa"),   # Currioman Bay (30km to station)
    ("curtis-bay",                            "8574680",  "noaa"),   # Curtis Bay (5km to station)
    ("curtis-cove",                           "8418150",  "noaa"),   # Curtis Cove (30km to station)
    ("cuselich-bay",                          "8760721",  "noaa"),   # Cuselich Bay (36km to station)
    ("custer-bayou",                          "8726384",  "noaa"),   # Custer Bayou (8km to station)
    ("custis-cove",                           "8631044",  "noaa"),   # Custis Cove (20km to station)
    ("customhouse-bay",                       "8760721",  "noaa"),   # Customhouse Bay (18km to station)
    ("customhouse-cove",                      "9450460",  "noaa"),   # Customhouse Cove (37km to station)
    ("cutter-cove",                           "9415102",  "noaa"),   # Cutter Cove (14km to station)
    ("cutting-shed-cove",                     "8418150",  "noaa"),   # Cutting Shed Cove (3km to station)
    ("cuttyhunk-harbor",                      "8447930",  "noaa"),   # Cuttyhunk Harbor (23km to station)
    ("cuvacan-cove",                          "9451600",  "noaa"),   # Cuvacan Cove (30km to station)
    ("cypress-bay",                           "8661070",  "noaa"),   # Cypress Bay (13km to station)
    ("cypress-cove",                          "9413450",  "noaa"),   # Cypress Cove (11km to station)
    ("cypress-creek",                         "8575512",  "noaa"),   # Cypress Creek (11km to station)
    ("cyprien-bay",                           "8760721",  "noaa"),   # Cyprien Bay (30km to station)
    ("dolive-bay",                            "8737048",  "noaa"),   # D'Olive Bay (13km to station)
    ("dt-fleming-beach",                      "1615680",  "noaa"),   # D.T. Fleming Beach (23km to station)
    ("dabob-broad-spit",                      "9444900",  "noaa"),   # Dabob Broad Spit (34km to station)
    ("dalehite-cove",                         "8771486",  "noaa"),   # Dalehite Cove (10km to station)
    ("dall-bay",                              "9450460",  "noaa"),   # Dall Bay (21km to station)
    ("dam-cove",                              "8418150",  "noaa"),   # Dam Cove (38km to station)
    ("dames-quarter-creek",                   "8571421",  "noaa"),   # Dames Quarter Creek (14km to station)
    ("dan-bay",                               "8767816",  "noaa"),   # Dan Bay (13km to station)
    ("dan-slide",                             "8767816",  "noaa"),   # Dan Slide (12km to station)
    ("dans-cove",                             "9455500",  "noaa"),   # Dan's Cove (3km to station)
    ("dana-cove",                             "8771486",  "noaa"),   # Dana Cove (12km to station)
    ("danbury-bay",                           "8467150",  "noaa"),   # Danbury Bay (37km to station)
    ("danforth-cove",                         "8418150",  "noaa"),   # Danforth Cove (3km to station)
    ("danforth-cove-beach",                   "8418150",  "noaa"),   # Danforth Cove Beach (3km to station)
    ("daniel-ave-beach",                      "8465705",  "noaa"),   # Daniel Ave. Beach (19km to station)
    ("dare-beach",                            "9443090",  "noaa"),   # Dare Beach (33km to station)
    ("dash-point-state-park-beach",           "9446484",  "noaa"),   # Dash Point State Park Beach (6km to station)
    ("daugherty-creek",                       "8571421",  "noaa"),   # Daugherty Creek (28km to station)
    ("daughtry-bayou",                        "8727520",  "noaa"),   # Daughtry Bayou (1km to station)
    ("dauphin-beach",                         "8735180",  "noaa"),   # Dauphin Beach (4km to station)
    ("dave-inside-pond",                      "8760721",  "noaa"),   # Dave Inside Pond (7km to station)
    ("dave-outside-pond",                     "8760721",  "noaa"),   # Dave Outside Pond (8km to station)
    ("davis-creek",                           "8635750",  "noaa"),   # Davis Creek (30km to station)
    ("davis-hole",                            "2695535",  "noaa"),   # Davis Hole (1km to station)
    ("day-inlet",                             "9432780",  "noaa"),   # Day Inlet (3km to station)
    ("de-anza-cove",                          "9410230",  "noaa"),   # De Anza Cove (9km to station)
    ("decoursey-cove",                        "8575512",  "noaa"),   # DeCoursey Cove (30km to station)
    ("degroff-bay",                           "9451600",  "noaa"),   # DeGroff Bay (19km to station)
    ("detour-reef",                           "9075099",  "noaa"),   # DeTour Reef (4km to station)
    ("dead-boys-bay",                         "9076024",  "noaa"),   # Dead Boy's Bay (19km to station)
    ("dead-horse-bay",                        "8531680",  "noaa"),   # Dead Horse Bay (16km to station)
    ("dead-mans-cove",                        "8574680",  "noaa"),   # Dead Man's Cove (22km to station)
    ("dead-women-bend",                       "8760721",  "noaa"),   # Dead Women Bend (14km to station)
    ("dead-women-inside-pond",                "8760721",  "noaa"),   # Dead Women Inside Pond (11km to station)
    ("dead-women-outside-pond",               "8760721",  "noaa"),   # Dead Women Outside Pond (12km to station)
    ("dead-and-bones-cove",                   "8635750",  "noaa"),   # Dead and Bones Cove (36km to station)
    ("deadman-bay",                           "9052000",  "noaa"),   # Deadman Bay (15km to station)
    ("deadman-pond",                          "8760721",  "noaa"),   # Deadman Pond (10km to station)
    ("deadwood-cove",                         "8575512",  "noaa"),   # Deadwood Cove (15km to station)
    ("dean-brook-cove",                       "8413320",  "noaa"),   # Dean Brook Cove (39km to station)
    ("deans-hole",                            "8557380",  "noaa"),   # Deans Hole (23km to station)
    ("deary-cove",                            "8639348",  "noaa"),   # Deary Cove (27km to station)
    ("death-pond",                            "8760721",  "noaa"),   # Death Pond (6km to station)
    ("deckbay",                               "9751381",  "noaa"),   # Deckbay (24km to station)
    ("deemers-beach",                         "8551910",  "noaa"),   # Deemer's Beach (10km to station)
    ("deep-bay",                              "8652587",  "noaa"),   # Deep Bay (34km to station)
    ("deep-bend",                             "8656483",  "noaa"),   # Deep Bend (40km to station)
    ("deep-bottom-cove",                      "8447930",  "noaa"),   # Deep Bottom Cove (18km to station)
    ("deep-creek",                            "8575512",  "noaa"),   # Deep Creek (19km to station)
    ("deep-gut",                              "8656483",  "noaa"),   # Deep Gut (35km to station)
    ("deep-hole",                             "8557380",  "noaa"),   # Deep Hole (24km to station)
    ("deep-inlet",                            "9451600",  "noaa"),   # Deep Inlet (11km to station)
    ("deep-lagoon",                           "8725520",  "noaa"),   # Deep Lagoon (13km to station)
    ("deep-lake",                             "8761724",  "noaa"),   # Deep Lake (38km to station)
    ("deep-river-cove",                       "8461490",  "noaa"),   # Deep River Cove (28km to station)
    ("deephead-swash",                        "8661070",  "noaa"),   # Deephead Swash (11km to station)
    ("deer-creek",                            "8652587",  "noaa"),   # Deer Creek (31km to station)
    ("deer-field-shores",                     "8656483",  "noaa"),   # Deer Field Shores (5km to station)
    ("deer-pond",                             "8656483",  "noaa"),   # Deer Pond (21km to station)
    ("del-mar-dog-beach",                     "9410230",  "noaa"),   # Del Mar Dog Beach (12km to station)
    ("delancey-cove",                         "8516945",  "noaa"),   # Delancey Cove (13km to station)
    ("delaney-bay",                           "8311062",  "noaa"),   # Delaney Bay (13km to station)
    ("delarof-harbor",                        "9459450",  "noaa"),   # Delarof Harbor (17km to station)
    ("deleware-avenue-beach",                 "9063079",  "noaa"),   # Deleware Avenue Beach (14km to station)
    ("delray-public-beach",                   "8722670",  "noaa"),   # Delray Public Beach (13km to station)
    ("dels-boat-basin",                       "9052000",  "noaa"),   # Dels Boat Basin (18km to station)
    ("delta-basin",                           "8534720",  "noaa"),   # Delta Basin (2km to station)
    ("delta-bend",                            "8760721",  "noaa"),   # Delta Bend (13km to station)
    ("delvan-bay",                            "8737048",  "noaa"),   # Delvan Bay (5km to station)
    ("delwood-beach",                         "8729108",  "noaa"),   # Delwood Beach (5km to station)
    ("denis-bay",                             "9751381",  "noaa"),   # Denis Bay (7km to station)
    ("densmore-bay",                          "8311062",  "noaa"),   # Densmore Bay (1km to station)
    ("depot-street-beach",                    "8447435",  "noaa"),   # Depot Street Beach (15km to station)
    ("dering-harbor",                         "8510560",  "noaa"),   # Dering Harbor (33km to station)
    ("dermo-bayou",                           "9087031",  "noaa"),   # Dermo Bayou (30km to station)
    ("derring-gully",                         "8770475",  "noaa"),   # Derring Gully (10km to station)
    ("desert-cove",                           "8638610",  "noaa"),   # Desert Cove (14km to station)
    ("devers-bay",                            "9751381",  "noaa"),   # Devers Bay (6km to station)
    ("devils-bathing-beach",                  "8418150",  "noaa"),   # Devil's Bathing Beach (4km to station)
    ("devils-bay",                            "9751381",  "noaa"),   # Devil's Bay (32km to station)
    ("devils-hole",                           "2695535",  "noaa"),   # Devil's Hole (6km to station)
    ("devils-churn",                          "9435380",  "noaa"),   # Devils Churn (38km to station)
    ("devils-slide-beach",                    "9414290",  "noaa"),   # Devils Slide Beach (27km to station)
    ("devils-punchbowl",                      "9444090",  "noaa"),   # Devil’s Punchbowl (26km to station)
    ("devonshire-bay",                        "2695540",  "noaa"),   # Devonshire Bay (9km to station)
    ("devonshire-bay-beach",                  "2695540",  "noaa"),   # Devonshire Bay Beach (9km to station)
    ("devore-arm",                            "9432780",  "noaa"),   # Devore Arm (27km to station)
    ("dewees-inlet",                          "8665530",  "noaa"),   # Dewees Inlet (19km to station)
    ("diamond-cove",                          "8418150",  "noaa"),   # Diamond Cove (5km to station)
    ("dibblees-beach",                        "9440422",  "noaa"),   # Dibblees Beach (3km to station)
    ("dick-bay",                              "8658163",  "noaa"),   # Dick Bay (16km to station)
    ("dickerman-cut",                         "8728690",  "noaa"),   # Dickerman Cut (33km to station)
    ("dickerson-creek",                       "8510560",  "noaa"),   # Dickerson Creek (32km to station)
    ("dickinson-bay",                         "8571892",  "noaa"),   # Dickinson Bay (6km to station)
    ("digdeguash-basin",                      "8410140",  "noaa"),   # Digdeguash Basin (32km to station)
    ("dingley-cove",                          "8418150",  "noaa"),   # Dingley Cove (33km to station)
    ("dipper-cove",                           "8418150",  "noaa"),   # Dipper Cove (27km to station)
    ("ditch-cove",                            "8656483",  "noaa"),   # Ditch Cove (20km to station)
    ("ditleff-beach",                         "9751381",  "noaa"),   # Ditleff Beach (4km to station)
    ("dividing-creek",                        "8575512",  "noaa"),   # Dividing Creek (10km to station)
    ("dix-cove",                              "8631044",  "noaa"),   # Dix Cove (21km to station)
    ("dixie-beach",                           "8725520",  "noaa"),   # Dixie Beach (27km to station)
    ("dixon-bay",                             "8760721",  "noaa"),   # Dixon Bay (11km to station)
    ("dixons-bay",                            "8311062",  "noaa"),   # Dixons Bay (21km to station)
    ("dixson-st-beach",                       "8465705",  "noaa"),   # Dixson St. Beach (10km to station)
    ("dobbins-pond",                          "8575512",  "noaa"),   # Dobbins Pond (11km to station)
    ("doctors-arm",                           "8723970",  "noaa"),   # Doctors Arm (25km to station)
    ("dodge-bay",                             "9052000",  "noaa"),   # Dodge Bay (10km to station)
    ("doe-bay",                               "2695540",  "noaa"),   # Doe Bay (10km to station)
    ("dog-beach",                             "8575512",  "noaa"),   # Dog Beach (15km to station)
    ("dogfish-cove",                          "8413320",  "noaa"),   # Dogfish Cove (20km to station)
    ("doghole-basin",                         "8729840",  "noaa"),   # Doghole Basin (24km to station)
    ("dogwood-harbor",                        "8571892",  "noaa"),   # Dogwood Harbor (27km to station)
    ("dolgoi-harbor",                         "9459881",  "noaa"),   # Dolgoi Harbor (36km to station)
    ("dollar-bay",                            "8771013",  "noaa"),   # Dollar Bay (6km to station)
    ("dolly-bay",                             "8726724",  "noaa"),   # Dolly Bay (18km to station)
    ("dollys-bay",                            "2695535",  "noaa"),   # Dolly's Bay (3km to station)
    ("dolomi-bay",                            "9450460",  "noaa"),   # Dolomi Bay (35km to station)
    ("dolphin-beach",                         "8594900",  "noaa"),   # Dolphin Beach (40km to station)
    ("donaldson-bay",                         "8311062",  "noaa"),   # Donaldson Bay (26km to station)
    ("donkey-beach",                          "1611400",  "noaa"),   # Donkey Beach (19km to station)
    ("donlins-cove",                          "8635750",  "noaa"),   # Donlins Cove (15km to station)
    ("donovan-cove",                          "8411060",  "noaa"),   # Donovan Cove (35km to station)
    ("door-point-lagoon",                     "8747437",  "noaa"),   # Door Point Lagoon (32km to station)
    ("dorado-del-mar-beach",                  "9755371",  "noaa"),   # Dorado del Mar Beach (17km to station)
    ("dorenoi-bay",                           "9459450",  "noaa"),   # Dorenoi Bay (35km to station)
    ("dorothea-bay",                          "9751381",  "noaa"),   # Dorothea Bay (26km to station)
    ("dorothy-cove",                          "9451600",  "noaa"),   # Dorothy Cove (40km to station)
    ("dorries-cove",                          "8510560",  "noaa"),   # Dorrie's Cove (32km to station)
    ("dorseys-cove",                          "8418150",  "noaa"),   # Dorseys Cove (8km to station)
    ("dossin-park-beach",                     "8465705",  "noaa"),   # Dossin Park Beach (27km to station)
    ("doty-cove",                             "9452210",  "noaa"),   # Doty Cove (24km to station)
    ("double-bayou",                          "8728690",  "noaa"),   # Double Bayou (16km to station)
    ("double-bluff-beach",                    "9444900",  "noaa"),   # Double Bluff Beach (23km to station)
    ("double-bluff-county-park",              "9444900",  "noaa"),   # Double Bluff County Park (23km to station)
    ("double-branch-bay",                     "8726607",  "noaa"),   # Double Branch Bay (18km to station)
    ("double-headshot-cove",                  "8411060",  "noaa"),   # Double Headshot Cove (8km to station)
    ("dougs-cove",                            "8447930",  "noaa"),   # Doug's Cove (10km to station)
    ("doughty-cove",                          "8418150",  "noaa"),   # Doughty Cove (34km to station)
    ("douglas-island-harbor",                 "8413320",  "noaa"),   # Douglas Island Harbor (29km to station)
    ("doves-cove",                            "8573364",  "noaa"),   # Doves Cove (18km to station)
    ("dowdy-bay",                             "8656483",  "noaa"),   # Dowdy Bay (38km to station)
    ("dowest-slough",                         "9415144",  "noaa"),   # Dowest Slough (18km to station)
    ("doyle-cove",                            "8635750",  "noaa"),   # Doyle Cove (20km to station)
    ("drakes-estero",                         "9415020",  "noaa"),   # Drakes Estero (6km to station)
    ("dredge-harbor",                         "8546252",  "noaa"),   # Dredge Harbor (10km to station)
    ("dredgeboat-slough",                     "8771341",  "noaa"),   # Dredgeboat Slough (12km to station)
    ("drew-cove",                             "8447930",  "noaa"),   # Drew Cove (9km to station)
    ("drews-bay",                             "2695535",  "noaa"),   # Drew's Bay (3km to station)
    ("driftwood-bay",                         "9462620",  "noaa"),   # Driftwood Bay (24km to station)
    ("driftwood-cove",                        "9451054",  "noaa"),   # Driftwood Cove (11km to station)
    ("drouard-bay",                           "9014070",  "noaa"),   # Drouard Bay (12km to station)
    ("druif-bay",                             "9751381",  "noaa"),   # Druif Bay (25km to station)
    ("drum-bay",                              "8635750",  "noaa"),   # Drum Bay (20km to station)
    ("drum-bed",                              "8537121",  "noaa"),   # Drum Bed (9km to station)
    ("drum-cove",                             "8635750",  "noaa"),   # Drum Cove (8km to station)
    ("drummer-cove",                          "8447435",  "noaa"),   # Drummer Cove (25km to station)
    ("drunk-bay",                             "9751381",  "noaa"),   # Drunk Bay (3km to station)
    ("dubois-beach",                          "8461490",  "noaa"),   # DuBois Beach (16km to station)
    ("ducan-slough",                          "9455500",  "noaa"),   # Ducan Slough (12km to station)
    ("duck-creek",                            "8447435",  "noaa"),   # Duck Creek (27km to station)
    ("duck-harbor-beach",                     "8447435",  "noaa"),   # Duck Harbor Beach (30km to station)
    ("duck-hole",                             "8651370",  "noaa"),   # Duck Hole (16km to station)
    ("duck-island-cove",                      "8571421",  "noaa"),   # Duck Island Cove (8km to station)
    ("duck-island-harbor",                    "8467150",  "noaa"),   # Duck Island Harbor (32km to station)
    ("duck-island-roads",                     "8461490",  "noaa"),   # Duck Island Roads (35km to station)
    ("duck-point-cove",                       "8571421",  "noaa"),   # Duck Point Cove (8km to station)
    ("duck-pond",                             "8721604",  "noaa"),   # Duck Pond (5km to station)
    ("ducker-bay",                            "8737048",  "noaa"),   # Ducker Bay (11km to station)
    ("duckroost-cove",                        "8721604",  "noaa"),   # Duckroost Cove (40km to station)
    ("dudley-bay",                            "9075099",  "noaa"),   # Dudley Bay (20km to station)
    ("duffy-cove",                            "8413320",  "noaa"),   # Duffy Cove (26km to station)
    ("dukes-lake-beach",                      "9076027",  "noaa"),   # Dukes Lake Beach (18km to station)
    ("duluth-harbor-basin",                   "9099064",  "noaa"),   # Duluth Harbor Basin (1km to station)
    ("duluth-harbor-basin-northern-section",  "9099064",  "noaa"),   # Duluth Harbor Basin Northern Section (1km to station)
    ("duluth-harbor-basin-southern-section",  "9099064",  "noaa"),   # Duluth Harbor Basin Southern Section (2km to station)
    ("dume-cove",                             "9410840",  "noaa"),   # Dume Cove (28km to station)
    ("dumfoundling-bay",                      "8722956",  "noaa"),   # Dumfoundling Bay (15km to station)
    ("dummit-cove",                           "8721604",  "noaa"),   # Dummit Cove (37km to station)
    ("dun-cove",                              "8571892",  "noaa"),   # Dun Cove (29km to station)
    ("duncan-bay",                            "9075080",  "noaa"),   # Duncan Bay (26km to station)
    ("dundas-bay",                            "9452634",  "noaa"),   # Dundas Bay (18km to station)
    ("dundee-creek",                          "8573364",  "noaa"),   # Dundee Creek (18km to station)
    ("dune-drift-beach",                      "9416841",  "noaa"),   # Dune Drift Beach (28km to station)
    ("dune-pond",                             "8760721",  "noaa"),   # Dune Pond (12km to station)
    ("dunedin-beach",                         "8726724",  "noaa"),   # Dunedin Beach (9km to station)
    ("dunes-landing-beach",                   "8447435",  "noaa"),   # Dunes Landing Beach (23km to station)
    ("dungan-cove",                           "8635750",  "noaa"),   # Dungan Cove (6km to station)
    ("dunham-bay",                            "8774513",  "noaa"),   # Dunham Bay (11km to station)
    ("dunhams-cove",                          "8413320",  "noaa"),   # Dunhams Cove (24km to station)
    ("dunlevy-bay",                           "9087031",  "noaa"),   # Dunlevy Bay (37km to station)
    ("dunn-beach",                            "8413320",  "noaa"),   # Dunn Beach (37km to station)
    ("dunn-sound",                            "8661070",  "noaa"),   # Dunn Sound (38km to station)
    ("dunnings-lagoon",                       "9455500",  "noaa"),   # Dunnings Lagoon (14km to station)
    ("dunton-cove",                           "8632200",  "noaa"),   # Dunton Cove (6km to station)
    ("dutch-island-harbor",                   "8452660",  "noaa"),   # Dutch Island Harbor (6km to station)
    ("dutch-john-bay",                        "9052000",  "noaa"),   # Dutch John Bay (25km to station)
    ("duvall-creek",                          "8575512",  "noaa"),   # Duvall Creek (6km to station)
    ("dyckman-street-beach",                  "8516945",  "noaa"),   # Dyckman Street Beach (16km to station)
    ("dyer-bay",                              "8413320",  "noaa"),   # Dyer Bay (23km to station)
    ("dyer-cove",                             "8537121",  "noaa"),   # Dyer Cove (15km to station)
    ("dyer-harbor",                           "8413320",  "noaa"),   # Dyer Harbor (24km to station)
    ("eagers-bay",                            "8311030",  "noaa"),   # Eagers Bay (20km to station)
    ("eagle-dock-beach",                      "8516945",  "noaa"),   # Eagle Dock Beach (26km to station)
    ("eagle-nest",                            "8725520",  "noaa"),   # Eagle Nest (21km to station)
    ("eagle-nest-bay",                        "8652587",  "noaa"),   # Eagle Nest Bay (8km to station)
    ("earl-cove",                             "9452634",  "noaa"),   # Earl Cove (8km to station)
    ("earle-road-beach",                      "8447435",  "noaa"),   # Earle Road Beach (12km to station)
    ("east-atlantic-beach",                   "8516945",  "noaa"),   # East Atlantic Beach (26km to station)
    ("east-bay-junop",                        "8764314",  "noaa"),   # East Bay Junop (39km to station)
    ("east-bayou",                            "8728690",  "noaa"),   # East Bayou (14km to station)
    ("east-branch-little-kennebec-bay",       "8411060",  "noaa"),   # East Branch Little Kennebec Bay (18km to station)
    ("east-champagne-bay",                    "8761724",  "noaa"),   # East Champagne Bay (9km to station)
    ("east-conrad-creek",                     "8721604",  "noaa"),   # East Conrad Creek (18km to station)
    ("east-cote-blanche-bay",                 "8764227",  "noaa"),   # East Cote Blanche Bay (32km to station)
    ("east-cove",                             "8768094",  "noaa"),   # East Cove (14km to station)
    ("east-cove-beach",                       "8518962",  "noaa"),   # East Cove Beach (21km to station)
    ("east-end-bay",                          "9751364",  "noaa"),   # East End Bay (14km to station)
    ("east-end-beach",                        "8418150",  "noaa"),   # East End Beach (10km to station)
    ("east-gulf-place",                       "8735180",  "noaa"),   # East Gulf Place (37km to station)
    ("east-harbor",                           "9063079",  "noaa"),   # East Harbor (6km to station)
    ("east-hole",                             "8728690",  "noaa"),   # East Hole (14km to station)
    ("east-horseneck-beach",                  "8452660",  "noaa"),   # East Horseneck Beach (24km to station)
    ("east-jetty",                            "8729840",  "noaa"),   # East Jetty (36km to station)
    ("east-moran-bay",                        "9075080",  "noaa"),   # East Moran Bay (10km to station)
    ("east-norwalk-harbor",                   "8467150",  "noaa"),   # East Norwalk Harbor (21km to station)
    ("east-park-beach",                       "9063079",  "noaa"),   # East Park Beach (26km to station)
    ("east-patos-island-cove",                "9449880",  "noaa"),   # East Patos Island Cove (27km to station)
    ("east-pocket",                           "8774513",  "noaa"),   # East Pocket (6km to station)
    ("east-pond",                             "8413320",  "noaa"),   # East Pond (14km to station)
    ("east-rive-beach",                       "8465705",  "noaa"),   # East Rive Beach (23km to station)
    ("east-sandusky-bay",                     "9063079",  "noaa"),   # East Sandusky Bay (14km to station)
    ("east-sandwich-beach",                   "8447930",  "noaa"),   # East Sandwich Beach (32km to station)
    ("east-side-cove",                        "8413320",  "noaa"),   # East Side Cove (36km to station)
    ("east-whale-bay",                        "2695540",  "noaa"),   # East Whale Bay (18km to station)
    ("eastchester-bay",                       "8516945",  "noaa"),   # Eastchester Bay (5km to station)
    ("eastern-bay",                           "8575512",  "noaa"),   # Eastern Bay (21km to station)
    ("eastern-bend",                          "8658120",  "noaa"),   # Eastern Bend (40km to station)
    ("eastern-branch-corrotoman-river",       "8635750",  "noaa"),   # Eastern Branch Corrotoman River (32km to station)
    ("eastern-cove",                          "8413320",  "noaa"),   # Eastern Cove (33km to station)
    ("eastern-green-beach",                   "8729210",  "noaa"),   # Eastern Green Beach (14km to station)
    ("eastern-harbor",                        "8413320",  "noaa"),   # Eastern Harbor (40km to station)
    ("eastern-point-harbor",                  "8413320",  "noaa"),   # Eastern Point Harbor (9km to station)
    ("eastern-water",                         "8311062",  "noaa"),   # Eastern Water (22km to station)
    ("eastmouth-bay",                         "8656483",  "noaa"),   # Eastmouth Bay (13km to station)
    ("easton-bay",                            "8452660",  "noaa"),   # Easton Bay (4km to station)
    ("easton-cove",                           "8637689",  "noaa"),   # Easton Cove (14km to station)
    ("eastons-beach",                         "8452660",  "noaa"),   # Easton's Beach (4km to station)
    ("eastville-beach",                       "8447930",  "noaa"),   # Eastville Beach (10km to station)
    ("eatons-neck-basin",                     "8467150",  "noaa"),   # Eatons Neck Basin (31km to station)
    ("eau-gallie-beach",                      "8721604",  "noaa"),   # Eau Gallie Beach (31km to station)
    ("eccles-lagoon",                         "9454050",  "noaa"),   # Eccles Lagoon (3km to station)
    ("echo-bay",                              "8516945",  "noaa"),   # Echo Bay (10km to station)
    ("echo-lake-beach",                       "8413320",  "noaa"),   # Echo Lake Beach (14km to station)
    ("eddy-sound",                            "8658163",  "noaa"),   # Eddy Sound (15km to station)
    ("edgar-cove",                            "8571892",  "noaa"),   # Edgar Cove (28km to station)
    ("edgar-prong",                           "8557380",  "noaa"),   # Edgar Prong (22km to station)
    ("edge-cove",                             "8534720",  "noaa"),   # Edge Cove (28km to station)
    ("edge-creek",                            "8571892",  "noaa"),   # Edge Creek (23km to station)
    ("edgewater-beach",                       "9063063",  "noaa"),   # Edgewater Beach (10km to station)
    ("edgewater-haven",                       "8638610",  "noaa"),   # Edgewater Haven (5km to station)
    ("edun-cove",                             "9414290",  "noaa"),   # Edun Cove (27km to station)
    ("eel-bay",                               "8311062",  "noaa"),   # Eel Bay (10km to station)
    ("eel-grass-cove",                        "8447435",  "noaa"),   # Eel Grass Cove (32km to station)
    ("eel-pond",                              "8447930",  "noaa"),   # Eel Pond (11km to station)
    ("eel-river",                             "8447930",  "noaa"),   # Eel River (25km to station)
    ("ekaha",                                 "1611400",  "noaa"),   # Ekaha (16km to station)
    ("el-boquern",                            "9755371",  "noaa"),   # El Boquerón (3km to station)
    ("el-cajon-bay",                          "9075065",  "noaa"),   # El Cajon Bay (9km to station)
    ("el-ojo-del-buey",                       "9755371",  "noaa"),   # El Ojo del Buey (15km to station)
    ("el-pescador-beach",                     "9410840",  "noaa"),   # El Pescador Beach (36km to station)
    ("el-realito-bay",                        "8779280",  "noaa"),   # El Realito Bay (2km to station)
    ("elberts-cove",                          "8571892",  "noaa"),   # Elberts Cove (22km to station)
    ("elbow-bay",                             "2695540",  "noaa"),   # Elbow Bay (13km to station)
    ("eleanor-cove",                          "9453220",  "noaa"),   # Eleanor Cove (22km to station)
    ("eleanors-cove",                         "8447930",  "noaa"),   # Eleanors Cove (22km to station)
    ("electric-avenue-beach",                 "8447930",  "noaa"),   # Electric Avenue Beach (25km to station)
    ("eleilei-bay",                           "1615680",  "noaa"),   # Eleilei Bay (15km to station)
    ("elephant-bay",                          "9751381",  "noaa"),   # Elephant Bay (24km to station)
    ("eleven-prong",                          "8727520",  "noaa"),   # Eleven Prong (22km to station)
    ("elfin-cove",                            "9452634",  "noaa"),   # Elfin Cove (1km to station)
    ("eli-cove",                              "8574680",  "noaa"),   # Eli Cove (14km to station)
    ("elk-bay",                               "9751381",  "noaa"),   # Elk Bay (5km to station)
    ("elk-fence-north-beach",                 "9415020",  "noaa"),   # Elk Fence North Beach (21km to station)
    ("elk-fence-south-beach",                 "9415020",  "noaa"),   # Elk Fence South Beach (21km to station)
    ("ell-cove",                              "9451600",  "noaa"),   # Ell Cove (35km to station)
    ("ellinger-cove",                         "8571421",  "noaa"),   # Ellinger Cove (37km to station)
    ("ellis-bay",                             "8571421",  "noaa"),   # Ellis Bay (14km to station)
    ("elm-tree-cove",                         "8418150",  "noaa"),   # Elm Tree Cove (5km to station)
    ("elmar-beach",                           "9414523",  "noaa"),   # Elmar Beach (21km to station)
    ("eloi-bay",                              "8761305",  "noaa"),   # Eloi Bay (31km to station)
    ("emerald-cove",                          "8775296",  "noaa"),   # Emerald Cove (4km to station)
    ("emerson-bayou",                         "8726384",  "noaa"),   # Emerson Bayou (14km to station)
    ("emery-cove",                            "8413320",  "noaa"),   # Emery Cove (8km to station)
    ("emilys-bay",                            "2695535",  "noaa"),   # Emily's Bay (2km to station)
    ("emmons-bayou",                          "8729108",  "noaa"),   # Emmons Bayou (9km to station)
    ("enchanted-cove",                        "9410170",  "noaa"),   # Enchanted Cove (8km to station)
    ("encinal-beach",                         "9410840",  "noaa"),   # Encinal Beach (36km to station)
    ("english-navy-cove",                     "8729840",  "noaa"),   # English Navy Cove (7km to station)
    ("englishman-bay",                        "8411060",  "noaa"),   # Englishman Bay (22km to station)
    ("enighed-pond",                          "9751381",  "noaa"),   # Enighed Pond (7km to station)
    ("ensenada-breas",                        "9755371",  "noaa"),   # Ensenada Breñas (22km to station)
    ("ensenada-comezn",                       "9753216",  "noaa"),   # Ensenada Comezón (19km to station)
    ("ensenada-dakity",                       "9752235",  "noaa"),   # Ensenada Dakity (3km to station)
    ("ensenada-fulladosa",                    "9752235",  "noaa"),   # Ensenada Fulladosa (2km to station)
    ("ensenada-honda",                        "9752235",  "noaa"),   # Ensenada Honda (2km to station)
    ("ensenada-las-pardas",                   "9759110",  "noaa"),   # Ensenada Las Pardas (13km to station)
    ("ensenada-malena",                       "9752235",  "noaa"),   # Ensenada Malena (3km to station)
    ("ensenada-sombe",                        "9752695",  "noaa"),   # Ensenada Sombe (1km to station)
    ("ensenada-sombre",                       "9752695",  "noaa"),   # Ensenada Sombre (1km to station)
    ("ensenada-de-boca-vieja",                "9755371",  "noaa"),   # Ensenada de Boca Vieja (6km to station)
    ("ensenada-del-cementerio",               "9752235",  "noaa"),   # Ensenada del Cementerio (2km to station)
    ("ensenada-del-coronel",                  "9752235",  "noaa"),   # Ensenada del Coronel (2km to station)
    ("ensenada-del-pirata",                   "9752695",  "noaa"),   # Ensenada del Pirata (4km to station)
    ("ensomhed-bay",                          "9751381",  "noaa"),   # Ensomhed Bay (23km to station)
    ("erskine-bay",                           "9462620",  "noaa"),   # Erskine Bay (16km to station)
    ("escambia-bay",                          "8729840",  "noaa"),   # Escambia Bay (16km to station)
    ("escondido-beach",                       "9410840",  "noaa"),   # Escondido Beach (25km to station)
    ("esopus-meadows-beach",                  "8518962",  "noaa"),   # Esopus Meadows Beach (17km to station)
    ("estero-de-limantour",                   "9415020",  "noaa"),   # Estero De Limantour (8km to station)
    ("estes-cove",                            "8774770",  "noaa"),   # Estes Cove (7km to station)
    ("esther-march-bay",                      "9052000",  "noaa"),   # Esther March Bay (22km to station)
    ("europa-bay",                            "9751381",  "noaa"),   # Europa Bay (1km to station)
    ("eustis-beach",                          "8447930",  "noaa"),   # Eustis Beach (16km to station)
    ("eva-bay",                               "9751381",  "noaa"),   # Eva Bay (14km to station)
    ("ewells-prong",                          "8635750",  "noaa"),   # Ewells Prong (37km to station)
    ("ewens-bay",                             "8571892",  "noaa"),   # Ewens Bay (9km to station)
    ("eye-harbour",                           "8311062",  "noaa"),   # Eye Harbour (5km to station)
    ("fishing-beach",                         "8531680",  "noaa"),   # FIshing Beach (4km to station)
    ("fairfield-public-beach",                "8467150",  "noaa"),   # Fairfield Public Beach (10km to station)
    ("fairmount-avenue-southwest-street-end", "9446484",  "noaa"),   # Fairmount Avenue Southwest Street End (36km to station)
    ("fairport-harbor-lakefront-park",        "9063053",  "noaa"),   # Fairport Harbor Lakefront Park (0km to station)
    ("fairview-cove",                         "9075099",  "noaa"),   # Fairview Cove (6km to station)
    ("fairyland-creek",                       "2695540",  "noaa"),   # Fairyland Creek (13km to station)
    ("falling-cove",                          "8571421",  "noaa"),   # Falling Cove (7km to station)
    ("falmouth-beach",                        "8447930",  "noaa"),   # Falmouth Beach (4km to station)
    ("falmouth-harbor",                       "9459450",  "noaa"),   # Falmouth Harbor (36km to station)
    ("falmouth-inner-harbor",                 "8447930",  "noaa"),   # Falmouth Inner Harbor (6km to station)
    ("false-klamath-cove",                    "9419750",  "noaa"),   # False Klamath Cove (18km to station)
    ("false-mouth-bay",                       "8761305",  "noaa"),   # False Mouth Bay (28km to station)
    ("false-presque-isle-harbor",             "9075065",  "noaa"),   # False Presque Isle Harbor (21km to station)
    ("fan-shell-beach",                       "9413450",  "noaa"),   # Fan Shell Beach (8km to station)
    ("fannin-bayou",                          "8729108",  "noaa"),   # Fannin Bayou (14km to station)
    ("farview-beach",                         "8465705",  "noaa"),   # Farview Beach (11km to station)
    ("farwell-cove",                          "8418150",  "noaa"),   # Farwell Cove (29km to station)
    ("feather-bed-shoal",                     "9052000",  "noaa"),   # Feather Bed Shoal (3km to station)
    ("fenwick-beach",                         "8570283",  "noaa"),   # Fenwick Beach (16km to station)
    ("fernald-cove",                          "8413320",  "noaa"),   # Fernald Cove (14km to station)
    ("ferrand-bay",                           "8761724",  "noaa"),   # Ferrand Bay (33km to station)
    ("ferry-beach",                           "8516945",  "noaa"),   # Ferry Beach (21km to station)
    ("ferry-cove",                            "8557380",  "noaa"),   # Ferry Cove (24km to station)
    ("ferry-cutoff",                          "8729840",  "noaa"),   # Ferry Cutoff (18km to station)
    ("fiddlers-cove",                         "8447930",  "noaa"),   # Fiddlers Cove (14km to station)
    ("fiddlers-elbow",                        "8311062",  "noaa"),   # Fiddlers Elbow (6km to station)
    ("fiddlers-green-beach",                  "8516945",  "noaa"),   # Fiddlers Green Beach (30km to station)
    ("field-cove",                            "8658120",  "noaa"),   # Field Cove (20km to station)
    ("fiesta-bay",                            "9410170",  "noaa"),   # Fiesta Bay (9km to station)
    ("fillingim-landing",                     "8729840",  "noaa"),   # Fillingim Landing (35km to station)
    ("fillmans-creek",                        "8726724",  "noaa"),   # Fillmans Creek (28km to station)
    ("final-bay",                             "9462620",  "noaa"),   # Final Bay (20km to station)
    ("finlayson-point-beach",                 "9449880",  "noaa"),   # Finlayson Point Beach (30km to station)
    ("finney-creek",                          "8631044",  "noaa"),   # Finney Creek (3km to station)
    ("first-cove",                            "8575512",  "noaa"),   # First Cove (17km to station)
    ("fish-bay",                              "9751381",  "noaa"),   # Fish Bay (4km to station)
    ("fish-creek-public-beach",               "9087088",  "noaa"),   # Fish Creek Public Beach (27km to station)
    ("fish-house-cove",                       "8418150",  "noaa"),   # Fish House Cove (32km to station)
    ("fish-pond",                             "8773701",  "noaa"),   # Fish Pond (10km to station)
    ("fish-rock-beach",                       "9416841",  "noaa"),   # Fish Rock Beach (17km to station)
    ("fish-trap-bay",                         "8725520",  "noaa"),   # Fish Trap Bay (34km to station)
    ("fisher-bay",                            "9014070",  "noaa"),   # Fisher Bay (10km to station)
    ("fisher-beach",                          "8447435",  "noaa"),   # Fisher Beach (34km to station)
    ("fisher-cove",                           "8631044",  "noaa"),   # Fisher Cove (18km to station)
    ("fisherman-bay",                         "9416841",  "noaa"),   # Fisherman Bay (40km to station)
    ("fishermans-beach",                      "8449130",  "noaa"),   # Fisherman's Beach (5km to station)
    ("fishermans-landing",                    "8447435",  "noaa"),   # Fisherman's Landing (5km to station)
    ("fishermans-bay",                        "8761724",  "noaa"),   # Fishermans Bay (14km to station)
    ("fishermans-cove",                       "8638610",  "noaa"),   # Fishermans Cove (13km to station)
    ("fishermans-inlet",                      "8632200",  "noaa"),   # Fishermans Inlet (7km to station)
    ("fishery-bay",                           "9063079",  "noaa"),   # Fishery Bay (15km to station)
    ("fishing-dog-beach",                     "8639348",  "noaa"),   # Fishing & Dog Beach (31km to station)
    ("fishing-bay",                           "8637689",  "noaa"),   # Fishing Bay (36km to station)
    ("fishing-bend",                          "8764314",  "noaa"),   # Fishing Bend (11km to station)
    ("fishing-cove",                          "8452660",  "noaa"),   # Fishing Cove (13km to station)
    ("fishing-creek",                         "8575512",  "noaa"),   # Fishing Creek (8km to station)
    ("fishing-ditch",                         "8571421",  "noaa"),   # Fishing Ditch (36km to station)
    ("fishing-gut",                           "8631044",  "noaa"),   # Fishing Gut (37km to station)
    ("fishing-shore",                         "8594900",  "noaa"),   # Fishing Shore (8km to station)
    ("fishing-smack-bay",                     "8761305",  "noaa"),   # Fishing Smack Bay (37km to station)
    ("five-islands-cove",                     "8413320",  "noaa"),   # Five Islands Cove (37km to station)
    ("flag-cove",                             "8571421",  "noaa"),   # Flag Cove (14km to station)
    ("flag-harbor",                           "8570283",  "noaa"),   # Flag Harbor (36km to station)
    ("flanders-pond-beach",                   "8413320",  "noaa"),   # Flanders Pond Beach (17km to station)
    ("flanners-beach",                        "8656483",  "noaa"),   # Flanners Beach (39km to station)
    ("flat-bay",                              "8761305",  "noaa"),   # Flat Bay (25km to station)
    ("flat-bight",                            "9462620",  "noaa"),   # Flat Bight (38km to station)
    ("flat-cove",                             "8452944",  "noaa"),   # Flat Cove (12km to station)
    ("flatboat-inside-pond",                  "8760721",  "noaa"),   # Flatboat Inside Pond (9km to station)
    ("flatboat-outside-pond",                 "8760721",  "noaa"),   # Flatboat Outside Pond (11km to station)
    ("flatcap-basin",                         "8571421",  "noaa"),   # Flatcap Basin (28km to station)
    ("flatland-cove",                         "8571421",  "noaa"),   # Flatland Cove (24km to station)
    ("flatts-wharf",                          "2695540",  "noaa"),   # Flatts Wharf (6km to station)
    ("flatty-cove",                           "8571892",  "noaa"),   # Flatty Cove (16km to station)
    ("flax-pond",                             "8447435",  "noaa"),   # Flax Pond (20km to station)
    ("fleeton-bay",                           "8635750",  "noaa"),   # Fleeton Bay (26km to station)
    ("fleets-bay",                            "8635750",  "noaa"),   # Fleets Bay (40km to station)
    ("fleets-cove",                           "8635750",  "noaa"),   # Fleets Cove (9km to station)
    ("fletchers-cove",                        "8594900",  "noaa"),   # Fletchers Cove (9km to station)
    ("fleur-pond",                            "8760721",  "noaa"),   # Fleur Pond (11km to station)
    ("flint-beach",                           "9449880",  "noaa"),   # Flint Beach (17km to station)
    ("floods-hole",                           "8638610",  "noaa"),   # Floods Hole (18km to station)
    ("flowers-bay",                           "9076024",  "noaa"),   # Flowers Bay (32km to station)
    ("flowers-cove",                          "8571421",  "noaa"),   # Flowers Cove (20km to station)
    ("flowing-well-creek",                    "8721604",  "noaa"),   # Flowing Well Creek (10km to station)
    ("floyds-bay",                            "8637689",  "noaa"),   # Floyds Bay (14km to station)
    ("floyds-cove",                           "8635750",  "noaa"),   # Floyds Cove (10km to station)
    ("flynn-bay",                             "8311062",  "noaa"),   # Flynn Bay (18km to station)
    ("flynns-beach",                          "8454000",  "noaa"),   # Flynns Beach (29km to station)
    ("fodder-house-cove",                     "8577330",  "noaa"),   # Fodder House Cove (18km to station)
    ("fog-point-cove",                        "8571421",  "noaa"),   # Fog Point Cove (21km to station)
    ("fogg-cove",                             "8413320",  "noaa"),   # Fogg Cove (23km to station)
    ("fogland",                               "8452660",  "noaa"),   # Fogland (11km to station)
    ("folkingham-cove",                       "8411060",  "noaa"),   # Folkingham Cove (37km to station)
    ("fool-inlet",                            "9452210",  "noaa"),   # Fool Inlet (34km to station)
    ("foot-of-the-lane",                      "2695540",  "noaa"),   # Foot of the Lane (11km to station)
    ("footbridge-beach",                      "8419870",  "noaa"),   # Footbridge Beach (24km to station)
    ("fords-beach",                           "8516945",  "noaa"),   # Fords Beach (30km to station)
    ("fords-cove",                            "8571421",  "noaa"),   # Fords Cove (25km to station)
    ("forest-bay",                            "9075014",  "noaa"),   # Forest Bay (7km to station)
    ("forest-cove",                           "8635027",  "noaa"),   # Forest Cove (15km to station)
    ("forked-creek",                          "8575512",  "noaa"),   # Forked Creek (9km to station)
    ("forrest-landing-cove",                  "8577330",  "noaa"),   # Forrest Landing Cove (8km to station)
    ("fort-blanc-bay",                        "8761724",  "noaa"),   # Fort Blanc Bay (3km to station)
    ("fort-cove",                             "8452660",  "noaa"),   # Fort Cove (4km to station)
    ("fort-hase-cove",                        "1612480",  "noaa"),   # Fort Hase Cove (6km to station)
    ("fort-hill-bay",                         "2695535",  "noaa"),   # Fort Hill Bay (5km to station)
    ("fort-hill-beach",                       "8516945",  "noaa"),   # Fort Hill Beach (26km to station)
    ("fort-kamehameha-beach",                 "1612340",  "noaa"),   # Fort Kamehameha Beach (10km to station)
    ("fort-macon-creek",                      "8656483",  "noaa"),   # Fort Macon Creek (2km to station)
    ("fort-pond-bay",                         "8510560",  "noaa"),   # Fort Pond Bay (1km to station)
    ("fort-trumbull-beach",                   "8467150",  "noaa"),   # Fort Trumbull Beach (11km to station)
    ("fortescue-beach",                       "8537121",  "noaa"),   # Fortescue Beach (19km to station)
    ("fortin-bay",                            "8656483",  "noaa"),   # Fortin Bay (25km to station)
    ("fortuna-bay",                           "9752235",  "noaa"),   # Fortuna Bay (30km to station)
    ("fortuna-bay-beach",                     "9752235",  "noaa"),   # Fortuna Bay Beach (31km to station)
    ("fortunes-rocks-beach",                  "8418150",  "noaa"),   # Fortunes Rocks Beach (27km to station)
    ("fortunes-rocks-cove",                   "8418150",  "noaa"),   # Fortunes Rocks Cove (29km to station)
    ("forty-acre-bay",                        "8725520",  "noaa"),   # Forty Acre Bay (26km to station)
    ("foss-beach",                            "8419870",  "noaa"),   # Foss Beach (8km to station)
    ("fossil-beach",                          "8637689",  "noaa"),   # Fossil Beach (29km to station)
    ("foster-bay",                            "8725520",  "noaa"),   # Foster Bay (34km to station)
    ("foster-cove",                           "8461490",  "noaa"),   # Foster Cove (21km to station)
    ("fosters-bay",                           "8311062",  "noaa"),   # Fosters Bay (27km to station)
    ("foulweather-bluff-beach",               "9444900",  "noaa"),   # Foulweather Bluff Beach (24km to station)
    ("fountain-cove",                         "8635750",  "noaa"),   # Fountain Cove (8km to station)
    ("four-mile-cove",                        "8725520",  "noaa"),   # Four Mile Cove (6km to station)
    ("fourleague-bay",                        "8764227",  "noaa"),   # Fourleague Bay (23km to station)
    ("fourth-of-july-beach",                  "9449880",  "noaa"),   # Fourth of July Beach (8km to station)
    ("fowl-river-bay",                        "8735180",  "noaa"),   # Fowl River Bay (16km to station)
    ("fox-creek",                             "8575512",  "noaa"),   # Fox Creek (12km to station)
    ("fox-hill-cove",                         "8447386",  "noaa"),   # Fox Hill Cove (3km to station)
    ("fox-hole",                              "9459450",  "noaa"),   # Fox Hole (11km to station)
    ("fox-hole-creek",                        "8571892",  "noaa"),   # Fox Hole Creek (17km to station)
    ("fox-island-sand-spit",                  "9446484",  "noaa"),   # Fox Island Sand Spit (19km to station)
    ("foxs-pond",                             "8760721",  "noaa"),   # Foxs Pond (15km to station)
    ("fraland-cove",                          "8537121",  "noaa"),   # Fraland Cove (6km to station)
    ("frames-cove",                           "8557380",  "noaa"),   # Frames Cove (22km to station)
    ("francis-bay",                           "9751381",  "noaa"),   # Francis Bay (6km to station)
    ("francis-bay-beach",                     "9751381",  "noaa"),   # Francis Bay Beach (6km to station)
    ("francis-beach",                         "9414523",  "noaa"),   # Francis Beach (21km to station)
    ("francis-cove",                          "9450460",  "noaa"),   # Francis Cove (37km to station)
    ("francois-bay",                          "8767816",  "noaa"),   # Francois Bay (31km to station)
    ("francois-bend",                         "8760721",  "noaa"),   # Francois Bend (15km to station)
    ("frank-bay",                             "9751381",  "noaa"),   # Frank Bay (8km to station)
    ("frank-moody-state-beach",               "8454000",  "noaa"),   # Frank Moody State Beach (10km to station)
    ("franks-bay",                            "2695540",  "noaa"),   # Frank's Bay (20km to station)
    ("fred-bayou",                            "8729108",  "noaa"),   # Fred Bayou (10km to station)
    ("freddy-beach",                          "8418150",  "noaa"),   # Freddy Beach (24km to station)
    ("freeman-park",                          "8658163",  "noaa"),   # Freeman Park (18km to station)
    ("french-bay",                            "9751381",  "noaa"),   # French Bay (20km to station)
    ("french-creek-bay",                      "8311062",  "noaa"),   # French Creek Bay (16km to station)
    ("french-duck-pond",                      "8760721",  "noaa"),   # French Duck Pond (5km to station)
    ("french-harbor",                         "9450460",  "noaa"),   # French Harbor (32km to station)
    ("french-watering-place",                 "8447930",  "noaa"),   # French Watering Place (11km to station)
    ("frenchman-bay",                         "9751381",  "noaa"),   # Frenchman Bay (19km to station)
    ("freshwater-bayou",                      "8771341",  "noaa"),   # Freshwater Bayou (13km to station)
    ("friars-bay-beach",                      "8410140",  "noaa"),   # Friars Bay Beach (4km to station)
    ("friis-bay",                             "9751381",  "noaa"),   # Friis Bay (3km to station)
    ("fritz-cove",                            "9452210",  "noaa"),   # Fritz Cove (14km to station)
    ("frog-cove",                             "8311062",  "noaa"),   # Frog Cove (24km to station)
    ("front-beach",                           "8465705",  "noaa"),   # Front Beach (7km to station)
    ("front-cove",                            "8638610",  "noaa"),   # Front Cove (19km to station)
    ("frying-pan",                            "9463502",  "noaa"),   # Frying Pan (31km to station)
    ("fryingpan-cove",                        "8573364",  "noaa"),   # Fryingpan Cove (18km to station)
    ("fulcher-creek",                         "8656483",  "noaa"),   # Fulcher Creek (7km to station)
    ("fuller-bay",                            "9052000",  "noaa"),   # Fuller Bay (4km to station)
    ("fuller-street-beach",                   "8447930",  "noaa"),   # Fuller Street Beach (20km to station)
    ("fundy-cove",                            "8419870",  "noaa"),   # Fundy Cove (33km to station)
    ("funter-bay",                            "9452210",  "noaa"),   # Funter Bay (29km to station)
    ("futch-beach",                           "8661070",  "noaa"),   # Futch Beach (35km to station)
    ("futch-cove",                            "8721604",  "noaa"),   # Futch Cove (22km to station)
    ("gable-creek",                           "8656483",  "noaa"),   # Gable Creek (3km to station)
    ("gailies-bay",                           "8311062",  "noaa"),   # Gailies Bay (22km to station)
    ("gainer-bayou",                          "8729108",  "noaa"),   # Gainer Bayou (15km to station)
    ("galena-bay",                            "9454240",  "noaa"),   # Galena Bay (25km to station)
    ("galge-cove",                            "9751381",  "noaa"),   # Galge Cove (8km to station)
    ("galilee-salt-pond-harbor",              "8452660",  "noaa"),   # Galilee Salt Pond Harbor (21km to station)
    ("gallagher-beach",                       "9063020",  "noaa"),   # Gallagher Beach (5km to station)
    ("gallinipper-basin",                     "8721604",  "noaa"),   # Gallinipper Basin (31km to station)
    ("galloo-shoal",                          "9052000",  "noaa"),   # Galloo Shoal (28km to station)
    ("gamblers-bend",                         "8747437",  "noaa"),   # Gamblers Bend (24km to station)
    ("gambrill-cove",                         "8574680",  "noaa"),   # Gambrill Cove (12km to station)
    ("game-cove",                             "9452210",  "noaa"),   # Game Cove (35km to station)
    ("gangs-bayou",                           "8771486",  "noaa"),   # Gangs Bayou (6km to station)
    ("gansevoort-peninsula-sand-bluff",       "8518750",  "noaa"),   # Gansevoort Peninsula Sand Bluff (4km to station)
    ("garbage-beach",                         "8447930",  "noaa"),   # Garbage Beach (0km to station)
    ("garcitas-cove",                         "8773259",  "noaa"),   # Garcitas Cove (9km to station)
    ("garden-bayou",                          "8770613",  "noaa"),   # Garden Bayou (28km to station)
    ("gardenville-beach",                     "8726674",  "noaa"),   # Gardenville Beach (10km to station)
    ("gardners-basin",                        "8534720",  "noaa"),   # Gardners Basin (2km to station)
    ("gargathy-bay",                          "8631044",  "noaa"),   # Gargathy Bay (21km to station)
    ("gargathy-beach",                        "8631044",  "noaa"),   # Gargathy Beach (22km to station)
    ("gargathy-inlet",                        "8631044",  "noaa"),   # Gargathy Inlet (23km to station)
    ("garrett-island-beach",                  "8573927",  "noaa"),   # Garrett Island Beach (24km to station)
    ("garrison-bight",                        "8724580",  "noaa"),   # Garrison Bight (2km to station)
    ("garside-bay",                           "9075099",  "noaa"),   # Garside Bay (22km to station)
    ("gas-chambers",                          "9759394",  "noaa"),   # Gas Chambers (27km to station)
    ("gascony-cove",                          "8635750",  "noaa"),   # Gascony Cove (26km to station)
    ("gashouse-cove",                         "9414290",  "noaa"),   # Gashouse Cove (3km to station)
    ("gate-10-west",                          "8723214",  "noaa"),   # Gate 10 West (5km to station)
    ("gate-b-east",                           "8723214",  "noaa"),   # Gate B East (5km to station)
    ("gate-c-west",                           "8723214",  "noaa"),   # Gate C West (5km to station)
    ("gate-d-east",                           "8723214",  "noaa"),   # Gate D East (5km to station)
    ("gate-f-west",                           "8723214",  "noaa"),   # Gate F West (6km to station)
    ("gate-g-west",                           "8723214",  "noaa"),   # Gate G West (6km to station)
    ("gate-j-east",                           "8723214",  "noaa"),   # Gate J East (5km to station)
    ("gate-j-west",                           "8723214",  "noaa"),   # Gate J West (5km to station)
    ("gate-v",                                "8723214",  "noaa"),   # Gate V (6km to station)
    ("gates-bay",                             "8631044",  "noaa"),   # Gates Bay (2km to station)
    ("gateway-lagoon",                        "8516945",  "noaa"),   # Gateway Lagoon (36km to station)
    ("gator-creek",                           "8721604",  "noaa"),   # Gator Creek (30km to station)
    ("gator-hole",                            "8721604",  "noaa"),   # Gator Hole (22km to station)
    ("gauthier-pond",                         "8760721",  "noaa"),   # Gauthier Pond (10km to station)
    ("gavins-bay",                            "8311062",  "noaa"),   # Gavins Bay (18km to station)
    ("gawas-bay",                             "9076024",  "noaa"),   # Gawas Bay (19km to station)
    ("gay-head-town-beach",                   "8447930",  "noaa"),   # Gay Head Town Beach (25km to station)
    ("gaylor-cove",                           "8658120",  "noaa"),   # Gaylor Cove (32km to station)
    ("gedney-harbor",                         "9451054",  "noaa"),   # Gedney Harbor (28km to station)
    ("gem-beach",                             "9063079",  "noaa"),   # Gem Beach (8km to station)
    ("gem-cove",                              "9450460",  "noaa"),   # Gem Cove (14km to station)
    ("genesis-bay",                           "8536110",  "noaa"),   # Genesis Bay (17km to station)
    ("genoa-swimming-quarry",                 "9063085",  "noaa"),   # Genoa Swimming Quarry (22km to station)
    ("genti-bay",                             "9751381",  "noaa"),   # Genti Bay (3km to station)
    ("georges-bay",                           "2695540",  "noaa"),   # George's Bay (19km to station)
    ("georges-hole",                          "8773037",  "noaa"),   # George's hole (19km to station)
    ("georges-cove",                          "8635750",  "noaa"),   # Georges Cove (38km to station)
    ("georges-creek",                         "8652587",  "noaa"),   # Georges Creek (3km to station)
    ("georgiaville-beach",                    "8454000",  "noaa"),   # Georgiaville Beach (13km to station)
    ("georgiaville-pond-beach",               "8454000",  "noaa"),   # Georgiaville Pond Beach (13km to station)
    ("georgica-cove",                         "8510560",  "noaa"),   # Georgica Cove (25km to station)
    ("gerard-drive-beach",                    "8510560",  "noaa"),   # Gerard Drive Beach (15km to station)
    ("gerritsen-beach",                       "8518750",  "noaa"),   # Gerritsen Beach (15km to station)
    ("gerry-cove",                            "8419870",  "noaa"),   # Gerry Cove (3km to station)
    ("giants-neck-beach",                     "8461490",  "noaa"),   # Giants Neck Beach (14km to station)
    ("giants-ramp",                           "8418150",  "noaa"),   # Giants Ramp (4km to station)
    ("gibbons-bay",                           "2695540",  "noaa"),   # Gibbons Bay (7km to station)
    ("gibbs-creek",                           "8656483",  "noaa"),   # Gibbs Creek (5km to station)
    ("gibneys-hawksnest-beach",               "9751381",  "noaa"),   # Gibney's Hawksnest Beach (6km to station)
    ("gibraltar-bay",                         "9052000",  "noaa"),   # Gibraltar Bay (22km to station)
    ("gibson-beach",                          "9413450",  "noaa"),   # Gibson Beach (12km to station)
    ("gilberts-cove",                         "8447930",  "noaa"),   # Gilberts Cove (20km to station)
    ("giles-creek",                           "8447386",  "noaa"),   # Giles Creek (24km to station)
    ("gilgo-heading",                         "8516945",  "noaa"),   # Gilgo Heading (37km to station)
    ("gill-harbor",                           "9052000",  "noaa"),   # Gill Harbor (25km to station)
    ("gilley-beach",                          "8413320",  "noaa"),   # Gilley Beach (15km to station)
    ("gilmer-bay",                            "9451600",  "noaa"),   # Gilmer Bay (35km to station)
    ("gilmer-cove",                           "9451600",  "noaa"),   # Gilmer Cove (33km to station)
    ("gilmore-shore",                         "9052000",  "noaa"),   # Gilmore Shore (26km to station)
    ("gilpatrick-cove",                       "8413320",  "noaa"),   # Gilpatrick Cove (14km to station)
    ("gin-cove",                              "8410140",  "noaa"),   # Gin Cove (15km to station)
    ("gingerville-creek",                     "8575512",  "noaa"),   # Gingerville Creek (7km to station)
    ("ginny-beach",                           "8635750",  "noaa"),   # Ginny Beach (21km to station)
    ("girl-scout-camp-beach",                 "8452660",  "noaa"),   # Girl Scout Camp beach (10km to station)
    ("glass-bay",                             "8637689",  "noaa"),   # Glass Bay (10km to station)
    ("glebe-bay",                             "8575512",  "noaa"),   # Glebe Bay (8km to station)
    ("glebe-creek",                           "8575512",  "noaa"),   # Glebe Creek (8km to station)
    ("glen-island",                           "8516945",  "noaa"),   # Glen Island (8km to station)
    ("glen-lake-south-beach",                 "9444090",  "noaa"),   # Glen Lake South Beach (35km to station)
    ("glendon-road-beach",                    "8447435",  "noaa"),   # Glendon Road Beach (16km to station)
    ("glorietta-bay",                         "9410170",  "noaa"),   # Glorietta Bay (4km to station)
    ("glover-bight",                          "8725520",  "noaa"),   # Glover Bight (18km to station)
    ("gnat-cove",                             "9450460",  "noaa"),   # Gnat Cove (20km to station)
    ("goadreaus-harbor",                      "9087096",  "noaa"),   # Goadreaus Harbor (7km to station)
    ("goat-island-bay",                       "8652587",  "noaa"),   # Goat Island Bay (8km to station)
    ("goble-beach",                           "9440422",  "noaa"),   # Goble Beach (11km to station)
    ("godfrey-bay",                           "8637689",  "noaa"),   # Godfrey Bay (34km to station)
    ("godfreys-cove",                         "8419870",  "noaa"),   # Godfreys Cove (10km to station)
    ("goeller-cove",                          "8467150",  "noaa"),   # Goeller Cove (28km to station)
    ("gold-bluffs-beach",                     "9419750",  "noaa"),   # Gold Bluffs Beach (40km to station)
    ("gold-star-battalion-beach",             "8516945",  "noaa"),   # Gold Star Battalion Beach (30km to station)
    ("golf-course-cove",                      "8574680",  "noaa"),   # Golf Course Cove (20km to station)
    ("gonakadetseat-bay",                     "9453220",  "noaa"),   # Gonakadetseat Bay (5km to station)
    ("gondle-pond",                           "8760721",  "noaa"),   # Gondle Pond (9km to station)
    ("gonzales-beach",                        "9449880",  "noaa"),   # Gonzales Beach (28km to station)
    ("goochs-beach",                          "8419870",  "noaa"),   # Goochs Beach (36km to station)
    ("good-fortune-cove",                     "9435380",  "noaa"),   # Good Fortune Cove (39km to station)
    ("goose-bayou",                           "8729108",  "noaa"),   # Goose Bayou (8km to station)
    ("goose-cove",                            "8534720",  "noaa"),   # Goose Cove (21km to station)
    ("goose-creek",                           "8571421",  "noaa"),   # Goose Creek (21km to station)
    ("goose-harbor",                          "8631044",  "noaa"),   # Goose Harbor (39km to station)
    ("goose-harbor-cove",                     "8571421",  "noaa"),   # Goose Harbor Cove (25km to station)
    ("goose-island-outside-pond",             "8760721",  "noaa"),   # Goose Island Outside Pond (10km to station)
    ("goose-pond",                            "8575512",  "noaa"),   # Goose Pond (5km to station)
    ("goosefare-bay",                         "8418150",  "noaa"),   # Goosefare Bay (33km to station)
    ("gordons-beach",                         "9444090",  "noaa"),   # Gordon's Beach (40km to station)
    ("goss-bay",                              "8767816",  "noaa"),   # Goss Bay (11km to station)
    ("goulais-bay",                           "9076070",  "noaa"),   # Goulais Bay (22km to station)
    ("gouldsboro-bay",                        "8413320",  "noaa"),   # Gouldsboro Bay (19km to station)
    ("government-bay",                        "9075099",  "noaa"),   # Government Bay (33km to station)
    ("gowanus-bay",                           "8518750",  "noaa"),   # Gowanus Bay (4km to station)
    ("grace-point",                           "8635750",  "noaa"),   # Grace Point (35km to station)
    ("graces-cove",                           "8510560",  "noaa"),   # Grace's Cove (34km to station)
    ("grammers-cove",                         "8577330",  "noaa"),   # Grammers Cove (12km to station)
    ("granaway-deep",                         "2695540",  "noaa"),   # Granaway Deep (15km to station)
    ("grand-bay",                             "8737048",  "noaa"),   # Grand Bay (7km to station)
    ("grand-bayou",                           "8741533",  "noaa"),   # Grand Bayou (23km to station)
    ("grand-coin-pocket",                     "8761305",  "noaa"),   # Grand Coin Pocket (32km to station)
    ("grand-coquille-bay",                    "8760721",  "noaa"),   # Grand Coquille Bay (26km to station)
    ("grand-cove",                            "8447435",  "noaa"),   # Grand Cove (18km to station)
    ("grand-lagoon",                          "8729108",  "noaa"),   # Grand Lagoon (7km to station)
    ("grand-marais-harbor",                   "9099090",  "noaa"),   # Grand Marais Harbor (0km to station)
    ("grand-marais-lake",                     "9075099",  "noaa"),   # Grand Marais Lake (20km to station)
    ("grand-marsh-bay",                       "8413320",  "noaa"),   # Grand Marsh Bay (16km to station)
    ("grand-point-bay",                       "8761305",  "noaa"),   # Grand Point Bay (29km to station)
    ("grand-vue-beach",                       "8447930",  "noaa"),   # Grand Vue Beach (17km to station)
    ("grandmas-beach",                        "9449880",  "noaa"),   # Grandma's Beach (37km to station)
    ("grandview-bay",                         "9063020",  "noaa"),   # Grandview Bay (31km to station)
    ("granite-bay",                           "8465705",  "noaa"),   # Granite Bay (6km to station)
    ("granite-cove",                          "9452634",  "noaa"),   # Granite Cove (3km to station)
    ("granny-cove",                           "8721604",  "noaa"),   # Granny Cove (38km to station)
    ("grant-cove",                            "8413320",  "noaa"),   # Grant Cove (12km to station)
    ("granville-creek",                       "8575512",  "noaa"),   # Granville Creek (9km to station)
    ("grape-bay",                             "2695540",  "noaa"),   # Grape Bay (12km to station)
    ("grapetree-bay",                         "9751364",  "noaa"),   # Grapetree Bay (11km to station)
    ("grapetree-beach",                       "9751364",  "noaa"),   # Grapetree Beach (10km to station)
    ("grapevine-cove",                        "8577330",  "noaa"),   # Grapevine Cove (14km to station)
    ("grass-bay",                             "9075080",  "noaa"),   # Grass Bay (30km to station)
    ("grassers-lagoon",                       "9444900",  "noaa"),   # Grasser's Lagoon (14km to station)
    ("grassy-bay",                            "8534720",  "noaa"),   # Grassy Bay (9km to station)
    ("grassy-point-beach",                    "9751364",  "noaa"),   # Grassy Point Beach (9km to station)
    ("grassy-sound",                          "8536110",  "noaa"),   # Grassy Sound (13km to station)
    ("graveline-bay",                         "8735180",  "noaa"),   # Graveline Bay (6km to station)
    ("gravelly-bay",                          "9063020",  "noaa"),   # Gravelly Bay (30km to station)
    ("gravelly-point-beach",                  "8531680",  "noaa"),   # Gravelly Point Beach (7km to station)
    ("gravely-bay",                           "9052000",  "noaa"),   # Gravely Bay (31km to station)
    ("graves-harbor",                         "9452634",  "noaa"),   # Graves Harbor (24km to station)
    ("gravesend-bay",                         "8518750",  "noaa"),   # Gravesend Bay (12km to station)
    ("graveyard-cove",                        "9453220",  "noaa"),   # Graveyard Cove (3km to station)
    ("gray-cove",                             "8410140",  "noaa"),   # Gray Cove (33km to station)
    ("grays-creek",                           "8575512",  "noaa"),   # Grays Creek (12km to station)
    ("great-cove",                            "8571421",  "noaa"),   # Great Cove (6km to station)
    ("great-cove-creek",                      "8571421",  "noaa"),   # Great Cove Creek (6km to station)
    ("great-cruz-bay",                        "9751381",  "noaa"),   # Great Cruz Bay (7km to station)
    ("great-egging-beach",                    "8570283",  "noaa"),   # Great Egging Beach (16km to station)
    ("great-gut-cove",                        "8631044",  "noaa"),   # Great Gut Cove (7km to station)
    ("great-hammock-beach",                   "8461490",  "noaa"),   # Great Hammock Beach (27km to station)
    ("great-harbor",                          "8447930",  "noaa"),   # Great Harbor (1km to station)
    ("great-harbor-cove",                     "8418150",  "noaa"),   # Great Harbor Cove (19km to station)
    ("great-hollow-beach",                    "8447435",  "noaa"),   # Great Hollow Beach (38km to station)
    ("great-island-bay",                      "8656483",  "noaa"),   # Great Island Bay (24km to station)
    ("great-lameshur-bay",                    "9751381",  "noaa"),   # Great Lameshur Bay (0km to station)
    ("great-ledge-cove",                      "8418150",  "noaa"),   # Great Ledge Cove (8km to station)
    ("great-machipongo-inlet",                "8631044",  "noaa"),   # Great Machipongo Inlet (27km to station)
    ("great-pond",                            "8447930",  "noaa"),   # Great Pond (8km to station)
    ("great-pond-bay",                        "9751364",  "noaa"),   # Great Pond Bay (6km to station)
    ("great-pond-beach",                      "8447435",  "noaa"),   # Great Pond Beach (28km to station)
    ("great-pond-cove",                       "8411060",  "noaa"),   # Great Pond Cove (7km to station)
    ("great-sound",                           "8536110",  "noaa"),   # Great Sound (21km to station)
    ("green-bank",                            "9449880",  "noaa"),   # Green Bank (13km to station)
    ("green-cove",                            "9452210",  "noaa"),   # Green Cove (18km to station)
    ("green-island-breaker",                  "8411060",  "noaa"),   # Green Island Breaker (30km to station)
    ("green-pond",                            "8447930",  "noaa"),   # Green Pond (10km to station)
    ("green-run-bay",                         "8570283",  "noaa"),   # Green Run Bay (30km to station)
    ("greenhaven-beach",                      "8516945",  "noaa"),   # Greenhaven Beach (16km to station)
    ("greenhill-cove",                        "8574680",  "noaa"),   # Greenhill Cove (11km to station)
    ("greenlaw-cove",                         "8413320",  "noaa"),   # Greenlaw Cove (39km to station)
    ("greenmansion-cove",                     "8637689",  "noaa"),   # Greenmansion Cove (24km to station)
    ("greens-bay",                            "8311062",  "noaa"),   # Greens Bay (2km to station)
    ("greens-bayou",                          "8771450",  "noaa"),   # Greens Bayou (6km to station)
    ("greens-harbor",                         "8461490",  "noaa"),   # Greens Harbor (4km to station)
    ("greentop-harbor",                       "9452634",  "noaa"),   # Greentop Harbor (38km to station)
    ("greenwich-bay",                         "8452944",  "noaa"),   # Greenwich Bay (8km to station)
    ("greenwich-cove",                        "8516945",  "noaa"),   # Greenwich Cove (28km to station)
    ("greenwich-harbor",                      "8516945",  "noaa"),   # Greenwich Harbor (26km to station)
    ("greenwood-cove",                        "9416841",  "noaa"),   # Greenwood Cove (24km to station)
    ("greys-creek",                           "8570283",  "noaa"),   # Greys Creek (13km to station)
    ("greys-inlet",                           "8570283",  "noaa"),   # Greys Inlet (12km to station)
    ("grice-beach",                           "8665530",  "noaa"),   # Grice Beach (4km to station)
    ("grice-cove",                            "8665530",  "noaa"),   # Grice Cove (4km to station)
    ("griffin-cove",                          "9075080",  "noaa"),   # Griffin Cove (11km to station)
    ("griffins-cove",                         "8418150",  "noaa"),   # Griffin's Cove (12km to station)
    ("grimmells-beach",                       "8447386",  "noaa"),   # Grimmells Beach (11km to station)
    ("grindstone-bay",                        "8311062",  "noaa"),   # Grindstone Bay (24km to station)
    ("gringo-beach",                          "9752695",  "noaa"),   # Gringo Beach (5km to station)
    ("grinnells-beach",                       "8447386",  "noaa"),   # Grinnell's Beach (10km to station)
    ("griswold-cove",                         "8461490",  "noaa"),   # Griswold Cove (22km to station)
    ("grizzly-bay",                           "9415144",  "noaa"),   # Grizzly Bay (7km to station)
    ("grocelys-cove",                         "8571892",  "noaa"),   # Grocelys Cove (25km to station)
    ("grootpan-bay",                          "9751381",  "noaa"),   # Grootpan Bay (1km to station)
    ("grosvold-bay",                          "9459450",  "noaa"),   # Grosvold Bay (23km to station)
    ("groton-long-point-south-beach",         "8461490",  "noaa"),   # Groton Long Point South Beach (10km to station)
    ("grove-beach",                           "8461490",  "noaa"),   # Grove Beach (34km to station)
    ("guard-shore",                           "8631044",  "noaa"),   # Guard Shore (26km to station)
    ("guffin-bay",                            "9052000",  "noaa"),   # Guffin Bay (19km to station)
    ("gulf-beach",                            "8467150",  "noaa"),   # Gulf Beach (12km to station)
    ("gulf-harbors-beach-club",               "8726724",  "noaa"),   # Gulf Harbors Beach Club (30km to station)
    ("gulf-place",                            "8735180",  "noaa"),   # Gulf Place (37km to station)
    ("gulf-of-the-farallones",                "9414290",  "noaa"),   # Gulf of the Farallones (26km to station)
    ("gull-cove",                             "9452634",  "noaa"),   # Gull Cove (12km to station)
    ("gull-island-bay",                       "8652587",  "noaa"),   # Gull Island Bay (35km to station)
    ("gull-pond",                             "8510560",  "noaa"),   # Gull Pond (34km to station)
    ("gull-pond-beach",                       "8447435",  "noaa"),   # Gull Pond Beach (30km to station)
    ("gum-tree-cove",                         "9410170",  "noaa"),   # Gum Tree Cove (17km to station)
    ("gumtree-cove",                          "8635027",  "noaa"),   # Gumtree Cove (15km to station)
    ("gun-point-cove",                        "8418150",  "noaa"),   # Gun Point Cove (27km to station)
    ("gunbarrel-cove",                        "8571421",  "noaa"),   # Gunbarrel Cove (11km to station)
    ("gunner-bay",                            "2695535",  "noaa"),   # Gunner Bay (4km to station)
    ("gunners-cove",                          "8571421",  "noaa"),   # Gunners Cove (20km to station)
    ("gunpowder-river",                       "8573364",  "noaa"),   # Gunpowder River (19km to station)
    ("gut-port",                              "9075099",  "noaa"),   # Gut Port (3km to station)
    ("gutter-inlet",                          "8516945",  "noaa"),   # Gutter Inlet (33km to station)
    ("gwydyr-bay",                            "9497645",  "noaa"),   # Gwydyr Bay (16km to station)
    ("hackberry-bay",                         "8761724",  "noaa"),   # Hackberry Bay (28km to station)
    ("hackberry-beach",                       "8768094",  "noaa"),   # Hackberry Beach (28km to station)
    ("hadley-harbor",                         "8447930",  "noaa"),   # Hadley Harbor (2km to station)
    ("hadlock-cove",                          "8418150",  "noaa"),   # Hadlock Cove (4km to station)
    ("hadlyme-cove",                          "8461490",  "noaa"),   # Hadlyme Cove (27km to station)
    ("haida-canoe-cove",                      "9449880",  "noaa"),   # Haida Canoe Cove (17km to station)
    ("haigis-beach",                          "8447435",  "noaa"),   # Haigis Beach (17km to station)
    ("haikioawa-landing",                     "1615680",  "noaa"),   # Haikioawa Landing (35km to station)
    ("hakalau-bay",                           "1617760",  "noaa"),   # Hakalau Bay (20km to station)
    ("hakioawa",                              "1615680",  "noaa"),   # Hakioawa (34km to station)
    ("halawa-beach",                          "1615680",  "noaa"),   # Halawa Beach (40km to station)
    ("haldimand-bay",                         "9075080",  "noaa"),   # Haldimand Bay (12km to station)
    ("haleiwa-alii-beach",                    "1612480",  "noaa"),   # Haleiwa Alii Beach (38km to station)
    ("hales-beach",                           "8413320",  "noaa"),   # Hales Beach (32km to station)
    ("haley-anchorage",                       "9451600",  "noaa"),   # Haley Anchorage (39km to station)
    ("haley-cove",                            "8419870",  "noaa"),   # Haley Cove (15km to station)
    ("halfpenny-bay",                         "9751364",  "noaa"),   # Halfpenny Bay (5km to station)
    ("halibut-cove",                          "9452210",  "noaa"),   # Halibut Cove (33km to station)
    ("halibut-cove-lagoon",                   "9455500",  "noaa"),   # Halibut Cove Lagoon (33km to station)
    ("hall-cove",                             "8461490",  "noaa"),   # Hall Cove (22km to station)
    ("hallets-cove",                          "8518750",  "noaa"),   # Hallets Cove (10km to station)
    ("hallicom-cove",                         "8418150",  "noaa"),   # Hallicom Cove (12km to station)
    ("halloway-bayou",                        "8725520",  "noaa"),   # Halloway Bayou (34km to station)
    ("halls-harbor",                          "8651370",  "noaa"),   # Halls Harbor (11km to station)
    ("halo",                                  "1615680",  "noaa"),   # Halo (25km to station)
    ("halsteads-bay",                         "8311062",  "noaa"),   # Halsteads Bay (12km to station)
    ("hambleton-cove",                        "8575512",  "noaa"),   # Hambleton Cove (28km to station)
    ("hamblini-pond-beach",                   "8447930",  "noaa"),   # Hamblini Pond Beach (27km to station)
    ("hambrooks-bay",                         "8571892",  "noaa"),   # Hambrooks Bay (3km to station)
    ("hamilton-bay",                          "9076024",  "noaa"),   # Hamilton Bay (28km to station)
    ("hamilton-beach",                        "9449880",  "noaa"),   # Hamilton Beach (32km to station)
    ("hamilton-harbour",                      "2695540",  "noaa"),   # Hamilton Harbour (13km to station)
    ("hammett-cove",                          "8447930",  "noaa"),   # Hammett Cove (22km to station)
    ("hammock-bay",                           "8729840",  "noaa"),   # Hammock Bay (36km to station)
    ("hammock-cove",                          "8534720",  "noaa"),   # Hammock Cove (13km to station)
    ("hammonds-bend",                         "8447435",  "noaa"),   # Hammonds Bend (9km to station)
    ("hams-bay",                              "9751401",  "noaa"),   # Hams Bay (16km to station)
    ("hamsterly-beach",                       "9449880",  "noaa"),   # Hamsterly Beach (28km to station)
    ("hanakaape-bay",                         "1611400",  "noaa"),   # Hanakaape Bay (14km to station)
    ("hanakapiai-beach",                      "1611400",  "noaa"),   # Hanakapiʻai Beach (38km to station)
    ("hanakailio-beach",                      "1612480",  "noaa"),   # Hanaka‘ilio Beach (36km to station)
    ("hanamaulu-beach",                       "1611400",  "noaa"),   # Hanamaulu Beach (5km to station)
    ("hanauma-beach",                         "1612340",  "noaa"),   # Hanauma Beach (18km to station)
    ("hanawana-bay",                          "1615680",  "noaa"),   # Hanawana Bay (27km to station)
    ("hand-trollers-cove",                    "9452210",  "noaa"),   # Hand Trollers Cove (33km to station)
    ("hands-creek",                           "8510560",  "noaa"),   # Hands Creek (21km to station)
    ("handsome-bay",                          "9751381",  "noaa"),   # Handsome Bay (35km to station)
    ("hannahs-cove",                          "8411060",  "noaa"),   # Hannahs Cove (36km to station)
    ("hansen-bay",                            "9751381",  "noaa"),   # Hansen Bay (6km to station)
    ("hansen-bay-beach",                      "9751381",  "noaa"),   # Hansen Bay Beach (6km to station)
    ("hansons-cove",                          "8635750",  "noaa"),   # Hansons Cove (17km to station)
    ("hapuna-bay",                            "1617433",  "noaa"),   # Hapuna Bay (5km to station)
    ("hapuu-bay",                             "1617433",  "noaa"),   # Hapuu Bay (24km to station)
    ("harbor-cove",                           "8575512",  "noaa"),   # Harbor Cove (26km to station)
    ("harbor-grace",                          "8418150",  "noaa"),   # Harbor Grace (8km to station)
    ("harbor-north",                          "9063079",  "noaa"),   # Harbor North (22km to station)
    ("harbor-point-beach",                    "8516945",  "noaa"),   # Harbor Point Beach (27km to station)
    ("harbor-of-refuge",                      "9075014",  "noaa"),   # Harbor of Refuge (1km to station)
    ("harbour-beach",                         "2695535",  "noaa"),   # Harbour Beach (3km to station)
    ("hardestys-cove",                        "8575512",  "noaa"),   # Hardestys Cove (9km to station)
    ("harmans-bay",                           "2695540",  "noaa"),   # Harman's Bay (18km to station)
    ("harmony-bay",                           "9076070",  "noaa"),   # Harmony Bay (39km to station)
    ("harmony-beach",                         "9076070",  "noaa"),   # Harmony Beach (39km to station)
    ("harness-creek",                         "8575512",  "noaa"),   # Harness Creek (6km to station)
    ("harper-creek",                          "8577330",  "noaa"),   # Harper Creek (4km to station)
    ("harpswell-cove",                        "8418150",  "noaa"),   # Harpswell Cove (33km to station)
    ("harpswell-harbor",                      "8418150",  "noaa"),   # Harpswell Harbor (22km to station)
    ("harpswell-sound",                       "8418150",  "noaa"),   # Harpswell Sound (26km to station)
    ("harris-beach",                          "9751381",  "noaa"),   # Harris Beach (23km to station)
    ("harris-cove",                           "9451054",  "noaa"),   # Harris Cove (24km to station)
    ("harrison-bayou",                        "8729210",  "noaa"),   # Harrison Bayou (11km to station)
    ("harrison-cove",                         "8635027",  "noaa"),   # Harrison Cove (18km to station)
    ("harry-tappen-beach",                    "8516945",  "noaa"),   # Harry Tappen Beach (10km to station)
    ("harrys-pond",                           "8760721",  "noaa"),   # Harrys Pond (7km to station)
    ("harsimus-cove",                         "8518750",  "noaa"),   # Harsimus Cove (3km to station)
    ("hart-bay",                              "9751381",  "noaa"),   # Hart Bay (6km to station)
    ("hart-bay-beach",                        "9751381",  "noaa"),   # Hart Bay Beach (6km to station)
    ("hartney-bay",                           "9454050",  "noaa"),   # Hartney Bay (10km to station)
    ("harts-cove",                            "8575512",  "noaa"),   # Harts Cove (3km to station)
    ("harts-harbor",                          "8447930",  "noaa"),   # Harts Harbor (15km to station)
    ("harveys-beach",                         "8461490",  "noaa"),   # Harveys Beach (27km to station)
    ("hashamomuck-beach",                     "8510560",  "noaa"),   # Hashamomuck Beach (38km to station)
    ("haskins-cove",                          "8571892",  "noaa"),   # Haskins Cove (20km to station)
    ("hassler-harbor",                        "9450460",  "noaa"),   # Hassler Harbor (18km to station)
    ("hatchet-lake",                          "8761724",  "noaa"),   # Hatchet Lake (14km to station)
    ("hate-cove",                             "8419870",  "noaa"),   # Hate Cove (37km to station)
    ("hatteras-bight",                        "8654467",  "noaa"),   # Hatteras Bight (12km to station)
    ("haula",                                 "1611400",  "noaa"),   # Haula (8km to station)
    ("haulover-bay",                          "9751381",  "noaa"),   # Haulover Bay (6km to station)
    ("haulover-beach",                        "8722956",  "noaa"),   # Haulover Beach (19km to station)
    ("haulover-inlet",                        "8635027",  "noaa"),   # Haulover Inlet (29km to station)
    ("haulover-nude-beach",                   "8722956",  "noaa"),   # Haulover Nude Beach (18km to station)
    ("havens-anchorage",                      "9416841",  "noaa"),   # Havens Anchorage (17km to station)
    ("havens-beach",                          "8510560",  "noaa"),   # Havens Beach (27km to station)
    ("havilland-bay",                         "9076070",  "noaa"),   # Havilland Bay (36km to station)
    ("havilland-shores-beach",                "9076070",  "noaa"),   # Havilland Shores Beach (35km to station)
    ("hawaiian-electric-beach-park",          "1612340",  "noaa"),   # Hawaiian Electric Beach Park (28km to station)
    ("hawini-bay",                            "1615680",  "noaa"),   # Hawini Bay (25km to station)
    ("hawk-cove",                             "8573364",  "noaa"),   # Hawk Cove (13km to station)
    ("hawk-hill-beach",                       "8516945",  "noaa"),   # Hawk Hill Beach (31km to station)
    ("hawk-inlet",                            "9452210",  "noaa"),   # Hawk Inlet (28km to station)
    ("hawkins-cove",                          "8575512",  "noaa"),   # Hawkins Cove (2km to station)
    ("hawkins-point-shoal",                   "8574680",  "noaa"),   # Hawkins Point Shoal (8km to station)
    ("hawksnest-bay",                         "9751381",  "noaa"),   # Hawksnest Bay (7km to station)
    ("hawley-ave-beach",                      "8465705",  "noaa"),   # Hawley Ave. Beach (9km to station)
    ("hawthorn-cove",                         "8573364",  "noaa"),   # Hawthorn Cove (14km to station)
    ("hawthorne-beach",                       "8516945",  "noaa"),   # Hawthorne Beach (22km to station)
    ("hawtree-basin",                         "8518750",  "noaa"),   # Hawtree Basin (16km to station)
    ("hay-bay",                               "8311062",  "noaa"),   # Hay Bay (20km to station)
    ("hay-harbor",                            "8461490",  "noaa"),   # Hay Harbor (14km to station)
    ("hayden-bay",                            "8418150",  "noaa"),   # Hayden Bay (30km to station)
    ("hayden-cove",                           "8635027",  "noaa"),   # Hayden Cove (19km to station)
    ("hayes-bayou",                           "8726384",  "noaa"),   # Hayes Bayou (13km to station)
    ("hayground-cove",                        "8510560",  "noaa"),   # Hayground Cove (35km to station)
    ("haynes-inlet",                          "9432780",  "noaa"),   # Haynes Inlet (15km to station)
    ("hayward-bay",                           "9087088",  "noaa"),   # Hayward Bay (31km to station)
    ("hayward-cove",                          "8571892",  "noaa"),   # Hayward Cove (24km to station)
    ("haywood-inlet",                         "9432780",  "noaa"),   # Haywood Inlet (3km to station)
    ("hazard-beach",                          "8452660",  "noaa"),   # Hazard Beach (5km to station)
    ("hazard-cove",                           "8557380",  "noaa"),   # Hazard Cove (14km to station)
    ("head-beach",                            "8418150",  "noaa"),   # Head Beach (32km to station)
    ("head-cove",                             "8418150",  "noaa"),   # Head Cove (32km to station)
    ("head-harbor",                           "8411060",  "noaa"),   # Head Harbor (31km to station)
    ("head-of-bay",                           "8516945",  "noaa"),   # Head of Bay (20km to station)
    ("head-of-bay-cove",                      "8557380",  "noaa"),   # Head of Bay Cove (10km to station)
    ("head-of-harbor",                        "8447930",  "noaa"),   # Head of Harbor (8km to station)
    ("head-of-the-gut",                       "8557380",  "noaa"),   # Head of the Gut (18km to station)
    ("head-of-the-harbor",                    "8449130",  "noaa"),   # Head of the Harbor (8km to station)
    ("head-of-the-hole",                      "8656483",  "noaa"),   # Head of the Hole (28km to station)
    ("headland-cove",                         "9413450",  "noaa"),   # Headland Cove (11km to station)
    ("headly-cove",                           "8635750",  "noaa"),   # Headly Cove (4km to station)
    ("headquarters-bay",                      "8311062",  "noaa"),   # Headquarters Bay (13km to station)
    ("heal-eddy",                             "8418150",  "noaa"),   # Heal Eddy (40km to station)
    ("heard-cove",                            "8413320",  "noaa"),   # Heard Cove (25km to station)
    ("hearns-cove",                           "8571421",  "noaa"),   # Hearns Cove (8km to station)
    ("hearts-desire-beach",                   "9415020",  "noaa"),   # Heart's Desire Beach (17km to station)
    ("heather-bay",                           "9454240",  "noaa"),   # Heather Bay (39km to station)
    ("hebden-cove",                           "8639348",  "noaa"),   # Hebden Cove (20km to station)
    ("hell-hole",                             "8766072",  "noaa"),   # Hell Hole (21km to station)
    ("hell-pass-coast",                       "8761305",  "noaa"),   # Hell Pass Coast (36km to station)
    ("hell-peckney-bay",                      "8725520",  "noaa"),   # Hell Peckney Bay (22km to station)
    ("hells-half-acre",                       "8726384",  "noaa"),   # Hells Half Acre (3km to station)
    ("hells-hole",                            "9454050",  "noaa"),   # Hells Hole (38km to station)
    ("helm-bay",                              "9450460",  "noaa"),   # Helm Bay (39km to station)
    ("helms-cove",                            "8540433",  "noaa"),   # Helms Cove (12km to station)
    ("hemlock-bay",                           "9450460",  "noaa"),   # Hemlock Bay (19km to station)
    ("hemlock-cove",                          "8516945",  "noaa"),   # Hemlock Cove (39km to station)
    ("hempstead-bay",                         "8516945",  "noaa"),   # Hempstead Bay (29km to station)
    ("hen-cove",                              "8447930",  "noaa"),   # Hen Cove (18km to station)
    ("henderson-bay",                         "9052000",  "noaa"),   # Henderson Bay (29km to station)
    ("hendrik-bay",                           "9751381",  "noaa"),   # Hendrik Bay (29km to station)
    ("hendrix-creek",                         "8518750",  "noaa"),   # Hendrix Creek (13km to station)
    ("henry-jones-creek",                     "8656483",  "noaa"),   # Henry Jones Creek (12km to station)
    ("herald-harbor-beach-1",                 "8575512",  "noaa"),   # Herald Harbor Beach 1 (10km to station)
    ("herendeen-bay",                         "9463502",  "noaa"),   # Herendeen Bay (23km to station)
    ("hero-beach",                            "8413320",  "noaa"),   # Hero Beach (33km to station)
    ("herods-cove",                           "8419870",  "noaa"),   # Herods Cove (9km to station)
    ("heron-bay",                             "8735180",  "noaa"),   # Heron Bay (11km to station)
    ("herrick-bay",                           "8413320",  "noaa"),   # Herrick Bay (30km to station)
    ("herring-bay",                           "8575512",  "noaa"),   # Herring Bay (26km to station)
    ("herring-brook-beach",                   "8447435",  "noaa"),   # Herring Brook Beach (16km to station)
    ("herring-creek",                         "8577330",  "noaa"),   # Herring Creek (17km to station)
    ("herring-pond-beach",                    "8447435",  "noaa"),   # Herring Pond Beach (15km to station)
    ("hester-cove",                           "8635750",  "noaa"),   # Hester Cove (20km to station)
    ("hewlett-bay",                           "8516945",  "noaa"),   # Hewlett Bay (22km to station)
    ("hickam-harbor-beach",                   "1612340",  "noaa"),   # Hickam Harbor Beach (9km to station)
    ("hickory-bay",                           "8665530",  "noaa"),   # Hickory Bay (32km to station)
    ("hickory-cove",                          "8557380",  "noaa"),   # Hickory Cove (23km to station)
    ("hickory-creek-bay",                     "8654467",  "noaa"),   # Hickory Creek Bay (40km to station)
    ("hickorynut-cove",                       "8637689",  "noaa"),   # Hickorynut Cove (34km to station)
    ("hicks-beach",                           "8516945",  "noaa"),   # Hicks Beach (25km to station)
    ("hicks-cove",                            "8452660",  "noaa"),   # Hicks Cove (20km to station)
    ("hidden-anchorage",                      "9410170",  "noaa"),   # Hidden Anchorage (7km to station)
    ("hidden-beach",                          "9419750",  "noaa"),   # Hidden Beach (20km to station)
    ("hidden-cove",                           "9454050",  "noaa"),   # Hidden Cove (14km to station)
    ("hidden-creek",                          "8575512",  "noaa"),   # Hidden Creek (18km to station)
    ("higbee-beach",                          "8536110",  "noaa"),   # Higbee Beach (1km to station)
    ("higgs-bay",                             "2695535",  "noaa"),   # Higgs Bay (2km to station)
    ("high-island-bay",                       "9087096",  "noaa"),   # High Island Bay (31km to station)
    ("hiller-cove",                           "8447930",  "noaa"),   # Hiller Cove (17km to station)
    ("hillerys-cove",                         "8654467",  "noaa"),   # Hillerys Cove (37km to station)
    ("hills-bay",                             "8637689",  "noaa"),   # Hills Bay (33km to station)
    ("hills-beach",                           "8418150",  "noaa"),   # Hills Beach (25km to station)
    ("hills-beach-cove",                      "8418150",  "noaa"),   # Hills Beach Cove (25km to station)
    ("hills-cove",                            "8573364",  "noaa"),   # Hills Cove (10km to station)
    ("hills-creek",                           "8635750",  "noaa"),   # Hills Creek (32km to station)
    ("hills-point-cove",                      "8571892",  "noaa"),   # Hills Point Cove (21km to station)
    ("hillsboro-bay",                         "8722956",  "noaa"),   # Hillsboro Bay (20km to station)
    ("hillsborough-bay",                      "8726674",  "noaa"),   # Hillsborough Bay (10km to station)
    ("hingle-pond",                           "8760721",  "noaa"),   # Hingle Pond (12km to station)
    ("hinson-bay",                            "2695540",  "noaa"),   # Hinson Bay (10km to station)
    ("hive-bay",                              "9462620",  "noaa"),   # Hive Bay (26km to station)
    ("hoanuanu-bay",                          "1611400",  "noaa"),   # Ho'anuanu Bay (30km to station)
    ("hoai-bay",                              "1611400",  "noaa"),   # Hoai Bay (15km to station)
    ("hoai-bay-lawai-beach",                  "1611400",  "noaa"),   # Hoai Bay / Lawai Beach (15km to station)
    ("hoalua-bay",                            "1615680",  "noaa"),   # Hoalua Bay (26km to station)
    ("hobie-island-beach",                    "8723214",  "noaa"),   # Hobie Island Beach (4km to station)
    ("hobie-island-beach-park",               "8723214",  "noaa"),   # Hobie Island Beach Park (2km to station)
    ("hodges-bayou",                          "8729108",  "noaa"),   # Hodges Bayou (15km to station)
    ("hodges-cove",                           "8637689",  "noaa"),   # Hodges Cove (9km to station)
    ("hodgon-cove",                           "8413320",  "noaa"),   # Hodgon Cove (18km to station)
    ("hog-inlet",                             "8661070",  "noaa"),   # Hog Inlet (36km to station)
    ("hog-island-bay",                        "8631044",  "noaa"),   # Hog Island Bay (20km to station)
    ("hog-marsh-creek",                       "8577330",  "noaa"),   # Hog Marsh Creek (21km to station)
    ("hog-neck-bay",                          "8510560",  "noaa"),   # Hog Neck Bay (40km to station)
    ("hog-and-hominy-cove",                   "8726674",  "noaa"),   # Hog and Hominy Cove (11km to station)
    ("hogfish-bay",                           "2695540",  "noaa"),   # Hogfish Bay (12km to station)
    ("hogpen-bay",                            "8656483",  "noaa"),   # Hogpen Bay (17km to station)
    ("hoktaheen-cove",                        "9452634",  "noaa"),   # Hoktaheen Cove (18km to station)
    ("holana-bay",                            "1617433",  "noaa"),   # Holana Bay (24km to station)
    ("hole-in-the-wall",                      "9076024",  "noaa"),   # Hole in the Wall (20km to station)
    ("hole-in-the-wall-beach",                "8461490",  "noaa"),   # Hole-in-the-Wall Beach (10km to station)
    ("holiday-beach",                         "8775237",  "noaa"),   # Holiday Beach (3km to station)
    ("holiday-cove",                          "8726724",  "noaa"),   # Holiday Cove (18km to station)
    ("holland-island-bay",                    "8571421",  "noaa"),   # Holland Island Bay (11km to station)
    ("holliday-bay",                          "9052000",  "noaa"),   # Holliday Bay (11km to station)
    ("hollingsworth-beach",                   "9751364",  "noaa"),   # Hollingsworth Beach (12km to station)
    ("holly-grove-cove",                      "8631044",  "noaa"),   # Holly Grove Cove (22km to station)
    ("holly-shelter-bay",                     "8658163",  "noaa"),   # Holly Shelter Bay (28km to station)
    ("hollywoods-beach",                      "8447930",  "noaa"),   # Hollywoods Beach (16km to station)
    ("holmes-bay",                            "8411060",  "noaa"),   # Holmes Bay (9km to station)
    ("holmes-cove",                           "8536110",  "noaa"),   # Holmes Cove (20km to station)
    ("home-bay",                              "9415020",  "noaa"),   # Home Bay (9km to station)
    ("homewood-cove",                         "8575512",  "noaa"),   # Homewood Cove (5km to station)
    ("honda-cove",                            "9418767",  "noaa"),   # Honda Cove (31km to station)
    ("honeymoon-beach",                       "9751381",  "noaa"),   # Honeymoon Beach (8km to station)
    ("honker-bay",                            "9414750",  "noaa"),   # Honker Bay (19km to station)
    ("honokahua-bay",                         "1615680",  "noaa"),   # Honokahua Bay (23km to station)
    ("honokaope-bay",                         "1617433",  "noaa"),   # Honokaope Bay (12km to station)
    ("honokeana-bay",                         "1615680",  "noaa"),   # Honokeana Bay (23km to station)
    ("honokohau-bay",                         "1615680",  "noaa"),   # Honokohau Bay (21km to station)
    ("honokowai-beach-park",                  "1615680",  "noaa"),   # Honokowai Beach Park (24km to station)
    ("honolii-beach",                         "1617760",  "noaa"),   # Honoli‘i Beach (5km to station)
    ("honolii-cove",                          "1617760",  "noaa"),   # Honoli‘i Cove (5km to station)
    ("honolulu-nui-bay",                      "1615680",  "noaa"),   # Honolulu Nui Bay (39km to station)
    ("honoman-bay",                           "1615680",  "noaa"),   # Honomanū Bay (32km to station)
    ("honomuni-harbor",                       "1615680",  "noaa"),   # Honomuni Harbor (38km to station)
    ("hononana",                              "1615680",  "noaa"),   # Hononana (17km to station)
    ("honop-beach",                           "1611400",  "noaa"),   # Honopū Beach (40km to station)
    ("honouli-maloo-bay-beach",               "1615680",  "noaa"),   # Honouli Maloo Bay Beach (37km to station)
    ("honouli-wai",                           "1615680",  "noaa"),   # Honouli Wai (37km to station)
    ("honoulimaloo",                          "1615680",  "noaa"),   # Honoulimalo‘o (38km to station)
    ("hookipa-park-beach",                    "1615680",  "noaa"),   # Hookipa Park Beach (12km to station)
    ("hooks-creek-lake-beach",                "8531680",  "noaa"),   # Hooks Creek Lake Beach (22km to station)
    ("hoolawa-bay",                           "1615680",  "noaa"),   # Hoolawa Bay (24km to station)
    ("hooper-beach",                          "9413450",  "noaa"),   # Hooper Beach (40km to station)
    ("hooper-cove",                           "8571892",  "noaa"),   # Hooper Cove (21km to station)
    ("hope-pond-beach",                       "8454000",  "noaa"),   # Hope Pond Beach (16km to station)
    ("hopkins-creek",                         "8575512",  "noaa"),   # Hopkins Creek (10km to station)
    ("horn-harbor",                           "8637689",  "noaa"),   # Horn Harbor (23km to station)
    ("horne-bay",                             "8571892",  "noaa"),   # Horne Bay (6km to station)
    ("horse-duck-pond",                       "8760721",  "noaa"),   # Horse Duck Pond (6km to station)
    ("horse-foot-cove",                       "8534720",  "noaa"),   # Horse Foot Cove (24km to station)
    ("horse-island-bayou",                    "8770613",  "noaa"),   # Horse Island Bayou (22km to station)
    ("horse-island-cove",                     "8656483",  "noaa"),   # Horse Island Cove (26km to station)
    ("horse-marine-lagoon",                   "9457804",  "noaa"),   # Horse Marine Lagoon (30km to station)
    ("horse-thief-bay",                       "8311062",  "noaa"),   # Horse Thief Bay (5km to station)
    ("horsefoot-path-beach",                  "8447435",  "noaa"),   # Horsefoot Path Beach (23km to station)
    ("horseshoe-bayou",                       "8729108",  "noaa"),   # Horseshoe Bayou (28km to station)
    ("horseshoe-cove",                        "8418150",  "noaa"),   # Horseshoe Cove (29km to station)
    ("horseshoe-harbor",                      "8516945",  "noaa"),   # Horseshoe Harbor (12km to station)
    ("horseshoe-harbour",                     "9076070",  "noaa"),   # Horseshoe Harbour (25km to station)
    ("horseshoe-pond",                        "8760721",  "noaa"),   # Horseshoe Pond (9km to station)
    ("horsey-bay",                            "9052000",  "noaa"),   # Horsey Bay (22km to station)
    ("horton-bay",                            "8656483",  "noaa"),   # Horton Bay (31km to station)
    ("horton-cove",                           "8461490",  "noaa"),   # Horton Cove (8km to station)
    ("hospital-bay",                          "8760721",  "noaa"),   # Hospital Bay (20km to station)
    ("hospital-cove",                         "8447930",  "noaa"),   # Hospital Cove (16km to station)
    ("hospital-pond",                         "8760721",  "noaa"),   # Hospital Pond (9km to station)
    ("hot-springs-bay",                       "9451600",  "noaa"),   # Hot Springs Bay (24km to station)
    ("hotchkiss-cove",                        "8465705",  "noaa"),   # Hotchkiss Cove (11km to station)
    ("hotchkiss-cove-beach",                  "8465705",  "noaa"),   # Hotchkiss Cove Beach (10km to station)
    ("hotchkiss-grove-beach",                 "8465705",  "noaa"),   # Hotchkiss Grove Beach (10km to station)
    ("house-cove",                            "8411060",  "noaa"),   # House Cove (2km to station)
    ("house-creek",                           "8594900",  "noaa"),   # House Creek (31km to station)
    ("howard-bay",                            "9452210",  "noaa"),   # Howard Bay (39km to station)
    ("howard-cove",                           "8411060",  "noaa"),   # Howard Cove (14km to station)
    ("howard-park-beach",                     "8726724",  "noaa"),   # Howard Park Beach (20km to station)
    ("howards-bay",                           "2695535",  "noaa"),   # Howard's Bay (4km to station)
    ("huckins-beach",                         "8410140",  "noaa"),   # Huckins Beach (6km to station)
    ("huckleberry-hollow-bay",                "8311062",  "noaa"),   # Huckleberry Hollow Bay (21km to station)
    ("hudson-creek",                          "8571892",  "noaa"),   # Hudson Creek (17km to station)
    ("hudson-park-beach",                     "8516945",  "noaa"),   # Hudson Park Beach (11km to station)
    ("huffman-harbor",                        "9452210",  "noaa"),   # Huffman Harbor (30km to station)
    ("huguenot-beach",                        "8531680",  "noaa"),   # Huguenot Beach (16km to station)
    ("huldas-cove",                           "8452660",  "noaa"),   # Hulda's Cove (21km to station)
    ("hull-bay",                              "9751381",  "noaa"),   # Hull Bay (25km to station)
    ("hull-bay-beach",                        "9751381",  "noaa"),   # Hull Bay Beach (25km to station)
    ("hull-cove",                             "8452660",  "noaa"),   # Hull Cove (7km to station)
    ("hulls-cove",                            "8413320",  "noaa"),   # Hulls Cove (4km to station)
    ("humble-cut",                            "8771972",  "noaa"),   # Humble Cut (12km to station)
    ("humboldt-bay",                          "9418767",  "noaa"),   # Humboldt Bay (2km to station)
    ("humboldt-harbor",                       "9459450",  "noaa"),   # Humboldt Harbor (0km to station)
    ("hummock-cove",                          "8631044",  "noaa"),   # Hummock Cove (3km to station)
    ("humpback-bay",                          "9462620",  "noaa"),   # Humpback Bay (27km to station)
    ("humpback-cove",                         "9453220",  "noaa"),   # Humpback Cove (15km to station)
    ("humpy-cove",                            "9457804",  "noaa"),   # Humpy Cove (15km to station)
    ("hunakai-beach",                         "1612340",  "noaa"),   # Hunakai Beach (10km to station)
    ("hundred-acre-cove",                     "8452944",  "noaa"),   # Hundred Acre Cove (6km to station)
    ("hungars-beach",                         "8632200",  "noaa"),   # Hungars Beach (24km to station)
    ("hunger-bay",                            "8418150",  "noaa"),   # Hunger Bay (26km to station)
    ("hungry-bay",                            "2695540",  "noaa"),   # Hungry Bay (11km to station)
    ("hungryman-cove",                        "9432780",  "noaa"),   # Hungryman Cove (4km to station)
    ("hunnewell-beach",                       "8418150",  "noaa"),   # Hunnewell Beach (38km to station)
    ("hunters-beach",                         "8413320",  "noaa"),   # Hunters Beach (10km to station)
    ("hunters-beach-cove",                    "8413320",  "noaa"),   # Hunters Beach Cove (11km to station)
    ("hunters-harbor",                        "8575512",  "noaa"),   # Hunters Harbor (13km to station)
    ("huntington-harbor",                     "8516945",  "noaa"),   # Huntington Harbor (30km to station)
    ("hunts-cove",                            "8635750",  "noaa"),   # Hunts Cove (38km to station)
    ("hurricane-bay",                         "8725520",  "noaa"),   # Hurricane Bay (22km to station)
    ("hurricane-harbor",                      "8723214",  "noaa"),   # Hurricane Harbor (5km to station)
    ("hurricane-hole",                        "9751381",  "noaa"),   # Hurricane Hole (4km to station)
    ("hurricane-beach",                       "8447930",  "noaa"),   # Hurricane beach (14km to station)
    ("hussey-sound",                          "8418150",  "noaa"),   # Hussey Sound (6km to station)
    ("hutchins-cove",                         "8419870",  "noaa"),   # Hutchins Cove (3km to station)
    ("huylers-beach",                         "8516945",  "noaa"),   # Huylers Beach (19km to station)
    ("hyannis-inner-harbor",                  "8447435",  "noaa"),   # Hyannis Inner Harbor (27km to station)
    ("hyannis-outer-harbor",                  "8447435",  "noaa"),   # Hyannis Outer Harbor (29km to station)
    ("hyannis-port-beach",                    "8447435",  "noaa"),   # Hyannis Port Beach (30km to station)
    ("hyde-hole",                             "8452944",  "noaa"),   # Hyde Hole (3km to station)
    ("hyndman-bay",                           "9075099",  "noaa"),   # Hyndman Bay (38km to station)
    ("hynes-bay",                             "8773037",  "noaa"),   # Hynes Bay (10km to station)
    ("hhaha-bay",                             "1615680",  "noaa"),   # Hāhaha Bay (35km to station)
    ("hlona-cove",                            "1612340",  "noaa"),   # Hālona Cove (20km to station)
    ("hula-beach",                            "1611400",  "noaa"),   # Hāʻula Beach (8km to station)
    ("ibis-cove",                             "8720218",  "noaa"),   # Ibis Cove (20km to station)
    ("ice-harbor",                            "8551910",  "noaa"),   # Ice Harbor (5km to station)
    ("ice-house-cove",                        "8637689",  "noaa"),   # Ice House Cove (22km to station)
    ("ice-pond",                              "1617760",  "noaa"),   # Ice Pond (1km to station)
    ("idlewood-beach",                        "9087031",  "noaa"),   # Idlewood Beach (2km to station)
    ("iliilinaehehe-bay",                     "1617433",  "noaa"),   # Iliilinaehehe Bay (12km to station)
    ("ilin-bay",                              "9452634",  "noaa"),   # Ilin Bay (40km to station)
    ("iliuliuk-bay",                          "9462620",  "noaa"),   # Iliuliuk Bay (3km to station)
    ("iliuliuk-harbor",                       "9462620",  "noaa"),   # Iliuliuk Harbor (0km to station)
    ("inbocht-bay",                           "8518962",  "noaa"),   # Inbocht Bay (18km to station)
    ("india-basin",                           "9414750",  "noaa"),   # India Basin (7km to station)
    ("indian-bay",                            "8735180",  "noaa"),   # Indian Bay (4km to station)
    ("indian-cove",                           "8465705",  "noaa"),   # Indian Cove (19km to station)
    ("indian-cove-beach",                     "8465705",  "noaa"),   # Indian Cove Beach (19km to station)
    ("indian-creek",                          "8575512",  "noaa"),   # Indian Creek (15km to station)
    ("indian-hammock-cove",                   "8571421",  "noaa"),   # Indian Hammock Cove (37km to station)
    ("indian-harbor",                         "8516945",  "noaa"),   # Indian Harbor (26km to station)
    ("indian-lagoon",                         "8728690",  "noaa"),   # Indian Lagoon (25km to station)
    ("indian-mound-bay",                      "8761305",  "noaa"),   # Indian Mound Bay (37km to station)
    ("indian-mound-beach",                    "8447930",  "noaa"),   # Indian Mound Beach (26km to station)
    ("indian-river-bay",                      "8557380",  "noaa"),   # Indian River Bay (20km to station)
    ("indian-river-lagoon",                   "8721604",  "noaa"),   # Indian River Lagoon (40km to station)
    ("indiantown-beach",                      "8461490",  "noaa"),   # Indiantown Beach (28km to station)
    ("indiantown-cove",                       "8635027",  "noaa"),   # Indiantown Cove (19km to station)
    ("indiantown-harbor",                     "8461490",  "noaa"),   # Indiantown Harbor (28km to station)
    ("ingleside-cove",                        "8775283",  "noaa"),   # Ingleside Cove (3km to station)
    ("ingram-bay",                            "8635750",  "noaa"),   # Ingram Bay (27km to station)
    ("ingram-beach",                          "8661070",  "noaa"),   # Ingram Beach (28km to station)
    ("inian-cove",                            "9452634",  "noaa"),   # Inian Cove (8km to station)
    ("inland-harbor",                         "9087096",  "noaa"),   # Inland Harbor (0km to station)
    ("inman-road-beach",                      "8447435",  "noaa"),   # Inman Road Beach (14km to station)
    ("inner-harbor",                          "8574680",  "noaa"),   # Inner Harbor (3km to station)
    ("inner-harbour",                         "9052000",  "noaa"),   # Inner Harbour (17km to station)
    ("inner-winter-harbor",                   "8413320",  "noaa"),   # Inner Winter Harbor (9km to station)
    ("inside-beach",                          "9455500",  "noaa"),   # Inside Beach (0km to station)
    ("insley-cove",                           "8571421",  "noaa"),   # Insley Cove (10km to station)
    ("inspecting-creek",                      "8575512",  "noaa"),   # Inspecting Creek (14km to station)
    ("intercoastal",                          "8729840",  "noaa"),   # Intercoastal (25km to station)
    ("iodine-beach",                          "8510560",  "noaa"),   # Iodine Beach (8km to station)
    ("ipsenancy-creek",                       "8571421",  "noaa"),   # Ipsenancy Creek (28km to station)
    ("irish-cove",                            "9454240",  "noaa"),   # Irish Cove (40km to station)
    ("iroquois-beach",                        "8311030",  "noaa"),   # Iroquois Beach (22km to station)
    ("isaacs-bay",                            "9751364",  "noaa"),   # Isaacs Bay (13km to station)
    ("isaacs-bay-beach",                      "9751364",  "noaa"),   # Isaacs Bay Beach (14km to station)
    ("isaacson-bay",                          "9075065",  "noaa"),   # Isaacson Bay (4km to station)
    ("isabella-beach",                        "8461490",  "noaa"),   # Isabella Beach (15km to station)
    ("isabella-point-road-beach",             "9449880",  "noaa"),   # Isabella Point Road Beach (40km to station)
    ("isaiahs-gully",                         "8452660",  "noaa"),   # Isaiahs Gully (37km to station)
    ("island-creek",                          "8635750",  "noaa"),   # Island Creek (13km to station)
    ("island-field-cove",                     "8631044",  "noaa"),   # Island Field Cove (27km to station)
    ("island-harbor",                         "9075099",  "noaa"),   # Island Harbor (8km to station)
    ("islington-bay",                         "9076024",  "noaa"),   # Islington Bay (34km to station)
    ("israels-cove",                          "8447930",  "noaa"),   # Israels Cove (10km to station)
    ("ivor-cove",                             "9457804",  "noaa"),   # Ivor Cove (26km to station)
    ("ivy-bay",                               "8311062",  "noaa"),   # Ivy Bay (7km to station)
    ("izaak-walton-bay",                      "9076070",  "noaa"),   # Izaak Walton Bay (10km to station)
    ("izembek-slough",                        "9459881",  "noaa"),   # Izembek Slough (40km to station)
    ("j-p-luby",                              "8775792",  "noaa"),   # J P Luby (4km to station)
    ("jack-bay",                              "9751364",  "noaa"),   # Jack Bay (12km to station)
    ("jack-cove",                             "8635750",  "noaa"),   # Jack Cove (39km to station)
    ("jackal-cove",                           "8725520",  "noaa"),   # Jackal Cove (30km to station)
    ("jackass-bay",                           "8760721",  "noaa"),   # Jackass Bay (13km to station)
    ("jacko-camp-bay",                        "8761724",  "noaa"),   # Jacko Camp Bay (34km to station)
    ("jacks",                                 "8770613",  "noaa"),   # Jacks (28km to station)
    ("jacks-bay",                             "8656483",  "noaa"),   # Jacks Bay (36km to station)
    ("jacks-cove",                            "8575512",  "noaa"),   # Jacks Cove (6km to station)
    ("jackson-beach",                         "9449880",  "noaa"),   # Jackson Beach (3km to station)
    ("jackson-cove",                          "8467150",  "noaa"),   # Jackson Cove (26km to station)
    ("jackson-cove-beach",                    "8467150",  "noaa"),   # Jackson Cove Beach (26km to station)
    ("jackson-creek",                         "8575512",  "noaa"),   # Jackson Creek (22km to station)
    ("jacob-riis-park-beach-1",               "8531680",  "noaa"),   # Jacob Riis Park Beach 1 (17km to station)
    ("jacob-riis-park-beach-10",              "8531680",  "noaa"),   # Jacob Riis Park Beach 10 (16km to station)
    ("jacob-riis-park-beach-11",              "8531680",  "noaa"),   # Jacob Riis Park Beach 11 (16km to station)
    ("jacob-riis-park-beach-12",              "8531680",  "noaa"),   # Jacob Riis Park Beach 12 (15km to station)
    ("jacob-riis-park-beach-13",              "8531680",  "noaa"),   # Jacob Riis Park Beach 13 (15km to station)
    ("jacob-riis-park-beach-14",              "8531680",  "noaa"),   # Jacob Riis Park Beach 14 (15km to station)
    ("jacob-riis-park-beach-2",               "8531680",  "noaa"),   # Jacob Riis Park Beach 2 (16km to station)
    ("jacob-riis-park-beach-3",               "8531680",  "noaa"),   # Jacob Riis Park Beach 3 (16km to station)
    ("jacob-riis-park-beach-4",               "8531680",  "noaa"),   # Jacob Riis Park Beach 4 (16km to station)
    ("jacob-riis-park-beach-5",               "8531680",  "noaa"),   # Jacob Riis Park Beach 5 (16km to station)
    ("jacob-riis-park-beach-6",               "8531680",  "noaa"),   # Jacob Riis Park Beach 6 (16km to station)
    ("jacob-riis-park-beach-7",               "8531680",  "noaa"),   # Jacob Riis Park Beach 7 (16km to station)
    ("jacob-riis-park-beach-8",               "8531680",  "noaa"),   # Jacob Riis Park Beach 8 (16km to station)
    ("jacob-riis-park-beach-9",               "8531680",  "noaa"),   # Jacob Riis Park Beach 9 (16km to station)
    ("jacobs-public-beach",                   "8465705",  "noaa"),   # Jacobs Public Beach (20km to station)
    ("jade-harbor",                           "9454240",  "noaa"),   # Jade Harbor (37km to station)
    ("jamboree-bay",                          "9451600",  "noaa"),   # Jamboree Bay (40km to station)
    ("james-cove",                            "8635750",  "noaa"),   # James Cove (39km to station)
    ("james-pond",                            "8575512",  "noaa"),   # James Pond (13km to station)
    ("jamestown-bay",                         "9451600",  "noaa"),   # Jamestown Bay (3km to station)
    ("janes-cove",                            "8447930",  "noaa"),   # Janes Cove (19km to station)
    ("japan-outside-pond",                    "8760721",  "noaa"),   # Japan Outside Pond (15km to station)
    ("jarrett-bay",                           "8656483",  "noaa"),   # Jarrett Bay (19km to station)
    ("jarvis-sound",                          "8536110",  "noaa"),   # Jarvis Sound (8km to station)
    ("jasper-beach",                          "8411060",  "noaa"),   # Jasper Beach (13km to station)
    ("jay-bird-shoals",                       "8658120",  "noaa"),   # Jay Bird Shoals (40km to station)
    ("jean-plaisance-bay",                    "8761724",  "noaa"),   # Jean Plaisance Bay (36km to station)
    ("jeanette-creek",                        "8665530",  "noaa"),   # Jeanette Creek (7km to station)
    ("jellison-cove",                         "8413320",  "noaa"),   # Jellison Cove (11km to station)
    ("jenkins-cove",                          "8635750",  "noaa"),   # Jenkins Cove (26km to station)
    ("jenkins-sound",                         "8536110",  "noaa"),   # Jenkins Sound (16km to station)
    ("jennings-bay",                          "2695540",  "noaa"),   # Jennings Bay (20km to station)
    ("jensen-harbor",                         "9087096",  "noaa"),   # Jensen Harbor (36km to station)
    ("jeremy-cove",                           "8449130",  "noaa"),   # Jeremy Cove (6km to station)
    ("jericho-bay",                           "8413320",  "noaa"),   # Jericho Bay (35km to station)
    ("jerry-bay",                             "8656483",  "noaa"),   # Jerry Bay (20km to station)
    ("jerry-harbor",                          "9451054",  "noaa"),   # Jerry Harbor (26km to station)
    ("jerrys-cove",                           "8573364",  "noaa"),   # Jerrys Cove (12km to station)
    ("jerusalem-bayou",                       "9087031",  "noaa"),   # Jerusalem Bayou (38km to station)
    ("jesse-beach",                           "8413320",  "noaa"),   # Jesse Beach (32km to station)
    ("jetty-beach",                           "9413450",  "noaa"),   # Jetty Beach (24km to station)
    ("jewell-gillespie-park-beach",           "9087096",  "noaa"),   # Jewell Gillespie Park Beach (37km to station)
    ("jewfish-basin",                         "8724580",  "noaa"),   # Jewfish Basin (14km to station)
    ("jewfish-hole",                          "8723970",  "noaa"),   # Jewfish Hole (35km to station)
    ("jews-bay",                              "2695540",  "noaa"),   # Jews Bay (18km to station)
    ("jobs-neck-cove",                        "8447930",  "noaa"),   # Jobs Neck Cove (20km to station)
    ("jobsons-cove",                          "2695540",  "noaa"),   # Jobson's Cove (17km to station)
    ("jobsons-cove-beach",                    "2695540",  "noaa"),   # Jobson's Cove Beach (17km to station)
    ("jock-mock-bay",                         "9099090",  "noaa"),   # Jock Mock Bay (33km to station)
    ("jocko-bay",                             "9075099",  "noaa"),   # Jocko Bay (24km to station)
    ("joe-bay",                               "8726384",  "noaa"),   # Joe Bay (6km to station)
    ("joe-brown-pond",                        "8760721",  "noaa"),   # Joe Brown Pond (10km to station)
    ("joe-cooley-bay",                        "8767816",  "noaa"),   # Joe Cooley Bay (21km to station)
    ("joe-dennis-pond",                       "8760721",  "noaa"),   # Joe Dennis Pond (11km to station)
    ("joe-dollar-bay",                        "9075099",  "noaa"),   # Joe Dollar Bay (35km to station)
    ("joe-hamel-beach",                       "9449880",  "noaa"),   # Joe Hamel Beach (40km to station)
    ("joe-welsh-bay",                         "9052000",  "noaa"),   # Joe Welsh Bay (17km to station)
    ("joel-stone-beach",                      "8311062",  "noaa"),   # Joel Stone Beach (18km to station)
    ("joemma-beach",                          "9446484",  "noaa"),   # Joemma Beach (30km to station)
    ("joes-bay",                              "8760721",  "noaa"),   # Joes Bay (11km to station)
    ("joes-cove",                             "8571421",  "noaa"),   # Joes Cove (12km to station)
    ("joes-pond",                             "8760721",  "noaa"),   # Joes Pond (12km to station)
    ("john-bay",                              "9451054",  "noaa"),   # John Bay (4km to station)
    ("john-brewers-bay",                      "9751381",  "noaa"),   # John Brewers Bay (27km to station)
    ("john-cove",                             "8418150",  "noaa"),   # John Cove (11km to station)
    ("john-creek",                            "8635750",  "noaa"),   # John Creek (31km to station)
    ("john-johnson-pond",                     "8760721",  "noaa"),   # John Johnson Pond (7km to station)
    ("john-small-cove",                       "8413320",  "noaa"),   # John Small Cove (12km to station)
    ("john-smiths-bay",                       "2695535",  "noaa"),   # John Smith's Bay (6km to station)
    ("john-smiths-bay-beach",                 "2695535",  "noaa"),   # John Smith's Bay Beach (6km to station)
    ("johns-cove",                            "8418150",  "noaa"),   # John's Cove (12km to station)
    ("johns-folly-bay",                       "9751381",  "noaa"),   # John's Folly Bay (2km to station)
    ("johns-creek",                           "8575512",  "noaa"),   # Johns Creek (18km to station)
    ("johns-folly-beach",                     "9751381",  "noaa"),   # Johns Folly Beach (2km to station)
    ("johnson-bay",                           "9751381",  "noaa"),   # Johnson Bay (3km to station)
    ("johnson-bayou",                         "8729108",  "noaa"),   # Johnson Bayou (14km to station)
    ("johnson-cove",                          "8729840",  "noaa"),   # Johnson Cove (34km to station)
    ("johnson-creek",                         "8656483",  "noaa"),   # Johnson Creek (22km to station)
    ("johnson-slough",                        "9455500",  "noaa"),   # Johnson Slough (11km to station)
    ("johnsons-bay",                          "8656483",  "noaa"),   # Johnsons Bay (13km to station)
    ("joiners-cove",                          "8573364",  "noaa"),   # Joiners Cove (13km to station)
    ("jolly-bay",                             "8729210",  "noaa"),   # Jolly Bay (34km to station)
    ("jones-bay",                             "8516945",  "noaa"),   # Jones Bay (30km to station)
    ("jones-bayou",                           "8726384",  "noaa"),   # Jones Bayou (21km to station)
    ("jones-cove",                            "8632200",  "noaa"),   # Jones Cove (4km to station)
    ("jones-creek",                           "8571421",  "noaa"),   # Jones Creek (26km to station)
    ("jose-bay",                              "8741533",  "noaa"),   # Jose Bay (14km to station)
    ("joseph-sanford-jr-channel",             "8516945",  "noaa"),   # Joseph Sanford Jr. Channel (22km to station)
    ("joshia-cove",                           "8557380",  "noaa"),   # Joshia Cove (23km to station)
    ("joshia-prong",                          "8557380",  "noaa"),   # Joshia Prong (22km to station)
    ("joshua-cove",                           "8465705",  "noaa"),   # Joshua Cove (17km to station)
    ("josiahs-cove",                          "8418150",  "noaa"),   # Josiahs Cove (5km to station)
    ("joy-bay",                               "8413320",  "noaa"),   # Joy Bay (21km to station)
    ("joy-cove",                              "8413320",  "noaa"),   # Joy Cove (21km to station)
    ("joy-harbor",                            "8574680",  "noaa"),   # Joy Harbor (14km to station)
    ("joyce-beach",                           "8413320",  "noaa"),   # Joyce Beach (29km to station)
    ("jubb-cove",                             "8575512",  "noaa"),   # Jubb Cove (16km to station)
    ("juddville-bay",                         "9087088",  "noaa"),   # Juddville Bay (25km to station)
    ("judith-sound",                          "8635750",  "noaa"),   # Judith Sound (2km to station)
    ("judiths-fancy-beach",                   "9751364",  "noaa"),   # Judiths Fancy Beach (6km to station)
    ("jug-bay",                               "8594900",  "noaa"),   # Jug Bay (30km to station)
    ("jug-lake",                              "8764227",  "noaa"),   # Jug Lake (39km to station)
    ("jumbie-bay",                            "9751381",  "noaa"),   # Jumbie Bay (6km to station)
    ("jumbile-cove",                          "8771486",  "noaa"),   # Jumbile Cove (15km to station)
    ("jump-run",                              "8656483",  "noaa"),   # Jump Run (16km to station)
    ("juniper-trail-beach",                   "8447386",  "noaa"),   # Juniper Trail Beach (7km to station)
    ("k-9-coastline",                         "9063063",  "noaa"),   # K-9 Coastline (11km to station)
    ("king-lake",                             "8764314",  "noaa"),   # KIng Lake (40km to station)
    ("kailiili-bay",                          "1612480",  "noaa"),   # Ka'ili'ili Bay (20km to station)
    ("kaopala-beach",                         "1615680",  "noaa"),   # Ka'opala Beach (23km to station)
    ("kachemak-bay",                          "9455500",  "noaa"),   # Kachemak Bay (36km to station)
    ("kaelehuluhulu-beach",                   "1617433",  "noaa"),   # Kaelehuluhulu Beach (36km to station)
    ("kaguyak-bay",                           "9457804",  "noaa"),   # Kaguyak Bay (32km to station)
    ("kahana-bay-beach",                      "1612480",  "noaa"),   # Kahana Bay Beach (16km to station)
    ("kahauloa-cove",                         "1612340",  "noaa"),   # Kahauloa Cove (19km to station)
    ("kahe-point",                            "1612340",  "noaa"),   # Kahe Point (28km to station)
    ("kaheka-bay",                            "1611400",  "noaa"),   # Kaheka Bay (15km to station)
    ("kahekili-beach",                        "1615680",  "noaa"),   # Kahekili Beach (24km to station)
    ("kahoiawa-bay",                          "1617433",  "noaa"),   # Kahoiawa Bay (32km to station)
    ("kahuwai-bay",                           "1617433",  "noaa"),   # Kahuwai Bay (28km to station)
    ("kahuwai-beach",                         "1617433",  "noaa"),   # Kahuwai Beach (28km to station)
    ("kaiaka-bay",                            "1612480",  "noaa"),   # Kaiaka Bay (38km to station)
    ("kaiaka-bay-beach",                      "1612480",  "noaa"),   # Kaiaka Bay Beach (38km to station)
    ("kaihalulu",                             "1612480",  "noaa"),   # Kaihalulu (37km to station)
    ("kaihalulu-beach",                       "1612480",  "noaa"),   # Kaihalulu Beach (37km to station)
    ("kaihuokapuaa",                          "1612340",  "noaa"),   # Kaihuokapuaa (18km to station)
    ("kain-cove",                             "8773146",  "noaa"),   # Kain Cove (8km to station)
    ("kaipapau-beach",                        "1612480",  "noaa"),   # Kaipapa‘U Beach (25km to station)
    ("kakapa-bay",                            "1617433",  "noaa"),   # Kakapa Bay (30km to station)
    ("kalaeio-beach",                         "1612480",  "noaa"),   # Kalaeʻōʻio Beach (14km to station)
    ("kalalau-beach",                         "1611400",  "noaa"),   # Kalalau Beach (40km to station)
    ("kalamanu",                              "1617760",  "noaa"),   # Kalamanu (30km to station)
    ("kalapaki-beach",                        "1611400",  "noaa"),   # Kalapaki Beach (1km to station)
    ("kalekta-bay",                           "9462620",  "noaa"),   # Kalekta Bay (17km to station)
    ("kalepolepo-beach-park",                 "1615680",  "noaa"),   # Kalepolepo Beach Park (14km to station)
    ("kalhagu-cove",                          "9452400",  "noaa"),   # Kalhagu Cove (38km to station)
    ("kalihiwai-bay",                         "1611400",  "noaa"),   # Kalihiwai Bay (31km to station)
    ("kalinin-bay",                           "9451600",  "noaa"),   # Kalinin Bay (40km to station)
    ("kaluhikaa-beach",                       "1617433",  "noaa"),   # Kaluhikaa Beach (2km to station)
    ("kamaole-i-beach",                       "1615680",  "noaa"),   # Kamaole I Beach (19km to station)
    ("kamaole-ii-beach",                      "1615680",  "noaa"),   # Kamaole II Beach (20km to station)
    ("kamaole-iii-beach",                     "1615680",  "noaa"),   # Kamaole III Beach (20km to station)
    ("kanaha-beach",                          "1615680",  "noaa"),   # Kanaha Beach (3km to station)
    ("kanapou-bay",                           "1615680",  "noaa"),   # Kanapou Bay (39km to station)
    ("kaneakua-cove",                         "1612480",  "noaa"),   # Kaneakua Cove (36km to station)
    ("kanga-bay",                             "9451600",  "noaa"),   # Kanga Bay (18km to station)
    ("kapana-bay",                            "1617433",  "noaa"),   # Kapana Bay (23km to station)
    ("kapes-bayou",                           "8728690",  "noaa"),   # Kapes Bayou (32km to station)
    ("kapuaraaka",                            "1615680",  "noaa"),   # Kapuaraaka (18km to station)
    ("kaplama-basin",                         "1612340",  "noaa"),   # Kapālama Basin (2km to station)
    ("kaslokan-point",                        "9459881",  "noaa"),   # Kaslokan Point (14km to station)
    ("kasnyku-bay",                           "9451600",  "noaa"),   # Kasnyku Bay (35km to station)
    ("kauffman-bay",                          "9075065",  "noaa"),   # Kauffman Bay (24km to station)
    ("kauhala",                               "1612480",  "noaa"),   # Kauhala (37km to station)
    ("kaulahao-beach",                        "1615680",  "noaa"),   # Kaulahao Beach (10km to station)
    ("kaunaoa-bay",                           "1617433",  "noaa"),   # Kauna‘oa Bay (4km to station)
    ("kaupo-cove",                            "1612480",  "noaa"),   # Kaupo Cove (18km to station)
    ("kawailoa-bay",                          "1611400",  "noaa"),   # Kawailoa Bay (9km to station)
    ("kawailoa-beach",                        "1612480",  "noaa"),   # Kawailoa Beach (38km to station)
    ("kawainui-bay",                          "1617760",  "noaa"),   # Kawainui Bay (10km to station)
    ("kayak-beach",                           "9455500",  "noaa"),   # Kayak Beach (16km to station)
    ("kayak-cove",                            "8418150",  "noaa"),   # Kayak Cove (6km to station)
    ("kaula-bay",                             "1612340",  "noaa"),   # Ka‘ula Bay (28km to station)
    ("keauhou",                               "1617760",  "noaa"),   # Keauhou (15km to station)
    ("keawaakio",                             "1612340",  "noaa"),   # Keawaakio (20km to station)
    ("keawaeli-bay",                          "1617433",  "noaa"),   # Keawaeli Bay (24km to station)
    ("keawaiki",                              "1612340",  "noaa"),   # Keawaiki (40km to station)
    ("keawaiki-bay",                          "1617433",  "noaa"),   # Keawaiki Bay (18km to station)
    ("keawakapu-beach-north",                 "1615680",  "noaa"),   # Keawakapu Beach North (22km to station)
    ("keawakapu-beach-south",                 "1615680",  "noaa"),   # Keawakapu Beach South (22km to station)
    ("keawalai-bay",                          "1615680",  "noaa"),   # Keawala‘i Bay (28km to station)
    ("keawanui-bay",                          "1617433",  "noaa"),   # Keawanui Bay (11km to station)
    ("keaweula-bay",                          "1617433",  "noaa"),   # Keawe‘ula Bay (17km to station)
    ("keeling-cove",                          "8638610",  "noaa"),   # Keeling Cove (22km to station)
    ("keeny-cove",                            "8461490",  "noaa"),   # Keeny Cove (7km to station)
    ("kees-bayou",                            "8729840",  "noaa"),   # Kees Bayou (27km to station)
    ("kegotank-bay",                          "8631044",  "noaa"),   # Kegotank Bay (25km to station)
    ("kehena-beach",                          "1617760",  "noaa"),   # Kehena Beach (40km to station)
    ("kehoe-beach",                           "9415020",  "noaa"),   # Kehoe Beach (18km to station)
    ("keil-cove",                             "9414863",  "noaa"),   # Keil Cove (7km to station)
    ("keiths-cove",                           "8773037",  "noaa"),   # Keith's cove (17km to station)
    ("kekaa-beach",                           "1615680",  "noaa"),   # Keka'a Beach (24km to station)
    ("kelgaya-bay",                           "9452400",  "noaa"),   # Kelgaya Bay (27km to station)
    ("kelham-beach",                          "9415020",  "noaa"),   # Kelham Beach (13km to station)
    ("kell-bay",                              "9451054",  "noaa"),   # Kell Bay (33km to station)
    ("keller-beach",                          "9414863",  "noaa"),   # Keller Beach (1km to station)
    ("kellers-shelter",                       "9410840",  "noaa"),   # Kellers Shelter (17km to station)
    ("kelley-cove",                           "8658120",  "noaa"),   # Kelley Cove (35km to station)
    ("kelleys-bay",                           "8447435",  "noaa"),   # Kelleys Bay (18km to station)
    ("kelleys-island-state-park-public-beach", "9063079",  "noaa"),   # Kelleys Island State Park Public Beach (8km to station)
    ("kellogg-road-beach",                    "9419750",  "noaa"),   # Kellogg Road Beach (14km to station)
    ("kelloggs-beach",                        "9410170",  "noaa"),   # Kellogg's Beach (6km to station)
    ("kelly-bay",                             "9099064",  "noaa"),   # Kelly Bay (9km to station)
    ("kelly-cove",                            "8631044",  "noaa"),   # Kelly Cove (22km to station)
    ("kelly-gap",                             "8760721",  "noaa"),   # Kelly Gap (40km to station)
    ("kellys-bay",                            "8311030",  "noaa"),   # Kellys Bay (2km to station)
    ("kelp-bay",                              "9451600",  "noaa"),   # Kelp Bay (40km to station)
    ("kemeys-cove",                           "8516945",  "noaa"),   # Kemeys Cove (38km to station)
    ("kempff-bay",                            "9457804",  "noaa"),   # Kempff Bay (4km to station)
    ("kens-beach",                            "9451054",  "noaa"),   # Ken's Beach (0km to station)
    ("kennedy-beach",                         "8418150",  "noaa"),   # Kennedy Beach (13km to station)
    ("kennel-beach",                          "8656483",  "noaa"),   # Kennel Beach (40km to station)
    ("kenny-cove",                            "9454050",  "noaa"),   # Kenny Cove (25km to station)
    ("kennydale-beach",                       "9446484",  "noaa"),   # Kennydale Beach (32km to station)
    ("kenomene",                              "1611400",  "noaa"),   # Kenomene (34km to station)
    ("kentuck-inlet",                         "9432780",  "noaa"),   # Kentuck Inlet (13km to station)
    ("keoneloa-bay",                          "1611400",  "noaa"),   # Keoneloa Bay (12km to station)
    ("keonenui-beach",                        "1615680",  "noaa"),   # Keonenui Beach (23km to station)
    ("kerchimbo-bay",                         "8747437",  "noaa"),   # Kerchimbo Bay (38km to station)
    ("kerr-bay",                              "9052000",  "noaa"),   # Kerr Bay (31km to station)
    ("kesson-bayou",                          "8725520",  "noaa"),   # Kesson Bayou (34km to station)
    ("kettle-cove",                           "8447930",  "noaa"),   # Kettle Cove (10km to station)
    ("key-west-bight",                        "8724580",  "noaa"),   # Key West Bight (1km to station)
    ("keyes-beach",                           "8447435",  "noaa"),   # Keyes Beach (29km to station)
    ("keyes-memorial-beach",                  "8447435",  "noaa"),   # Keyes Memorial Beach (29km to station)
    ("kiawah-beachwalker-park",               "8665530",  "noaa"),   # Kiawah Beachwalker Park (29km to station)
    ("kidd-harbor",                           "8465705",  "noaa"),   # Kidd Harbor (13km to station)
    ("kiddel-bay",                            "9751381",  "noaa"),   # Kiddel Bay (2km to station)
    ("kiddies-beach",                         "8461490",  "noaa"),   # Kiddie's Beach (7km to station)
    ("kidney-cove",                           "9451600",  "noaa"),   # Kidney Cove (16km to station)
    ("kikaua-point-beach",                    "1617433",  "noaa"),   # Kikaua Point Beach (30km to station)
    ("kilauea-bay",                           "1611400",  "noaa"),   # Kilauea Bay (30km to station)
    ("kilkenny-cove",                         "8413320",  "noaa"),   # Kilkenny Cove (17km to station)
    ("killmon-cove",                          "8631044",  "noaa"),   # Killmon Cove (23km to station)
    ("kilner-bay",                            "9099064",  "noaa"),   # Kilner Bay (9km to station)
    ("kimballs-bay",                          "9099064",  "noaa"),   # Kimballs Bay (10km to station)
    ("kimbles-beach",                         "8536110",  "noaa"),   # Kimbles Beach (16km to station)
    ("kimple-beach",                          "9449880",  "noaa"),   # Kimple Beach (16km to station)
    ("king-charles-hole",                     "2695540",  "noaa"),   # King Charles Hole (18km to station)
    ("king-cove",                             "9459881",  "noaa"),   # King Cove (3km to station)
    ("king-fisher-beach",                     "8773701",  "noaa"),   # King Fisher Beach (2km to station)
    ("king-park-beach",                       "8452660",  "noaa"),   # King Park Beach (3km to station)
    ("kingsborough-beach-park",               "8531680",  "noaa"),   # Kingsborough Beach Park (14km to station)
    ("kingsbury-bay",                         "9099064",  "noaa"),   # Kingsbury Bay (9km to station)
    ("kingsmill-beach",                       "8637689",  "noaa"),   # Kingsmill Beach (16km to station)
    ("kingston-beach",                        "8661070",  "noaa"),   # Kingston Beach (18km to station)
    ("kingston-harbour",                      "9052000",  "noaa"),   # Kingston Harbour (16km to station)
    ("kingston-point-beach",                  "8518962",  "noaa"),   # Kingston Point Beach (10km to station)
    ("kinney-shores-beach",                   "8418150",  "noaa"),   # Kinney Shores Beach (22km to station)
    ("kinsey-bayou",                          "8729840",  "noaa"),   # Kinsey Bayou (23km to station)
    ("kinzie-cove",                           "8725520",  "noaa"),   # Kinzie Cove (19km to station)
    ("kipakaone-bay",                         "1615680",  "noaa"),   # Kipakaone Bay (40km to station)
    ("kirby-cove",                            "9414290",  "noaa"),   # Kirby Cove (3km to station)
    ("kisselen-bay",                          "9462620",  "noaa"),   # Kisselen Bay (18km to station)
    ("kitchen-anchorage",                     "9459881",  "noaa"),   # Kitchen Anchorage (15km to station)
    ("kitchen-pond",                          "8760721",  "noaa"),   # Kitchen Pond (5km to station)
    ("kitkun-bay",                            "9450460",  "noaa"),   # Kitkun Bay (38km to station)
    ("kiwanis-bay",                           "9414523",  "noaa"),   # Kiwanis Bay (22km to station)
    ("kiwanis-beach",                         "9075080",  "noaa"),   # Kiwanis Beach (11km to station)
    ("klein-bay",                             "9751381",  "noaa"),   # Klein Bay (5km to station)
    ("kliuchevoi-bay",                        "9451600",  "noaa"),   # Kliuchevoi Bay (24km to station)
    ("klosterman-bayou",                      "8726724",  "noaa"),   # Klosterman Bayou (16km to station)
    ("knight-bay",                            "9751364",  "noaa"),   # Knight Bay (11km to station)
    ("knights-hole",                          "2695540",  "noaa"),   # Knight's Hole (18km to station)
    ("knik-arm",                              "9455920",  "noaa"),   # Knik Arm (18km to station)
    ("knoll-bay",                             "9457804",  "noaa"),   # Knoll Bay (40km to station)
    ("knollwood-beach",                       "8516945",  "noaa"),   # Knollwood Beach (33km to station)
    ("knotts-island-bay",                     "8651370",  "noaa"),   # Knotts Island Bay (38km to station)
    ("knudson-cove",                          "9450460",  "noaa"),   # Knudson Cove (19km to station)
    ("kornoeljes-beach",                      "9451054",  "noaa"),   # Kornoelje's Beach (0km to station)
    ("korovin-bay",                           "9459450",  "noaa"),   # Korovin Bay (18km to station)
    ("koyuktolik-bay",                        "9455500",  "noaa"),   # Koyuktolik Bay (25km to station)
    ("krause-lagoon",                         "9751401",  "noaa"),   # Krause Lagoon (1km to station)
    ("kreamer-bayou",                         "8726724",  "noaa"),   # Kreamer Bayou (20km to station)
    ("krestof-sound",                         "9451600",  "noaa"),   # Krestof Sound (22km to station)
    ("krogh-beach",                           "8531680",  "noaa"),   # Krogh Beach (19km to station)
    ("krum-bay",                              "9751381",  "noaa"),   # Krum Bay (25km to station)
    ("kuap-pond",                             "1612340",  "noaa"),   # Kuapā Pond (17km to station)
    ("kuheeia-bay",                           "1615680",  "noaa"),   # Kuheeia Bay (37km to station)
    ("kuiaha-bay",                            "1615680",  "noaa"),   # Kuiaha Bay (16km to station)
    ("kukuiula-bay",                          "1611400",  "noaa"),   # Kukuiula Bay (16km to station)
    ("kumimi-beach-20-mile-beach",            "1615680",  "noaa"),   # Kumimi Beach (20 Mile Beach) (37km to station)
    ("kumukea-beach",                         "1617433",  "noaa"),   # Kumukea Beach (29km to station)
    ("kusian-cove",                           "8631044",  "noaa"),   # Kusian Cove (14km to station)
    ("kuau-bay",                              "1615680",  "noaa"),   # Ku‘au Bay (10km to station)
    ("kuau-cove",                             "1615680",  "noaa"),   # Ku‘au Cove (11km to station)
    ("kwain-bay",                             "9450460",  "noaa"),   # Kwain Bay (32km to station)
    ("kneohe-bay",                            "1612480",  "noaa"),   # Kāne‘ohe Bay (4km to station)
    ("kkea-bay",                              "1617433",  "noaa"),   # Kēōkea Bay (23km to station)
    ("kholo-bay",                             "1617433",  "noaa"),   # Kīholo Bay (22km to station)
    ("kheia-bay",                             "1615680",  "noaa"),   # Kūheia Bay (36km to station)
    ("khi-bay",                               "1617760",  "noaa"),   # Kūhiō Bay (0km to station)
    ("khi-beach",                             "1617433",  "noaa"),   # Kūhiō Beach (30km to station)
    ("kau-cove",                              "1615680",  "noaa"),   # Kūʻau Cove (11km to station)
    ("l-street-bathing-beach",                "8531680",  "noaa"),   # L Street Bathing Beach (32km to station)
    ("lhomme-pond",                           "8760721",  "noaa"),   # L'Homme Pond (5km to station)
    ("lanse-creuse-bay",                      "9014070",  "noaa"),   # L'anse Creuse Bay (25km to station)
    ("lac-private-beach-3",                   "8418150",  "noaa"),   # LAC private Beach 3 (40km to station)
    ("lac-private-beach-5",                   "8418150",  "noaa"),   # LAC private Beach 5 (40km to station)
    ("la-costa-beach",                        "9410840",  "noaa"),   # La Costa Beach (13km to station)
    ("la-escale",                             "8779770",  "noaa"),   # La Escale (11km to station)
    ("la-fanduca",                            "9753216",  "noaa"),   # La Fanduca (19km to station)
    ("la-jolla-tide-pools",                   "9410230",  "noaa"),   # La Jolla Tide Pools (4km to station)
    ("la-jungla",                             "9759110",  "noaa"),   # La Jungla (9km to station)
    ("la-pared-playa",                        "9753216",  "noaa"),   # La Pared Playa (10km to station)
    ("la-piedra-beach",                       "9410840",  "noaa"),   # La Piedra Beach (36km to station)
    ("la-plaisance-bay",                      "9063085",  "noaa"),   # La Plaisance Bay (21km to station)
    ("la-playita",                            "9759394",  "noaa"),   # La Playita (16km to station)
    ("la-pocita",                             "9759394",  "noaa"),   # La Pocita (35km to station)
    ("la-rose-bay",                           "8311062",  "noaa"),   # La Rose Bay (24km to station)
    ("la-tete-bay",                           "8760721",  "noaa"),   # La Tete Bay (38km to station)
    ("lagrange-bayou",                        "8729210",  "noaa"),   # LaGrange Bayou (38km to station)
    ("lagrange-beach",                        "9751401",  "noaa"),   # LaGrange Beach (14km to station)
    ("lac-la-buche",                          "8741533",  "noaa"),   # Lac La Buche (2km to station)
    ("lackeys-bay",                           "8447930",  "noaa"),   # Lackeys Bay (3km to station)
    ("lacy-cove",                             "9452634",  "noaa"),   # Lacy Cove (3km to station)
    ("lafitte-bay",                           "8735180",  "noaa"),   # Lafitte Bay (6km to station)
    ("lagoon-beach",                          "1617433",  "noaa"),   # Lagoon Beach (14km to station)
    ("laguna-de-los-olmos",                   "8776604",  "noaa"),   # Laguna De Los Olmos (33km to station)
    ("laguna-salada",                         "8776604",  "noaa"),   # Laguna Salada (29km to station)
    ("laika-lane-beach",                      "8725520",  "noaa"),   # Laika Lane Beach (35km to station)
    ("laird-bayou",                           "8729108",  "noaa"),   # Laird Bayou (14km to station)
    ("lake-andre",                            "8761724",  "noaa"),   # Lake Andre (13km to station)
    ("lake-anza-beach",                       "9414863",  "noaa"),   # Lake Anza Beach (14km to station)
    ("lake-barcroft-beach",                   "8594900",  "noaa"),   # Lake Barcroft Beach (11km to station)
    ("lake-beseck-beach",                     "8465705",  "noaa"),   # Lake Beseck Beach (30km to station)
    ("lake-borgne",                           "8761305",  "noaa"),   # Lake Borgne (19km to station)
    ("lake-calebasse",                        "8761305",  "noaa"),   # Lake Calebasse (22km to station)
    ("lake-chapeau",                          "8764314",  "noaa"),   # Lake Chapeau (14km to station)
    ("lake-claire-beach",                     "8575512",  "noaa"),   # Lake Claire Beach (8km to station)
    ("lake-fortuna",                          "8761305",  "noaa"),   # Lake Fortuna (29km to station)
    ("lake-grand-ecaille",                    "8761724",  "noaa"),   # Lake Grand Ecaille (19km to station)
    ("lake-hillsmere",                        "8575512",  "noaa"),   # Lake Hillsmere (6km to station)
    ("lake-mabel",                            "8722956",  "noaa"),   # Lake Mabel (1km to station)
    ("lake-machias",                          "8761305",  "noaa"),   # Lake Machias (25km to station)
    ("lake-martin",                           "8729108",  "noaa"),   # Lake Martin (6km to station)
    ("lake-mechant",                          "8764227",  "noaa"),   # Lake Mechant (40km to station)
    ("lake-minnewaska-beach",                 "8518962",  "noaa"),   # Lake Minnewaska Beach (40km to station)
    ("lake-mohegan-beach",                    "8467150",  "noaa"),   # Lake Mohegan Beach (7km to station)
    ("lake-myosotis-swimming-area",           "8518979",  "noaa"),   # Lake Myosotis Swimming Area (34km to station)
    ("lake-ogleton",                          "8575512",  "noaa"),   # Lake Ogleton (4km to station)
    ("lake-pierre",                           "8761724",  "noaa"),   # Lake Pierre (17km to station)
    ("lake-pond",                             "8760721",  "noaa"),   # Lake Pond (6km to station)
    ("lake-raccourci",                        "8761724",  "noaa"),   # Lake Raccourci (38km to station)
    ("lake-robinson",                         "8761724",  "noaa"),   # Lake Robinson (23km to station)
    ("lake-tashmoo-town-beach",               "8447930",  "noaa"),   # Lake Tashmoo Town Beach (7km to station)
    ("lake-temescal-beach",                   "9414750",  "noaa"),   # Lake Temescal Beach (10km to station)
    ("lake-trois-jeans",                      "8761724",  "noaa"),   # Lake Trois Jeans (40km to station)
    ("lake-union-park-kayak-launch-and-beach", "9446484",  "noaa"),   # Lake Union Park Kayak Launch and Beach (40km to station)
    ("lake-van-vac",                          "8729108",  "noaa"),   # Lake Van Vac (2km to station)
    ("lake-walk",                             "9099090",  "noaa"),   # Lake Walk (18km to station)
    ("lake-of-second-trees",                  "8761305",  "noaa"),   # Lake of Second Trees (20km to station)
    ("lakeman-harbor",                        "8411060",  "noaa"),   # Lakeman Harbor (24km to station)
    ("lakes-bay",                             "8534720",  "noaa"),   # Lakes Bay (7km to station)
    ("lakes-cove",                            "8571421",  "noaa"),   # Lakes Cove (13km to station)
    ("lakeshore-beach",                       "8747437",  "noaa"),   # Lakeshore Beach (13km to station)
    ("lakeview-park-west-beach",              "9014070",  "noaa"),   # Lakeview Park West Beach (39km to station)
    ("lakewood-beach",                        "8661070",  "noaa"),   # Lakewood Beach (4km to station)
    ("lamb-beach",                            "9063085",  "noaa"),   # Lamb Beach (12km to station)
    ("lamb-cove",                             "8410140",  "noaa"),   # Lamb Cove (25km to station)
    ("lambert-beach",                         "9751381",  "noaa"),   # Lambert Beach (21km to station)
    ("lamphier-cove",                         "8465705",  "noaa"),   # Lamphier Cove (7km to station)
    ("lamson-cove",                           "8418150",  "noaa"),   # Lamson Cove (4km to station)
    ("lancaster-cove",                        "9450460",  "noaa"),   # Lancaster Cove (32km to station)
    ("landing-cove",                          "8639348",  "noaa"),   # Landing Cove (32km to station)
    ("landlocked-bay",                        "9454240",  "noaa"),   # Landlocked Bay (34km to station)
    ("landons-bay",                           "8311062",  "noaa"),   # Landons Bay (11km to station)
    ("landry-bay",                            "8761724",  "noaa"),   # Landry Bay (32km to station)
    ("lane-beach",                            "8577330",  "noaa"),   # Lane Beach (16km to station)
    ("langes-bay",                            "9087096",  "noaa"),   # Langes Bay (39km to station)
    ("langford-sand",                         "8571421",  "noaa"),   # Langford Sand (36km to station)
    ("langfords-bay",                         "8573364",  "noaa"),   # Langfords Bay (14km to station)
    ("laniloa-beach",                         "1612480",  "noaa"),   # Laniloa Beach (27km to station)
    ("larch-bay",                             "9451054",  "noaa"),   # Larch Bay (6km to station)
    ("large-pond",                            "9751381",  "noaa"),   # Large Pond (8km to station)
    ("largo-inlet",                           "8726724",  "noaa"),   # Largo Inlet (12km to station)
    ("larkin-bay",                            "8311062",  "noaa"),   # Larkin Bay (27km to station)
    ("larkington-cove",                       "8575512",  "noaa"),   # Larkington Cove (8km to station)
    ("larrabee-cove",                         "8411060",  "noaa"),   # Larrabee Cove (13km to station)
    ("larsen-harbor",                         "9087096",  "noaa"),   # Larsen Harbor (38km to station)
    ("larsens-beach",                         "1611400",  "noaa"),   # Larsen's Beach (28km to station)
    ("lash-lighter-basin",                    "9414750",  "noaa"),   # Lash Lighter Basin (7km to station)
    ("lathrop-bayou",                         "8729108",  "noaa"),   # Lathrop Bayou (26km to station)
    ("latigo-beach",                          "9410840",  "noaa"),   # Latigo Beach (23km to station)
    ("latty-cove",                            "8413320",  "noaa"),   # Latty Cove (22km to station)
    ("laudholm-beach",                        "8419870",  "noaa"),   # Laudholm Beach (32km to station)
    ("laurence-pond",                         "8760721",  "noaa"),   # Laurence Pond (14km to station)
    ("lawai-bay",                             "1611400",  "noaa"),   # Lawai Bay (17km to station)
    ("lawrence-cove",                         "8635750",  "noaa"),   # Lawrence Cove (31km to station)
    ("laws-cove",                             "8571421",  "noaa"),   # Laws Cove (10km to station)
    ("lawson-bay",                            "8761305",  "noaa"),   # Lawson Bay (30km to station)
    ("lawyers-cove",                          "8573364",  "noaa"),   # Lawyers Cove (13km to station)
    ("le-gates-cove",                         "8571892",  "noaa"),   # Le Gates Cove (19km to station)
    ("leask-cove",                            "9450460",  "noaa"),   # Leask Cove (21km to station)
    ("leason-cove",                           "8577330",  "noaa"),   # Leason Cove (2km to station)
    ("lechuza-beach",                         "9410840",  "noaa"),   # Lechuza Beach (34km to station)
    ("lecompte-bay",                          "8571892",  "noaa"),   # Lecompte Bay (9km to station)
    ("lee-county-dog-beach",                  "8725520",  "noaa"),   # Lee County Dog Beach (30km to station)
    ("lee-river",                             "8447386",  "noaa"),   # Lee River (3km to station)
    ("leeds-pond-beach",                      "8516945",  "noaa"),   # Leeds Pond Beach (5km to station)
    ("lees-cove",                             "8635750",  "noaa"),   # Lees Cove (38km to station)
    ("leesoffskaia-bay",                      "9451600",  "noaa"),   # Leesoffskaia Bay (7km to station)
    ("left-foot-lake-beach",                  "9087088",  "noaa"),   # Left Foot Lake Beach (35km to station)
    ("left-head",                             "9463502",  "noaa"),   # Left Head (24km to station)
    ("lefthand-bay",                          "9459450",  "noaa"),   # Lefthand Bay (27km to station)
    ("leigh-bay",                             "9076070",  "noaa"),   # Leigh Bay (4km to station)
    ("leinster-bay",                          "9751381",  "noaa"),   # Leinster Bay (6km to station)
    ("leisure-lagoon",                        "9410170",  "noaa"),   # Leisure Lagoon (8km to station)
    ("lena-beach",                            "9452210",  "noaa"),   # Lena Beach (22km to station)
    ("lena-cove",                             "9452210",  "noaa"),   # Lena Cove (23km to station)
    ("lenard-harbor",                         "9459881",  "noaa"),   # Lenard Harbor (11km to station)
    ("leonard-cove",                          "8571892",  "noaa"),   # Leonard Cove (10km to station)
    ("lerch-creek",                           "8575512",  "noaa"),   # Lerch Creek (17km to station)
    ("lerkenlund-bay",                        "9751381",  "noaa"),   # Lerkenlund Bay (23km to station)
    ("letnikof-cove",                         "9452400",  "noaa"),   # Letnikof Cove (31km to station)
    ("letter-cove",                           "8571421",  "noaa"),   # Letter Cove (18km to station)
    ("levering-creek",                        "8571421",  "noaa"),   # Levering Creek (26km to station)
    ("lewes-public-beach",                    "8557380",  "noaa"),   # Lewes Public Beach (1km to station)
    ("lewis-creek",                           "8577330",  "noaa"),   # Lewis Creek (3km to station)
    ("libby-arm",                             "9432780",  "noaa"),   # Libby Arm (5km to station)
    ("libby-cove",                            "8411060",  "noaa"),   # Libby Cove (14km to station)
    ("lighthouse-bay",                        "8652587",  "noaa"),   # Lighthouse Bay (3km to station)
    ("lighthouse-bayou",                      "8728690",  "noaa"),   # Lighthouse Bayou (37km to station)
    ("lighthouse-cove",                       "8570283",  "noaa"),   # Lighthouse Cove (15km to station)
    ("lighthouse-inlet",                      "8665530",  "noaa"),   # Lighthouse Inlet (11km to station)
    ("lighting-knot-cove",                    "8571421",  "noaa"),   # Lighting Knot Cove (23km to station)
    ("lilly-bay",                             "9087088",  "noaa"),   # Lilly Bay (38km to station)
    ("lily-bay",                              "8311062",  "noaa"),   # Lily Bay (10km to station)
    ("lily-cove",                             "8413320",  "noaa"),   # Lily Cove (39km to station)
    ("limantour-beach",                       "9415020",  "noaa"),   # Limantour Beach (9km to station)
    ("lime-kiln-beach",                       "9063079",  "noaa"),   # Lime Kiln Beach (13km to station)
    ("limehouse-cove",                        "8574680",  "noaa"),   # Limehouse Cove (17km to station)
    ("limestone-bay",                         "9751381",  "noaa"),   # Limestone Bay (24km to station)
    ("limestone-inlet",                       "9452210",  "noaa"),   # Limestone Inlet (39km to station)
    ("limetree-bay",                          "9751401",  "noaa"),   # Limetree Bay (1km to station)
    ("limetree-beach",                        "9751381",  "noaa"),   # Limetree Beach (20km to station)
    ("limetree-cove",                         "9751381",  "noaa"),   # Limetree Cove (6km to station)
    ("limewood-beach",                        "8465705",  "noaa"),   # Limewood Beach (10km to station)
    ("lincoln-anchorage",                     "9452210",  "noaa"),   # Lincoln Anchorage (38km to station)
    ("lincoln-bay",                           "9075065",  "noaa"),   # Lincoln Bay (12km to station)
    ("lindamoor-community-beach",             "8575512",  "noaa"),   # Lindamoor Community Beach (3km to station)
    ("lindberg-beach",                        "9751381",  "noaa"),   # Lindberg Beach (26km to station)
    ("lindbergh-bay",                         "9751381",  "noaa"),   # Lindbergh Bay (26km to station)
    ("lindros-arm",                           "9432780",  "noaa"),   # Lindros Arm (30km to station)
    ("lindsey-cove",                          "8465705",  "noaa"),   # Lindsey Cove (7km to station)
    ("linger-longer-beach",                   "9444900",  "noaa"),   # Linger Longer Beach (36km to station)
    ("lingo-cove",                            "8557380",  "noaa"),   # Lingo Cove (16km to station)
    ("lionshead-lake-beach",                  "8518750",  "noaa"),   # Lionshead Lake Beach (37km to station)
    ("lisianski-inlet",                       "9452634",  "noaa"),   # Lisianski Inlet (24km to station)
    ("lithia-springs",                        "8726674",  "noaa"),   # Lithia Springs (20km to station)
    ("little-aberdeen-creek",                 "8575512",  "noaa"),   # Little Aberdeen Creek (6km to station)
    ("little-allen-harbor",                   "8452944",  "noaa"),   # Little Allen Harbor (12km to station)
    ("little-assawoman-bay",                  "8570283",  "noaa"),   # Little Assawoman Bay (17km to station)
    ("little-bayou",                          "8726520",  "noaa"),   # Little Bayou (4km to station)
    ("little-beach",                          "8534720",  "noaa"),   # Little Beach (16km to station)
    ("little-bellows-bay",                    "8651370",  "noaa"),   # Little Bellows Bay (40km to station)
    ("little-bend",                           "8747437",  "noaa"),   # Little Bend (26km to station)
    ("little-big-lake",                       "8747437",  "noaa"),   # Little Big Lake (34km to station)
    ("little-bois-bubert-harbor",             "8413320",  "noaa"),   # Little Bois Bubert Harbor (27km to station)
    ("little-bokeelia-bay",                   "8725520",  "noaa"),   # Little Bokeelia Bay (31km to station)
    ("little-bordeaux-bay",                   "9751381",  "noaa"),   # Little Bordeaux Bay (31km to station)
    ("little-branch-bay",                     "9451054",  "noaa"),   # Little Branch Bay (13km to station)
    ("little-buttermilk-bay",                 "8447930",  "noaa"),   # Little Buttermilk Bay (27km to station)
    ("little-catfish-basin",                  "8729840",  "noaa"),   # Little Catfish Basin (24km to station)
    ("little-cinnamon-bay-beach",             "9751381",  "noaa"),   # Little Cinnamon Bay Beach (5km to station)
    ("little-clapboard-creek",                "8720219",  "noaa"),   # Little Clapboard Creek (5km to station)
    ("little-clearinghole",                   "9751381",  "noaa"),   # Little Clearinghole (23km to station)
    ("little-cockroach-bay",                  "8726384",  "noaa"),   # Little Cockroach Bay (9km to station)
    ("little-coculus-bay",                    "9751381",  "noaa"),   # Little Coculus Bay (19km to station)
    ("little-coquille-bay",                   "8760721",  "noaa"),   # Little Coquille Bay (28km to station)
    ("little-cove",                           "8418150",  "noaa"),   # Little Cove (12km to station)
    ("little-creek",                          "8656483",  "noaa"),   # Little Creek (38km to station)
    ("little-creek-cove",                     "8638610",  "noaa"),   # Little Creek Cove (15km to station)
    ("little-devil-bayou",                    "8774230",  "noaa"),   # Little Devil Bayou (13km to station)
    ("little-dix-bay",                        "9751381",  "noaa"),   # Little Dix Bay (35km to station)
    ("little-dolly-bay",                      "8726724",  "noaa"),   # Little Dolly Bay (18km to station)
    ("little-egging-beach",                   "8570283",  "noaa"),   # Little Egging Beach (15km to station)
    ("little-falls-reservoir",                "8594900",  "noaa"),   # Little Falls Reservoir (13km to station)
    ("little-goat-island-bay",                "8651370",  "noaa"),   # Little Goat Island Bay (10km to station)
    ("little-harbor",                         "8447930",  "noaa"),   # Little Harbor (1km to station)
    ("little-harbor-sound",                   "8516945",  "noaa"),   # Little Harbor Sound (13km to station)
    ("little-hawknest-beach",                 "9751381",  "noaa"),   # Little Hawknest Beach (7km to station)
    ("little-hell-gate",                      "8518750",  "noaa"),   # Little Hell Gate (12km to station)
    ("little-hickory-bay",                    "8725520",  "noaa"),   # Little Hickory Bay (36km to station)
    ("little-holly-cove",                     "8411060",  "noaa"),   # Little Holly Cove (6km to station)
    ("little-honker-bay",                     "9415144",  "noaa"),   # Little Honker Bay (18km to station)
    ("little-house-cove",                     "8413320",  "noaa"),   # Little House Cove (33km to station)
    ("little-hunters-beach",                  "8413320",  "noaa"),   # Little Hunters Beach (10km to station)
    ("little-john-cove",                      "9415102",  "noaa"),   # Little John Cove (15km to station)
    ("little-johnson-bayou",                  "8729210",  "noaa"),   # Little Johnson Bayou (11km to station)
    ("little-kennebec-bay",                   "8411060",  "noaa"),   # Little Kennebec Bay (18km to station)
    ("little-kingston-creek",                 "8577330",  "noaa"),   # Little Kingston Creek (4km to station)
    ("little-krum-bay",                       "9751381",  "noaa"),   # Little Krum Bay (24km to station)
    ("little-lake",                           "8761724",  "noaa"),   # Little Lake (30km to station)
    ("little-lake-pond",                      "8760721",  "noaa"),   # Little Lake Pond (5km to station)
    ("little-lameshur-bay",                   "9751381",  "noaa"),   # Little Lameshur Bay (0km to station)
    ("little-magens",                         "9751381",  "noaa"),   # Little Magens (22km to station)
    ("little-maho-bay",                       "9751381",  "noaa"),   # Little Maho Bay (5km to station)
    ("little-maho-beach",                     "9751381",  "noaa"),   # Little Maho Beach (5km to station)
    ("little-mcpherson-bayou",                "8726520",  "noaa"),   # Little McPherson Bayou (12km to station)
    ("little-mothers-beach",                  "8419870",  "noaa"),   # Little Mother's Beach (35km to station)
    ("little-muscamoot-bay",                  "9014070",  "noaa"),   # Little Muscamoot Bay (10km to station)
    ("little-narragansett-bay",               "8461490",  "noaa"),   # Little Narragansett Bay (20km to station)
    ("little-neck-creek",                     "8571892",  "noaa"),   # Little Neck Creek (25km to station)
    ("little-north-beach",                    "9449880",  "noaa"),   # Little North Beach (31km to station)
    ("little-oyster-bar-point",               "8729108",  "noaa"),   # Little Oyster Bar Point (18km to station)
    ("little-pasture-cove",                   "8770971",  "noaa"),   # Little Pasture Cove (2km to station)
    ("little-peconic-bay",                    "8510560",  "noaa"),   # Little Peconic Bay (38km to station)
    ("little-pleasant-bay",                   "8447435",  "noaa"),   # Little Pleasant Bay (8km to station)
    ("little-pokegama-bay",                   "9099064",  "noaa"),   # Little Pokegama Bay (13km to station)
    ("little-pond-beach",                     "8411060",  "noaa"),   # Little Pond Beach (31km to station)
    ("little-pond-cove",                      "8452660",  "noaa"),   # Little Pond Cove (15km to station)
    ("little-puffin-bay",                     "9451054",  "noaa"),   # Little Puffin Bay (8km to station)
    ("little-reef-bay-beach",                 "9751381",  "noaa"),   # Little Reef Bay Beach (3km to station)
    ("little-river-state-beach",              "9418767",  "noaa"),   # Little River State Beach (29km to station)
    ("little-round-bay",                      "8575512",  "noaa"),   # Little Round Bay (10km to station)
    ("little-sabine-bay",                     "8729840",  "noaa"),   # Little Sabine Bay (10km to station)
    ("little-sand-bay",                       "8311062",  "noaa"),   # Little Sand Bay (20km to station)
    ("little-shamrock-cove",                  "8775283",  "noaa"),   # Little Shamrock Cove (8km to station)
    ("little-shelter-bay",                    "9075099",  "noaa"),   # Little Shelter Bay (27km to station)
    ("little-sound",                          "2695540",  "noaa"),   # Little Sound (18km to station)
    ("little-swash-opening",                  "8654467",  "noaa"),   # Little Swash Opening (20km to station)
    ("little-trunk-bay",                      "9751381",  "noaa"),   # Little Trunk Bay (32km to station)
    ("little-turtle-bay",                     "2695540",  "noaa"),   # Little Turtle Bay (15km to station)
    ("little-twentyseven-pond",               "8760721",  "noaa"),   # Little Twentyseven Pond (9km to station)
    ("little-whale-cove",                     "9435380",  "noaa"),   # Little Whale Cove (19km to station)
    ("little-white-lake",                     "8766072",  "noaa"),   # Little White Lake (26km to station)
    ("littlejohn-lagoon",                     "9459881",  "noaa"),   # Littlejohn Lagoon (39km to station)
    ("live-oak-bay",                          "8761724",  "noaa"),   # Live Oak Bay (18km to station)
    ("lizzamonde-pond",                       "8760721",  "noaa"),   # Lizzamonde Pond (12km to station)
    ("lloyd-bay",                             "8637689",  "noaa"),   # Lloyd Bay (13km to station)
    ("lloyd-beach",                           "8516945",  "noaa"),   # Lloyd Beach (26km to station)
    ("lloyd-neck-estates-beach",              "8516945",  "noaa"),   # Lloyd Neck Estates Beach (30km to station)
    ("lloydhaven-beach",                      "8516945",  "noaa"),   # Lloydhaven Beach (29km to station)
    ("loagy-bay",                             "8447435",  "noaa"),   # Loagy Bay (24km to station)
    ("lobster-cove",                          "8461490",  "noaa"),   # Lobster Cove (11km to station)
    ("lobster-pound-beach",                   "8418150",  "noaa"),   # Lobster Pound Beach (3km to station)
    ("lobster-pound-cove",                    "8418150",  "noaa"),   # Lobster Pound Cove (3km to station)
    ("lobsterville-beach",                    "8447930",  "noaa"),   # Lobsterville Beach (22km to station)
    ("loch-arbour-village-beach-club",        "8531680",  "noaa"),   # Loch Arbour Village Beach Club (26km to station)
    ("locust-cove",                           "8575512",  "noaa"),   # Locust Cove (15km to station)
    ("locust-pond",                           "8760721",  "noaa"),   # Locust Pond (8km to station)
    ("loden-pond",                            "8575512",  "noaa"),   # Loden Pond (6km to station)
    ("loggerhead-beach",                      "8723970",  "noaa"),   # Loggerhead Beach (18km to station)
    ("logwood-cove",                          "8510560",  "noaa"),   # Logwood Cove (37km to station)
    ("lohmeyers-cove",                        "9063079",  "noaa"),   # Lohmeyer's Cove (21km to station)
    ("lokoawa-bay",                           "1611400",  "noaa"),   # Lokoawa Bay (20km to station)
    ("lollys-beach",                          "8725520",  "noaa"),   # Lolly's Beach (31km to station)
    ("lombos-hole",                           "8418150",  "noaa"),   # Lombos Hole (29km to station)
    ("lone-cove",                             "8413320",  "noaa"),   # Lone Cove (30km to station)
    ("lone-tree-creek",                       "8654467",  "noaa"),   # Lone Tree Creek (38km to station)
    ("lonesome-bay",                          "8311062",  "noaa"),   # Lonesome Bay (28km to station)
    ("long-arm",                              "9450460",  "noaa"),   # Long Arm (27km to station)
    ("long-bar",                              "8410140",  "noaa"),   # Long Bar (19km to station)
    ("long-bay",                              "9751381",  "noaa"),   # Long Bay (21km to station)
    ("long-bayou",                            "8726520",  "noaa"),   # Long Bayou (14km to station)
    ("long-beach",                            "8516945",  "noaa"),   # Long Beach (27km to station)
    ("long-beach-bay",                        "8510560",  "noaa"),   # Long Beach Bay (28km to station)
    ("long-beach-middle-harbor",              "9410840",  "noaa"),   # Long Beach Middle Harbor (39km to station)
    ("long-cove",                             "8452660",  "noaa"),   # Long Cove (17km to station)
    ("long-cove-beach",                       "9415020",  "noaa"),   # Long Cove Beach (18km to station)
    ("long-creek",                            "8571421",  "noaa"),   # Long Creek (25km to station)
    ("long-haul-creek",                       "8571892",  "noaa"),   # Long Haul Creek (29km to station)
    ("long-key-bight",                        "8723970",  "noaa"),   # Long Key Bight (34km to station)
    ("long-lake",                             "8773037",  "noaa"),   # Long Lake (18km to station)
    ("long-lake-cove",                        "8411060",  "noaa"),   # Long Lake Cove (36km to station)
    ("long-mill-cove",                        "8413320",  "noaa"),   # Long Mill Cove (19km to station)
    ("long-pond",                             "8651370",  "noaa"),   # Long Pond (18km to station)
    ("long-pond-beach",                       "8410140",  "noaa"),   # Long Pond Beach (31km to station)
    ("long-reach",                            "8418150",  "noaa"),   # Long Reach (32km to station)
    ("long-sands",                            "8419870",  "noaa"),   # Long Sands (14km to station)
    ("longmeadow-beach",                      "8452944",  "noaa"),   # Longmeadow Beach (2km to station)
    ("lookout-bight",                         "8656483",  "noaa"),   # Lookout Bight (17km to station)
    ("loomis-pond",                           "8760721",  "noaa"),   # Loomis Pond (13km to station)
    ("loon-b",                                "8311062",  "noaa"),   # Loon B (27km to station)
    ("loop-beach",                            "8447930",  "noaa"),   # Loop Beach (22km to station)
    ("lord-baltimores-bay",                   "8577330",  "noaa"),   # Lord Baltimores Bay (2km to station)
    ("lord-cove",                             "8461490",  "noaa"),   # Lord Cove (22km to station)
    ("lords-pocket",                          "9451054",  "noaa"),   # Lords Pocket (39km to station)
    ("lordship-beach",                        "8467150",  "noaa"),   # Lordship Beach (6km to station)
    ("lorraine-bay",                          "9063020",  "noaa"),   # Lorraine Bay (26km to station)
    ("los-pescadores",                        "9753216",  "noaa"),   # Los Pescadores (11km to station)
    ("lost-bay",                              "8771972",  "noaa"),   # Lost Bay (15km to station)
    ("lost-coast",                            "9418767",  "noaa"),   # Lost Coast (40km to station)
    ("lost-cove",                             "9452634",  "noaa"),   # Lost Cove (37km to station)
    ("lotus-bay",                             "9063020",  "noaa"),   # Lotus Bay (37km to station)
    ("louden-cove",                           "8516945",  "noaa"),   # Louden Cove (30km to station)
    ("louise-cove",                           "9451600",  "noaa"),   # Louise Cove (40km to station)
    ("louse-point",                           "8510560",  "noaa"),   # Louse Point (15km to station)
    ("lovenlund-bay",                         "9751381",  "noaa"),   # Lovenlund Bay (21km to station)
    ("lovers-cove",                           "9449880",  "noaa"),   # Lovers Cove (14km to station)
    ("low-beach",                             "8449130",  "noaa"),   # Low Beach (11km to station)
    ("lowe-cove",                             "8410140",  "noaa"),   # Lowe Cove (26km to station)
    ("lowell-cove",                           "8418150",  "noaa"),   # Lowell Cove (24km to station)
    ("lower-bay",                             "8531680",  "noaa"),   # Lower Bay (6km to station)
    ("lower-beach",                           "8510560",  "noaa"),   # Lower Beach (29km to station)
    ("lower-big-bay",                         "8311030",  "noaa"),   # Lower Big Bay (14km to station)
    ("lower-deep-bay",                        "8311030",  "noaa"),   # Lower Deep Bay (25km to station)
    ("lower-greens-cove",                     "8571421",  "noaa"),   # Lower Greens Cove (18km to station)
    ("lower-harvey-cove",                     "8418150",  "noaa"),   # Lower Harvey Cove (33km to station)
    ("lower-herring-cove",                    "8411060",  "noaa"),   # Lower Herring Cove (32km to station)
    ("lower-pine-cove",                       "8467150",  "noaa"),   # Lower Pine Cove (36km to station)
    ("lower-san-jacinto-bay",                 "8770613",  "noaa"),   # Lower San Jacinto Bay (4km to station)
    ("lower-sugarloaf-sound",                 "8724580",  "noaa"),   # Lower Sugarloaf Sound (25km to station)
    ("lower-thirty-six-bay",                  "8725520",  "noaa"),   # Lower Thirty-six Bay (26km to station)
    ("lower-wass-cove",                       "8413320",  "noaa"),   # Lower Wass Cove (40km to station)
    ("lowman-beach",                          "9446484",  "noaa"),   # Lowman Beach (30km to station)
    ("lowrey-creek",                          "8635750",  "noaa"),   # Lowrey Creek (32km to station)
    ("lowry-cove",                            "8571892",  "noaa"),   # Lowry Cove (10km to station)
    ("lows-bay",                              "8727520",  "noaa"),   # Lows Bay (24km to station)
    ("lucas-cove",                            "8577330",  "noaa"),   # Lucas Cove (17km to station)
    ("lucas-lake",                            "8773037",  "noaa"),   # Lucas Lake (6km to station)
    ("lucien-pond",                           "8760721",  "noaa"),   # Lucien Pond (5km to station)
    ("luckse-sound",                          "8418150",  "noaa"),   # Luckse Sound (9km to station)
    ("lucky-cove",                            "9450460",  "noaa"),   # Lucky Cove (27km to station)
    ("lucy-cove",                             "8573364",  "noaa"),   # Lucy Cove (13km to station)
    ("lucy-vincent-beach",                    "8447930",  "noaa"),   # Lucy Vincent Beach (21km to station)
    ("ludingtons-cove",                       "9075014",  "noaa"),   # Ludingtons Cove (5km to station)
    ("ludlam-bay",                            "8534720",  "noaa"),   # Ludlam Bay (31km to station)
    ("lumber-bay",                            "9459450",  "noaa"),   # Lumber Bay (17km to station)
    ("lumber-cove",                           "9452634",  "noaa"),   # Lumber Cove (40km to station)
    ("luna-pier-public-beach",                "9063085",  "noaa"),   # Luna Pier Public Beach (13km to station)
    ("lunada-bay",                            "9410840",  "noaa"),   # Lunada Bay (27km to station)
    ("lungrun-cove",                          "8726724",  "noaa"),   # Lungrun Cove (11km to station)
    ("lunt-harbor",                           "8413320",  "noaa"),   # Lunt Harbor (33km to station)
    ("lutak-inlet",                           "9452400",  "noaa"),   # Lutak Inlet (19km to station)
    ("lydia-ann-channel",                     "8775241",  "noaa"),   # Lydia Ann Channel (4km to station)
    ("lyford-cove",                           "9414863",  "noaa"),   # Lyford Cove (7km to station)
    ("lyles-bay",                             "8447930",  "noaa"),   # Lyles Bay (20km to station)
    ("lyn-ary-beach",                         "9455920",  "noaa"),   # Lyn Ary Beach (5km to station)
    ("lynch-cove",                            "8574680",  "noaa"),   # Lynch Cove (8km to station)
    ("lynhaven-inlet",                        "8638610",  "noaa"),   # Lynhaven Inlet (21km to station)
    ("lynn-haven-bayou",                      "8729108",  "noaa"),   # Lynn Haven Bayou (11km to station)
    ("lynnhaven-bay",                         "8638610",  "noaa"),   # Lynnhaven Bay (23km to station)
    ("lynnhaven-roads",                       "8638610",  "noaa"),   # Lynnhaven Roads (22km to station)
    ("lyons-beach",                           "9440422",  "noaa"),   # Lyons Beach (33km to station)
    ("lytle-beach",                           "9446484",  "noaa"),   # Lytle Beach (38km to station)
    ("lwai-beach",                            "1611400",  "noaa"),   # Lāwaʻi Beach (17km to station)
    ("lie-bay",                               "1612480",  "noaa"),   # Lā‘ie Bay (28km to station)
    ("lahi-beach",                            "1612340",  "noaa"),   # Lē'ahi Beach (7km to station)
    ("lp-beach",                              "1615680",  "noaa"),   # Lōpā Beach (37km to station)
    ("macfadden-beach",                       "8770822",  "noaa"),   # MacFadden Beach (24km to station)
    ("mackenzies-bar",                        "8410140",  "noaa"),   # MacKenzies Bar (24km to station)
    ("macatawa-park-beach",                   "9087031",  "noaa"),   # Macatawa Park Beach (1km to station)
    ("macbeth-bay",                           "9075099",  "noaa"),   # Macbeth Bay (39km to station)
    ("maccubins-cove",                        "8575512",  "noaa"),   # Maccubins Cove (8km to station)
    ("machias-bay",                           "8411060",  "noaa"),   # Machias Bay (11km to station)
    ("mack-cove",                             "8411060",  "noaa"),   # Mack Cove (20km to station)
    ("mack-pond",                             "8760721",  "noaa"),   # Mack Pond (9km to station)
    ("mackerel-cove",                         "8452660",  "noaa"),   # Mackerel Cove (5km to station)
    ("mackerel-cove-beach",                   "8452660",  "noaa"),   # Mackerel Cove Beach (5km to station)
    ("mackinac-bay",                          "9076024",  "noaa"),   # Mackinac Bay (34km to station)
    ("macklyn-cove",                          "9419750",  "noaa"),   # Macklyn Cove (35km to station)
    ("macky-bay",                             "8729840",  "noaa"),   # Macky Bay (15km to station)
    ("macum-creek",                           "8575512",  "noaa"),   # Macum Creek (18km to station)
    ("madaket-harbor",                        "8449130",  "noaa"),   # Madaket Harbor (10km to station)
    ("madequecham-beach",                     "8449130",  "noaa"),   # Madequecham Beach (6km to station)
    ("madrona-beach",                         "9449880",  "noaa"),   # Madrona Beach (17km to station)
    ("maeaea-beach",                          "1612480",  "noaa"),   # Maeaea Beach (37km to station)
    ("magaguadavic-basin",                    "8410140",  "noaa"),   # Magaguadavic Basin (28km to station)
    ("magansett-harbor",                      "8447930",  "noaa"),   # Magansett Harbor (15km to station)
    ("magens-bay",                            "9751381",  "noaa"),   # Magen's Bay (23km to station)
    ("maggies-cove",                          "8771972",  "noaa"),   # Maggies Cove (12km to station)
    ("magic-island-lagoon",                   "1612340",  "noaa"),   # Magic Island lagoon (3km to station)
    ("magnolia-bend",                         "8741533",  "noaa"),   # Magnolia Bend (36km to station)
    ("magothy-bay",                           "8632200",  "noaa"),   # Magothy Bay (6km to station)
    ("mags-hole",                             "8726384",  "noaa"),   # Mags Hole (10km to station)
    ("mahaiula-bay",                          "1617433",  "noaa"),   # Mahaiula Bay (36km to station)
    ("mahaiula-beach",                        "1617433",  "noaa"),   # Mahaiula Beach (36km to station)
    ("mahars-beach",                          "8410140",  "noaa"),   # Mahars Beach (34km to station)
    ("mahoe-bay",                             "9751381",  "noaa"),   # Mahoe Bay (37km to station)
    ("mai-poina-beach-park",                  "1615680",  "noaa"),   # Mai Poina Beach Park (14km to station)
    ("maiden-cove",                           "8418150",  "noaa"),   # Maiden Cove (4km to station)
    ("maiden-cove-beach",                     "8418150",  "noaa"),   # Maiden Cove Beach (4km to station)
    ("maidstone-park-beach",                  "8510560",  "noaa"),   # Maidstone Park Beach (19km to station)
    ("mail-bay",                              "9751381",  "noaa"),   # Mail Bay (27km to station)
    ("mailboat-harbor",                       "8631044",  "noaa"),   # Mailboat Harbor (36km to station)
    ("main-creek",                            "8575512",  "noaa"),   # Main Creek (16km to station)
    ("main-street-beach",                     "9063079",  "noaa"),   # Main Street Beach (22km to station)
    ("maintop-bay",                           "9415020",  "noaa"),   # Maintop Bay (33km to station)
    ("maison-beach",                          "8661070",  "noaa"),   # Maison Beach (17km to station)
    ("maitland-bay",                          "8311030",  "noaa"),   # Maitland Bay (12km to station)
    ("major-hole-bay",                        "8631044",  "noaa"),   # Major Hole Bay (9km to station)
    ("major-inside-pond",                     "8760721",  "noaa"),   # Major Inside Pond (7km to station)
    ("major-outside-pond",                    "8760721",  "noaa"),   # Major Outside Pond (8km to station)
    ("majors-bay",                            "2695540",  "noaa"),   # Major's Bay (5km to station)
    ("majors-cove",                           "8447930",  "noaa"),   # Majors Cove (14km to station)
    ("majors-harbor",                         "8510560",  "noaa"),   # Majors Harbor (27km to station)
    ("makaiwa-bay",                           "1617433",  "noaa"),   # Makaiwa Bay (11km to station)
    ("makako-bay",                            "1617433",  "noaa"),   # Makako Bay (39km to station)
    ("makamah-beach",                         "8467150",  "noaa"),   # Makamah Beach (30km to station)
    ("makapuu-beach-park",                    "1612480",  "noaa"),   # Makapuu Beach Park (19km to station)
    ("makapuu-beach",                         "1612480",  "noaa"),   # Makapu‘U Beach (18km to station)
    ("makawa-bay",                            "1615680",  "noaa"),   # Makaīwa Bay (28km to station)
    ("makena-bay",                            "1615680",  "noaa"),   # Makena Bay (27km to station)
    ("makena-landing",                        "1615680",  "noaa"),   # Makena Landing (27km to station)
    ("makolea-beach",                         "1617433",  "noaa"),   # Makolea Beach (38km to station)
    ("makuleia-bay",                          "1615680",  "noaa"),   # Makuleia Bay (22km to station)
    ("makushin-bay",                          "9462620",  "noaa"),   # Makushin Bay (32km to station)
    ("malga-bay",                             "9462620",  "noaa"),   # Malga Bay (27km to station)
    ("maliko-bay",                            "1615680",  "noaa"),   # Maliko Bay (14km to station)
    ("mallard-beach",                         "8516945",  "noaa"),   # Mallard Beach (26km to station)
    ("mallard-pond",                          "8651370",  "noaa"),   # Mallard Pond (9km to station)
    ("mallet-bayou",                          "8729210",  "noaa"),   # Mallet Bayou (37km to station)
    ("mallock-beach",                         "8410140",  "noaa"),   # Mallock Beach (3km to station)
    ("mallows-bay",                           "8635027",  "noaa"),   # Mallows Bay (26km to station)
    ("mamacoke-cove",                         "8461490",  "noaa"),   # Mamacoke Cove (2km to station)
    ("mamalu-bay",                            "1612480",  "noaa"),   # Mamalu Bay (19km to station)
    ("mamanasco-beach",                       "8467150",  "noaa"),   # Mamanasco Beach (33km to station)
    ("man-of-war-harbor",                     "8747437",  "noaa"),   # Man of War Harbor (27km to station)
    ("manatee-county-beach",                  "8726384",  "noaa"),   # Manatee County Beach (22km to station)
    ("mance-marine-basin",                    "8311062",  "noaa"),   # Mance Marine Basin (3km to station)
    ("manchenil-bay",                         "9751364",  "noaa"),   # Manchenil Bay (5km to station)
    ("manchioneel-bay",                       "9751381",  "noaa"),   # Manchioneel Bay (23km to station)
    ("mandahl-bay",                           "9751381",  "noaa"),   # Mandahl Bay (19km to station)
    ("mandahl-bay-beach",                     "9751381",  "noaa"),   # Mandahl Bay Beach (19km to station)
    ("mandalay-channel",                      "8726724",  "noaa"),   # Mandalay Channel (1km to station)
    ("mangrove-lagoon",                       "9751381",  "noaa"),   # Mangrove Lagoon (16km to station)
    ("manhasset-bay-estates-association-beach", "8516945",  "noaa"),   # Manhasset Bay Estates Association Beach (5km to station)
    ("maniboajo-bay",                         "9075080",  "noaa"),   # Maniboajo Bay (12km to station)
    ("manila-bay-beach",                      "9063079",  "noaa"),   # Manila Bay Beach (20km to station)
    ("maniniholo-bay",                        "1611400",  "noaa"),   # Maniniholo Bay (37km to station)
    ("mankiller-bay",                         "8534720",  "noaa"),   # Mankiller Bay (5km to station)
    ("mann-inside-pond",                      "8760721",  "noaa"),   # Mann Inside Pond (7km to station)
    ("mann-outside-pond",                     "8760721",  "noaa"),   # Mann Outside Pond (8km to station)
    ("manor-beach",                           "8516945",  "noaa"),   # Manor Beach (12km to station)
    ("mantokuji-bay",                         "1615680",  "noaa"),   # Mantokuji Bay (10km to station)
    ("maple-cove",                            "8418150",  "noaa"),   # Maple Cove (38km to station)
    ("maquoit-bay",                           "8418150",  "noaa"),   # Maquoit Bay (27km to station)
    ("margaret-bay",                          "9462620",  "noaa"),   # Margaret Bay (1km to station)
    ("margarets-bay",                         "2695540",  "noaa"),   # Margaret's Bay (18km to station)
    ("mariatown-bay",                         "8311030",  "noaa"),   # Mariatown Bay (30km to station)
    ("marine-street-beach",                   "9410230",  "noaa"),   # Marine Street Beach (4km to station)
    ("mariners-basin",                        "9410170",  "noaa"),   # Mariners Basin (9km to station)
    ("marion-scott-cove",                     "8632200",  "noaa"),   # Marion Scott Cove (10km to station)
    ("marks-bay",                             "9076070",  "noaa"),   # Marks Bay (8km to station)
    ("marks-cove",                            "8447930",  "noaa"),   # Marks Cove (24km to station)
    ("marl-bay",                              "9075080",  "noaa"),   # Marl Bay (19km to station)
    ("marlboro-beach",                        "8413320",  "noaa"),   # Marlboro Beach (11km to station)
    ("marlettes-bay",                         "9076070",  "noaa"),   # Marlette's Bay (38km to station)
    ("marley-beach",                          "2695540",  "noaa"),   # Marley Beach (15km to station)
    ("maroon-hole",                           "9751401",  "noaa"),   # Maroon Hole (15km to station)
    ("marquis-basin",                         "8729840",  "noaa"),   # Marquis Basin (30km to station)
    ("marriott-cove",                         "8575512",  "noaa"),   # Marriott Cove (10km to station)
    ("marsh-bay",                             "8721604",  "noaa"),   # Marsh Bay (35km to station)
    ("marsh-bay-creek",                       "8721604",  "noaa"),   # Marsh Bay Creek (35km to station)
    ("marshalls-cove",                        "8410140",  "noaa"),   # Marshalls Cove (29km to station)
    ("marshy-bayou",                          "8726724",  "noaa"),   # Marshy Bayou (23km to station)
    ("martel-bay",                            "9751364",  "noaa"),   # Martel Bay (2km to station)
    ("marthas-beach",                         "9444900",  "noaa"),   # Martha's Beach (34km to station)
    ("martin-bay",                            "8570283",  "noaa"),   # Martin Bay (32km to station)
    ("martin-cove",                           "8577330",  "noaa"),   # Martin Cove (12km to station)
    ("martin-lagoon",                         "8574680",  "noaa"),   # Martin Lagoon (15km to station)
    ("martin-ridge-cove",                     "8413320",  "noaa"),   # Martin Ridge Cove (25km to station)
    ("martinelli-beach",                      "8447930",  "noaa"),   # Martinelli Beach (12km to station)
    ("martinica-beach",                       "9759394",  "noaa"),   # Martinica Beach (33km to station)
    ("martins-beach",                         "9414523",  "noaa"),   # Martins Beach (23km to station)
    ("martins-cove",                          "8413320",  "noaa"),   # Martins Cove (17km to station)
    ("martins-pond",                          "8575512",  "noaa"),   # Martins Pond (4km to station)
    ("marvin-beach",                          "8467150",  "noaa"),   # Marvin Beach (20km to station)
    ("mary-anns-pond",                        "8654467",  "noaa"),   # Mary Anns Pond (27km to station)
    ("mary-bowers-pond",                      "8760721",  "noaa"),   # Mary Bowers Pond (5km to station)
    ("mary-creek",                            "9751381",  "noaa"),   # Mary Creek (5km to station)
    ("mary-i-anchorage",                      "9450460",  "noaa"),   # Mary I Anchorage (37km to station)
    ("marys-lake",                            "8726384",  "noaa"),   # Marys Lake (9km to station)
    ("mascarene-shore",                       "8410140",  "noaa"),   # Mascarene Shore (22km to station)
    ("mash-harbor",                           "8413320",  "noaa"),   # Mash Harbor (40km to station)
    ("mashacket-cove",                        "8447930",  "noaa"),   # Mashacket Cove (20km to station)
    ("maskinonge-bay",                        "9076027",  "noaa"),   # Maskinonge Bay (12km to station)
    ("mason-bay",                             "8411060",  "noaa"),   # Mason Bay (29km to station)
    ("mason-inlet",                           "8658163",  "noaa"),   # Mason Inlet (4km to station)
    ("masonboro-island-reserve",              "8658163",  "noaa"),   # Masonboro Island Reserve (12km to station)
    ("masonville-cove",                       "8574680",  "noaa"),   # Masonville Cove (3km to station)
    ("massalina-bayou",                       "8729108",  "noaa"),   # Massalina Bayou (1km to station)
    ("massapequa-cove",                       "8516945",  "noaa"),   # Massapequa Cove (30km to station)
    ("mast-cove",                             "8419870",  "noaa"),   # Mast Cove (6km to station)
    ("masta-bay",                             "9076033",  "noaa"),   # Masta Bay (5km to station)
    ("masters-bayou",                         "8726607",  "noaa"),   # Masters Bayou (6km to station)
    ("mastuxet-cove",                         "8461490",  "noaa"),   # Mastuxet Cove (23km to station)
    ("matecumbe-harbor",                      "8723970",  "noaa"),   # Matecumbe Harbor (40km to station)
    ("mateo-coast-state-beaches",             "9414523",  "noaa"),   # Mateo Coast State Beaches (21km to station)
    ("mathias-cove",                          "8575512",  "noaa"),   # Mathias Cove (16km to station)
    ("matoaka-beach",                         "8577330",  "noaa"),   # Matoaka Beach (17km to station)
    ("mattakeset-bay",                        "8447930",  "noaa"),   # Mattakeset Bay (24km to station)
    ("mattapoisett-town-beach",               "8447930",  "noaa"),   # Mattapoisett Town Beach (18km to station)
    ("mattatuck-beach",                       "8465705",  "noaa"),   # Mattatuck Beach (31km to station)
    ("matthew-j-buono-beach",                 "8518750",  "noaa"),   # Matthew J. Buono Beach (10km to station)
    ("matthews-cove",                         "8635750",  "noaa"),   # Matthews Cove (27km to station)
    ("maud-bay",                              "9075099",  "noaa"),   # Maud Bay (7km to station)
    ("maulua-bay",                            "1617760",  "noaa"),   # Maulua Bay (30km to station)
    ("maumee-bay",                            "9063085",  "noaa"),   # Maumee Bay (6km to station)
    ("maumee-mooring-basin",                  "9063085",  "noaa"),   # Maumee Mooring Basin (1km to station)
    ("maunalua-bay",                          "1612340",  "noaa"),   # Maunalua Bay (12km to station)
    ("maurice-river-cove",                    "8536110",  "noaa"),   # Maurice River Cove (27km to station)
    ("mauumae-beach",                         "1617433",  "noaa"),   # Mauumae Beach (2km to station)
    ("maxwell-cove",                          "8418150",  "noaa"),   # Maxwell Cove (11km to station)
    ("maxwell-place-beach",                   "8518750",  "noaa"),   # Maxwell Place Beach (5km to station)
    ("may-newburger-cove",                    "8516945",  "noaa"),   # May Newburger Cove (9km to station)
    ("maylynns-beach",                        "9451054",  "noaa"),   # Maylynn's Beach (0km to station)
    ("maynadier-creek",                       "8575512",  "noaa"),   # Maynadier Creek (10km to station)
    ("mayo-beach",                            "8447435",  "noaa"),   # Mayo Beach (28km to station)
    ("maziers-pond",                          "8760721",  "noaa"),   # Maziers Pond (3km to station)
    ("mcclures-beach",                        "9415020",  "noaa"),   # McClures Beach (22km to station)
    ("mccook-park-beach",                     "8461490",  "noaa"),   # McCook Park Beach (10km to station)
    ("mccovey-cove",                          "9414290",  "noaa"),   # McCovey Cove (8km to station)
    ("mccrary-cove",                          "8727520",  "noaa"),   # McCrary Cove (6km to station)
    ("mccreadys-cove",                        "8571421",  "noaa"),   # McCreadys Cove (9km to station)
    ("mcdonald-bay",                          "8311030",  "noaa"),   # McDonald Bay (24km to station)
    ("mcdonell-bay",                          "9052000",  "noaa"),   # McDonell Bay (12km to station)
    ("mcgalls-bay",                           "2695535",  "noaa"),   # McGall's Bay (8km to station)
    ("mcheard-cove",                          "8413320",  "noaa"),   # McHeard Cove (25km to station)
    ("mckans-bay",                            "8635750",  "noaa"),   # McKans Bay (30km to station)
    ("mckay-bay",                             "8726674",  "noaa"),   # McKay Bay (1km to station)
    ("mckay-cove",                            "8577330",  "noaa"),   # McKay Cove (17km to station)
    ("mcleods-bay",                           "9076024",  "noaa"),   # McLeod's Bay (39km to station)
    ("mcpherson-bayou",                       "8726520",  "noaa"),   # McPherson Bayou (12km to station)
    ("mcrae-bay",                             "9075080",  "noaa"),   # McRae Bay (22km to station)
    ("mecox-bay",                             "8510560",  "noaa"),   # Mecox Bay (35km to station)
    ("medeiros-beach",                        "8447930",  "noaa"),   # Medeiros Beach (21km to station)
    ("meekins-creek",                         "8571892",  "noaa"),   # Meekins Creek (19km to station)
    ("meher-beach",                           "8661070",  "noaa"),   # Meher Beach (20km to station)
    ("melager-cove",                          "8771486",  "noaa"),   # Melager Cove (8km to station)
    ("mellows-cove",                          "8413320",  "noaa"),   # Mellows Cove (30km to station)
    ("menahaunt-beach",                       "8447930",  "noaa"),   # Menahaunt Beach (10km to station)
    ("menefee-anchorage",                     "9450460",  "noaa"),   # Menefee Anchorage (40km to station)
    ("menemsha-basin",                        "8447930",  "noaa"),   # Menemsha Basin (20km to station)
    ("menemsha-bight",                        "8447930",  "noaa"),   # Menemsha Bight (21km to station)
    ("menemsha-hills-reservation-beach",      "8447930",  "noaa"),   # Menemsha Hills Reservation Beach (18km to station)
    ("menhaden-lane-beach",                   "8510560",  "noaa"),   # Menhaden Lane Beach (31km to station)
    ("menhinick-drive-beach",                 "9449880",  "noaa"),   # Menhinick Drive Beach (38km to station)
    ("mennebeck-bay",                         "9751381",  "noaa"),   # Mennebeck Bay (6km to station)
    ("menokin-bay",                           "8635750",  "noaa"),   # Menokin Bay (30km to station)
    ("mentzel-bayou",                         "8771486",  "noaa"),   # Mentzel Bayou (8km to station)
    ("mercerwood-shore-club-beach",           "9446484",  "noaa"),   # Mercerwood Shore Club beach (37km to station)
    ("merchants-beach",                       "9432780",  "noaa"),   # Merchants Beach (13km to station)
    ("meredith-creek",                        "8575512",  "noaa"),   # Meredith Creek (5km to station)
    ("merepoint-bay",                         "8418150",  "noaa"),   # Merepoint Bay (27km to station)
    ("merkle-bay",                            "8656483",  "noaa"),   # Merkle Bay (38km to station)
    ("merkle-hammock-creek",                  "8656483",  "noaa"),   # Merkle Hammock Creek (37km to station)
    ("merriam-beach",                         "8447930",  "noaa"),   # Merriam Beach (16km to station)
    ("merrick-bay",                           "8516945",  "noaa"),   # Merrick Bay (26km to station)
    ("merrickville-public-beach",             "8311030",  "noaa"),   # Merrickville Public Beach (36km to station)
    ("merriconeag-sound",                     "8418150",  "noaa"),   # Merriconeag Sound (20km to station)
    ("merrimack-inlet",                       "8419870",  "noaa"),   # Merrimack Inlet (30km to station)
    ("merriman-cove",                         "8418150",  "noaa"),   # Merriman Cove (26km to station)
    ("merritt-cove",                          "8413320",  "noaa"),   # Merritt Cove (40km to station)
    ("merry-cove",                            "8418150",  "noaa"),   # Merry Cove (36km to station)
    ("mesquite-bay",                          "8774230",  "noaa"),   # Mesquite Bay (10km to station)
    ("mess-tent-cove",                        "8311062",  "noaa"),   # Mess Tent Cove (13km to station)
    ("methelin-bay",                          "2695540",  "noaa"),   # Methelin Bay (18km to station)
    ("metompkin-bay",                         "8631044",  "noaa"),   # Metompkin Bay (15km to station)
    ("metompkin-inlet",                       "8631044",  "noaa"),   # Metompkin Inlet (12km to station)
    ("metzelaar-bay",                         "9075065",  "noaa"),   # Metzelaar Bay (22km to station)
    ("meudon-beach",                          "8516945",  "noaa"),   # Meudon Beach (17km to station)
    ("meyers-cove",                           "8726724",  "noaa"),   # Meyers Cove (22km to station)
    ("miacomet-beach",                        "8449130",  "noaa"),   # Miacomet Beach (6km to station)
    ("michoud-slip",                          "8761955",  "noaa"),   # Michoud Slip (22km to station)
    ("micklers-landing",                      "8720218",  "noaa"),   # Mickler's Landing (27km to station)
    ("middens-creek",                         "8656483",  "noaa"),   # Middens Creek (15km to station)
    ("middle-arm",                            "9454050",  "noaa"),   # Middle Arm (6km to station)
    ("middle-arm-kelp-bay",                   "9451600",  "noaa"),   # Middle Arm Kelp Bay (38km to station)
    ("middle-bay",                            "8741533",  "noaa"),   # Middle Bay (15km to station)
    ("middle-bay-cove",                       "8418150",  "noaa"),   # Middle Bay Cove (32km to station)
    ("middle-beach",                          "8413320",  "noaa"),   # Middle Beach (34km to station)
    ("middle-branch-patapsco-river",          "8574680",  "noaa"),   # Middle Branch Patapsco River (4km to station)
    ("middle-cove",                           "8461490",  "noaa"),   # Middle Cove (25km to station)
    ("middle-creek",                          "8654467",  "noaa"),   # Middle Creek (39km to station)
    ("middle-ground",                         "8760721",  "noaa"),   # Middle Ground (24km to station)
    ("middle-pass",                           "8775241",  "noaa"),   # Middle Pass (7km to station)
    ("middle-point-bay",                      "8311030",  "noaa"),   # Middle Point Bay (26km to station)
    ("middle-point-cove",                     "8447930",  "noaa"),   # Middle Point Cove (19km to station)
    ("middle-prong",                          "8721604",  "noaa"),   # Middle Prong (20km to station)
    ("middle-quarter-cove",                   "8573364",  "noaa"),   # Middle Quarter Cove (18km to station)
    ("middle-slough",                         "9415144",  "noaa"),   # Middle Slough (16km to station)
    ("middle-sound",                          "8658163",  "noaa"),   # Middle Sound (6km to station)
    ("middle-tampa-bay",                      "8726520",  "noaa"),   # Middle Tampa Bay (7km to station)
    ("middle-waterway",                       "9446484",  "noaa"),   # Middle Waterway (2km to station)
    ("middletown-anchorage",                  "8654467",  "noaa"),   # Middletown Anchorage (39km to station)
    ("midgett-cove",                          "8652587",  "noaa"),   # Midgett Cove (28km to station)
    ("midway-inlet",                          "8661070",  "noaa"),   # Midway Inlet (29km to station)
    ("mielkoi-cove",                          "9451600",  "noaa"),   # Mielkoi Cove (10km to station)
    ("miguel-bay",                            "8726384",  "noaa"),   # Miguel Bay (8km to station)
    ("milburn-bay",                           "9052000",  "noaa"),   # Milburn Bay (31km to station)
    ("milburn-creek",                         "8577330",  "noaa"),   # Milburn Creek (17km to station)
    ("mile-arm-bay",                          "8311062",  "noaa"),   # Mile Arm Bay (23km to station)
    ("mile-end-cove",                         "8454000",  "noaa"),   # Mile End Cove (1km to station)
    ("mile-rock-beach",                       "9414290",  "noaa"),   # Mile Rock Beach (4km to station)
    ("mile-zero-beach",                       "9449880",  "noaa"),   # Mile Zero Beach (30km to station)
    ("miley-creek",                           "8577330",  "noaa"),   # Miley Creek (24km to station)
    ("mill-bayou",                            "8726384",  "noaa"),   # Mill Bayou (13km to station)
    ("mill-beach",                            "9419750",  "noaa"),   # Mill Beach (35km to station)
    ("mill-creek",                            "8575512",  "noaa"),   # Mill Creek (3km to station)
    ("mill-creek-cove",                       "8551910",  "noaa"),   # Mill Creek Cove (5km to station)
    ("mill-pond",                             "8447435",  "noaa"),   # Mill Pond (12km to station)
    ("millar-bay",                            "8726384",  "noaa"),   # Millar Bay (26km to station)
    ("millen-bay",                            "9052000",  "noaa"),   # Millen Bay (8km to station)
    ("millenbeck-prong",                      "8635750",  "noaa"),   # Millenbeck Prong (37km to station)
    ("miller-cove",                           "8637689",  "noaa"),   # Miller Cove (31km to station)
    ("miller-creek",                          "8570283",  "noaa"),   # Miller Creek (19km to station)
    ("millers-bay",                           "8311062",  "noaa"),   # Millers Bay (38km to station)
    ("millers-bayou",                         "8726724",  "noaa"),   # Millers Bayou (35km to station)
    ("millhouse-bay",                         "2695535",  "noaa"),   # Millhouse Bay (4km to station)
    ("milliken-cove",                         "8661070",  "noaa"),   # Milliken Cove (40km to station)
    ("millway-beach",                         "8447435",  "noaa"),   # Millway Beach (29km to station)
    ("milo-cove",                             "1612340",  "noaa"),   # Milo Cove (28km to station)
    ("milton-harbor",                         "8516945",  "noaa"),   # Milton Harbor (16km to station)
    ("milwaukee-waterway",                    "9446484",  "noaa"),   # Milwaukee Waterway (1km to station)
    ("mine-cove",                             "8571421",  "noaa"),   # Mine Cove (23km to station)
    ("mine-creek",                            "8571421",  "noaa"),   # Mine Creek (22km to station)
    ("mine-harbor",                           "9463502",  "noaa"),   # Mine Harbor (26km to station)
    ("miner-cove",                            "9451054",  "noaa"),   # Miner Cove (7km to station)
    ("mink-island-bay",                       "8632200",  "noaa"),   # Mink Island Bay (13km to station)
    ("minnow-creek",                          "8575512",  "noaa"),   # Minnow Creek (5km to station)
    ("minot-forest-beach",                    "8447930",  "noaa"),   # Minot Forest Beach (26km to station)
    ("minout-pond",                           "8760721",  "noaa"),   # Minout Pond (4km to station)
    ("minuteman-beach",                       "9412110",  "noaa"),   # Minuteman Beach (37km to station)
    ("misery-bay",                            "9075065",  "noaa"),   # Misery Bay (10km to station)
    ("mismer-bay",                            "9075080",  "noaa"),   # Mismer Bay (32km to station)
    ("mission-bay",                           "9410170",  "noaa"),   # Mission Bay (9km to station)
    ("missisippi-river-general-anchorage",    "8761955",  "noaa"),   # Missisippi River General Anchorage (14km to station)
    ("mist-cove",                             "9451054",  "noaa"),   # Mist Cove (31km to station)
    ("mistake-harbor",                        "8411060",  "noaa"),   # Mistake Harbor (33km to station)
    ("mitchell-bay",                          "8311030",  "noaa"),   # Mitchell Bay (21km to station)
    ("mitchell-beach",                        "8461490",  "noaa"),   # Mitchell Beach (5km to station)
    ("mitchell-bluff",                        "8573364",  "noaa"),   # Mitchell Bluff (1km to station)
    ("mitchell-cove",                         "8413320",  "noaa"),   # Mitchell Cove (22km to station)
    ("mitchelville-beach",                    "8670870",  "noaa"),   # Mitchelville Beach (31km to station)
    ("mite-cove",                             "9452634",  "noaa"),   # Mite Cove (15km to station)
    ("mobbly-bay",                            "8726724",  "noaa"),   # Mobbly Bay (18km to station)
    ("mobbly-bayou",                          "8726724",  "noaa"),   # Mobbly Bayou (18km to station)
    ("mockhorn-bay",                          "8632200",  "noaa"),   # Mockhorn Bay (13km to station)
    ("moffat-bay",                            "9075099",  "noaa"),   # Moffat Bay (26km to station)
    ("moffet-lagoon",                         "9459881",  "noaa"),   # Moffet Lagoon (40km to station)
    ("mokapu-beach",                          "1615680",  "noaa"),   # Mokapu Beach (22km to station)
    ("mokihana-bay",                          "1617760",  "noaa"),   # Mokihana Bay (8km to station)
    ("mokolii-view-point",                    "1612480",  "noaa"),   # Mokolii View Point (10km to station)
    ("mokuauia-beach",                        "1612480",  "noaa"),   # Moku‘Auia Beach (30km to station)
    ("molasses-pond-beach",                   "8413320",  "noaa"),   # Molasses Pond Beach (33km to station)
    ("molly-cove",                            "8447930",  "noaa"),   # Molly Cove (18km to station)
    ("mollys-gut",                            "8311030",  "noaa"),   # Molly's Gut (25km to station)
    ("mollys-cove",                           "8447930",  "noaa"),   # Mollys Cove (18km to station)
    ("moloaa-bay",                            "1611400",  "noaa"),   # Moloaʻa Bay (27km to station)
    ("momauguin-beach",                       "8465705",  "noaa"),   # Momauguin Beach (5km to station)
    ("monastery-beach",                       "9413450",  "noaa"),   # Monastery Beach (10km to station)
    ("monatou-bay",                           "9087096",  "noaa"),   # Monatou Bay (38km to station)
    ("mondays-creek",                         "8594900",  "noaa"),   # Mondays Creek (29km to station)
    ("money-beach",                           "8728690",  "noaa"),   # Money Beach (29km to station)
    ("money-island-bay",                      "8656483",  "noaa"),   # Money Island Bay (5km to station)
    ("monhegan-bluffs-beach",                 "8510560",  "noaa"),   # Monhegan Bluffs Beach (35km to station)
    ("monhonan-cove",                         "8413320",  "noaa"),   # Monhonan Cove (29km to station)
    ("monie-bay",                             "8571421",  "noaa"),   # Monie Bay (18km to station)
    ("monkey-hole",                           "2695540",  "noaa"),   # Monkey Hole (20km to station)
    ("monks-bath-beach",                      "9751401",  "noaa"),   # Monks Bath Beach (16km to station)
    ("monomoy-beach",                         "8449130",  "noaa"),   # Monomoy Beach (1km to station)
    ("monsod-bay",                            "8447930",  "noaa"),   # Monsod Bay (2km to station)
    ("montara-state-beach",                   "9414523",  "noaa"),   # Montara State Beach (27km to station)
    ("montauk-county-park-rv-campground",     "8510560",  "noaa"),   # Montauk County Park RV Campground (4km to station)
    ("monte-bay",                             "9751381",  "noaa"),   # Monte Bay (5km to station)
    ("monterey-state-beach",                  "9413450",  "noaa"),   # Monterey State Beach (2km to station)
    ("monti-bay",                             "9453220",  "noaa"),   # Monti Bay (3km to station)
    ("montowese-beach",                       "8465705",  "noaa"),   # Montowese Beach (9km to station)
    ("monument-cove",                         "8413320",  "noaa"),   # Monument Cove (8km to station)
    ("moody-beach",                           "8419870",  "noaa"),   # Moody Beach (25km to station)
    ("moolack-beach",                         "9435380",  "noaa"),   # Moolack Beach (8km to station)
    ("moon-bay",                              "8571421",  "noaa"),   # Moon Bay (27km to station)
    ("mooney-harbor",                         "8724580",  "noaa"),   # Mooney Harbor (33km to station)
    ("moore-creek",                           "8721604",  "noaa"),   # Moore Creek (21km to station)
    ("moores-beach",                          "8536110",  "noaa"),   # Moores Beach (24km to station)
    ("mooring-basin",                         "8573927",  "noaa"),   # Mooring Basin (0km to station)
    ("moose-snare-cove",                      "8411060",  "noaa"),   # Moose Snare Cove (17km to station)
    ("moosup-pond-beach",                     "8454000",  "noaa"),   # Moosup Pond Beach (40km to station)
    ("moran-creek",                           "8635750",  "noaa"),   # Moran Creek (34km to station)
    ("morgan-bay",                            "8413320",  "noaa"),   # Morgan Bay (23km to station)
    ("morgan-harbor",                         "8761305",  "noaa"),   # Morgan Harbor (36km to station)
    ("morgan-pond",                           "8760721",  "noaa"),   # Morgan Pond (3km to station)
    ("morning-beach",                         "2695540",  "noaa"),   # Morning Beach (17km to station)
    ("morningside-beach",                     "8465705",  "noaa"),   # Morningside Beach (12km to station)
    ("morningstar-bay",                       "9751381",  "noaa"),   # Morningstar Bay (21km to station)
    ("morningstar-beach",                     "9751381",  "noaa"),   # Morningstar Beach (21km to station)
    ("morris-bay",                            "8637689",  "noaa"),   # Morris Bay (31km to station)
    ("morris-cove",                           "8510560",  "noaa"),   # Morris Cove (30km to station)
    ("morrisburg-beach",                      "8311030",  "noaa"),   # Morrisburg Beach (33km to station)
    ("morristown-bay",                        "8311030",  "noaa"),   # Morristown Bay (18km to station)
    ("morro-rock-beach",                      "9412110",  "noaa"),   # Morro Rock Beach (25km to station)
    ("morrow-cove",                           "9415102",  "noaa"),   # Morrow Cove (10km to station)
    ("morsell-creek",                         "8577330",  "noaa"),   # Morsell Creek (25km to station)
    ("mortensens-lagoon",                     "9459881",  "noaa"),   # Mortensens Lagoon (20km to station)
    ("mortimer-spit",                         "9449880",  "noaa"),   # Mortimer Spit (30km to station)
    ("moser-bay",                             "9450460",  "noaa"),   # Moser Bay (26km to station)
    ("moshup-beach",                          "8447930",  "noaa"),   # Moshup Beach (24km to station)
    ("mosquito-bay",                          "8764314",  "noaa"),   # Mosquito Bay (21km to station)
    ("mosquito-bay-beach",                    "9752695",  "noaa"),   # Mosquito Bay Beach (3km to station)
    ("mosquito-bight",                        "8761305",  "noaa"),   # Mosquito Bight (28km to station)
    ("mosquito-cove",                         "8516945",  "noaa"),   # Mosquito Cove (11km to station)
    ("mosquito-harbor",                       "8413320",  "noaa"),   # Mosquito Harbor (11km to station)
    ("mosquito-pass",                         "8764227",  "noaa"),   # Mosquito Pass (22km to station)
    ("moss-bluff-bay",                        "8767816",  "noaa"),   # Moss Bluff Bay (9km to station)
    ("moss-pond",                             "8575512",  "noaa"),   # Moss Pond (6km to station)
    ("moth-bay",                              "9450460",  "noaa"),   # Moth Bay (19km to station)
    ("mothers-beach",                         "9410840",  "noaa"),   # Mother's Beach (5km to station)
    ("mott-cove",                             "8516945",  "noaa"),   # Mott Cove (10km to station)
    ("motts-basin",                           "8516945",  "noaa"),   # Motts Basin (22km to station)
    ("motts-creek",                           "8652587",  "noaa"),   # Motts Creek (0km to station)
    ("mouillage-cove",                        "9751381",  "noaa"),   # Mouillage Cove (19km to station)
    ("mount-airy-cove",                       "8631044",  "noaa"),   # Mount Airy Cove (21km to station)
    ("mount-baker-beach",                     "9446484",  "noaa"),   # Mount Baker Beach (36km to station)
    ("mount-hope-bay",                        "8447386",  "noaa"),   # Mount Hope Bay (4km to station)
    ("mount-vernon-beach",                    "8571421",  "noaa"),   # Mount Vernon Beach (18km to station)
    ("mountaindale-beach",                    "8454000",  "noaa"),   # Mountaindale Beach (14km to station)
    ("mowry-beach",                           "8410140",  "noaa"),   # Mowry Beach (6km to station)
    ("moyle-cove",                            "8510560",  "noaa"),   # Moyle Cove (39km to station)
    ("mud-bay",                               "9075065",  "noaa"),   # Mud Bay (32km to station)
    ("mud-bayou",                             "8729108",  "noaa"),   # Mud Bayou (11km to station)
    ("mud-cove",                              "8461490",  "noaa"),   # Mud Cove (11km to station)
    ("mud-hole",                              "8411060",  "noaa"),   # Mud Hole (35km to station)
    ("muddy-cove",                            "8447930",  "noaa"),   # Muddy Cove (17km to station)
    ("muddy-creek",                           "8571421",  "noaa"),   # Muddy Creek (33km to station)
    ("muddy-creek-bay",                       "9063079",  "noaa"),   # Muddy Creek Bay (25km to station)
    ("muddy-hook-cove",                       "8571421",  "noaa"),   # Muddy Hook Cove (13km to station)
    ("mudhole-bay",                           "8764314",  "noaa"),   # Mudhole Bay (38km to station)
    ("mulberry-cove",                         "8720219",  "noaa"),   # Mulberry Cove (22km to station)
    ("muller-bay",                            "9751381",  "noaa"),   # Muller Bay (13km to station)
    ("muller-bay-beach",                      "9751381",  "noaa"),   # Muller Bay Beach (13km to station)
    ("mullet-cove",                           "8764314",  "noaa"),   # Mullet Cove (6km to station)
    ("mullet-creek-bay",                      "8311062",  "noaa"),   # Mullet Creek Bay (8km to station)
    ("mullet-key-bayou",                      "8726384",  "noaa"),   # Mullet Key Bayou (16km to station)
    ("mullet-lake",                           "8747437",  "noaa"),   # Mullet Lake (35km to station)
    ("mumford-cove",                          "8461490",  "noaa"),   # Mumford Cove (9km to station)
    ("mundys-bay",                            "9075099",  "noaa"),   # Mundy's Bay (40km to station)
    ("munfort-cove",                          "8418150",  "noaa"),   # Munfort Cove (29km to station)
    ("municipal-yacht-harbor",                "9414863",  "noaa"),   # Municipal Yacht Harbor (11km to station)
    ("murdock-bay",                           "8725520",  "noaa"),   # Murdock Bay (39km to station)
    ("murdock-bayou",                         "8725520",  "noaa"),   # Murdock Bayou (36km to station)
    ("murdock-beach",                         "9444090",  "noaa"),   # Murdock Beach (32km to station)
    ("murdocks-eddy",                         "8747437",  "noaa"),   # Murdocks Eddy (34km to station)
    ("murk-bay",                              "9452634",  "noaa"),   # Murk Bay (26km to station)
    ("murphy-cove",                           "9452634",  "noaa"),   # Murphy Cove (23km to station)
    ("murphys-beach",                         "8311062",  "noaa"),   # Murphy's Beach (13km to station)
    ("murphys-cove",                          "8729840",  "noaa"),   # Murphys Cove (15km to station)
    ("murray-bay",                            "9052000",  "noaa"),   # Murray Bay (10km to station)
    ("murray-bayou",                          "8729108",  "noaa"),   # Murray Bayou (22km to station)
    ("murray-marsh-cove",                     "8557380",  "noaa"),   # Murray Marsh Cove (19km to station)
    ("murray-point",                          "8729108",  "noaa"),   # Murray Point (22km to station)
    ("murrays-anchorage",                     "2695540",  "noaa"),   # Murray's Anchorage (2km to station)
    ("muscallonge-bay",                       "9075080",  "noaa"),   # Muscallonge Bay (35km to station)
    ("muscle-hole",                           "8571421",  "noaa"),   # Muscle Hole (16km to station)
    ("musquash-cove",                         "8413320",  "noaa"),   # Musquash Cove (33km to station)
    ("mussel-cove",                           "8418150",  "noaa"),   # Mussel Cove (13km to station)
    ("mustin-beach",                          "8729840",  "noaa"),   # Mustin Beach (10km to station)
    ("my-lords-bay",                          "2695540",  "noaa"),   # My Lord's Bay (4km to station)
    ("myer-creek",                            "8635750",  "noaa"),   # Myer Creek (34km to station)
    ("myrick-cove",                           "8413320",  "noaa"),   # Myrick Cove (8km to station)
    ("myrtle-bay",                            "8651370",  "noaa"),   # Myrtle Bay (10km to station)
    ("myrtle-grove-sound",                    "8658163",  "noaa"),   # Myrtle Grove Sound (15km to station)
    ("myrtle-island-beach",                   "8632200",  "noaa"),   # Myrtle Island Beach (16km to station)
    ("myrtle-point-public-beach",             "9432780",  "noaa"),   # Myrtle Point Public Beach (34km to station)
    ("mhukona-harbor",                        "1617433",  "noaa"),   # Māhukona Harbor (18km to station)
    ("mklei-beach",                           "1612340",  "noaa"),   # Mākālei Beach (7km to station)
    ("mmala-bay",                             "1612340",  "noaa"),   # Māmala Bay (9km to station)
    ("nabbs-creek",                           "8574680",  "noaa"),   # Nabbs Creek (12km to station)
    ("nadzaheen-cove",                        "9450460",  "noaa"),   # Nadzaheen Cove (15km to station)
    ("naginak-cove",                          "9462620",  "noaa"),   # Naginak Cove (32km to station)
    ("nahku-bay",                             "9452400",  "noaa"),   # Nahku Bay (2km to station)
    ("nail-bay",                              "9751381",  "noaa"),   # Nail Bay (37km to station)
    ("nalima-wai",                            "1615680",  "noaa"),   # Nalima Wai (20km to station)
    ("namalu-bay",                            "1615680",  "noaa"),   # Namalu Bay (24km to station)
    ("nanakuli-beach-park",                   "1612340",  "noaa"),   # Nanakuli Beach Park (30km to station)
    ("nantuxent-cove",                        "8537121",  "noaa"),   # Nantuxent Cove (10km to station)
    ("nanuku-inlet",                          "1617433",  "noaa"),   # Nanuku Inlet (11km to station)
    ("nanzatico-bay",                         "8635027",  "noaa"),   # Nanzatico Bay (19km to station)
    ("napili-beach",                          "1615680",  "noaa"),   # Napili Beach (23km to station)
    ("naples-beach",                          "9414523",  "noaa"),   # Naples Beach (22km to station)
    ("narraguagus-bay",                       "8413320",  "noaa"),   # Narraguagus Bay (32km to station)
    ("narrow-mouth-cove",                     "8658120",  "noaa"),   # Narrow Mouth Cove (26km to station)
    ("narrows-cove",                          "8725520",  "noaa"),   # Narrows Cove (36km to station)
    ("naskeag-harbor",                        "8413320",  "noaa"),   # Naskeag Harbor (32km to station)
    ("nasketucket-bay",                       "8447930",  "noaa"),   # Nasketucket Bay (16km to station)
    ("nateekin-bay",                          "9462620",  "noaa"),   # Nateekin Bay (5km to station)
    ("nathaniel-bay",                         "9751381",  "noaa"),   # Nathaniel Bay (4km to station)
    ("nats-cove",                             "8557380",  "noaa"),   # Nats Cove (16km to station)
    ("nats-creek",                            "8577330",  "noaa"),   # Nats Creek (6km to station)
    ("natty-point-cove",                      "8635750",  "noaa"),   # Natty Point Cove (29km to station)
    ("nauset-bay",                            "8447435",  "noaa"),   # Nauset Bay (17km to station)
    ("nauyaug-coast",                         "8461490",  "noaa"),   # Nauyaug Coast (12km to station)
    ("navesink-beach",                        "8531680",  "noaa"),   # Navesink Beach (9km to station)
    ("navy-bar",                              "8410140",  "noaa"),   # Navy Bar (18km to station)
    ("navy-bay",                              "9052000",  "noaa"),   # Navy Bay (15km to station)
    ("navy-cove",                             "8735180",  "noaa"),   # Navy Cove (10km to station)
    ("navy-island-shoal",                     "8410140",  "noaa"),   # Navy Island Shoal (18km to station)
    ("nawalagwis-magic-beach",                "9449880",  "noaa"),   # Nawalagwis (Magic Beach) (18km to station)
    ("nawiliwili-bay",                        "1611400",  "noaa"),   # Nawiliwili Bay (1km to station)
    ("nawiliwili-harbor",                     "1611400",  "noaa"),   # Nawiliwili Harbor (0km to station)
    ("nayses-bay",                            "8637689",  "noaa"),   # Nayses Bay (33km to station)
    ("nazareth-bay",                          "9751381",  "noaa"),   # Nazareth Bay (14km to station)
    ("neal-cove",                             "9410170",  "noaa"),   # Neal Cove (18km to station)
    ("neale-sound",                           "8635027",  "noaa"),   # Neale Sound (17km to station)
    ("neals-beach",                           "8635750",  "noaa"),   # Neals Beach (24km to station)
    ("neals-cove",                            "8419870",  "noaa"),   # Neals Cove (34km to station)
    ("necker-bay",                            "9451600",  "noaa"),   # Necker Bay (40km to station)
    ("neds-hole",                             "2695540",  "noaa"),   # Ned's Hole (18km to station)
    ("needle-beach",                          "8639348",  "noaa"),   # Needle Beach (7km to station)
    ("negro-bay",                             "8735180",  "noaa"),   # Negro Bay (17km to station)
    ("negro-cove",                            "8571421",  "noaa"),   # Negro Cove (11km to station)
    ("nehenta-bay",                           "9450460",  "noaa"),   # Nehenta Bay (22km to station)
    ("nellies-cove",                          "9431647",  "noaa"),   # Nellies Cove (1km to station)
    ("nelson-lagoon",                         "9463502",  "noaa"),   # Nelson Lagoon (32km to station)
    ("neltjeberg-bay",                        "9751381",  "noaa"),   # Neltjeberg Bay (26km to station)
    ("neptune-bay",                           "9455500",  "noaa"),   # Neptune Bay (21km to station)
    ("neue-bay",                              "1617433",  "noaa"),   # Neue Bay (23km to station)
    ("neva-bay",                              "9451600",  "noaa"),   # Neva Bay (30km to station)
    ("new-barn-cove",                         "8418150",  "noaa"),   # New Barn Cove (30km to station)
    ("new-dorp-beach",                        "8531680",  "noaa"),   # New Dorp Beach (13km to station)
    ("new-harbor",                            "8510560",  "noaa"),   # New Harbor (36km to station)
    ("new-inlet",                             "8632200",  "noaa"),   # New Inlet (19km to station)
    ("new-place-cove",                        "8418150",  "noaa"),   # New Place Cove (38km to station)
    ("new-port-pass",                         "8775792",  "noaa"),   # New Port Pass (5km to station)
    ("new-river-bayou",                       "8728690",  "noaa"),   # New River Bayou (33km to station)
    ("new-topsail-inlet",                     "8658163",  "noaa"),   # New Topsail Inlet (18km to station)
    ("new-york-slough",                       "9415144",  "noaa"),   # New York Slough (16km to station)
    ("newcomb-hollow-beach",                  "8447435",  "noaa"),   # Newcomb Hollow Beach (30km to station)
    ("newfound-bay",                          "9751381",  "noaa"),   # Newfound Bay (7km to station)
    ("newfound-harbor",                       "8723970",  "noaa"),   # Newfound Harbor (30km to station)
    ("newman-bayou",                          "8729108",  "noaa"),   # Newman Bayou (14km to station)
    ("newman-cove",                           "8413320",  "noaa"),   # Newman Cove (18km to station)
    ("newport-bay",                           "8570283",  "noaa"),   # Newport Bay (15km to station)
    ("newport-cove",                          "8413320",  "noaa"),   # Newport Cove (7km to station)
    ("newport-harbor",                        "8452660",  "noaa"),   # Newport Harbor (2km to station)
    ("newport-sand-beach",                    "8518750",  "noaa"),   # Newport Sand Beach (4km to station)
    ("newton-town-beach",                     "8419870",  "noaa"),   # Newton Town Beach (34km to station)
    ("nicholas-canyon-beach",                 "9410840",  "noaa"),   # Nicholas Canyon Beach (39km to station)
    ("nicholl-pond",                          "8760721",  "noaa"),   # Nicholl Pond (12km to station)
    ("nickel-plate-beach",                    "9063079",  "noaa"),   # Nickel Plate Beach (23km to station)
    ("nikiski-bay",                           "9455760",  "noaa"),   # Nikiski Bay (9km to station)
    ("niles-beach",                           "9414523",  "noaa"),   # Niles beach (20km to station)
    ("nils-bay",                              "9076070",  "noaa"),   # Nils Bay (33km to station)
    ("ninemile-bay",                          "8761305",  "noaa"),   # Ninemile Bay (32km to station)
    ("ninigret-beach",                        "8452660",  "noaa"),   # Ninigret Beach (30km to station)
    ("ninneegoes-bay",                        "9087096",  "noaa"),   # Ninneegoes Bay (33km to station)
    ("nisqually-reach",                       "9446484",  "noaa"),   # Nisqually Reach (30km to station)
    ("nix-cove",                              "8638610",  "noaa"),   # Nix Cove (17km to station)
    ("no-ache-bay",                           "8652587",  "noaa"),   # No Ache Bay (32km to station)
    ("no-name-beach",                         "9415020",  "noaa"),   # No Name Beach (20km to station)
    ("no-name-harbor",                        "8723214",  "noaa"),   # No Name Harbor (6km to station)
    ("no-thorofare-bay",                      "9451600",  "noaa"),   # No Thorofare Bay (8km to station)
    ("noank-town-dock-beach",                 "8461490",  "noaa"),   # Noank Town Dock Beach (11km to station)
    ("nobadeer-beach",                        "8449130",  "noaa"),   # Nobadeer Beach (6km to station)
    ("nobscusset-harbor",                     "8447435",  "noaa"),   # Nobscusset Harbor (21km to station)
    ("nohiu",                                 "1611400",  "noaa"),   # Nohiu (2km to station)
    ("nolfi-cove",                            "9455920",  "noaa"),   # Nolfi Cove (31km to station)
    ("nom-outside-pond",                      "8760721",  "noaa"),   # Nom Outside Pond (11km to station)
    ("nomini-bay",                            "8635750",  "noaa"),   # Nomini Bay (28km to station)
    ("noname-beach",                          "8447930",  "noaa"),   # Noname Beach (22km to station)
    ("nonesuch-cove",                         "8418150",  "noaa"),   # Nonesuch Cove (12km to station)
    ("nonsuch-bay",                           "2695535",  "noaa"),   # Nonsuch Bay (4km to station)
    ("norman-cove",                           "8571421",  "noaa"),   # Norman Cove (5km to station)
    ("normans-creek",                         "8575512",  "noaa"),   # Normans Creek (18km to station)
    ("north-arm-moira-sound",                 "9450460",  "noaa"),   # North Arm Moira Sound (40km to station)
    ("north-banks",                           "8725520",  "noaa"),   # North Banks (36km to station)
    ("north-basin",                           "8536110",  "noaa"),   # North Basin (21km to station)
    ("north-cove",                            "8461490",  "noaa"),   # North Cove (24km to station)
    ("north-cove-yacht-harbor",               "8518750",  "noaa"),   # North Cove Yacht Harbor (1km to station)
    ("north-cypress-creek",                   "8575512",  "noaa"),   # North Cypress Creek (11km to station)
    ("north-east-beach-area",                 "8573927",  "noaa"),   # North East Beach Area (16km to station)
    ("north-end-beach",                       "8534720",  "noaa"),   # North End Beach (9km to station)
    ("north-end-bottom",                      "8571421",  "noaa"),   # North End Bottom (24km to station)
    ("north-fishtail-bay",                    "9075080",  "noaa"),   # North Fishtail Bay (22km to station)
    ("north-fork-chase-creek",                "8575512",  "noaa"),   # North Fork Chase Creek (5km to station)
    ("north-haulover-beach",                  "9751381",  "noaa"),   # North Haulover Beach (6km to station)
    ("north-karako-bay",                      "8747437",  "noaa"),   # North Karako Bay (31km to station)
    ("north-lagoon",                          "2695540",  "noaa"),   # North Lagoon (7km to station)
    ("north-landing-beach",                   "8518962",  "noaa"),   # North Landing Beach (21km to station)
    ("north-litchfield-beach",                "8661070",  "noaa"),   # North Litchfield Beach (24km to station)
    ("north-marina",                          "9413450",  "noaa"),   # North Marina (12km to station)
    ("north-maumee-bay",                      "9063085",  "noaa"),   # North Maumee Bay (7km to station)
    ("north-paia-beach",                      "1615680",  "noaa"),   # North Paia Beach (12km to station)
    ("north-point-creek",                     "8574680",  "noaa"),   # North Point Creek (13km to station)
    ("north-pond",                            "8449130",  "noaa"),   # North Pond (14km to station)
    ("north-pond-barrier-beach",              "9063079",  "noaa"),   # North Pond Barrier Beach (8km to station)
    ("north-san-diego-bay",                   "9410170",  "noaa"),   # North San Diego Bay (2km to station)
    ("north-sea-bathing-beach",               "8510560",  "noaa"),   # North Sea Bathing Beach (40km to station)
    ("north-severn-beach",                    "8575512",  "noaa"),   # North Severn Beach (1km to station)
    ("north-shore",                           "9052000",  "noaa"),   # North Shore (11km to station)
    ("north-shore-bay",                       "8760721",  "noaa"),   # North Shore Bay (14km to station)
    ("north-swimming-beach",                  "9063079",  "noaa"),   # North Swimming Beach (6km to station)
    ("northcut-bay",                          "9087096",  "noaa"),   # Northcut Bay (37km to station)
    ("northeast-bay",                         "8575512",  "noaa"),   # Northeast Bay (18km to station)
    ("northeast-cove",                        "8571421",  "noaa"),   # Northeast Cove (7km to station)
    ("northeast-harbor",                      "8411060",  "noaa"),   # Northeast Harbor (8km to station)
    ("northeast-prong",                       "8652587",  "noaa"),   # Northeast Prong (30km to station)
    ("northern-pond",                         "8654467",  "noaa"),   # Northern Pond (27km to station)
    ("northport-basin",                       "8467150",  "noaa"),   # Northport Basin (31km to station)
    ("northwest-cove",                        "8447930",  "noaa"),   # Northwest Cove (16km to station)
    ("northwest-harbor",                      "8510560",  "noaa"),   # Northwest Harbor (25km to station)
    ("northwest-jack-williams-bay",           "8747437",  "noaa"),   # Northwest Jack Williams Bay (31km to station)
    ("norton-basin",                          "8516945",  "noaa"),   # Norton Basin (23km to station)
    ("norton-point-beach",                    "8447930",  "noaa"),   # Norton Point Beach (24km to station)
    ("norwood-cove",                          "8413320",  "noaa"),   # Norwood Cove (15km to station)
    ("nottingham-town-beach",                 "8419870",  "noaa"),   # Nottingham Town Beach (31km to station)
    ("nowiskay-cove",                         "9450460",  "noaa"),   # Nowiskay Cove (40km to station)
    ("noyack-creek",                          "8510560",  "noaa"),   # Noyack Creek (35km to station)
    ("nuaailua-bay",                          "1615680",  "noaa"),   # Nua‘ailua Bay (32km to station)
    ("nueces-bay",                            "8775296",  "noaa"),   # Nueces Bay (6km to station)
    ("nugent-bay",                            "9751364",  "noaa"),   # Nugent Bay (5km to station)
    ("nugent-beach-private",                  "9063085",  "noaa"),   # Nugent Beach (Private) (5km to station)
    ("number-three-bay",                      "9455760",  "noaa"),   # Number Three Bay (22km to station)
    ("nunovulnuk-harbor",                     "9468333",  "noaa"),   # Nunovulnuk Harbor (39km to station)
    ("nurse-lagoon",                          "9459881",  "noaa"),   # Nurse Lagoon (25km to station)
    ("nyes-cove",                             "8447930",  "noaa"),   # Nyes Cove (16km to station)
    ("nkeikiapua",                            "1615680",  "noaa"),   # Nākeikiapua (38km to station)
    ("nnwale-bay",                            "1617760",  "noaa"),   # Nānāwale Bay (28km to station)
    ("oak-bayou",                             "8771486",  "noaa"),   # Oak Bayou (12km to station)
    ("oak-island-cabana",                     "8658120",  "noaa"),   # Oak Island Cabana (38km to station)
    ("oak-neck-beach",                        "8516945",  "noaa"),   # Oak Neck Beach (19km to station)
    ("oak-point-harbor",                      "9063079",  "noaa"),   # Oak Point Harbor (15km to station)
    ("oakdale-beach",                         "8518979",  "noaa"),   # Oakdale Beach (11km to station)
    ("oakland-basin",                         "8729840",  "noaa"),   # Oakland Basin (28km to station)
    ("oakland-middle-harbor",                 "9414750",  "noaa"),   # Oakland Middle Harbor (4km to station)
    ("oakland-outer-harbor",                  "9414750",  "noaa"),   # Oakland Outer Harbor (5km to station)
    ("oakleigh-cove",                         "8574680",  "noaa"),   # Oakleigh Cove (9km to station)
    ("oarweed-cove",                          "8419870",  "noaa"),   # Oarweed Cove (22km to station)
    ("obstruction-pass-beach",                "9449880",  "noaa"),   # Obstruction Pass Beach (15km to station)
    ("occupessatuxet-cove",                   "8452944",  "noaa"),   # Occupessatuxet Cove (4km to station)
    ("ocean-city-inlet",                      "8570283",  "noaa"),   # Ocean City Inlet (0km to station)
    ("ocean-creek-beach",                     "8661070",  "noaa"),   # Ocean Creek Beach (22km to station)
    ("ocean-drive-beach",                     "8661070",  "noaa"),   # Ocean Drive Beach (30km to station)
    ("ocean-house-beach",                     "8461490",  "noaa"),   # Ocean House Beach (22km to station)
    ("ocean-lakes-beach",                     "8661070",  "noaa"),   # Ocean Lakes Beach (5km to station)
    ("ocean-terrace-public-beach",            "8723214",  "noaa"),   # Ocean Terrace Public Beach (15km to station)
    ("oceano-dunes",                          "9412110",  "noaa"),   # Oceano Dunes (13km to station)
    ("oceanside-city-beach",                  "9410230",  "noaa"),   # Oceanside City Beach (38km to station)
    ("ockway-bay",                            "8447930",  "noaa"),   # Ockway Bay (18km to station)
    ("octave-pond",                           "8760721",  "noaa"),   # Octave Pond (8km to station)
    ("octopus-pond",                          "8570283",  "noaa"),   # Octopus Pond (4km to station)
    ("odiak-slough",                          "9454050",  "noaa"),   # Odiak Slough (2km to station)
    ("ohiki-bay",                             "1617433",  "noaa"),   # Ohiki Bay (20km to station)
    ("ohlson-beach",                          "9416841",  "noaa"),   # Ohlson Beach (32km to station)
    ("oilles-creek",                          "8656483",  "noaa"),   # Oilles Creek (6km to station)
    ("okahanikan-cove",                       "8571421",  "noaa"),   # Okahanikan Cove (4km to station)
    ("okiokiolepe-pond",                      "1612340",  "noaa"),   # Okiʻokiolepe Pond (12km to station)
    ("olander-lake-beach",                    "9063085",  "noaa"),   # Olander Lake Beach (20km to station)
    ("old-basin-cove",                        "8557380",  "noaa"),   # Old Basin Cove (21km to station)
    ("old-brazos-river",                      "8772471",  "noaa"),   # Old Brazos River (5km to station)
    ("old-breach-cut",                        "8510560",  "noaa"),   # Old Breach Cut (36km to station)
    ("old-bull-bay",                          "8720219",  "noaa"),   # Old Bull Bay (30km to station)
    ("old-cove",                              "8631044",  "noaa"),   # Old Cove (27km to station)
    ("old-cutler-bay",                        "8723214",  "noaa"),   # Old Cutler Bay (11km to station)
    ("old-field-beach",                       "8467150",  "noaa"),   # Old Field Beach (24km to station)
    ("old-finds-bight",                       "8724580",  "noaa"),   # Old Finds Bight (22km to station)
    ("old-harbor",                            "8510560",  "noaa"),   # Old Harbor (36km to station)
    ("old-harbour",                           "8419870",  "noaa"),   # Old Harbour (1km to station)
    ("old-hill-bay",                          "8654467",  "noaa"),   # Old Hill Bay (40km to station)
    ("old-house-cove",                        "8571421",  "noaa"),   # Old House Cove (30km to station)
    ("old-kaguyak-bay",                       "9457804",  "noaa"),   # Old Kaguyak Bay (30km to station)
    ("old-lighthouse-beach",                  "8654467",  "noaa"),   # Old Lighthouse Beach (17km to station)
    ("old-mans-lagoon",                       "9459881",  "noaa"),   # Old Mans Lagoon (19km to station)
    ("old-mill-basin",                        "9087031",  "noaa"),   # Old Mill Basin (12km to station)
    ("old-mill-beach",                        "9076024",  "noaa"),   # Old Mill Beach (39km to station)
    ("old-mill-cove",                         "8635750",  "noaa"),   # Old Mill Cove (38km to station)
    ("old-navy-cove",                         "8729840",  "noaa"),   # Old Navy Cove (5km to station)
    ("old-orchard-cove",                      "8447386",  "noaa"),   # Old Orchard Cove (10km to station)
    ("old-place-cove",                        "8575512",  "noaa"),   # Old Place Cove (5km to station)
    ("old-river",                             "8729840",  "noaa"),   # Old River (28km to station)
    ("old-river-bay",                         "8767816",  "noaa"),   # Old River Bay (25km to station)
    ("old-river-cove",                        "8770475",  "noaa"),   # Old River Cove (15km to station)
    ("old-road-bay",                          "8574680",  "noaa"),   # Old Road Bay (12km to station)
    ("old-salt-work-beach",                   "8452660",  "noaa"),   # Old Salt Work Beach (4km to station)
    ("old-shore-beach",                       "9099090",  "noaa"),   # Old Shore Beach (2km to station)
    ("old-stump-lake",                        "8760721",  "noaa"),   # Old Stump Lake (24km to station)
    ("old-tampa-bay",                         "8726607",  "noaa"),   # Old Tampa Bay (7km to station)
    ("old-tom-bayou",                         "8725520",  "noaa"),   # Old Tom Bayou (33km to station)
    ("old-town-bay",                          "8767816",  "noaa"),   # Old Town Bay (11km to station)
    ("old-womans-cove",                       "8575512",  "noaa"),   # Old Womans Cove (2km to station)
    ("olde-port-beach",                       "9412110",  "noaa"),   # Olde Port Beach (1km to station)
    ("oldhouse-cove",                         "8413320",  "noaa"),   # Oldhouse Cove (13km to station)
    ("olds-cove",                             "8638610",  "noaa"),   # Olds Cove (19km to station)
    ("olimpic-beach",                         "8761305",  "noaa"),   # Olimpic Beach (36km to station)
    ("oliver-inlet",                          "9452210",  "noaa"),   # Oliver Inlet (21km to station)
    ("olivers-hole",                          "8461490",  "noaa"),   # Olivers Hole (22km to station)
    ("olmstad-bay",                           "9075099",  "noaa"),   # Olmstad Bay (2km to station)
    ("olsen-bay",                             "9454050",  "noaa"),   # Olsen Bay (32km to station)
    ("ommaney-bay",                           "9451054",  "noaa"),   # Ommaney Bay (9km to station)
    ("oneloa-beach",                          "1615680",  "noaa"),   # Oneloa Beach (23km to station)
    ("oneuli-beach",                          "1615680",  "noaa"),   # One‘uli Beach (28km to station)
    ("onomea-bay",                            "1617760",  "noaa"),   # Onomea Bay (9km to station)
    ("opeechee-heights-beach",                "8447930",  "noaa"),   # Opeechee Heights Beach (31km to station)
    ("open-bay",                              "9450460",  "noaa"),   # Open Bay (20km to station)
    ("ophir-beach",                           "9431647",  "noaa"),   # Ophir Beach (23km to station)
    ("oppenheimer-beach",                     "9751381",  "noaa"),   # Oppenheimer Beach (7km to station)
    ("orca-bay",                              "9454050",  "noaa"),   # Orca Bay (25km to station)
    ("orchard-bay",                           "8311030",  "noaa"),   # Orchard Bay (27km to station)
    ("orchard-cove",                          "8635750",  "noaa"),   # Orchard Cove (26km to station)
    ("orchard-creek",                         "8570283",  "noaa"),   # Orchard Creek (10km to station)
    ("orel-anchorage",                        "9451054",  "noaa"),   # Orel Anchorage (37km to station)
    ("orient-harbor",                         "8510560",  "noaa"),   # Orient Harbor (31km to station)
    ("orrs-cove",                             "8418150",  "noaa"),   # Orrs Cove (33km to station)
    ("oscars-bay",                            "8311062",  "noaa"),   # Oscars Bay (20km to station)
    ("ossabaw-sound",                         "8670870",  "noaa"),   # Ossabaw Sound (24km to station)
    ("ostego-bay",                            "8725520",  "noaa"),   # Ostego Bay (25km to station)
    ("ostermayer-bayou",                      "8771972",  "noaa"),   # Ostermayer Bayou (14km to station)
    ("otis-beach",                            "8413320",  "noaa"),   # Otis Beach (36km to station)
    ("otis-cove",                             "8652587",  "noaa"),   # Otis Cove (22km to station)
    ("ottens-harbor",                         "8536110",  "noaa"),   # Ottens Harbor (12km to station)
    ("otter-bay",                             "9459450",  "noaa"),   # Otter Bay (31km to station)
    ("otter-cove",                            "8413320",  "noaa"),   # Otter Cove (9km to station)
    ("otter-creek",                           "9751381",  "noaa"),   # Otter Creek (5km to station)
    ("otter-creek-bay",                       "8311062",  "noaa"),   # Otter Creek Bay (1km to station)
    ("outer-harbor-entrance-channel",         "9414750",  "noaa"),   # Outer Harbor Entrance Channel (5km to station)
    ("outer-megansett-harbor",                "8447930",  "noaa"),   # Outer Megansett Harbor (15km to station)
    ("outlet-bay",                            "8632200",  "noaa"),   # Outlet Bay (27km to station)
    ("outside-beach",                         "9455500",  "noaa"),   # Outside Beach (2km to station)
    ("oval-beach",                            "9087031",  "noaa"),   # Oval Beach (12km to station)
    ("over-cove",                             "8413320",  "noaa"),   # Over Cove (24km to station)
    ("owen-beach",                            "9446484",  "noaa"),   # Owen Beach (10km to station)
    ("owen-park-beach",                       "8447930",  "noaa"),   # Owen Park Beach (9km to station)
    ("owens-bay",                             "8656483",  "noaa"),   # Owens Bay (35km to station)
    ("oxen-bayou",                            "8771486",  "noaa"),   # Oxen Bayou (6km to station)
    ("oxon-cove",                             "8594900",  "noaa"),   # Oxon Cove (7km to station)
    ("oyster-creek",                          "8575512",  "noaa"),   # Oyster Creek (6km to station)
    ("oyster-creek-gut",                      "8631044",  "noaa"),   # Oyster Creek Gut (37km to station)
    ("oyster-harbors-beach",                  "8447930",  "noaa"),   # Oyster Harbors Beach (23km to station)
    ("oyster-prong",                          "8721604",  "noaa"),   # Oyster Prong (18km to station)
    ("oyster-river-beach",                    "8465705",  "noaa"),   # Oyster River Beach (8km to station)
    ("pwea-beach",                            "8516945",  "noaa"),   # PWEA Beach (5km to station)
    ("pa-ma-waa",                             "1611400",  "noaa"),   # Pa Ma Waa (38km to station)
    ("pacquereau-bay",                        "9751381",  "noaa"),   # Pacquereau Bay (21km to station)
    ("paddy-bay",                             "8760721",  "noaa"),   # Paddy Bay (13km to station)
    ("paddy-biddle-cove",                     "8573927",  "noaa"),   # Paddy Biddle Cove (4km to station)
    ("paddy-creek",                           "8418150",  "noaa"),   # Paddy Creek (36km to station)
    ("paerdegat-basin",                       "8518750",  "noaa"),   # Paerdegat Basin (12km to station)
    ("pages-cove",                            "8465705",  "noaa"),   # Pages Cove (6km to station)
    ("pailleen-queue-pond",                   "8760721",  "noaa"),   # Pailleen Queue Pond (10km to station)
    ("paines-creek-beach",                    "8447435",  "noaa"),   # Paine's Creek Beach (16km to station)
    ("pains-bay",                             "8652587",  "noaa"),   # Pains Bay (35km to station)
    ("pakala",                                "1611400",  "noaa"),   # Pakala (28km to station)
    ("pakala-beach",                          "1611400",  "noaa"),   # Pakala Beach (31km to station)
    ("pakamoi",                               "1611400",  "noaa"),   # Pakamoi (8km to station)
    ("paki-bay",                              "1617760",  "noaa"),   # Paki Bay (14km to station)
    ("palauea-beach",                         "1615680",  "noaa"),   # Palauea Beach (25km to station)
    ("palm-tree-island",                      "8658163",  "noaa"),   # Palm Tree Island (2km to station)
    ("palma-sola-bay",                        "8726384",  "noaa"),   # Palma Sola Bay (20km to station)
    ("palmer-cove",                           "8461490",  "noaa"),   # Palmer Cove (9km to station)
    ("palmer-inlet",                          "8516945",  "noaa"),   # Palmer Inlet (6km to station)
    ("palmer-lake-shady-side",                "9446484",  "noaa"),   # Palmer Lake "Shady side" (29km to station)
    ("palmer-lake-sunny-side",                "9446484",  "noaa"),   # Palmer Lake "Sunny side" (29km to station)
    ("palmers-cove",                          "8635750",  "noaa"),   # Palmers Cove (26km to station)
    ("palomarin-beach",                       "9415020",  "noaa"),   # Palomarin Beach (21km to station)
    ("panama-city-beaches",                   "8729210",  "noaa"),   # Panama City Beaches (2km to station)
    ("papaa-bay",                             "1611400",  "noaa"),   # Papaa Bay (25km to station)
    ("paraplane-cove",                        "8632200",  "noaa"),   # Paraplane Cove (30km to station)
    ("paraquita-bay",                         "9751381",  "noaa"),   # Paraquita Bay (19km to station)
    ("parched-corn-bay",                      "8652587",  "noaa"),   # Parched Corn Bay (30km to station)
    ("parish-creek",                          "8575512",  "noaa"),   # Parish Creek (16km to station)
    ("park-creek",                            "8575512",  "noaa"),   # Park Creek (11km to station)
    ("park-east-on-leash-dog-beach",          "8729840",  "noaa"),   # Park East On-Leash Dog Beach (15km to station)
    ("park-lake",                             "8575512",  "noaa"),   # Park Lake (11km to station)
    ("park-west-on-leash-dog-beach",          "8729840",  "noaa"),   # Park West On-Leash Dog Beach (9km to station)
    ("parker-bayou",                          "8729108",  "noaa"),   # Parker Bayou (7km to station)
    ("parker-creek",                          "8575512",  "noaa"),   # Parker Creek (24km to station)
    ("parking-lot-beach",                     "9451054",  "noaa"),   # Parking Lot Beach (0km to station)
    ("parks-cove",                            "8516945",  "noaa"),   # Parks Cove (29km to station)
    ("parkwood-beach",                        "8447930",  "noaa"),   # Parkwood Beach (25km to station)
    ("parramore-beach",                       "8631044",  "noaa"),   # Parramore Beach (9km to station)
    ("parrit-cove",                           "8413320",  "noaa"),   # Parrit Cove (22km to station)
    ("parrot-bay",                            "9751381",  "noaa"),   # Parrot Bay (3km to station)
    ("parrotts-bay",                          "9052000",  "noaa"),   # Parrotts Bay (30km to station)
    ("parshas-bay",                           "9454050",  "noaa"),   # Parshas Bay (29km to station)
    ("parsonage-cove",                        "8516945",  "noaa"),   # Parsonage Cove (24km to station)
    ("parsons-bay",                           "8637689",  "noaa"),   # Parsons Bay (19km to station)
    ("parsons-bay-beach",                     "2695540",  "noaa"),   # Parsons Bay Beach (15km to station)
    ("parsons-beach",                         "8419870",  "noaa"),   # Parsons Beach (34km to station)
    ("partridge-cove",                        "8413320",  "noaa"),   # Partridge Cove (15km to station)
    ("party-cove",                            "9446484",  "noaa"),   # Party Cove (17km to station)
    ("pasa-a-grille-beach",                   "8726520",  "noaa"),   # Pasa A Grille Beach (14km to station)
    ("passeonkquis-cove",                     "8452944",  "noaa"),   # Passeonkquis Cove (5km to station)
    ("pasture-creek",                         "8656483",  "noaa"),   # Pasture Creek (28km to station)
    ("pasture-point-cove",                    "8557380",  "noaa"),   # Pasture Point Cove (23km to station)
    ("patrick-afb-beach",                     "8721604",  "noaa"),   # Patrick AFB Beach (19km to station)
    ("patricks-cove",                         "9014070",  "noaa"),   # Patricks Cove (21km to station)
    ("pats-bay",                              "8774230",  "noaa"),   # Pats Bay (17km to station)
    ("patten-bay",                            "8413320",  "noaa"),   # Patten Bay (24km to station)
    ("patten-cove",                           "8411060",  "noaa"),   # Patten Cove (27km to station)
    ("patterson-bay",                         "9451054",  "noaa"),   # Patterson Bay (36km to station)
    ("paukpahu",                              "1617760",  "noaa"),   # Paukūpahu (7km to station)
    ("paul-cove",                             "8571421",  "noaa"),   # Paul Cove (11km to station)
    ("paul-pond",                             "8760721",  "noaa"),   # Paul Pond (8km to station)
    ("pauls-beach",                           "8531680",  "noaa"),   # Paul's Beach (21km to station)
    ("pauoa-bay",                             "1617433",  "noaa"),   # Pauoa Bay (10km to station)
    ("pauwalu-harbor",                        "1615680",  "noaa"),   # Pauwalu Harbor (38km to station)
    ("pawpaw-cove",                           "8571892",  "noaa"),   # Pawpaw Cove (28km to station)
    ("pawpaw-hollow",                         "8577330",  "noaa"),   # Pawpaw Hollow (18km to station)
    ("pawtuxet-cove",                         "8454000",  "noaa"),   # Pawtuxet Cove (5km to station)
    ("payne-cove",                            "8447386",  "noaa"),   # Payne Cove (12km to station)
    ("paynes-creek",                          "8510560",  "noaa"),   # Paynes Creek (32km to station)
    ("paynes-pond",                           "9063085",  "noaa"),   # Paynes Pond (15km to station)
    ("peachorchard-cove",                     "8574680",  "noaa"),   # Peachorchard Cove (7km to station)
    ("peacocks-pocket",                       "8721604",  "noaa"),   # Peacocks Pocket (25km to station)
    ("pear-tree-cove",                        "8447930",  "noaa"),   # Pear Tree Cove (17km to station)
    ("pear-tree-point-cove",                  "8467150",  "noaa"),   # Pear Tree Point Cove (29km to station)
    ("pearl-basin",                           "8724580",  "noaa"),   # Pearl Basin (4km to station)
    ("pearl-bayou",                           "8729108",  "noaa"),   # Pearl Bayou (7km to station)
    ("pearl-harbor",                          "9452210",  "noaa"),   # Pearl Harbor (30km to station)
    ("pearson-creek",                         "8577330",  "noaa"),   # Pearson Creek (5km to station)
    ("pebble-cove",                           "8418150",  "noaa"),   # Pebble Cove (3km to station)
    ("pebbley-beach",                         "8465705",  "noaa"),   # Pebbley Beach (9km to station)
    ("pebbly-beach",                          "8510560",  "noaa"),   # Pebbly Beach (37km to station)
    ("peck-bay",                              "8534720",  "noaa"),   # Peck Bay (20km to station)
    ("peck-beach",                            "8534720",  "noaa"),   # Peck Beach (21km to station)
    ("peckham-beach",                         "8452660",  "noaa"),   # Peckham Beach (8km to station)
    ("peckhams-pond",                         "8447930",  "noaa"),   # Peckhams Pond (20km to station)
    ("peeks-creek",                           "8570283",  "noaa"),   # Peeks Creek (11km to station)
    ("pejuan-cove",                           "8725520",  "noaa"),   # Pejuan Cove (35km to station)
    ("pelham-bay",                            "8516945",  "noaa"),   # Pelham Bay (7km to station)
    ("pelican-beach",                         "9751381",  "noaa"),   # Pelican Beach (13km to station)
    ("pelican-cove",                          "8726607",  "noaa"),   # Pelican Cove (14km to station)
    ("pelican-cove-beach",                    "9751364",  "noaa"),   # Pelican Cove Beach (4km to station)
    ("pelican-harbor",                        "9452634",  "noaa"),   # Pelican Harbor (27km to station)
    ("pelican-north-beach",                   "9415020",  "noaa"),   # Pelican North Beach (22km to station)
    ("pelican-state-beach",                   "9419750",  "noaa"),   # Pelican State Beach (28km to station)
    ("pendills-bay",                          "9076070",  "noaa"),   # Pendills Bay (34km to station)
    ("penfield-beach",                        "8467150",  "noaa"),   # Penfield Beach (7km to station)
    ("pentagon-lagoon-yacht-basin",           "8594900",  "noaa"),   # Pentagon Lagoon Yacht Basin (2km to station)
    ("peos-bay",                              "9052000",  "noaa"),   # Peos Bay (8km to station)
    ("pepper-grove-cove",                     "8771341",  "noaa"),   # Pepper Grove Cove (12km to station)
    ("perch-bay",                             "8311030",  "noaa"),   # Perch Bay (15km to station)
    ("perch-cove",                            "8534720",  "noaa"),   # Perch Cove (11km to station)
    ("perdido-bay",                           "8729840",  "noaa"),   # Perdido Bay (24km to station)
    ("pereira-cove",                          "9415102",  "noaa"),   # Pereira Cove (13km to station)
    ("perico-bayou",                          "8726384",  "noaa"),   # Perico Bayou (18km to station)
    ("perkins-beach",                         "9063063",  "noaa"),   # Perkins Beach (11km to station)
    ("perkins-cove",                          "8419870",  "noaa"),   # Perkins Cove (21km to station)
    ("perles-beach",                          "9414290",  "noaa"),   # Perles Beach (6km to station)
    ("perry-cove",                            "8575512",  "noaa"),   # Perry Cove (16km to station)
    ("perseverance-bay",                      "9751381",  "noaa"),   # Perseverance Bay (28km to station)
    ("pershing-cove",                         "8557380",  "noaa"),   # Pershing Cove (23km to station)
    ("peshtigo-harbor",                       "9087088",  "noaa"),   # Peshtigo Harbor (14km to station)
    ("pest-house-shore",                      "8449130",  "noaa"),   # Pest House Shore (2km to station)
    ("petegrow-cove",                         "8411060",  "noaa"),   # Petegrow Cove (15km to station)
    ("peter-bay",                             "9751381",  "noaa"),   # Peter Bay (6km to station)
    ("peter-bay-beach",                       "9751381",  "noaa"),   # Peter Bay Beach (5km to station)
    ("peter-cove",                            "8418150",  "noaa"),   # Peter Cove (20km to station)
    ("peter-tuckers-bay",                     "2695540",  "noaa"),   # Peter Tucker's Bay (13km to station)
    ("petermans-basin",                       "8729840",  "noaa"),   # Petermans Basin (18km to station)
    ("peters-cove",                           "8575512",  "noaa"),   # Peters Cove (2km to station)
    ("peters-ditch",                          "8654467",  "noaa"),   # Peters Ditch (24km to station)
    ("peters-pond-at-oakcrest-cove-beach",    "8447930",  "noaa"),   # Peters Pond at Oakcrest Cove Beach (24km to station)
    ("peterson-bay",                          "9455500",  "noaa"),   # Peterson Bay (29km to station)
    ("peterson-bayou",                        "8726384",  "noaa"),   # Peterson Bayou (10km to station)
    ("petit-felix-pond",                      "8760721",  "noaa"),   # Petit Felix Pond (7km to station)
    ("petrof-bay",                            "9451054",  "noaa"),   # Petrof Bay (40km to station)
    ("pettaquamscutt-cove",                   "8452660",  "noaa"),   # Pettaquamscutt Cove (13km to station)
    ("pettegrow-beach",                       "8411060",  "noaa"),   # Pettegrow Beach (13km to station)
    ("pettes-cove-beach",                     "8410140",  "noaa"),   # Pettes Cove Beach (25km to station)
    ("pettys-bayou",                          "9087031",  "noaa"),   # Pettys Bayou (35km to station)
    ("pettys-bight",                          "8461490",  "noaa"),   # Pettys Bight (28km to station)
    ("pettys-pond",                           "8651370",  "noaa"),   # Pettys Pond (7km to station)
    ("pea-blanca",                            "9759394",  "noaa"),   # Peña Blanca (28km to station)
    ("philbricks-beach",                      "8419870",  "noaa"),   # Philbricks Beach (12km to station)
    ("philips-inlet",                         "8729210",  "noaa"),   # Philips Inlet (12km to station)
    ("phillip-burton-memorial-beach",         "9414290",  "noaa"),   # Phillip Burton Memorial Beach (12km to station)
    ("phillips-cove",                         "8419870",  "noaa"),   # Phillips Cove (19km to station)
    ("phipps-cove",                           "8654467",  "noaa"),   # Phipps Cove (32km to station)
    ("phocana-bay",                           "9450460",  "noaa"),   # Phocana Bay (20km to station)
    ("pickeral-cove",                         "8413320",  "noaa"),   # Pickeral Cove (36km to station)
    ("pickerel-cove",                         "8447930",  "noaa"),   # Pickerel Cove (22km to station)
    ("pickett-bay",                           "8761724",  "noaa"),   # Pickett Bay (30km to station)
    ("pickleweed-inlet",                      "9414290",  "noaa"),   # Pickleweed Inlet (11km to station)
    ("picnic-harbor",                         "9455500",  "noaa"),   # Picnic Harbor (26km to station)
    ("picnic-island-beach",                   "8726607",  "noaa"),   # Picnic Island Beach (1km to station)
    ("pico-beach",                            "8447930",  "noaa"),   # Pico Beach (18km to station)
    ("pier-4-beach",                          "8518750",  "noaa"),   # Pier 4 Beach (1km to station)
    ("pierce-beach",                          "8447386",  "noaa"),   # Pierce Beach (7km to station)
    ("pierce-creek",                          "8656483",  "noaa"),   # Pierce Creek (36km to station)
    ("pierle-bay",                            "8761724",  "noaa"),   # Pierle Bay (32km to station)
    ("pierson-cove",                          "8537121",  "noaa"),   # Pierson Cove (9km to station)
    ("pig-bayou",                             "8728690",  "noaa"),   # Pig Bayou (38km to station)
    ("pigeon-cove",                           "9075099",  "noaa"),   # Pigeon Cove (7km to station)
    ("pigeon-hill-bay",                       "8413320",  "noaa"),   # Pigeon Hill Bay (26km to station)
    ("pigeon-hill-cove",                      "8413320",  "noaa"),   # Pigeon Hill Cove (26km to station)
    ("pigeon-river-bay",                      "9075080",  "noaa"),   # Pigeon River Bay (38km to station)
    ("pigeonhouse-creek",                     "8571421",  "noaa"),   # Pigeonhouse Creek (15km to station)
    ("pilale-bay",                            "1615680",  "noaa"),   # Pilale Bay (22km to station)
    ("pilchard-bay",                          "2695540",  "noaa"),   # Pilchard Bay (20km to station)
    ("piledriver-cove",                       "9452210",  "noaa"),   # Piledriver Cove (31km to station)
    ("pileriver-cove",                        "9452210",  "noaa"),   # Pileriver Cove (32km to station)
    ("pillar-point-harbor-beach",             "9414523",  "noaa"),   # Pillar Point Harbor Beach (23km to station)
    ("pilot-cove",                            "9075099",  "noaa"),   # Pilot Cove (31km to station)
    ("pilot-harbor",                          "8728690",  "noaa"),   # Pilot Harbor (25km to station)
    ("pine-creek-bay",                        "9087031",  "noaa"),   # Pine Creek Bay (6km to station)
    ("pine-island-bay",                       "8651370",  "noaa"),   # Pine Island Bay (7km to station)
    ("pine-island-pond",                      "8447930",  "noaa"),   # Pine Island Pond (16km to station)
    ("pine-island-sound",                     "8725520",  "noaa"),   # Pine Island Sound (30km to station)
    ("pine-key-bight",                        "8723970",  "noaa"),   # Pine Key Bight (25km to station)
    ("pineapple-beach",                       "9751381",  "noaa"),   # Pineapple Beach (16km to station)
    ("pines-lake-west-beach",                 "8518750",  "noaa"),   # Pines Lake West Beach (39km to station)
    ("pines-on-the-severn-community-beach",   "8575512",  "noaa"),   # Pines on the Severn Community Beach (5km to station)
    ("piney-cove",                            "8573364",  "noaa"),   # Piney Cove (20km to station)
    ("piney-creek",                           "8575512",  "noaa"),   # Piney Creek (19km to station)
    ("piney-creek-cove",                      "8573927",  "noaa"),   # Piney Creek Cove (10km to station)
    ("piney-island-bay",                      "8656483",  "noaa"),   # Piney Island Bay (34km to station)
    ("piney-island-cove",                     "8571421",  "noaa"),   # Piney Island Cove (4km to station)
    ("piney-neck-cove",                       "8577330",  "noaa"),   # Piney Neck Cove (22km to station)
    ("piney-point-beach",                     "8635750",  "noaa"),   # Piney Point Beach (16km to station)
    ("piney-point-creek",                     "8635750",  "noaa"),   # Piney Point Creek (18km to station)
    ("pinham-bay",                            "9751364",  "noaa"),   # Pinham Bay (8km to station)
    ("pink-beach---east-beach",               "2695535",  "noaa"),   # Pink Beach - East Beach (6km to station)
    ("pink-beach---west-beach",               "2695535",  "noaa"),   # Pink Beach - West Beach (6km to station)
    ("pink-house-cove",                       "8465705",  "noaa"),   # Pink House Cove (18km to station)
    ("pink-shack-cove",                       "8775283",  "noaa"),   # Pink Shack Cove (9km to station)
    ("pinkham-bay",                           "8413320",  "noaa"),   # Pinkham Bay (25km to station)
    ("pinnacle-cove",                         "9413450",  "noaa"),   # Pinnacle Cove (11km to station)
    ("pinquickset-cove",                      "8447930",  "noaa"),   # Pinquickset Cove (20km to station)
    ("pint-cove",                             "8419870",  "noaa"),   # Pint Cove (17km to station)
    ("pinta-cove",                            "9452634",  "noaa"),   # Pinta Cove (35km to station)
    ("pintail-pond",                          "8760721",  "noaa"),   # Pintail Pond (5km to station)
    ("pioneer-square-habitat-beach",          "9446484",  "noaa"),   # Pioneer Square Habitat Beach (38km to station)
    ("pipe-bay",                              "8761724",  "noaa"),   # Pipe Bay (22km to station)
    ("pipes-cove",                            "8510560",  "noaa"),   # Pipes Cove (35km to station)
    ("pirate-cove",                           "9435380",  "noaa"),   # Pirate Cove (22km to station)
    ("pirates-cove",                          "9451600",  "noaa"),   # Pirate's Cove (8km to station)
    ("pirateland-beach",                      "8661070",  "noaa"),   # Pirateland Beach (3km to station)
    ("pirates-cove-beach",                    "8419870",  "noaa"),   # Pirates Cove Beach (6km to station)
    ("pirates-beach",                         "8771486",  "noaa"),   # Pirates' Beach (12km to station)
    ("pistachio-beach",                       "9414523",  "noaa"),   # Pistachio Beach (39km to station)
    ("pitman-cove",                           "8635750",  "noaa"),   # Pitman Cove (35km to station)
    ("pitman-creek",                          "8656483",  "noaa"),   # Pitman Creek (33km to station)
    ("pitts-bay",                             "2695540",  "noaa"),   # Pitts Bay (12km to station)
    ("placid-et-al-state-number-1",           "9497645",  "noaa"),   # Placid Et Al State Number 1 (21km to station)
    ("placido-bayou",                         "8726520",  "noaa"),   # Placido Bayou (6km to station)
    ("plaice-cove",                           "8419870",  "noaa"),   # Plaice Cove (15km to station)
    ("plaice-cove-beach",                     "8419870",  "noaa"),   # Plaice Cove Beach (15km to station)
    ("planner-cove",                          "8631044",  "noaa"),   # Planner Cove (37km to station)
    ("planting-island-cove",                  "8447930",  "noaa"),   # Planting Island Cove (20km to station)
    ("plashes-pond",                          "8447435",  "noaa"),   # Plashes Pond (23km to station)
    ("platers-cove",                          "8571892",  "noaa"),   # Platers Cove (20km to station)
    ("playa-almirante",                       "9759394",  "noaa"),   # Playa Almirante (9km to station)
    ("playa-baha-salinas",                    "9759110",  "noaa"),   # Playa Bahía Salinas (16km to station)
    ("playa-ballena",                         "9759110",  "noaa"),   # Playa Ballena (19km to station)
    ("playa-black-eagle",                     "9759394",  "noaa"),   # Playa Black Eagle (17km to station)
    ("playa-blanca",                          "9753216",  "noaa"),   # Playa Blanca (15km to station)
    ("playa-bramadero",                       "9759394",  "noaa"),   # Playa Bramadero (6km to station)
    ("playa-buy",                             "9759110",  "noaa"),   # Playa Buyé (18km to station)
    ("playa-canalejo",                        "9753216",  "noaa"),   # Playa Canalejo (5km to station)
    ("playa-caracas",                         "9752695",  "noaa"),   # Playa Caracas (6km to station)
    ("playa-carlos-rosario",                  "9752235",  "noaa"),   # Playa Carlos Rosario (4km to station)
    ("playa-cayo-caribe",                     "9759110",  "noaa"),   # Playa Cayo Caribe (33km to station)
    ("playa-cayo-maria-langa",                "9759110",  "noaa"),   # Playa Cayo Maria Langa (31km to station)
    ("playa-cayo-norte",                      "9752235",  "noaa"),   # Playa Cayo Norte (6km to station)
    ("playa-chica-playa-rompeolas",           "9759394",  "noaa"),   # Playa Chica (Playa Rompeolas) (24km to station)
    ("playa-chiva",                           "9752695",  "noaa"),   # Playa Chiva (9km to station)
    ("playa-color",                           "9753216",  "noaa"),   # Playa Colorá (5km to station)
    ("playa-combate",                         "9759110",  "noaa"),   # Playa Combate (18km to station)
    ("playa-culebrita",                       "9752235",  "noaa"),   # Playa Culebrita (8km to station)
    ("playa-crcega",                          "9759394",  "noaa"),   # Playa Córcega (14km to station)
    ("playa-dienero",                         "9752235",  "noaa"),   # Playa Dienero (2km to station)
    ("playa-domes",                           "9759394",  "noaa"),   # Playa Domes (20km to station)
    ("playa-el-convento",                     "9753216",  "noaa"),   # Playa El Convento (4km to station)
    ("playa-el-espinar",                      "9759394",  "noaa"),   # Playa El Espinar (21km to station)
    ("playa-el-man",                          "9759394",  "noaa"),   # Playa El Maní (2km to station)
    ("playa-el-mojn-tranquilo",               "9759110",  "noaa"),   # Playa El Mojón Tranquilo (10km to station)
    ("playa-el-negro",                        "9752695",  "noaa"),   # Playa El Negro (39km to station)
    ("playa-el-pastillo",                     "9759394",  "noaa"),   # Playa El Pastillo (36km to station)
    ("playa-el-tuque",                        "9759110",  "noaa"),   # Playa El Tuque (39km to station)
    ("playa-escondida",                       "9752695",  "noaa"),   # Playa Escondida (10km to station)
    ("playa-esperanza",                       "9752695",  "noaa"),   # Playa Esperanza (0km to station)
    ("playa-espinar",                         "9759394",  "noaa"),   # Playa Espinar (20km to station)
    ("playa-flamenco",                        "9752235",  "noaa"),   # Playa Flamenco (4km to station)
    ("playa-garca",                           "9752695",  "noaa"),   # Playa García (6km to station)
    ("playa-grande",                          "9752695",  "noaa"),   # Playa Grande (12km to station)
    ("playa-guayans",                         "9753216",  "noaa"),   # Playa Guayanés (36km to station)
    ("playa-icacos",                          "9753216",  "noaa"),   # Playa Icacos (7km to station)
    ("playa-india-el-natural",                "9759394",  "noaa"),   # Playa India (El Natural) (27km to station)
    ("playa-isla-guilligan",                  "9759110",  "noaa"),   # Playa Isla Guilligan (18km to station)
    ("playa-isla-verde",                      "9755371",  "noaa"),   # Playa Isla Verde (10km to station)
    ("playa-jaboncillo",                      "9759110",  "noaa"),   # Playa Jaboncillo (15km to station)
    ("playa-joyuda",                          "9759394",  "noaa"),   # Playa Joyuda (12km to station)
    ("playa-la-ceiba",                        "9752695",  "noaa"),   # Playa La Ceiba (6km to station)
    ("playa-la-puente",                       "9759394",  "noaa"),   # Playa La Puente (5km to station)
    ("playa-la-puntilla",                     "9755371",  "noaa"),   # Playa La Puntilla (0km to station)
    ("playa-la-ruina",                        "9759394",  "noaa"),   # Playa La Ruina (30km to station)
    ("playa-la-ventana",                      "9759110",  "noaa"),   # Playa La Ventana (25km to station)
    ("playa-laguna",                          "9759394",  "noaa"),   # Playa Laguna (9km to station)
    ("playa-las-80",                          "9753216",  "noaa"),   # Playa Las 80 (26km to station)
    ("playa-las-pardas",                      "9759110",  "noaa"),   # Playa Las Pardas (13km to station)
    ("playa-los-machos",                      "9753216",  "noaa"),   # Playa Los Machos (8km to station)
    ("playa-los-pozos",                       "9759110",  "noaa"),   # Playa Los Pozos (16km to station)
    ("playa-los-tubos",                       "9755371",  "noaa"),   # Playa Los Tubos (36km to station)
    ("playa-luis-pea",                        "9752235",  "noaa"),   # Playa Luis Peña (3km to station)
    ("playa-manzanilla",                      "9752235",  "noaa"),   # Playa Manzanilla (5km to station)
    ("playa-mar-chiquita",                    "9755371",  "noaa"),   # Playa Mar Chiquita (39km to station)
    ("playa-mara",                            "9759394",  "noaa"),   # Playa María (19km to station)
    ("playa-media-luna",                      "9752695",  "noaa"),   # Playa Media Luna (2km to station)
    ("playa-medio-mundo",                     "9753216",  "noaa"),   # Playa Medio Mundo (9km to station)
    ("playa-melones",                         "9752235",  "noaa"),   # Playa Melones (1km to station)
    ("playa-moja-casabe",                     "9759110",  "noaa"),   # Playa Moja Casabe (18km to station)
    ("playa-montones",                        "9759394",  "noaa"),   # Playa Montones (34km to station)
    ("playa-mosquito",                        "9752235",  "noaa"),   # Playa Mosquito (4km to station)
    ("playa-navo",                            "9752695",  "noaa"),   # Playa Navío (3km to station)
    ("playa-novillo",                         "9752695",  "noaa"),   # Playa Novillo (4km to station)
    ("playa-ocean-park",                      "9755371",  "noaa"),   # Playa Ocean Park (6km to station)
    ("playa-pea",                             "9755371",  "noaa"),   # Playa Peña (2km to station)
    ("playa-pine-grove",                      "9755371",  "noaa"),   # Playa Pine Grove (11km to station)
    ("playa-pools",                           "9759394",  "noaa"),   # Playa Pools (20km to station)
    ("playa-prieta",                          "9752695",  "noaa"),   # Playa Prieta (8km to station)
    ("playa-punta-arenas",                    "9759394",  "noaa"),   # Playa Punta Arenas (9km to station)
    ("playa-punta-higero",                    "9759394",  "noaa"),   # Playa Punta Higüero (19km to station)
    ("playa-pblica",                          "9755371",  "noaa"),   # Playa Pública (20km to station)
    ("playa-resaca",                          "9752235",  "noaa"),   # Playa Resaca (4km to station)
    ("playa-rosada",                          "9759110",  "noaa"),   # Playa Rosada (2km to station)
    ("playa-salinas",                         "9759110",  "noaa"),   # Playa Salinas (15km to station)
    ("playa-san-juan-leighton",               "9410840",  "noaa"),   # Playa San Juan Leighton (35km to station)
    ("playa-santa",                           "9759110",  "noaa"),   # Playa Santa (10km to station)
    ("playa-sardinera",                       "9759938",  "noaa"),   # Playa Sardinera (1km to station)
    ("playa-steps",                           "9759394",  "noaa"),   # Playa Steps (18km to station)
    ("playa-sun-bay",                         "9752695",  "noaa"),   # Playa Sun Bay (1km to station)
    ("playa-tamarindo",                       "9752235",  "noaa"),   # Playa Tamarindo (2km to station)
    ("playa-tampico",                         "9752235",  "noaa"),   # Playa Tampico (1km to station)
    ("playa-teresa",                          "9752695",  "noaa"),   # Playa Teresa (39km to station)
    ("playa-tortola",                         "9752235",  "noaa"),   # Playa Tortola (5km to station)
    ("playa-tortuga",                         "9752235",  "noaa"),   # Playa Tortuga (8km to station)
    ("playa-uvero",                           "9759938",  "noaa"),   # Playa Uvero (5km to station)
    ("playa-vaca-talega",                     "9755371",  "noaa"),   # Playa Vacía Talega (22km to station)
    ("playa-zon",                             "9752235",  "noaa"),   # Playa Zoní (5km to station)
    ("playa-de-cascajo",                      "9752235",  "noaa"),   # Playa de Cascajo (1km to station)
    ("playa-de-guayanilla",                   "9759110",  "noaa"),   # Playa de Guayanilla (29km to station)
    ("playa-de-levittown",                    "9755371",  "noaa"),   # Playa de Levittown (6km to station)
    ("playa-de-tamarindo",                    "9759110",  "noaa"),   # Playa de Tamarindo (21km to station)
    ("playa-de-vega",                         "9755371",  "noaa"),   # Playa de Vega (29km to station)
    ("playa-de-las-tres-palmitas",            "9755371",  "noaa"),   # Playa de las Tres Palmitas (19km to station)
    ("playa-de-los-tocones",                  "9755371",  "noaa"),   # Playa de los Tocones (22km to station)
    ("playa-del-caribe-hilton",               "9755371",  "noaa"),   # Playa del Caribe Hilton (3km to station)
    ("playa-ltimo-trolley",                   "9755371",  "noaa"),   # Playa Último Trolley (7km to station)
    ("playalinda-beach-nudist-area",          "8721604",  "noaa"),   # Playalinda Beach (Nudist Area) (33km to station)
    ("playita-del-condado",                   "9755371",  "noaa"),   # Playita del Condado (5km to station)
    ("playpen",                               "9415144",  "noaa"),   # Playpen (22km to station)
    ("pleasant-road-beach",                   "8447435",  "noaa"),   # Pleasant Road Beach (13km to station)
    ("pleasure-beach",                        "8467150",  "noaa"),   # Pleasure Beach (2km to station)
    ("plum-bank-beach",                       "8461490",  "noaa"),   # Plum Bank Beach (27km to station)
    ("plummers-cove",                         "8720219",  "noaa"),   # Plummers Cove (23km to station)
    ("poolenalena-beach",                     "1615680",  "noaa"),   # Po'olenalena Beach (26km to station)
    ("pobblestone-cove",                      "8411060",  "noaa"),   # Pobblestone Cove (31km to station)
    ("pocahontas-creek",                      "8575512",  "noaa"),   # Pocahontas Creek (8km to station)
    ("pocha-pond",                            "8447930",  "noaa"),   # Pocha Pond (26km to station)
    ("pochet-creek-poshee",                   "8447435",  "noaa"),   # Pochet Creek (Poshee) (10km to station)
    ("pocita-de-piones",                      "9755371",  "noaa"),   # Pocita de Piñones (16km to station)
    ("pocket-beach",                          "9441102",  "noaa"),   # Pocket Beach (24km to station)
    ("pocomoke-sound",                        "8631044",  "noaa"),   # Pocomoke Sound (30km to station)
    ("poelua-bay",                            "1615680",  "noaa"),   # Poelua Bay (18km to station)
    ("poggy-bay",                             "8461490",  "noaa"),   # Poggy Bay (12km to station)
    ("pohakumanu-bay",                        "1617760",  "noaa"),   # Pohakumanu Bay (16km to station)
    ("pohoiki-bay",                           "1617760",  "noaa"),   # Pohoiki Bay (38km to station)
    ("point-aux-chenes-bay",                  "8741533",  "noaa"),   # Point Aux Chenes Bay (13km to station)
    ("point-bay",                             "2695540",  "noaa"),   # Point Bay (20km to station)
    ("point-beach",                           "8465705",  "noaa"),   # Point Beach (13km to station)
    ("point-breeze-beach",                    "9063020",  "noaa"),   # Point Breeze Beach (32km to station)
    ("point-judith-harbor-of-refuge",         "8452660",  "noaa"),   # Point Judith Harbor of Refuge (22km to station)
    ("point-lookout-creek",                   "8635750",  "noaa"),   # Point Lookout Creek (12km to station)
    ("point-molate-beach",                    "9414863",  "noaa"),   # Point Molate Beach (2km to station)
    ("point-sal-beach",                       "9412110",  "noaa"),   # Point Sal Beach (32km to station)
    ("point-san-pablo-yacht-harbor",          "9414863",  "noaa"),   # Point San Pablo Yacht Harbor (4km to station)
    ("point-of-grass-creek",                  "8656483",  "noaa"),   # Point of Grass Creek (39km to station)
    ("point-of-island-bay",                   "8656483",  "noaa"),   # Point of Island Bay (39km to station)
    ("point-of-rocks-landing-beach",          "8447435",  "noaa"),   # Point of Rocks Landing Beach (14km to station)
    ("pointe-a-la-hache-boat-harbor",         "8761305",  "noaa"),   # Pointe A La Hache Boat Harbor (35km to station)
    ("pointe-aux-chenes-bay",                 "9075080",  "noaa"),   # Pointe aux Chenes Bay (21km to station)
    ("pokegama-bay",                          "9099064",  "noaa"),   # Pokegama Bay (11km to station)
    ("pokey-dutch",                           "8747437",  "noaa"),   # Pokey Dutch (23km to station)
    ("polecat-bay",                           "8737048",  "noaa"),   # Polecat Bay (2km to station)
    ("polecat-bend",                          "8747437",  "noaa"),   # Polecat Bend (28km to station)
    ("policemens-cove",                       "8418150",  "noaa"),   # Policemen's Cove (29km to station)
    ("pollet-bay",                            "9014070",  "noaa"),   # Pollet Bay (13km to station)
    ("polo-beach",                            "1615680",  "noaa"),   # Polo Beach (24km to station)
    ("pololu-beach",                          "1617433",  "noaa"),   # Pololu Beach (21km to station)
    ("pomeroy-cove",                          "8419870",  "noaa"),   # Pomeroy Cove (9km to station)
    ("pond-bay",                              "9751381",  "noaa"),   # Pond Bay (5km to station)
    ("pond-cove",                             "8411060",  "noaa"),   # Pond Cove (23km to station)
    ("pond-creek",                            "8571421",  "noaa"),   # Pond Creek (34km to station)
    ("pond-point-beach",                      "8465705",  "noaa"),   # Pond Point Beach (13km to station)
    ("pone-cove",                             "8571421",  "noaa"),   # Pone Cove (6km to station)
    ("pontoon-bay",                           "8725520",  "noaa"),   # Pontoon Bay (18km to station)
    ("poorhouse-cove",                        "8639348",  "noaa"),   # Poorhouse Cove (23km to station)
    ("pope-bay",                              "8570283",  "noaa"),   # Pope Bay (34km to station)
    ("popes-creek",                           "8635027",  "noaa"),   # Popes Creek (19km to station)
    ("popham-creek",                          "8575512",  "noaa"),   # Popham Creek (15km to station)
    ("popilleau-bay",                         "9751381",  "noaa"),   # Popilleau Bay (4km to station)
    ("poplar-branch-bay",                     "8651370",  "noaa"),   # Poplar Branch Bay (13km to station)
    ("poplar-cove",                           "8631044",  "noaa"),   # Poplar Cove (16km to station)
    ("poplar-tree-bay",                       "9052000",  "noaa"),   # Poplar Tree Bay (4km to station)
    ("popplestone-cove",                      "8411060",  "noaa"),   # Popplestone Cove (36km to station)
    ("porcupine-bay",                         "9452634",  "noaa"),   # Porcupine Bay (40km to station)
    ("poropotank-bay",                        "8637689",  "noaa"),   # Poropotank Bay (31km to station)
    ("porpoise-bay",                          "8760721",  "noaa"),   # Porpoise Bay (12km to station)
    ("porpoise-cove",                         "8418150",  "noaa"),   # Porpoise Cove (37km to station)
    ("porpoise-harbor",                       "9459450",  "noaa"),   # Porpoise Harbor (33km to station)
    ("porretto-beach",                        "8771450",  "noaa"),   # Porretto Beach (2km to station)
    ("port-alexander",                        "9451054",  "noaa"),   # Port Alexander (0km to station)
    ("port-althorp",                          "9452634",  "noaa"),   # Port Althorp (4km to station)
    ("port-aransas-pass",                     "8775241",  "noaa"),   # Port Aransas Pass (1km to station)
    ("port-armstrong",                        "9451054",  "noaa"),   # Port Armstrong (5km to station)
    ("port-clinton-public-swimming-beach",    "9063079",  "noaa"),   # Port Clinton Public Swimming Beach (17km to station)
    ("port-conclusion",                       "9451054",  "noaa"),   # Port Conclusion (3km to station)
    ("port-everglades",                       "8722956",  "noaa"),   # Port Everglades (1km to station)
    ("port-fidalgo",                          "9454240",  "noaa"),   # Port Fidalgo (37km to station)
    ("port-graham",                           "9455500",  "noaa"),   # Port Graham (11km to station)
    ("port-gravina",                          "9454050",  "noaa"),   # Port Gravina (31km to station)
    ("port-herbert",                          "9451054",  "noaa"),   # Port Herbert (21km to station)
    ("port-johnson",                          "9450460",  "noaa"),   # Port Johnson (32km to station)
    ("port-krestof",                          "9451600",  "noaa"),   # Port Krestof (18km to station)
    ("port-lucy",                             "9451054",  "noaa"),   # Port Lucy (9km to station)
    ("port-malmesbury",                       "9451054",  "noaa"),   # Port Malmesbury (34km to station)
    ("port-mary",                             "9451600",  "noaa"),   # Port Mary (27km to station)
    ("port-mcarthur",                         "9451054",  "noaa"),   # Port McArthur (38km to station)
    ("port-moller",                           "9463502",  "noaa"),   # Port Moller (12km to station)
    ("port-mulgrave",                         "9453220",  "noaa"),   # Port Mulgrave (4km to station)
    ("port-newark",                           "8518750",  "noaa"),   # Port Newark (10km to station)
    ("port-royal-cove-beach",                 "2695540",  "noaa"),   # Port Royal Cove Beach (18km to station)
    ("port-sunlight-beach",                   "8577330",  "noaa"),   # Port Sunlight Beach (27km to station)
    ("port-valdez",                           "9454240",  "noaa"),   # Port Valdez (8km to station)
    ("port-walter",                           "9451054",  "noaa"),   # Port Walter (16km to station)
    ("porter-creek",                          "8575512",  "noaa"),   # Porter Creek (28km to station)
    ("portersville-bay",                      "8735180",  "noaa"),   # Portersville Bay (20km to station)
    ("portlock-harbour",                      "9076024",  "noaa"),   # Portlock Harbour (24km to station)
    ("portobago-bay",                         "8635027",  "noaa"),   # Portobago Bay (21km to station)
    ("ports-harbor",                          "8413320",  "noaa"),   # Ports Harbor (40km to station)
    ("portsmouth-harbor",                     "8419870",  "noaa"),   # Portsmouth Harbor (2km to station)
    ("portsmouth-olympic-harbour",            "9052000",  "noaa"),   # Portsmouth Olympic Harbour (18km to station)
    ("portuguese-bend",                       "9410840",  "noaa"),   # Portuguese Bend (33km to station)
    ("post-cove",                             "8461490",  "noaa"),   # Post Cove (27km to station)
    ("post-pond",                             "8760721",  "noaa"),   # Post Pond (9km to station)
    ("posten-bayou",                          "8729108",  "noaa"),   # Posten Bayou (7km to station)
    ("postle-cove",                           "8637689",  "noaa"),   # Postle Cove (31km to station)
    ("pot-cove",                              "8518750",  "noaa"),   # Pot Cove (11km to station)
    ("pot-nets-cove",                         "8557380",  "noaa"),   # Pot Nets Cove (19km to station)
    ("potagannissing-bay",                    "9075099",  "noaa"),   # Potagannissing Bay (6km to station)
    ("potato-pond",                           "8760721",  "noaa"),   # Potato Pond (11km to station)
    ("pottawattomie-bayou",                   "9087031",  "noaa"),   # Pottawattomie Bayou (29km to station)
    ("potter-cove",                           "8461490",  "noaa"),   # Potter Cove (21km to station)
    ("potters-pond",                          "9063085",  "noaa"),   # Potters Pond (15km to station)
    ("potts-harbor",                          "8418150",  "noaa"),   # Potts Harbor (19km to station)
    ("pounders-beach",                        "1612480",  "noaa"),   # Pounders Beach (26km to station)
    ("poupard-bay",                           "9075080",  "noaa"),   # Poupard Bay (16km to station)
    ("poverty-bay",                           "9075080",  "noaa"),   # Poverty Bay (35km to station)
    ("poverty-island-beach",                  "8461490",  "noaa"),   # Poverty Island Beach (22km to station)
    ("powell-bay",                            "9751364",  "noaa"),   # Powell Bay (9km to station)
    ("powell-cove",                           "8516945",  "noaa"),   # Powell Cove (6km to station)
    ("powells-bay",                           "8631044",  "noaa"),   # Powells Bay (36km to station)
    ("power-lake",                            "8774230",  "noaa"),   # Power Lake (18km to station)
    ("powers-landing",                        "8447435",  "noaa"),   # Powers Landing (28km to station)
    ("pratt-bayou",                           "8729108",  "noaa"),   # Pratt Bayou (6km to station)
    ("pratt-cove",                            "8461490",  "noaa"),   # Pratt Cove (28km to station)
    ("pratts-beach",                          "8516945",  "noaa"),   # Pratts Beach (13km to station)
    ("preacher-hole",                         "8727520",  "noaa"),   # Preacher Hole (11km to station)
    ("preble-cove",                           "8413320",  "noaa"),   # Preble Cove (16km to station)
    ("prentiss-bay",                          "9075099",  "noaa"),   # Prentiss Bay (24km to station)
    ("president-bay",                         "9451600",  "noaa"),   # President Bay (30km to station)
    ("pressure-point",                        "9759394",  "noaa"),   # Pressure Point (29km to station)
    ("preston-cove",                          "9052000",  "noaa"),   # Preston Cove (28km to station)
    ("pretty-marsh-harbor",                   "8413320",  "noaa"),   # Pretty Marsh Harbor (18km to station)
    ("price-bend",                            "8467150",  "noaa"),   # Price Bend (33km to station)
    ("price-cove",                            "8635750",  "noaa"),   # Price Cove (16km to station)
    ("price-inlet",                           "8665530",  "noaa"),   # Price Inlet (28km to station)
    ("prices-cove",                           "8571892",  "noaa"),   # Prices Cove (19km to station)
    ("primo-bay",                             "8725520",  "noaa"),   # Primo Bay (37km to station)
    ("prince-cove",                           "8447930",  "noaa"),   # Prince Cove (25km to station)
    ("prince-george-beach",                   "8661070",  "noaa"),   # Prince George Beach (36km to station)
    ("prince-ruperts-cove",                   "9751381",  "noaa"),   # Prince Rupert's Cove (21km to station)
    ("princes-bay",                           "8531680",  "noaa"),   # Princes Bay (17km to station)
    ("pringle-lake",                          "8773701",  "noaa"),   # Pringle Lake (20km to station)
    ("pritchard-island-beach",                "9446484",  "noaa"),   # Pritchard Island Beach (31km to station)
    ("private-beach",                         "8518962",  "noaa"),   # Private Beach (19km to station)
    ("privates-beach",                        "9413450",  "noaa"),   # Private's Beach (40km to station)
    ("privates-nude-beach",                   "9413450",  "noaa"),   # Private's Nude Beach (40km to station)
    ("privateer-bay",                         "9751381",  "noaa"),   # Privateer Bay (6km to station)
    ("promisla-bay",                          "9451600",  "noaa"),   # Promisla Bay (15km to station)
    ("prospect-beach",                        "8465705",  "noaa"),   # Prospect Beach (6km to station)
    ("prospect-harbor",                       "8413320",  "noaa"),   # Prospect Harbor (16km to station)
    ("protection-bay",                        "9462620",  "noaa"),   # Protection Bay (33km to station)
    ("proveausal-bay",                        "8764314",  "noaa"),   # Proveausal Bay (40km to station)
    ("prudden-bay",                           "2695540",  "noaa"),   # Prudden Bay (13km to station)
    ("prune-bay",                             "9751364",  "noaa"),   # Prune Bay (5km to station)
    ("prune-beach",                           "9751364",  "noaa"),   # Prune Beach (5km to station)
    ("pry-cove",                              "8571421",  "noaa"),   # Pry Cove (13km to station)
    ("pryibil-beach",                         "8516945",  "noaa"),   # Pryibil Beach (15km to station)
    ("puamana-beach-park",                    "1615680",  "noaa"),   # Puamana Beach Park (21km to station)
    ("public-beach",                          "8447930",  "noaa"),   # Public Beach (27km to station)
    ("public-beach-access-2",                 "8726384",  "noaa"),   # Public Beach Access 2 (40km to station)
    ("public-beach-access-3",                 "8726384",  "noaa"),   # Public Beach Access 3 (40km to station)
    ("public-beach-buzzards-bay",             "8447930",  "noaa"),   # Public Beach Buzzards Bay (2km to station)
    ("public-beach-quissett-harbor",          "8447930",  "noaa"),   # Public Beach Quissett Harbor (3km to station)
    ("public-hawknest-beach",                 "9751381",  "noaa"),   # Public Hawknest Beach (7km to station)
    ("puckett-creek",                         "8721604",  "noaa"),   # Puckett Creek (31km to station)
    ("pueo-bay",                              "1617433",  "noaa"),   # Pueo Bay (18km to station)
    ("puerco-beach",                          "9410840",  "noaa"),   # Puerco Beach (20km to station)
    ("puerto-chico",                          "9753216",  "noaa"),   # Puerto Chico (1km to station)
    ("puerto-diablo",                         "9752695",  "noaa"),   # Puerto Diablo (16km to station)
    ("puerto-ferro",                          "9752695",  "noaa"),   # Puerto Ferro (5km to station)
    ("puerto-manolillo",                      "9759394",  "noaa"),   # Puerto Manolillo (39km to station)
    ("puerto-medio-mundo",                    "9753216",  "noaa"),   # Puerto Medio Mundo (8km to station)
    ("puerto-mosquito",                       "9752695",  "noaa"),   # Puerto Mosquito (3km to station)
    ("puerto-negro",                          "9752695",  "noaa"),   # Puerto Negro (14km to station)
    ("puerto-quijano",                        "9759110",  "noaa"),   # Puerto Quijano (4km to station)
    ("puerto-real",                           "9759394",  "noaa"),   # Puerto Real (17km to station)
    ("puerto-yabucoa",                        "9752695",  "noaa"),   # Puerto Yabucoa (38km to station)
    ("puerto-de-culebra",                     "9752235",  "noaa"),   # Puerto de Culebra (0km to station)
    ("puerto-de-guayanilla",                  "9759110",  "noaa"),   # Puerto de Guayanilla (26km to station)
    ("puerto-de-humacao",                     "9753216",  "noaa"),   # Puerto de Humacao (23km to station)
    ("puerto-de-vieques",                     "9752695",  "noaa"),   # Puerto de Vieques (7km to station)
    ("puerto-del-manglar",                    "9752235",  "noaa"),   # Puerto del Manglar (5km to station)
    ("puerto-del-tortuguero",                 "9755371",  "noaa"),   # Puerto del Tortuguero (36km to station)
    ("puffin-bay",                            "9451054",  "noaa"),   # Puffin Bay (9km to station)
    ("pug-harbor",                            "8461490",  "noaa"),   # Pug Harbor (22km to station)
    ("puget-cove",                            "9453220",  "noaa"),   # Puget Cove (2km to station)
    ("puhala-bay",                            "1615680",  "noaa"),   # Puhala Bay (14km to station)
    ("puhi-bay",                              "1617760",  "noaa"),   # Puhi Bay (1km to station)
    ("pumpkin-bay",                           "8761305",  "noaa"),   # Pumpkin Bay (24km to station)
    ("punalau-beach",                         "1615680",  "noaa"),   # Punalau Beach (22km to station)
    ("punch-bowl",                            "8413320",  "noaa"),   # Punch Bowl (40km to station)
    ("punchbowl",                             "8418150",  "noaa"),   # Punchbowl (13km to station)
    ("punches-cove",                          "8635750",  "noaa"),   # Punches Cove (31km to station)
    ("punderson-lake-beach",                  "9063053",  "noaa"),   # Punderson Lake Beach (34km to station)
    ("pungers-cove",                          "8571421",  "noaa"),   # Pungers Cove (12km to station)
    ("pungers-creek",                         "8571421",  "noaa"),   # Pungers Creek (12km to station)
    ("puniawa-bay",                           "1615680",  "noaa"),   # Puniawa Bay (24km to station)
    ("punnett-bay",                           "9751364",  "noaa"),   # Punnett Bay (3km to station)
    ("punta-salinas",                         "9755371",  "noaa"),   # Punta Salinas (8km to station)
    ("punta-soldado",                         "9752235",  "noaa"),   # Punta Soldado (3km to station)
    ("purdy-bay",                             "9075014",  "noaa"),   # Purdy Bay (10km to station)
    ("purplehorse-beach",                     "8594900",  "noaa"),   # Purplehorse Beach (22km to station)
    ("purtan-bay",                            "8637689",  "noaa"),   # Purtan Bay (26km to station)
    ("puu-alii-bay",                          "1617433",  "noaa"),   # Puu Alii Bay (34km to station)
    ("puyallup-waterway",                     "9446484",  "noaa"),   # Puyallup Waterway (1km to station)
    ("pyramid-harbor",                        "9452400",  "noaa"),   # Pyramid Harbor (31km to station)
    ("pythers-cove",                          "8575512",  "noaa"),   # Pythers Cove (8km to station)
    ("pia-bay",                               "1615680",  "noaa"),   # Pā'ia Bay (9km to station)
    ("pia-bay-beach",                         "1615680",  "noaa"),   # Pā'ia Bay Beach (9km to station)
    ("pia-secret-beach",                      "1615680",  "noaa"),   # Pā'ia Secret Beach (9km to station)
    ("ppaaeanui-bay",                         "1615680",  "noaa"),   # Pāpaʻaʻeanui Bay (28km to station)
    ("ppai",                                  "1617760",  "noaa"),   # Pāpa‘i (9km to station)
    ("ppuaa",                                 "1617760",  "noaa"),   # Pāpua‘a (10km to station)
    ("pka-bay",                               "1612340",  "noaa"),   # Pōka‘ī Bay (37km to station)
    ("pkoo-harbor",                           "1615680",  "noaa"),   # Pūko‘o Harbor (39km to station)
    ("qikutulig-bay",                         "9455500",  "noaa"),   # Qikutulig Bay (35km to station)
    ("quahog-bay",                            "8418150",  "noaa"),   # Quahog Bay (30km to station)
    ("quail-hill-beach",                      "8516945",  "noaa"),   # Quail Hill Beach (29km to station)
    ("quanaduck-cove",                        "8461490",  "noaa"),   # Quanaduck Cove (16km to station)
    ("quanset-pond",                          "8447435",  "noaa"),   # Quanset Pond (6km to station)
    ("quarantine-bay",                        "8760721",  "noaa"),   # Quarantine Bay (36km to station)
    ("quarantine-shore",                      "8775237",  "noaa"),   # Quarantine Shore (8km to station)
    ("quarry-beach",                          "9414290",  "noaa"),   # Quarry Beach (7km to station)
    ("quarry-cove",                           "9412110",  "noaa"),   # Quarry Cove (17km to station)
    ("quarter-cove",                          "8635750",  "noaa"),   # Quarter Cove (31km to station)
    ("quarterman-cove",                       "8721604",  "noaa"),   # Quarterman Cove (7km to station)
    ("queen-kapiolani-beach",                 "1612340",  "noaa"),   # Queen Kapi'olani Beach (6km to station)
    ("queen-sewell-cove",                     "8447930",  "noaa"),   # Queen Sewell Cove (26km to station)
    ("queensway-bay",                         "9410840",  "noaa"),   # Queensway Bay (39km to station)
    ("quidnet-beach",                         "8449130",  "noaa"),   # Quidnet Beach (10km to station)
    ("quinby-inlet",                          "8631044",  "noaa"),   # Quinby Inlet (16km to station)
    ("quinns-bay",                            "9052000",  "noaa"),   # Quinns Bay (15km to station)
    ("quissett-harbor",                       "8447930",  "noaa"),   # Quissett Harbor (2km to station)
    ("quivira-basin",                         "9410170",  "noaa"),   # Quivira Basin (8km to station)
    ("quivira-bay",                           "8735180",  "noaa"),   # Quivira Bay (7km to station)
    ("quoddy-narrows",                        "8410140",  "noaa"),   # Quoddy Narrows (9km to station)
    ("quotonset-beach",                       "8461490",  "noaa"),   # Quotonset Beach (31km to station)
    ("rabbit-bay",                            "9075099",  "noaa"),   # Rabbit Bay (9km to station)
    ("rabbit-key-basin",                      "8723970",  "noaa"),   # Rabbit Key Basin (39km to station)
    ("raber-bay",                             "9075099",  "noaa"),   # Raber Bay (17km to station)
    ("raccoon-bay",                           "8651370",  "noaa"),   # Raccoon Bay (24km to station)
    ("raccoon-beach",                         "8410140",  "noaa"),   # Raccoon Beach (7km to station)
    ("raccoon-cove",                          "8557380",  "noaa"),   # Raccoon Cove (18km to station)
    ("raccoon-creek",                         "8656483",  "noaa"),   # Raccoon Creek (34km to station)
    ("raccoon-lake",                          "8761724",  "noaa"),   # Raccoon Lake (7km to station)
    ("raccourci-bay",                         "8764227",  "noaa"),   # Raccourci Bay (39km to station)
    ("race-cove",                             "8536110",  "noaa"),   # Race Cove (15km to station)
    ("rachel-cove",                           "8447435",  "noaa"),   # Rachel Cove (14km to station)
    ("rada-fajardo",                          "9753216",  "noaa"),   # Rada Fajardo (5km to station)
    ("radenbough-cove",                       "9450460",  "noaa"),   # Radenbough Cove (1km to station)
    ("radio-bay",                             "1617760",  "noaa"),   # Radio Bay (0km to station)
    ("radio-beach",                           "9414750",  "noaa"),   # Radio Beach (6km to station)
    ("rahal-bayou",                           "8773037",  "noaa"),   # Rahal Bayou (20km to station)
    ("railroad-bay",                          "9414523",  "noaa"),   # Railroad Bay (23km to station)
    ("railroad-corner",                       "8741533",  "noaa"),   # Railroad Corner (3km to station)
    ("railroad-creek",                        "8594900",  "noaa"),   # Railroad Creek (29km to station)
    ("ram-bay",                               "8467150",  "noaa"),   # Ram Bay (23km to station)
    ("ramsay-lake",                           "8575512",  "noaa"),   # Ramsay Lake (9km to station)
    ("ramsdell-cove",                         "8413320",  "noaa"),   # Ramsdell Cove (39km to station)
    ("ramshorn-bay",                          "8632200",  "noaa"),   # Ramshorn Bay (23km to station)
    ("randall-bay",                           "8516945",  "noaa"),   # Randall Bay (24km to station)
    ("range-light-beach",                     "9451054",  "noaa"),   # Range Light Beach (0km to station)
    ("ranger-stevens-beach",                  "9410840",  "noaa"),   # Ranger Steven's Beach (18km to station)
    ("rat-rock-cove",                         "9414863",  "noaa"),   # Rat Rock Cove (10km to station)
    ("rattlesnake-cove",                      "8728690",  "noaa"),   # Rattlesnake Cove (18km to station)
    ("ray-bay",                               "9052000",  "noaa"),   # Ray Bay (33km to station)
    ("raymond-beach",                         "8418150",  "noaa"),   # Raymond Beach (33km to station)
    ("raymond-cove",                          "9450460",  "noaa"),   # Raymond Cove (37km to station)
    ("raymonds-cove",                         "8635750",  "noaa"),   # Raymond's Cove (21km to station)
    ("raynolds-bay",                          "9075099",  "noaa"),   # Raynolds Bay (26km to station)
    ("rays-pond",                             "8575512",  "noaa"),   # Rays Pond (6km to station)
    ("reach-beach",                           "8413320",  "noaa"),   # Reach Beach (37km to station)
    ("rec-beach",                             "8418150",  "noaa"),   # Rec Beach (30km to station)
    ("red-cove",                              "9459450",  "noaa"),   # Red Cove (6km to station)
    ("red-cove-beach",                        "9459450",  "noaa"),   # Red Cove Beach (6km to station)
    ("red-fish-bay",                          "8778490",  "noaa"),   # Red Fish Bay (5km to station)
    ("red-head-cove",                         "8779280",  "noaa"),   # Red Head Cove (9km to station)
    ("red-hole",                              "2695535",  "noaa"),   # Red Hole (4km to station)
    ("red-mill-beach",                        "9440422",  "noaa"),   # Red Mill Beach (3km to station)
    ("red-point-bay",                         "8311030",  "noaa"),   # Red Point Bay (26km to station)
    ("redfield-cove",                         "9453220",  "noaa"),   # Redfield Cove (10km to station)
    ("redfish-bay",                           "8760721",  "noaa"),   # Redfish Bay (19km to station)
    ("redfish-bend",                          "8747437",  "noaa"),   # Redfish Bend (40km to station)
    ("redfish-cove",                          "8775283",  "noaa"),   # Redfish Cove (3km to station)
    ("redfish-lake",                          "8773701",  "noaa"),   # Redfish Lake (19km to station)
    ("redhead-bay",                           "8639348",  "noaa"),   # Redhead Bay (33km to station)
    ("redhead-cove",                          "9063079",  "noaa"),   # Redhead Cove (28km to station)
    ("redhead-outside-pond",                  "8760721",  "noaa"),   # Redhead Outside Pond (12km to station)
    ("redhook-bay",                           "9751381",  "noaa"),   # Redhook Bay (12km to station)
    ("redhouse-cove",                         "8575512",  "noaa"),   # Redhouse Cove (12km to station)
    ("redman-cove",                           "8573364",  "noaa"),   # Redman Cove (19km to station)
    ("redondo-beach-state-park",              "9410840",  "noaa"),   # Redondo Beach State Park (22km to station)
    ("redoubt-bay",                           "9455760",  "noaa"),   # Redoubt Bay (36km to station)
    ("redoubt-bayou",                         "8729840",  "noaa"),   # Redoubt Bayou (9km to station)
    ("reebs-bay",                             "9063020",  "noaa"),   # Reebs Bay (34km to station)
    ("reed-cove",                             "8418150",  "noaa"),   # Reed Cove (26km to station)
    ("reeder-beach",                          "9440422",  "noaa"),   # Reeder Beach (40km to station)
    ("reeds-bay",                             "1617760",  "noaa"),   # Reeds Bay (1km to station)
    ("reef-bay",                              "9751381",  "noaa"),   # Reef Bay (3km to station)
    ("reef-bay-beach",                        "9751381",  "noaa"),   # Reef Bay Beach (2km to station)
    ("reef-beach",                            "9751364",  "noaa"),   # Reef Beach (10km to station)
    ("reef-bight",                            "9462620",  "noaa"),   # Reef Bight (40km to station)
    ("reese-bay",                             "9462620",  "noaa"),   # Reese Bay (18km to station)
    ("refuge-cove",                           "9450460",  "noaa"),   # Refuge Cove (11km to station)
    ("refuge-beach",                          "9450460",  "noaa"),   # Refuge beach (21km to station)
    ("rejects-beach",                         "8452660",  "noaa"),   # Rejects Beach (6km to station)
    ("renaud-bend",                           "8760721",  "noaa"),   # Renaud Bend (18km to station)
    ("reseau-bay",                            "9751381",  "noaa"),   # Reseau Bay (24km to station)
    ("reserve-basin",                         "8545240",  "noaa"),   # Reserve Basin (6km to station)
    ("resort-point-cove",                     "9410840",  "noaa"),   # Resort Point Cove (28km to station)
    ("rest-house-shore",                      "8449130",  "noaa"),   # Rest House Shore (2km to station)
    ("revel-island-bay",                      "8631044",  "noaa"),   # Revel Island Bay (10km to station)
    ("revel-island-cove",                     "8631044",  "noaa"),   # Revel Island Cove (13km to station)
    ("revenge-bay",                           "9751381",  "noaa"),   # Revenge Bay (23km to station)
    ("revenge-beach",                         "9751381",  "noaa"),   # Revenge Beach (24km to station)
    ("reybold-cove",                          "8551910",  "noaa"),   # Reybold Cove (4km to station)
    ("rhode-river",                           "8575512",  "noaa"),   # Rhode River (14km to station)
    ("rice-patch-bay",                        "8661070",  "noaa"),   # Rice Patch Bay (29km to station)
    ("rich-cove",                             "8418150",  "noaa"),   # Rich Cove (33km to station)
    ("rich-inlet",                            "8658163",  "noaa"),   # Rich Inlet (12km to station)
    ("rich-memorial-town-beach",              "8418150",  "noaa"),   # Rich Memorial Town Beach (29km to station)
    ("richard-bayou",                         "8729108",  "noaa"),   # Richard Bayou (19km to station)
    ("richardsons-bay",                       "2695535",  "noaa"),   # Richardson's Bay (0km to station)
    ("richland-cove",                         "8571421",  "noaa"),   # Richland Cove (12km to station)
    ("richmond-inner-harbor",                 "9414863",  "noaa"),   # Richmond Inner Harbor (5km to station)
    ("richmond-island-harbor",                "8418150",  "noaa"),   # Richmond Island Harbor (12km to station)
    ("richmond-marina-bay",                   "9414863",  "noaa"),   # Richmond Marina Bay (5km to station)
    ("richwine-gravel-bar",                   "9442396",  "noaa"),   # Richwine Gravel Bar (3km to station)
    ("riddells-bay",                          "2695540",  "noaa"),   # Riddell's Bay (17km to station)
    ("ridgewood-beach",                       "9087031",  "noaa"),   # Ridgewood Beach (10km to station)
    ("ridgleys-cove",                         "8574680",  "noaa"),   # Ridgleys Cove (4km to station)
    ("ridley-cove",                           "8418150",  "noaa"),   # Ridley Cove (30km to station)
    ("ridout-creek",                          "8575512",  "noaa"),   # Ridout Creek (5km to station)
    ("right-head",                            "9463502",  "noaa"),   # Right Head (26km to station)
    ("riley-beach",                           "9087031",  "noaa"),   # Riley Beach (6km to station)
    ("riley-cove",                            "9446484",  "noaa"),   # Riley Cove (39km to station)
    ("rileys-bay",                            "9087088",  "noaa"),   # Rileys Bay (27km to station)
    ("ringgold-cove",                         "8575512",  "noaa"),   # Ringgold Cove (8km to station)
    ("rioll-cove",                            "8571892",  "noaa"),   # Rioll Cove (18km to station)
    ("ripley-cove",                           "8447930",  "noaa"),   # Ripley Cove (19km to station)
    ("ritter-cove",                           "8654467",  "noaa"),   # Ritter Cove (6km to station)
    ("river-cove",                            "8571892",  "noaa"),   # River Cove (26km to station)
    ("river-ledge",                           "8452660",  "noaa"),   # River Ledge (12km to station)
    ("riverside-bay",                         "8760721",  "noaa"),   # Riverside Bay (5km to station)
    ("roachs-shore",                          "8573927",  "noaa"),   # Roachs Shore (14km to station)
    ("roanoke-sound",                         "8652587",  "noaa"),   # Roanoke Sound (9km to station)
    ("robbins-hill-beach",                    "8447435",  "noaa"),   # Robbins Hill Beach (15km to station)
    ("roberts-bay",                           "8726384",  "noaa"),   # Roberts Bay (39km to station)
    ("roberts-cove",                          "9075065",  "noaa"),   # Roberts Cove (10km to station)
    ("robertson-cove",                        "8413320",  "noaa"),   # Robertson Cove (30km to station)
    ("robertson-island",                      "8729840",  "noaa"),   # Robertson Island (14km to station)
    ("robin-bay",                             "9751364",  "noaa"),   # Robin Bay (8km to station)
    ("robin-hood-bay",                        "8631044",  "noaa"),   # Robin Hood Bay (36km to station)
    ("robinson-bay",                          "2695540",  "noaa"),   # Robinson Bay (9km to station)
    ("robinson-bayou",                        "8729108",  "noaa"),   # Robinson Bayou (8km to station)
    ("robinson-cove",                         "8575512",  "noaa"),   # Robinson Cove (12km to station)
    ("robinson-pond",                         "8760721",  "noaa"),   # Robinson Pond (10km to station)
    ("robinsons-beach",                       "8531680",  "noaa"),   # Robinsons Beach (20km to station)
    ("rock-baie",                             "8311062",  "noaa"),   # Rock Baie (5km to station)
    ("rock-cove",                             "8575512",  "noaa"),   # Rock Cove (13km to station)
    ("rock-hole",                             "8635750",  "noaa"),   # Rock Hole (23km to station)
    ("rock-hole-cove",                        "8658120",  "noaa"),   # Rock Hole Cove (33km to station)
    ("rockaway-inlet",                        "8531680",  "noaa"),   # Rockaway Inlet (14km to station)
    ("rockhold-creek",                        "8575512",  "noaa"),   # Rockhold Creek (23km to station)
    ("rockport-beach-park",                   "8774770",  "noaa"),   # Rockport Beach Park (1km to station)
    ("rocky-bay",                             "8725520",  "noaa"),   # Rocky Bay (22km to station)
    ("rocky-beach",                           "8465705",  "noaa"),   # Rocky Beach (8km to station)
    ("rocky-cove",                            "8727520",  "noaa"),   # Rocky Cove (36km to station)
    ("rocky-hole",                            "2695535",  "noaa"),   # Rocky Hole (4km to station)
    ("rocky-neck-state-beach",                "8461490",  "noaa"),   # Rocky Neck State Beach (14km to station)
    ("rocky-pond-cove",                       "8413320",  "noaa"),   # Rocky Pond Cove (38km to station)
    ("rod-bay",                               "9751364",  "noaa"),   # Rod Bay (9km to station)
    ("rodanthe-public-beach-access",          "8652587",  "noaa"),   # Rodanthe Public Beach Access (24km to station)
    ("rogers-point-beach",                    "8413320",  "noaa"),   # Rogers Point Beach (20km to station)
    ("roggs-bay",                             "9075099",  "noaa"),   # Roggs Bay (2km to station)
    ("rogue-bluffs-beach",                    "8411060",  "noaa"),   # Rogue Bluffs Beach (22km to station)
    ("rogues-harbor",                         "8573927",  "noaa"),   # Rogues Harbor (16km to station)
    ("roiles-harbor",                         "8510560",  "noaa"),   # Roiles Harbor (38km to station)
    ("rolfe-cove",                            "9449880",  "noaa"),   # Rolfe Cove (26km to station)
    ("rollover-bay",                          "8770971",  "noaa"),   # Rollover Bay (1km to station)
    ("rollway-bay",                           "8311030",  "noaa"),   # Rollway Bay (29km to station)
    ("ronde-pond",                            "8760721",  "noaa"),   # Ronde Pond (12km to station)
    ("rones-bay",                             "8635750",  "noaa"),   # Rones Bay (38km to station)
    ("roque-island-harbor",                   "8411060",  "noaa"),   # Roque Island Harbor (25km to station)
    ("roque-island-ledge",                    "8411060",  "noaa"),   # Roque Island Ledge (28km to station)
    ("rosa-bay",                              "8761724",  "noaa"),   # Rosa Bay (33km to station)
    ("rosies-bight",                          "9455500",  "noaa"),   # Rosies Bight (32km to station)
    ("ross-cove",                             "8575512",  "noaa"),   # Ross Cove (12km to station)
    ("ross-cove-beach",                       "9414523",  "noaa"),   # Ross Cove Beach (25km to station)
    ("ross-creek",                            "8721604",  "noaa"),   # Ross Creek (21km to station)
    ("rotary-beach",                          "8311062",  "noaa"),   # Rotary Beach (18km to station)
    ("rouges-bay-beach",                      "9751381",  "noaa"),   # Rouge's Bay Beach (19km to station)
    ("round-bay",                             "9751381",  "noaa"),   # Round Bay (5km to station)
    ("round-cove",                            "8454000",  "noaa"),   # Round Cove (2km to station)
    ("round-hammock-bay",                     "8652587",  "noaa"),   # Round Hammock Bay (21km to station)
    ("round-hill-beach",                      "8447930",  "noaa"),   # Round Hill Beach (22km to station)
    ("round-lake-bay",                        "9052000",  "noaa"),   # Round Lake Bay (34km to station)
    ("round-pond",                            "8760721",  "noaa"),   # Round Pond (4km to station)
    ("rowayton-community-beach",              "8467150",  "noaa"),   # Rowayton Community Beach (25km to station)
    ("rowley-cove",                           "8570283",  "noaa"),   # Rowley Cove (36km to station)
    ("royal-palms-county-beach",              "9410840",  "noaa"),   # Royal Palms County Beach (36km to station)
    ("royal-point-bay",                       "8654467",  "noaa"),   # Royal Point Bay (39km to station)
    ("royalls-cove",                          "8419870",  "noaa"),   # Royalls Cove (11km to station)
    ("rubicon-beach",                         "9075014",  "noaa"),   # Rubicon Beach (10km to station)
    ("ruby-alton-mature-reserve-beach",       "9449880",  "noaa"),   # Ruby Alton Mature Reserve Beach (39km to station)
    ("rubys-bay",                             "9087096",  "noaa"),   # Rubys Bay (14km to station)
    ("ruckle-park-beach",                     "9449880",  "noaa"),   # Ruckle Park Beach (37km to station)
    ("rum-cove",                              "8413320",  "noaa"),   # Rum Cove (27km to station)
    ("rum-harbor",                            "8570283",  "noaa"),   # Rum Harbor (33km to station)
    ("rum-harbor-cove",                       "8570283",  "noaa"),   # Rum Harbor Cove (34km to station)
    ("rundell-cove",                          "8770613",  "noaa"),   # Rundell Cove (10km to station)
    ("runnel-bay",                            "9751381",  "noaa"),   # Runnel Bay (30km to station)
    ("runnings-bay",                          "8311062",  "noaa"),   # Runnings Bay (22km to station)
    ("rurik-harbor",                          "9453220",  "noaa"),   # Rurik Harbor (4km to station)
    ("rusho-bay",                             "8311062",  "noaa"),   # Rusho Bay (13km to station)
    ("russell-bayou",                         "8729840",  "noaa"),   # Russell Bayou (28km to station)
    ("russell-fiord",                         "9453220",  "noaa"),   # Russell Fiord (36km to station)
    ("ruths-bay",                             "2695535",  "noaa"),   # Ruth's Bay (4km to station)
    ("rutherford-beach",                      "8768094",  "noaa"),   # Rutherford Beach (20km to station)
    ("rutherford-waterfront-park",            "8518750",  "noaa"),   # Rutherford Waterfront Park (17km to station)
    ("ruyter-bay",                            "9751381",  "noaa"),   # Ruyter Bay (24km to station)
    ("ryder-beach",                           "8447435",  "noaa"),   # Ryder Beach (32km to station)
    ("ryder-cove",                            "8447435",  "noaa"),   # Ryder Cove (3km to station)
    ("rye-north-beach",                       "8419870",  "noaa"),   # Rye North Beach (8km to station)
    ("s-turns-beach",                         "1615680",  "noaa"),   # S-Turns Beach (24km to station)
    ("sdsu-beach",                            "9410230",  "noaa"),   # SDSU Beach (9km to station)
    ("sabot-pond",                            "8760721",  "noaa"),   # Sabot Pond (9km to station)
    ("sacchi-beach",                          "9432780",  "noaa"),   # Sacchi Beach (10km to station)
    ("sachem-head-harbor",                    "8465705",  "noaa"),   # Sachem Head Harbor (17km to station)
    ("sachuest-bay",                          "8452660",  "noaa"),   # Sachuest Bay (6km to station)
    ("sacremento-river",                      "9415144",  "noaa"),   # Sacremento River (18km to station)
    ("saddlebunch-harbor",                    "8724580",  "noaa"),   # Saddlebunch Harbor (18km to station)
    ("sadlers-cove",                          "8575512",  "noaa"),   # Sadlers Cove (27km to station)
    ("safety-sound",                          "9468756",  "noaa"),   # Safety Sound (33km to station)
    ("sage-bay",                              "8654467",  "noaa"),   # Sage Bay (40km to station)
    ("sage-beach",                            "9451600",  "noaa"),   # Sage Beach (1km to station)
    ("sail-bay",                              "9410230",  "noaa"),   # Sail Bay (9km to station)
    ("sailboat-cove",                         "9087031",  "noaa"),   # Sailboat Cove (34km to station)
    ("saint-andrew-bay",                      "8729108",  "noaa"),   # Saint Andrew Bay (3km to station)
    ("saint-andrew-sound",                    "8729108",  "noaa"),   # Saint Andrew Sound (20km to station)
    ("saint-andrews-bay",                     "8735180",  "noaa"),   # Saint Andrews Bay (11km to station)
    ("saint-catherine-sound",                 "8635027",  "noaa"),   # Saint Catherine Sound (24km to station)
    ("saint-celments-bay",                    "8577330",  "noaa"),   # Saint Celments Bay (25km to station)
    ("saint-clements-bay",                    "8577330",  "noaa"),   # Saint Clements Bay (26km to station)
    ("saint-croix-country-club-beach",        "9751401",  "noaa"),   # Saint Croix Country Club Beach (14km to station)
    ("saint-george-creek",                    "8635750",  "noaa"),   # Saint George Creek (15km to station)
    ("saint-george-island-beach",             "8635750",  "noaa"),   # Saint George Island Beach (14km to station)
    ("saint-george-sound",                    "8728690",  "noaa"),   # Saint George Sound (29km to station)
    ("saint-jerome-beach",                    "8635750",  "noaa"),   # Saint Jerome Beach (19km to station)
    ("saint-john-baptist-bay",                "9451600",  "noaa"),   # Saint John Baptist Bay (30km to station)
    ("saint-john-bay",                        "9751381",  "noaa"),   # Saint John Bay (13km to station)
    ("saint-joseph-bay",                      "8728690",  "noaa"),   # Saint Joseph Bay (36km to station)
    ("saint-joseph-sound",                    "8726724",  "noaa"),   # Saint Joseph Sound (12km to station)
    ("saint-marys-creek-beach",               "9751381",  "noaa"),   # Saint Mary's Creek Beach (5km to station)
    ("saint-matthews-bay",                    "9454050",  "noaa"),   # Saint Matthews Bay (38km to station)
    ("saint-paul-waterway",                   "9446484",  "noaa"),   # Saint Paul Waterway (1km to station)
    ("saint-vincent-sound",                   "8728690",  "noaa"),   # Saint Vincent Sound (11km to station)
    ("saint-vital-bay",                       "9075099",  "noaa"),   # Saint Vital Bay (8km to station)
    ("sakonnet-harbor",                       "8452660",  "noaa"),   # Sakonnet Harbor (12km to station)
    ("salal-cove",                            "9416841",  "noaa"),   # Salal Cove (25km to station)
    ("salinas-bay",                           "9412110",  "noaa"),   # Salinas Bay (30km to station)
    ("sally-cove",                            "8557380",  "noaa"),   # Sally Cove (15km to station)
    ("sallys-hole",                           "8311062",  "noaa"),   # Sallys Hole (26km to station)
    ("salmon-beach",                          "9446484",  "noaa"),   # Salmon Beach (9km to station)
    ("salmon-cove",                           "8461490",  "noaa"),   # Salmon Cove (34km to station)
    ("salmon-ranch",                          "9459450",  "noaa"),   # Salmon Ranch (6km to station)
    ("salmons-bay",                           "8726724",  "noaa"),   # Salmons Bay (20km to station)
    ("salomon-beach",                         "9751381",  "noaa"),   # Salomon Beach (8km to station)
    ("salsbury-cove",                         "8413320",  "noaa"),   # Salsbury Cove (8km to station)
    ("salsipuedes-bay",                       "9412110",  "noaa"),   # Salsipuedes Bay (31km to station)
    ("salt-bayou",                            "8770475",  "noaa"),   # Salt Bayou (12km to station)
    ("salt-box-beach",                        "8447435",  "noaa"),   # Salt Box Beach (18km to station)
    ("salt-camp-cove",                        "8413320",  "noaa"),   # Salt Camp Cove (27km to station)
    ("salt-chuck-bay",                        "9452634",  "noaa"),   # Salt Chuck Bay (6km to station)
    ("salt-harbor",                           "8411060",  "noaa"),   # Salt Harbor (10km to station)
    ("salt-kettle-bay",                       "2695540",  "noaa"),   # Salt Kettle Bay (13km to station)
    ("salt-lake",                             "8773259",  "noaa"),   # Salt Lake (20km to station)
    ("salt-pond",                             "8447435",  "noaa"),   # Salt Pond (16km to station)
    ("salt-pond-bay",                         "8447435",  "noaa"),   # Salt Pond Bay (16km to station)
    ("salt-river-bay",                        "9751364",  "noaa"),   # Salt River Bay (7km to station)
    ("salt-river-beach",                      "9751364",  "noaa"),   # Salt River Beach (8km to station)
    ("salt-river-bioluminescent-bay",         "9751364",  "noaa"),   # Salt River Bioluminescent Bay (6km to station)
    ("salt-works-bay",                        "8461490",  "noaa"),   # Salt Works Bay (30km to station)
    ("saltpeter-creek",                       "8573364",  "noaa"),   # Saltpeter Creek (17km to station)
    ("saltpond-bay",                          "9751381",  "noaa"),   # Saltpond Bay (2km to station)
    ("saltworks-creek",                       "8575512",  "noaa"),   # Saltworks Creek (5km to station)
    ("sam-abell-cove",                        "8577330",  "noaa"),   # Sam Abell Cove (5km to station)
    ("sam-ferrenti-east-beach-town-beach",    "8461490",  "noaa"),   # Sam Ferrenti East Beach Town Beach (34km to station)
    ("sam-ferretti-blue-shutters-town-beach", "8461490",  "noaa"),   # Sam Ferretti Blue Shutters Town Beach (33km to station)
    ("sam-halls-bay",                         "2695535",  "noaa"),   # Sam Hall's Bay (5km to station)
    ("samish-beach",                          "9449880",  "noaa"),   # Samish Beach (36km to station)
    ("sammys-beach",                          "8510560",  "noaa"),   # Sammys Beach (20km to station)
    ("sampson-cove",                          "8418150",  "noaa"),   # Sampson Cove (35km to station)
    ("sampsons-cove",                         "8447386",  "noaa"),   # Sampsons Cove (24km to station)
    ("sams-bayou",                            "8728690",  "noaa"),   # Sams Bayou (15km to station)
    ("sams-cove",                             "8635750",  "noaa"),   # Sams Cove (38km to station)
    ("samsing-cove",                          "9451600",  "noaa"),   # Samsing Cove (8km to station)
    ("san-antonio-bay",                       "8774230",  "noaa"),   # San Antonio Bay (10km to station)
    ("san-diego-bay",                         "9459450",  "noaa"),   # San Diego Bay (26km to station)
    ("san-domingo-creek",                     "8571892",  "noaa"),   # San Domingo Creek (26km to station)
    ("san-gregorio-beach",                    "9414523",  "noaa"),   # San Gregorio Beach (27km to station)
    ("san-gregorio-private-beach",            "9414523",  "noaa"),   # San Gregorio Private Beach (26km to station)
    ("san-jacinto-point-marsh",               "8770613",  "noaa"),   # San Jacinto Point Marsh (11km to station)
    ("san-juan-cove",                         "9455500",  "noaa"),   # San Juan Cove (18km to station)
    ("san-quentin-beach",                     "9414863",  "noaa"),   # San Quentin Beach (7km to station)
    ("sanborn-cove",                          "8411060",  "noaa"),   # Sanborn Cove (15km to station)
    ("sanborn-harbor",                        "9459450",  "noaa"),   # Sanborn Harbor (36km to station)
    ("sanborns-gut",                          "8656483",  "noaa"),   # Sanborns Gut (33km to station)
    ("sanctuary-bay",                         "8536110",  "noaa"),   # Sanctuary Bay (18km to station)
    ("sand-b",                                "8311062",  "noaa"),   # Sand B (26km to station)
    ("sand-bank-cove",                        "8510560",  "noaa"),   # Sand Bank Cove (36km to station)
    ("sand-bay",                              "9087088",  "noaa"),   # Sand Bay (28km to station)
    ("sand-bend",                             "8639348",  "noaa"),   # Sand Bend (33km to station)
    ("sand-cove",                             "8413320",  "noaa"),   # Sand Cove (9km to station)
    ("sand-cove-beach",                       "8413320",  "noaa"),   # Sand Cove Beach (40km to station)
    ("sand-cove-north",                       "8411060",  "noaa"),   # Sand Cove North (35km to station)
    ("sand-dune-beach",                       "8418150",  "noaa"),   # Sand Dune Beach (32km to station)
    ("sand-hill-cove",                        "8452660",  "noaa"),   # Sand Hill Cove (21km to station)
    ("sand-marsh-cove",                       "8536110",  "noaa"),   # Sand Marsh Cove (18km to station)
    ("sand-shoal-inlet",                      "8632200",  "noaa"),   # Sand Shoal Inlet (23km to station)
    ("sand-springs-beach",                    "9414290",  "noaa"),   # Sand Springs Beach (6km to station)
    ("sand-street-beach",                     "8467150",  "noaa"),   # Sand Street Beach (28km to station)
    ("sanders-bay",                           "9751381",  "noaa"),   # Sanders Bay (2km to station)
    ("sands-cove",                            "8573927",  "noaa"),   # Sands Cove (24km to station)
    ("sands-point-village-beach",             "8516945",  "noaa"),   # Sands Point Village Beach (9km to station)
    ("sandspur-beach",                        "8723970",  "noaa"),   # Sandspur Beach (16km to station)
    ("sandy-bay",                             "8741533",  "noaa"),   # Sandy Bay (24km to station)
    ("sandy-beach-south",                     "9459450",  "noaa"),   # Sandy Beach South (4km to station)
    ("sandy-hill-beach",                      "8571421",  "noaa"),   # Sandy Hill Beach (22km to station)
    ("sandy-hole",                            "2695540",  "noaa"),   # Sandy Hole (4km to station)
    ("sandy-island-bay",                      "8631044",  "noaa"),   # Sandy Island Bay (14km to station)
    ("sandy-island-cove",                     "8571421",  "noaa"),   # Sandy Island Cove (9km to station)
    ("sandy-river-beach",                     "8411060",  "noaa"),   # Sandy River Beach (30km to station)
    ("sandys-beach",                          "8723214",  "noaa"),   # Sandy's Beach (6km to station)
    ("sandyland-beach",                       "8577330",  "noaa"),   # Sandyland Beach (22km to station)
    ("sanford-cove",                          "8411060",  "noaa"),   # Sanford Cove (24km to station)
    ("sanibel-bayous",                        "8725520",  "noaa"),   # Sanibel Bayous (32km to station)
    ("santa-clara-cove",                      "9410230",  "noaa"),   # Santa Clara Cove (9km to station)
    ("santa-cruz-anchorage",                  "9413450",  "noaa"),   # Santa Cruz Anchorage (40km to station)
    ("santa-maria-bay",                       "9751381",  "noaa"),   # Santa Maria Bay (29km to station)
    ("santa-maria-beach",                     "9415020",  "noaa"),   # Santa Maria Beach (11km to station)
    ("santa-marias-beach",                    "9413450",  "noaa"),   # Santa Maria's Beach (40km to station)
    ("santa-monica-bay",                      "9410840",  "noaa"),   # Santa Monica Bay (9km to station)
    ("santa-rosa-sound",                      "8729840",  "noaa"),   # Santa Rosa Sound (35km to station)
    ("sapbush-bay",                           "8311062",  "noaa"),   # Sapbush Bay (22km to station)
    ("sapowet-cove",                          "8452660",  "noaa"),   # Sapowet Cove (13km to station)
    ("saquatucket-harbor",                    "8447435",  "noaa"),   # Saquatucket Harbor (9km to station)
    ("sardinera-beach",                       "9755371",  "noaa"),   # Sardinera Beach (18km to station)
    ("sargent-cove",                          "8413320",  "noaa"),   # Sargent Cove (10km to station)
    ("sasco-hill-beach",                      "8467150",  "noaa"),   # Sasco Hill Beach (10km to station)
    ("sassafras-cove",                        "8454000",  "noaa"),   # Sassafras Cove (1km to station)
    ("saugerties-beach",                      "8518962",  "noaa"),   # Saugerties Beach (6km to station)
    ("saultsman-cove",                        "8729840",  "noaa"),   # Saultsman Cove (18km to station)
    ("savannah-river-beach",                  "8670870",  "noaa"),   # Savannah River Beach (4km to station)
    ("sawmill-bay",                           "9052000",  "noaa"),   # Sawmill Bay (14km to station)
    ("sawmill-cove",                          "8635750",  "noaa"),   # Sawmill Cove (16km to station)
    ("sawyers-beach",                         "8419870",  "noaa"),   # Sawyers Beach (11km to station)
    ("sawyers-cove",                          "8413320",  "noaa"),   # Sawyers Cove (20km to station)
    ("saxon-bay",                             "8735180",  "noaa"),   # Saxon Bay (12km to station)
    ("sayward-beach",                         "9449880",  "noaa"),   # Sayward Beach (26km to station)
    ("scaffold-creek",                        "8575512",  "noaa"),   # Scaffold Creek (14km to station)
    ("scammon-cove",                          "9075099",  "noaa"),   # Scammon Cove (31km to station)
    ("scarabin-pond",                         "8760721",  "noaa"),   # Scarabin Pond (13km to station)
    ("scarboro-creek",                        "8652587",  "noaa"),   # Scarboro Creek (15km to station)
    ("scharrer-bayou",                        "8726724",  "noaa"),   # Scharrer Bayou (4km to station)
    ("scheides-cove",                         "8575512",  "noaa"),   # Scheides Cove (9km to station)
    ("schoodic-bay",                          "8413320",  "noaa"),   # Schoodic Bay (22km to station)
    ("schoodic-beach",                        "8413320",  "noaa"),   # Schoodic Beach (22km to station)
    ("schoodic-harbor",                       "8413320",  "noaa"),   # Schoodic Harbor (14km to station)
    ("school-creek",                          "8575512",  "noaa"),   # School Creek (17km to station)
    ("school-land-bay",                       "9432780",  "noaa"),   # School Land Bay (29km to station)
    ("schoolhouse-cove",                      "8574680",  "noaa"),   # Schoolhouse Cove (9km to station)
    ("schooner-bay",                          "9415020",  "noaa"),   # Schooner Bay (9km to station)
    ("schooner-cove",                         "8413320",  "noaa"),   # Schooner Cove (24km to station)
    ("schooner-gulch-state-beach",            "9416841",  "noaa"),   # Schooner Gulch State Beach (7km to station)
    ("schoonmaker-beach",                     "9414290",  "noaa"),   # Schoonmaker Beach (7km to station)
    ("schuberts-beach",                       "8467150",  "noaa"),   # Schuberts Beach (28km to station)
    ("scorton-neck-beach",                    "8447930",  "noaa"),   # Scorton Neck Beach (34km to station)
    ("scott-bay",                             "8760721",  "noaa"),   # Scott Bay (14km to station)
    ("scott-beach",                           "9751381",  "noaa"),   # Scott Beach (15km to station)
    ("scott-cove",                            "8467150",  "noaa"),   # Scott Cove (27km to station)
    ("scotten-bay",                           "9014070",  "noaa"),   # Scotten Bay (10km to station)
    ("scotts-beach",                          "8467150",  "noaa"),   # Scotts Beach (29km to station)
    ("scotts-cove",                           "8571421",  "noaa"),   # Scotts Cove (10km to station)
    ("scotty-bay",                            "9075099",  "noaa"),   # Scotty Bay (23km to station)
    ("scow-bay",                              "9451600",  "noaa"),   # Scow Bay (37km to station)
    ("scow-cove",                             "9452210",  "noaa"),   # Scow Cove (22km to station)
    ("scuba-diving-access-area",              "8518962",  "noaa"),   # Scuba Diving Access Area (40km to station)
    ("scull-bay",                             "8534720",  "noaa"),   # Scull Bay (12km to station)
    ("sculptured-beach",                      "9415020",  "noaa"),   # Sculptured Beach (11km to station)
    ("sea-bluff-beach",                       "8465705",  "noaa"),   # Sea Bluff Beach (6km to station)
    ("sea-cove",                              "8413320",  "noaa"),   # Sea Cove (28km to station)
    ("sea-cove-beach",                        "8418150",  "noaa"),   # Sea Cove Beach (23km to station)
    ("sea-cows-bay",                          "9751381",  "noaa"),   # Sea Cows Bay (14km to station)
    ("sea-haven-beach",                       "8658163",  "noaa"),   # Sea Haven Beach (40km to station)
    ("sea-lion-cove",                         "9415020",  "noaa"),   # Sea Lion Cove (3km to station)
    ("sea-otter-bay",                         "9453220",  "noaa"),   # Sea Otter Bay (5km to station)
    ("sea-pine-beach",                        "9416841",  "noaa"),   # Sea Pine Beach (27km to station)
    ("seaborg-bay",                           "9457804",  "noaa"),   # Seaborg Bay (16km to station)
    ("seabreeze-beach",                       "8639348",  "noaa"),   # Seabreeze Beach (31km to station)
    ("seabright-drive-beach",                 "9449880",  "noaa"),   # Seabright Drive Beach (38km to station)
    ("seacrest-estates-beach",                "8516945",  "noaa"),   # Seacrest Estates Beach (31km to station)
    ("seaflower-cove",                        "9457804",  "noaa"),   # Seaflower Cove (1km to station)
    ("seaglass-beach",                        "8418150",  "noaa"),   # Seaglass Beach (3km to station)
    ("seagull-pond",                          "8760721",  "noaa"),   # Seagull Pond (9km to station)
    ("seahorse-beach",                        "8577330",  "noaa"),   # Seahorse Beach (4km to station)
    ("seal-cove",                             "8418150",  "noaa"),   # Seal Cove (12km to station)
    ("seal-cove-beach",                       "8411060",  "noaa"),   # Seal Cove Beach (30km to station)
    ("seal-harbor",                           "8413320",  "noaa"),   # Seal Harbor (12km to station)
    ("seal-rookery",                          "9416841",  "noaa"),   # Seal Rookery (29km to station)
    ("sealing-cove",                          "9451600",  "noaa"),   # Sealing Cove (0km to station)
    ("sealion-cove",                          "9451600",  "noaa"),   # Sealion Cove (40km to station)
    ("seaplane-harbor",                       "9414750",  "noaa"),   # Seaplane Harbor (17km to station)
    ("search-bay",                            "9075080",  "noaa"),   # Search Bay (29km to station)
    ("seaside-beach",                         "8467150",  "noaa"),   # Seaside Beach (2km to station)
    ("seaweed-cove",                          "8452660",  "noaa"),   # Seaweed Cove (23km to station)
    ("sebago-town-beach",                     "8418150",  "noaa"),   # Sebago Town Beach (38km to station)
    ("sebasco-harbor",                        "8418150",  "noaa"),   # Sebasco Harbor (32km to station)
    ("secluded-bay",                          "9451600",  "noaa"),   # Secluded Bay (39km to station)
    ("second-bay",                            "8764044",  "noaa"),   # Second Bay (24km to station)
    ("second-cove",                           "8577330",  "noaa"),   # Second Cove (2km to station)
    ("second-sand-beach",                     "8410140",  "noaa"),   # Second Sand Beach (37km to station)
    ("secor-bay",                             "9063085",  "noaa"),   # Secor Bay (14km to station)
    ("secret-harbor-beach",                   "9751381",  "noaa"),   # Secret Harbor Beach (14km to station)
    ("sedge-cove",                            "8447930",  "noaa"),   # Sedge Cove (18km to station)
    ("sedgewick-cove",                        "8575512",  "noaa"),   # Sedgewick Cove (28km to station)
    ("sedgy-point-cove",                      "8571421",  "noaa"),   # Sedgy Point Cove (14km to station)
    ("seeleys-bay",                           "8311062",  "noaa"),   # Seeleys Bay (29km to station)
    ("segar-cove",                            "8452660",  "noaa"),   # Segar Cove (22km to station)
    ("seidler-beach",                         "8531680",  "noaa"),   # Seidler Beach (19km to station)
    ("seidlers-beach",                        "8531680",  "noaa"),   # Seidler's Beach (19km to station)
    ("seining-beach",                         "8637689",  "noaa"),   # Seining Beach (29km to station)
    ("selby-bay",                             "8575512",  "noaa"),   # Selby Bay (9km to station)
    ("selby-beach",                           "8575512",  "noaa"),   # Selby Beach (9km to station)
    ("selden-cove",                           "8461490",  "noaa"),   # Selden Cove (27km to station)
    ("seldovia-bay",                          "9455500",  "noaa"),   # Seldovia Bay (2km to station)
    ("sellman-creek",                         "8575512",  "noaa"),   # Sellman Creek (11km to station)
    ("selva-playa",                           "9753216",  "noaa"),   # Selva Playa (7km to station)
    ("seneca-creek",                          "8573364",  "noaa"),   # Seneca Creek (17km to station)
    ("seneca-sound",                          "8726674",  "noaa"),   # Seneca Sound (15km to station)
    ("senecal-bay",                           "8311062",  "noaa"),   # Senecal Bay (10km to station)
    ("senior-creek",                          "8635750",  "noaa"),   # Senior Creek (30km to station)
    ("sesuit-beach",                          "8447435",  "noaa"),   # Sesuit Beach (18km to station)
    ("sesuit-harbor",                         "8447435",  "noaa"),   # Sesuit Harbor (18km to station)
    ("setauket-harbor",                       "8467150",  "noaa"),   # Setauket Harbor (26km to station)
    ("seul-choix-bay",                        "9087096",  "noaa"),   # Seul Choix Bay (2km to station)
    ("seven-mile-beach",                      "8536110",  "noaa"),   # Seven Mile Beach (22km to station)
    ("seven-mouth-creek",                     "8726724",  "noaa"),   # Seven Mouth Creek (6km to station)
    ("seven-pines",                           "8726384",  "noaa"),   # Seven Pines (16km to station)
    ("sevenfathom-bay",                       "9451600",  "noaa"),   # Sevenfathom Bay (29km to station)
    ("sewards-cove",                          "8419870",  "noaa"),   # Sewards Cove (5km to station)
    ("sewee-bay",                             "8665530",  "noaa"),   # Sewee Bay (31km to station)
    ("sex-cove",                              "9446484",  "noaa"),   # Sex Cove (16km to station)
    ("seymoor-pond-beach",                    "8447435",  "noaa"),   # Seymoor pond beach (12km to station)
    ("seymour-bay",                           "9075099",  "noaa"),   # Seymour Bay (3km to station)
    ("shackleford-point",                     "8656483",  "noaa"),   # Shackleford Point (4km to station)
    ("shadow-cliffs-beach",                   "9414523",  "noaa"),   # Shadow Cliffs Beach (37km to station)
    ("shady-lake",                            "8575512",  "noaa"),   # Shady Lake (2km to station)
    ("shag-head-breaker",                     "8411060",  "noaa"),   # Shag Head Breaker (31km to station)
    ("shallow-bay",                           "8632200",  "noaa"),   # Shallow Bay (23km to station)
    ("shallow-bayou",                         "8761724",  "noaa"),   # Shallow Bayou (40km to station)
    ("shamrock-bay",                          "9451600",  "noaa"),   # Shamrock Bay (28km to station)
    ("shamrock-cove",                         "8775283",  "noaa"),   # Shamrock Cove (8km to station)
    ("shanks-creek",                          "8571421",  "noaa"),   # Shanks Creek (29km to station)
    ("shanty-bay",                            "8510560",  "noaa"),   # Shanty Bay (27km to station)
    ("shark-cove",                            "8418150",  "noaa"),   # Shark Cove (8km to station)
    ("shark-hole",                            "8447435",  "noaa"),   # Shark Hole (9km to station)
    ("shark-inlet",                           "9412110",  "noaa"),   # Shark Inlet (19km to station)
    ("sharpe-bay",                            "9075014",  "noaa"),   # Sharpe Bay (6km to station)
    ("shaw-bay",                              "8575512",  "noaa"),   # Shaw Bay (29km to station)
    ("shaw-cove",                             "8461490",  "noaa"),   # Shaw Cove (3km to station)
    ("shear-pen-pond",                        "8447930",  "noaa"),   # Shear Pen Pond (22km to station)
    ("sheep-bay",                             "9454050",  "noaa"),   # Sheep Bay (18km to station)
    ("sheep-pen-cove",                        "8452944",  "noaa"),   # Sheep Pen Cove (8km to station)
    ("sheep-point-cove",                      "8452660",  "noaa"),   # Sheep Point Cove (5km to station)
    ("sheephead-bayou",                       "8729108",  "noaa"),   # Sheephead Bayou (14km to station)
    ("sheephead-cove",                        "8575512",  "noaa"),   # Sheephead Cove (12km to station)
    ("sheepshead-bayou",                      "8728690",  "noaa"),   # Sheepshead Bayou (12km to station)
    ("sheepshead-harbor",                     "8571421",  "noaa"),   # Sheepshead Harbor (16km to station)
    ("sheffield-cove",                        "8452660",  "noaa"),   # Sheffield Cove (5km to station)
    ("sheffield-island-harbor",               "8467150",  "noaa"),   # Sheffield Island Harbor (24km to station)
    ("shelikof-bay",                          "9451600",  "noaa"),   # Shelikof Bay (29km to station)
    ("shell-landing-cove",                    "8557380",  "noaa"),   # Shell Landing Cove (13km to station)
    ("shell-point-bay",                       "8447930",  "noaa"),   # Shell Point Bay (24km to station)
    ("shell-point-cove",                      "8728690",  "noaa"),   # Shell Point Cove (18km to station)
    ("shellbank-basin",                       "8518750",  "noaa"),   # Shellbank Basin (16km to station)
    ("shelldrake-cove",                       "8418150",  "noaa"),   # Shelldrake Cove (26km to station)
    ("shelly-bay",                            "2695540",  "noaa"),   # Shelly Bay (6km to station)
    ("shelter-bay",                           "9455920",  "noaa"),   # Shelter Bay (23km to station)
    ("shelter-haven",                         "8536110",  "noaa"),   # Shelter Haven (20km to station)
    ("shelter-island-bay",                    "8534720",  "noaa"),   # Shelter Island Bay (8km to station)
    ("shelter-island-sound",                  "8510560",  "noaa"),   # Shelter Island Sound (34km to station)
    ("shennecossett-beach",                   "8461490",  "noaa"),   # Shennecossett Beach (6km to station)
    ("shepherds-cove",                        "8447386",  "noaa"),   # Shepherds Cove (12km to station)
    ("shepherds-hill-cove",                   "8419870",  "noaa"),   # Shepherds Hill Cove (2km to station)
    ("sheppard-bay",                          "9076024",  "noaa"),   # Sheppard Bay (34km to station)
    ("sheppards-cove",                        "8575512",  "noaa"),   # Sheppards Cove (9km to station)
    ("sherard-beach",                         "8410140",  "noaa"),   # Sherard Beach (26km to station)
    ("sherkston-beaches",                     "9063020",  "noaa"),   # Sherkston Beaches (20km to station)
    ("sherman-cove",                          "8729840",  "noaa"),   # Sherman Cove (14km to station)
    ("sherman-inlet",                         "8729840",  "noaa"),   # Sherman Inlet (13km to station)
    ("sherman-lake",                          "9415144",  "noaa"),   # Sherman Lake (21km to station)
    ("shields-cove",                          "8631044",  "noaa"),   # Shields Cove (17km to station)
    ("shifting-sands-beach",                  "8639348",  "noaa"),   # Shifting Sands Beach (31km to station)
    ("shimmo-creek",                          "8449130",  "noaa"),   # Shimmo Creek (2km to station)
    ("shingle-bay",                           "9076027",  "noaa"),   # Shingle Bay (9km to station)
    ("shingle-cove",                          "8418150",  "noaa"),   # Shingle Cove (34km to station)
    ("shingle-creek",                         "8654467",  "noaa"),   # Shingle Creek (12km to station)
    ("shingle-landing-prong",                 "8570283",  "noaa"),   # Shingle Landing Prong (12km to station)
    ("ship-cove",                             "8418150",  "noaa"),   # Ship Cove (4km to station)
    ("ship-harbor",                           "8413320",  "noaa"),   # Ship Harbor (20km to station)
    ("ship-yard-cove",                        "8411060",  "noaa"),   # Ship Yard Cove (26km to station)
    ("shippen-cove",                          "8573364",  "noaa"),   # Shippen Cove (13km to station)
    ("shipping-creek",                        "8575512",  "noaa"),   # Shipping Creek (15km to station)
    ("shipps-bay",                            "8639348",  "noaa"),   # Shipps Bay (33km to station)
    ("ships-bay",                             "8651370",  "noaa"),   # Ships Bay (26km to station)
    ("shipyard-bay",                          "9454050",  "noaa"),   # Shipyard Bay (3km to station)
    ("shipyard-cove",                         "8411060",  "noaa"),   # Shipyard Cove (15km to station)
    ("shirtpond-cove",                        "8571421",  "noaa"),   # Shirtpond Cove (24km to station)
    ("shiyi-bay",                             "9452400",  "noaa"),   # Shiyi Bay (26km to station)
    ("shoal-cast",                            "9450460",  "noaa"),   # Shoal Cast (25km to station)
    ("shoal-cove",                            "9450460",  "noaa"),   # Shoal Cove (24km to station)
    ("shoalwater-bay",                        "8773037",  "noaa"),   # Shoalwater Bay (12km to station)
    ("shoe-hole-bay",                         "8651370",  "noaa"),   # Shoe Hole Bay (8km to station)
    ("shoestring-bay",                        "8447930",  "noaa"),   # Shoestring Bay (20km to station)
    ("shop-gut",                              "8656483",  "noaa"),   # Shop Gut (34km to station)
    ("shore-acres-pool-club-beach",           "8516945",  "noaa"),   # Shore Acres Pool Club Beach (15km to station)
    ("shoreline-beach-park",                  "9410170",  "noaa"),   # Shoreline Beach Park (4km to station)
    ("shorey-cove",                           "8411060",  "noaa"),   # Shorey Cove (26km to station)
    ("short-bar",                             "8410140",  "noaa"),   # Short Bar (19km to station)
    ("short-cove",                            "8447930",  "noaa"),   # Short Cove (18km to station)
    ("shortys-pocket",                        "8721604",  "noaa"),   # Shortys Pocket (13km to station)
    ("shoup-bay",                             "9454240",  "noaa"),   # Shoup Bay (12km to station)
    ("shoys-beach",                           "9751364",  "noaa"),   # Shoys Beach (2km to station)
    ("shrewsbury-bay",                        "8531680",  "noaa"),   # Shrewsbury Bay (14km to station)
    ("shutter-arm",                           "9432780",  "noaa"),   # Shutter Arm (27km to station)
    ("side-o-th-bay",                         "8536110",  "noaa"),   # Side o' th' Bay (17km to station)
    ("sievers-cove",                          "8771341",  "noaa"),   # Sievers Cove (9km to station)
    ("siletz-bay",                            "9435380",  "noaa"),   # Siletz Bay (31km to station)
    ("sillery-bay",                           "8575512",  "noaa"),   # Sillery Bay (12km to station)
    ("silver-eel-cove",                       "8461490",  "noaa"),   # Silver Eel Cove (14km to station)
    ("silver-spring-cove",                    "8452660",  "noaa"),   # Silver Spring Cove (17km to station)
    ("simeon-bay",                            "9459450",  "noaa"),   # Simeon Bay (8km to station)
    ("similar-sound",                         "8724580",  "noaa"),   # Similar Sound (18km to station)
    ("simonton-cove",                         "8418150",  "noaa"),   # Simonton Cove (2km to station)
    ("simpson-beach",                         "9432780",  "noaa"),   # Simpson Beach (6km to station)
    ("simpson-lagoon",                        "9497645",  "noaa"),   # Simpson Lagoon (36km to station)
    ("sinepuxent-bay",                        "8570283",  "noaa"),   # Sinepuxent Bay (10km to station)
    ("singleton-swash",                       "8661070",  "noaa"),   # Singleton Swash (16km to station)
    ("sinitsin-cove",                         "9451600",  "noaa"),   # Sinitsin Cove (39km to station)
    ("sinky-bay",                             "2695540",  "noaa"),   # Sinky Bay (18km to station)
    ("sisek-cove",                            "9462620",  "noaa"),   # Sisek Cove (24km to station)
    ("sitcum-waterway",                       "9446484",  "noaa"),   # Sitcum Waterway (0km to station)
    ("sitgreaves-bay",                        "9075099",  "noaa"),   # Sitgreaves Bay (31km to station)
    ("sitts-bay",                             "8311062",  "noaa"),   # Sitts Bay (25km to station)
    ("skipjack-bay",                          "8760721",  "noaa"),   # Skipjack Bay (28km to station)
    ("skolfield-cove",                        "8418150",  "noaa"),   # Skolfield Cove (33km to station)
    ("skroggins-bay",                         "2695540",  "noaa"),   # Skroggins Bay (19km to station)
    ("skunk-sound",                           "8536110",  "noaa"),   # Skunk Sound (6km to station)
    ("slacks-bay",                            "8311062",  "noaa"),   # Slacks Bay (20km to station)
    ("slacks-pond-beach",                     "8454000",  "noaa"),   # Slacks Pond Beach (14km to station)
    ("slate-island-cove",                     "8411060",  "noaa"),   # Slate Island Cove (36km to station)
    ("slaughter-house-beach",                 "1615680",  "noaa"),   # Slaughter House Beach (22km to station)
    ("sleeths-bay",                           "9052000",  "noaa"),   # Sleeths Bay (37km to station)
    ("slide-ranch-north-beach",               "9414290",  "noaa"),   # Slide Ranch North Beach (14km to station)
    ("slim-bay",                              "8311062",  "noaa"),   # Slim Bay (22km to station)
    ("slip-1",                                "9446484",  "noaa"),   # Slip 1 (33km to station)
    ("slip-2",                                "9446484",  "noaa"),   # Slip 2 (32km to station)
    ("slip-3",                                "9446484",  "noaa"),   # Slip 3 (31km to station)
    ("slip-4",                                "9446484",  "noaa"),   # Slip 4 (31km to station)
    ("slip-6",                                "9446484",  "noaa"),   # Slip 6 (29km to station)
    ("sloan-cove",                            "8557380",  "noaa"),   # Sloan Cove (14km to station)
    ("sloanes-cove",                          "8418150",  "noaa"),   # Sloanes Cove (34km to station)
    ("slocum-inlet",                          "9452210",  "noaa"),   # Slocum Inlet (28km to station)
    ("slocums-river",                         "8447930",  "noaa"),   # Slocums River (25km to station)
    ("sloop-cove",                            "8574680",  "noaa"),   # Sloop Cove (14km to station)
    ("slough-cove",                           "8447930",  "noaa"),   # Slough Cove (21km to station)
    ("smack-bayou",                           "8729108",  "noaa"),   # Smack Bayou (2km to station)
    ("smacks-bayou",                          "8726520",  "noaa"),   # Smacks Bayou (5km to station)
    ("small-bay",                             "9462620",  "noaa"),   # Small Bay (11km to station)
    ("small-boat-lagoon",                     "9414750",  "noaa"),   # Small Boat Lagoon (13km to station)
    ("small-point-harbor",                    "8418150",  "noaa"),   # Small Point Harbor (32km to station)
    ("smelt-brook",                           "8413320",  "noaa"),   # Smelt Brook (25km to station)
    ("smelt-cove",                            "8413320",  "noaa"),   # Smelt Cove (13km to station)
    ("smelter-bay",                           "9075099",  "noaa"),   # Smelter Bay (40km to station)
    ("smith-bay",                             "8465705",  "noaa"),   # Smith Bay (23km to station)
    ("smith-bayou",                           "9087031",  "noaa"),   # Smith Bayou (35km to station)
    ("smith-beach",                           "8632200",  "noaa"),   # Smith Beach (22km to station)
    ("smith-beach-harbor",                    "8467150",  "noaa"),   # Smith Beach Harbor (18km to station)
    ("smith-cove",                            "8452944",  "noaa"),   # Smith Cove (4km to station)
    ("smith-creek",                           "8575512",  "noaa"),   # Smith Creek (18km to station)
    ("smiths-bay",                            "2695540",  "noaa"),   # Smith's Bay (21km to station)
    ("smiths-sound",                          "2695535",  "noaa"),   # Smith's Sound (3km to station)
    ("smokehouse-bay",                        "8725520",  "noaa"),   # Smokehouse Bay (24km to station)
    ("smokehouse-cove",                       "8570283",  "noaa"),   # Smokehouse Cove (8km to station)
    ("smuggler-cove",                         "9450460",  "noaa"),   # Smuggler Cove (27km to station)
    ("smugglers-cove",                        "9410170",  "noaa"),   # Smuggler's Cove (6km to station)
    ("smugglers-cove-beach",                  "9751381",  "noaa"),   # Smuggler's Cove Beach (9km to station)
    ("smugglers-bayou",                       "8773259",  "noaa"),   # Smugglers Bayou (10km to station)
    ("snail-bay",                             "8761724",  "noaa"),   # Snail Bay (22km to station)
    ("snake-island-cove",                     "8771972",  "noaa"),   # Snake Island Cove (10km to station)
    ("snake-pond-beach",                      "8447930",  "noaa"),   # Snake Pond Beach (21km to station)
    ("snare-cove",                            "8411060",  "noaa"),   # Snare Cove (36km to station)
    ("snell-island-harbor",                   "8726520",  "noaa"),   # Snell Island Harbor (4km to station)
    ("snipe-bay",                             "9451054",  "noaa"),   # Snipe Bay (27km to station)
    ("snorkel-park-beach",                    "2695540",  "noaa"),   # Snorkel Park Beach (13km to station)
    ("snow-cove",                             "8413320",  "noaa"),   # Snow Cove (37km to station)
    ("snows-cove",                            "8447435",  "noaa"),   # Snow's Cove (32km to station)
    ("snowshoe-bay",                          "9052000",  "noaa"),   # Snowshoe Bay (29km to station)
    ("snuggery-cove",                         "9443090",  "noaa"),   # Snuggery Cove (24km to station)
    ("snyder-bayou",                          "8771486",  "noaa"),   # Snyder Bayou (6km to station)
    ("soapstone-cove",                        "9452634",  "noaa"),   # Soapstone Cove (14km to station)
    ("soldier-bay",                           "2695535",  "noaa"),   # Soldier Bay (5km to station)
    ("soldier-hole",                          "8726384",  "noaa"),   # Soldier Hole (17km to station)
    ("solitude-bay",                          "9751364",  "noaa"),   # Solitude Bay (8km to station)
    ("solleys-cove",                          "8574680",  "noaa"),   # Solleys Cove (9km to station)
    ("somers-bay",                            "8534720",  "noaa"),   # Somers Bay (9km to station)
    ("somers-cove",                           "8534720",  "noaa"),   # Somers Cove (11km to station)
    ("somerset-long-bay-beach",               "2695540",  "noaa"),   # Somerset Long Bay Beach (18km to station)
    ("somes-cove",                            "8413320",  "noaa"),   # Somes Cove (19km to station)
    ("somes-harbor",                          "8413320",  "noaa"),   # Somes Harbor (10km to station)
    ("somes-sound",                           "8413320",  "noaa"),   # Somes Sound (11km to station)
    ("sommerville-basin",                     "8518750",  "noaa"),   # Sommerville Basin (22km to station)
    ("somoa-beach",                           "9418767",  "noaa"),   # Somoa Beach (6km to station)
    ("son-pond",                              "8760721",  "noaa"),   # Son Pond (12km to station)
    ("sonda-de-vieques",                      "9752235",  "noaa"),   # Sonda de Vieques (6km to station)
    ("sonofa-beach",                          "9751364",  "noaa"),   # Sonofa Beach (5km to station)
    ("sopers-hole",                           "9751381",  "noaa"),   # Sopers Hole (8km to station)
    ("soquel-cove",                           "9413450",  "noaa"),   # Soquel Cove (40km to station)
    ("sorrento-harbor",                       "8413320",  "noaa"),   # Sorrento Harbor (9km to station)
    ("sound-beach",                           "8631044",  "noaa"),   # Sound Beach (19km to station)
    ("sound-beach---east-beach",              "8467150",  "noaa"),   # Sound Beach - East Beach (30km to station)
    ("sound-beach---west-beach",              "8467150",  "noaa"),   # Sound Beach - West Beach (29km to station)
    ("sound-shore",                           "8571421",  "noaa"),   # Sound Shore (40km to station)
    ("soundside-beach",                       "8516945",  "noaa"),   # Soundside Beach (22km to station)
    ("soundview-beach",                       "8461490",  "noaa"),   # Soundview Beach (18km to station)
    ("south-arm-kelp-bay",                    "9451600",  "noaa"),   # South Arm Kelp Bay (34km to station)
    ("south-basin",                           "8536110",  "noaa"),   # South Basin (20km to station)
    ("south-bay",                             "8632200",  "noaa"),   # South Bay (16km to station)
    ("south-coconut-bayou",                   "8726384",  "noaa"),   # South Coconut Bayou (39km to station)
    ("south-cove",                            "8461490",  "noaa"),   # South Cove (24km to station)
    ("south-creek",                           "8575512",  "noaa"),   # South Creek (17km to station)
    ("south-fishtail-bay",                    "9075080",  "noaa"),   # South Fishtail Bay (24km to station)
    ("south-harbor",                          "8534720",  "noaa"),   # South Harbor (18km to station)
    ("south-haulover-bay",                    "9751381",  "noaa"),   # South Haulover Bay (6km to station)
    ("south-haulover-beach",                  "9751381",  "noaa"),   # South Haulover Beach (6km to station)
    ("south-head-beach",                      "8411060",  "noaa"),   # South Head Beach (26km to station)
    ("south-holgate-street-end",              "9446484",  "noaa"),   # South Holgate Street End (36km to station)
    ("south-jerry-cove",                      "8452660",  "noaa"),   # South Jerry Cove (20km to station)
    ("south-landing",                         "8518962",  "noaa"),   # South Landing (4km to station)
    ("south-leopard-creek",                   "8656483",  "noaa"),   # South Leopard Creek (10km to station)
    ("south-oceanside-beach",                 "9410230",  "noaa"),   # South Oceanside Beach (35km to station)
    ("south-oyster-bay",                      "8516945",  "noaa"),   # South Oyster Bay (32km to station)
    ("south-padre-island-nude-beach",         "8779280",  "noaa"),   # South Padre Island Nude Beach (13km to station)
    ("south-pass-lake",                       "8773037",  "noaa"),   # South Pass Lake (17km to station)
    ("south-pine-creek-beach",                "8467150",  "noaa"),   # South Pine Creek Beach (10km to station)
    ("south-point-higgins-beach",             "9450460",  "noaa"),   # South Point Higgins Beach (18km to station)
    ("south-pointe-beach",                    "8723214",  "noaa"),   # South Pointe Beach (5km to station)
    ("south-san-diego-bay",                   "9410170",  "noaa"),   # South San Diego Bay (7km to station)
    ("south-shore",                           "8449130",  "noaa"),   # South Shore (5km to station)
    ("south-sound",                           "9751381",  "noaa"),   # South Sound (40km to station)
    ("south-stop",                            "8726384",  "noaa"),   # South Stop (5km to station)
    ("southeast-jack-williams-bay",           "8747437",  "noaa"),   # Southeast Jack Williams Bay (31km to station)
    ("southern-cove",                         "8413320",  "noaa"),   # Southern Cove (34km to station)
    ("southern-water",                        "8311062",  "noaa"),   # Southern Water (20km to station)
    ("southhampton-bay",                      "9415102",  "noaa"),   # Southhampton Bay (6km to station)
    ("southport-beach",                       "8467150",  "noaa"),   # Southport Beach (11km to station)
    ("southport-harbor",                      "8467150",  "noaa"),   # Southport Harbor (9km to station)
    ("southren-cove",                         "8413320",  "noaa"),   # Southren Cove (33km to station)
    ("southwest-98th-street-end",             "9446484",  "noaa"),   # Southwest 98th Street End (28km to station)
    ("southwest-beach",                       "8447930",  "noaa"),   # Southwest Beach (16km to station)
    ("southwest-brace-point-drive-street-end", "9446484",  "noaa"),   # Southwest Brace Point Drive Street End (28km to station)
    ("southwest-bronson-way-street-end",      "9446484",  "noaa"),   # Southwest Bronson Way Street End (36km to station)
    ("southwest-cove",                        "8536110",  "noaa"),   # Southwest Cove (7km to station)
    ("spa-beach",                             "8726520",  "noaa"),   # Spa Beach (2km to station)
    ("spalding-bight",                        "8774513",  "noaa"),   # Spalding Bight (13km to station)
    ("spanish-bay",                           "8735180",  "noaa"),   # Spanish Bay (2km to station)
    ("spanish-harbor",                        "8723970",  "noaa"),   # Spanish Harbor (23km to station)
    ("spanish-landing-beach",                 "9410170",  "noaa"),   # Spanish Landing Beach (3km to station)
    ("spanish-wall-beach",                    "9759394",  "noaa"),   # Spanish Wall Beach (20km to station)
    ("spar-cove",                             "8418150",  "noaa"),   # Spar Cove (5km to station)
    ("sparrows-beach",                        "8575512",  "noaa"),   # Sparrows Beach (3km to station)
    ("spence-cove",                           "8570283",  "noaa"),   # Spence Cove (14km to station)
    ("spencer-creek",                         "8571892",  "noaa"),   # Spencer Creek (25km to station)
    ("spermaceti-cove",                       "8531680",  "noaa"),   # Spermaceti Cove (5km to station)
    ("spicer-bay",                            "8658163",  "noaa"),   # Spicer Bay (40km to station)
    ("spicers-cove",                          "8418150",  "noaa"),   # Spicers Cove (4km to station)
    ("spidercrab-bay",                        "8632200",  "noaa"),   # Spidercrab Bay (25km to station)
    ("spindle-cove",                          "8413320",  "noaa"),   # Spindle Cove (35km to station)
    ("spiral-cove",                           "9450460",  "noaa"),   # Spiral Cove (38km to station)
    ("spit-bay",                              "8656483",  "noaa"),   # Spit Bay (18km to station)
    ("spitting-caves",                        "1612340",  "noaa"),   # Spitting caves (17km to station)
    ("split-rock-cove",                       "8510560",  "noaa"),   # Split Rock Cove (33km to station)
    ("spooners-cove",                         "9412110",  "noaa"),   # Spooner's Cove (17km to station)
    ("sporthaven-beach",                      "9419750",  "noaa"),   # Sporthaven Beach (33km to station)
    ("spragues-cove",                         "8447930",  "noaa"),   # Spragues Cove (20km to station)
    ("sprat-bay",                             "9751381",  "noaa"),   # Sprat Bay (23km to station)
    ("sprat-beach",                           "9751381",  "noaa"),   # Sprat Beach (23km to station)
    ("sprat-hall-beach",                      "9751401",  "noaa"),   # Sprat Hall Beach (16km to station)
    ("sprat-hole",                            "9751401",  "noaa"),   # Sprat Hole (16km to station)
    ("spriggs-pond",                          "8575512",  "noaa"),   # Spriggs Pond (9km to station)
    ("sprigtail-pond",                        "8760721",  "noaa"),   # Sprigtail Pond (8km to station)
    ("spring-bay",                            "9751381",  "noaa"),   # Spring Bay (16km to station)
    ("spring-bayou",                          "8726724",  "noaa"),   # Spring Bayou (20km to station)
    ("spring-bayou-cove",                     "8773146",  "noaa"),   # Spring Bayou Cove (9km to station)
    ("spring-beach",                          "8418150",  "noaa"),   # Spring Beach (33km to station)
    ("spring-bennys-bay",                     "2695540",  "noaa"),   # Spring Benny's Bay (20km to station)
    ("spring-cove",                           "8635750",  "noaa"),   # Spring Cove (10km to station)
    ("spring-creek",                          "8577330",  "noaa"),   # Spring Creek (22km to station)
    ("spring-pond",                           "8510560",  "noaa"),   # Spring Pond (33km to station)
    ("springhill-brook",                      "8447930",  "noaa"),   # Springhill Brook (31km to station)
    ("spruce-cove",                           "8411060",  "noaa"),   # Spruce Cove (18km to station)
    ("spruce-point-cove",                     "8411060",  "noaa"),   # Spruce Point Cove (8km to station)
    ("spurling-cove",                         "8413320",  "noaa"),   # Spurling Cove (16km to station)
    ("spuyten-duyvil-beach",                  "8516945",  "noaa"),   # Spuyten Duyvil Beach (16km to station)
    ("spyglass-beach",                        "9087031",  "noaa"),   # Spyglass Beach (1km to station)
    ("squibnocket-beach",                     "8447930",  "noaa"),   # Squibnocket Beach (26km to station)
    ("squibnocket-bight",                     "8447930",  "noaa"),   # Squibnocket Bight (24km to station)
    ("squid-bay",                             "9452634",  "noaa"),   # Squid Bay (35km to station)
    ("squid-cove",                            "8413320",  "noaa"),   # Squid Cove (16km to station)
    ("st-catherines-beach",                   "2695535",  "noaa"),   # St Catherine's Beach (3km to station)
    ("st-petersburg-central-yacht-basin",     "8726520",  "noaa"),   # St Petersburg Central Yacht Basin (1km to station)
    ("st-petersburg-south-yacht-basin",       "8726520",  "noaa"),   # St Petersburg South Yacht Basin (1km to station)
    ("st-georges-harbour",                    "2695535",  "noaa"),   # St. George's Harbour (2km to station)
    ("st-hazards-beach",                      "9063079",  "noaa"),   # St. Hazards Beach (16km to station)
    ("st-lukes-bay",                          "9014070",  "noaa"),   # St. Lukes Bay (26km to station)
    ("staffords-bay",                         "8311062",  "noaa"),   # Staffords Bay (30km to station)
    ("stag-bay",                              "9452634",  "noaa"),   # Stag Bay (31km to station)
    ("stage-island-bay",                      "8418150",  "noaa"),   # Stage Island Bay (40km to station)
    ("stage-island-harbor",                   "8418150",  "noaa"),   # Stage Island Harbor (35km to station)
    ("stahl-bayou",                           "9087031",  "noaa"),   # Stahl Bayou (38km to station)
    ("stalley-bay",                           "9751381",  "noaa"),   # Stalley Bay (17km to station)
    ("stallion-cove",                         "8452660",  "noaa"),   # Stallion Cove (20km to station)
    ("stannard-beach",                        "8461490",  "noaa"),   # Stannard Beach (30km to station)
    ("staples-cove",                          "8418150",  "noaa"),   # Staples Cove (20km to station)
    ("staraya-bay",                           "9462620",  "noaa"),   # Staraya Bay (29km to station)
    ("starboard-cove",                        "8411060",  "noaa"),   # Starboard Cove (15km to station)
    ("starfish-cove",                         "9435380",  "noaa"),   # Starfish Cove (6km to station)
    ("starlite-beach",                        "9075065",  "noaa"),   # Starlite Beach (2km to station)
    ("starrigavan-bay",                       "9451600",  "noaa"),   # Starrigavan Bay (9km to station)
    ("starvation-cove",                       "8771486",  "noaa"),   # Starvation Cove (8km to station)
    ("state-park-beach",                      "8661070",  "noaa"),   # State Park Beach (1km to station)
    ("station-cove",                          "8557380",  "noaa"),   # Station Cove (17km to station)
    ("stave-island-harbor",                   "8413320",  "noaa"),   # Stave Island Harbor (7km to station)
    ("steelman-bay",                          "8534720",  "noaa"),   # Steelman Bay (14km to station)
    ("steels-cove",                           "8557380",  "noaa"),   # Steels Cove (18km to station)
    ("steers-beach",                          "8454000",  "noaa"),   # Steers Beach (17km to station)
    ("stehli-beach",                          "8516945",  "noaa"),   # Stehli Beach (18km to station)
    ("steilacoom-waterway",                   "9446484",  "noaa"),   # Steilacoom Waterway (15km to station)
    ("stella-bay",                            "9052000",  "noaa"),   # Stella Bay (29km to station)
    ("steps-beach",                           "8449130",  "noaa"),   # Steps Beach (2km to station)
    ("sterling-bay",                          "9075099",  "noaa"),   # Sterling Bay (12km to station)
    ("stetson-cove",                          "8447435",  "noaa"),   # Stetson Cove (2km to station)
    ("steve-fonyo-beach",                     "9449880",  "noaa"),   # Steve Fonyo Beach (31km to station)
    ("stevens-cove",                          "8510560",  "noaa"),   # Stevens Cove (32km to station)
    ("stevens-creek",                         "8575512",  "noaa"),   # Stevens Creek (14km to station)
    ("stevens-street-public-beach-access",    "8658163",  "noaa"),   # Stevens Street Public Beach Access (33km to station)
    ("stevenson-bay",                         "9075099",  "noaa"),   # Stevenson Bay (18km to station)
    ("steves-cove",                           "8571892",  "noaa"),   # Steves Cove (25km to station)
    ("stewart-beach",                         "8771450",  "noaa"),   # Stewart Beach (3km to station)
    ("stewart-beach-park",                    "8771450",  "noaa"),   # Stewart Beach Park (2km to station)
    ("stewart-cove",                          "8413320",  "noaa"),   # Stewart Cove (20km to station)
    ("stillhouse-cove",                       "8454000",  "noaa"),   # Stillhouse Cove (4km to station)
    ("stillwater-cove",                       "9413450",  "noaa"),   # Stillwater Cove (7km to station)
    ("sting-ray-cove",                        "8726724",  "noaa"),   # Sting Ray Cove (22km to station)
    ("stingaree-cove",                        "8770971",  "noaa"),   # Stingaree Cove (13km to station)
    ("stingaree-point-cove",                  "8631044",  "noaa"),   # Stingaree Point Cove (14km to station)
    ("stirling-basin",                        "8510560",  "noaa"),   # Stirling Basin (34km to station)
    ("stites-sound",                          "8536110",  "noaa"),   # Stites Sound (25km to station)
    ("stocks-harbour",                        "2695535",  "noaa"),   # Stocks Harbour (1km to station)
    ("stone-beach",                           "9063079",  "noaa"),   # Stone Beach (14km to station)
    ("stone-cove",                            "9063079",  "noaa"),   # Stone Cove (14km to station)
    ("stone-pond",                            "8760721",  "noaa"),   # Stone Pond (13km to station)
    ("stoneboro-beach",                       "9416841",  "noaa"),   # Stoneboro Beach (8km to station)
    ("stonehole-bay",                         "2695540",  "noaa"),   # Stonehole Bay (17km to station)
    ("stonehole-bay-beach",                   "2695540",  "noaa"),   # Stonehole Bay Beach (17km to station)
    ("stonehouse-cove",                       "8574680",  "noaa"),   # Stonehouse Cove (4km to station)
    ("stones-cove",                           "8465705",  "noaa"),   # Stones Cove (39km to station)
    ("stonewall-beach",                       "8447930",  "noaa"),   # Stonewall Beach (23km to station)
    ("stoney-beach",                          "8447930",  "noaa"),   # Stoney Beach (1km to station)
    ("stonington-harbor",                     "8461490",  "noaa"),   # Stonington Harbor (16km to station)
    ("stono-inlet",                           "8665530",  "noaa"),   # Stono Inlet (18km to station)
    ("stony-bay",                             "9751381",  "noaa"),   # Stony Bay (16km to station)
    ("stony-beach",                           "8461490",  "noaa"),   # Stony Beach (13km to station)
    ("stony-creek",                           "8574680",  "noaa"),   # Stony Creek (13km to station)
    ("stony-inlet",                           "8551910",  "noaa"),   # Stony Inlet (15km to station)
    ("stough-bayou",                          "8770808",  "noaa"),   # Stough Bayou (6km to station)
    ("stovell-bay",                           "2695540",  "noaa"),   # Stovell Bay (13km to station)
    ("stover-cove",                           "8413320",  "noaa"),   # Stover Cove (30km to station)
    ("strait-bay",                            "9462620",  "noaa"),   # Strait Bay (19km to station)
    ("strange-bayou",                         "8729108",  "noaa"),   # Strange Bayou (20km to station)
    ("strong-island-beach",                   "8447435",  "noaa"),   # Strong Island Beach (4km to station)
    ("stryker-bay",                           "9099064",  "noaa"),   # Stryker Bay (9km to station)
    ("stump-bay",                             "8656483",  "noaa"),   # Stump Bay (33km to station)
    ("stumpy-bay",                            "9751381",  "noaa"),   # Stumpy Bay (30km to station)
    ("stumpy-bay-beach",                      "9751381",  "noaa"),   # Stumpy Bay Beach (30km to station)
    ("sturgeon-cove",                         "8410140",  "noaa"),   # Sturgeon Cove (24km to station)
    ("styron-bay",                            "8656483",  "noaa"),   # Styron Bay (33km to station)
    ("sue-wood-bay",                          "2695540",  "noaa"),   # Sue Wood Bay (9km to station)
    ("sugar-bay",                             "9751364",  "noaa"),   # Sugar Bay (7km to station)
    ("sugar-beach",                           "9751364",  "noaa"),   # Sugar Beach (2km to station)
    ("sugar-cane-point-beach",                "2695540",  "noaa"),   # Sugar Cane Point Beach (17km to station)
    ("sugarbird-beach",                       "9751381",  "noaa"),   # Sugarbird Beach (25km to station)
    ("sugarhouse-cove",                       "8720219",  "noaa"),   # Sugarhouse Cove (35km to station)
    ("sugarloaf-beach",                       "8724580",  "noaa"),   # Sugarloaf Beach (26km to station)
    ("suicide-cove",                          "9452210",  "noaa"),   # Suicide Cove (28km to station)
    ("suisun-bay-reserve-fleet",              "9415102",  "noaa"),   # Suisun Bay Reserve Fleet (5km to station)
    ("sukoi-inlet",                           "9451600",  "noaa"),   # Sukoi Inlet (34km to station)
    ("sukon-strait",                          "9451600",  "noaa"),   # Sukon Strait (31km to station)
    ("summa-beach",                           "8722670",  "noaa"),   # Summa Beach (4km to station)
    ("summer-bay",                            "9462620",  "noaa"),   # Summer Bay (7km to station)
    ("summer-harbor",                         "8413320",  "noaa"),   # Summer Harbor (8km to station)
    ("sun-and-surf-beach-club",               "8516945",  "noaa"),   # Sun and Surf Beach Club (25km to station)
    ("sundown-bay",                           "8774230",  "noaa"),   # Sundown Bay (9km to station)
    ("sunfish-cove",                          "8311062",  "noaa"),   # Sunfish Cove (25km to station)
    ("sunken-forest",                         "8419870",  "noaa"),   # Sunken Forest (5km to station)
    ("sunny-cove",                            "9452210",  "noaa"),   # Sunny Cove (16km to station)
    ("sunny-cove-beach",                      "9413450",  "noaa"),   # Sunny Cove Beach (40km to station)
    ("sunny-harbor",                          "8534720",  "noaa"),   # Sunny Harbor (18km to station)
    ("sunny-ridge-beach",                     "8518750",  "noaa"),   # Sunny Ridge Beach (39km to station)
    ("sunray-beach",                          "8536110",  "noaa"),   # Sunray Beach (9km to station)
    ("sunrise-bay",                           "8722956",  "noaa"),   # Sunrise Bay (7km to station)
    ("sunrise-cove",                          "8413320",  "noaa"),   # Sunrise Cove (35km to station)
    ("sunrise-park-beach",                    "8665530",  "noaa"),   # Sunrise Park Beach (3km to station)
    ("sunset-bay",                            "9432780",  "noaa"),   # Sunset Bay (4km to station)
    ("sunset-beach",                          "8452660",  "noaa"),   # Sunset Beach (7km to station)
    ("sunset-beach-park",                     "9087088",  "noaa"),   # Sunset Beach Park (27km to station)
    ("sunset-bluff-beach",                    "9087031",  "noaa"),   # Sunset Bluff Beach (2km to station)
    ("sunset-cove",                           "8447930",  "noaa"),   # Sunset Cove (24km to station)
    ("sunset-park-beach",                     "9087088",  "noaa"),   # Sunset Park Beach (32km to station)
    ("sunset-state-beach",                    "9413450",  "noaa"),   # Sunset State Beach (32km to station)
    ("sunsi-bay",                             "9751381",  "noaa"),   # Sunsi Bay (17km to station)
    ("suprise-beach",                         "8418150",  "noaa"),   # Suprise Beach (13km to station)
    ("surf-bay",                              "2695535",  "noaa"),   # Surf Bay (4km to station)
    ("surfers-beach",                         "9759394",  "noaa"),   # Surfer's Beach (32km to station)
    ("surfers-end",                           "8452660",  "noaa"),   # Surfer's End (5km to station)
    ("surfing-beach",                         "8639348",  "noaa"),   # Surfing Beach (31km to station)
    ("surge-bay",                             "9452634",  "noaa"),   # Surge Bay (25km to station)
    ("survival-beach",                        "9759394",  "noaa"),   # Survival Beach (32km to station)
    ("sutherland-bayou",                      "8726724",  "noaa"),   # Sutherland Bayou (12km to station)
    ("suzar-bay",                             "9063085",  "noaa"),   # Suzar Bay (12km to station)
    ("swamp-cove",                            "8447435",  "noaa"),   # Swamp Cove (20km to station)
    ("swan-bay",                              "8534720",  "noaa"),   # Swan Bay (24km to station)
    ("swan-cove",                             "8575512",  "noaa"),   # Swan Cove (11km to station)
    ("swan-creek-cove",                       "8571421",  "noaa"),   # Swan Creek Cove (13km to station)
    ("swan-lake",                             "8774230",  "noaa"),   # Swan Lake (11km to station)
    ("swan-lake-association-beach",           "8447435",  "noaa"),   # Swan Lake Association Beach (22km to station)
    ("swan-pond",                             "8571421",  "noaa"),   # Swan Pond (6km to station)
    ("swan-pond-creek",                       "8571421",  "noaa"),   # Swan Pond Creek (6km to station)
    ("swans-bay",                             "2695540",  "noaa"),   # Swan's Bay (11km to station)
    ("swaney-cove",                           "8571421",  "noaa"),   # Swaney Cove (23km to station)
    ("swansea-town-beach",                    "8447386",  "noaa"),   # Swansea Town Beach (5km to station)
    ("swanzy-beach",                          "1612480",  "noaa"),   # Swanzy Beach (15km to station)
    ("swash-bay",                             "8631044",  "noaa"),   # Swash Bay (7km to station)
    ("swash-hole",                            "8637689",  "noaa"),   # Swash Hole (17km to station)
    ("sweatt-beach",                          "8454000",  "noaa"),   # Sweatt Beach (29km to station)
    ("swedes-beach",                          "9414290",  "noaa"),   # Swede's Beach (5km to station)
    ("swedes-bay",                            "9075080",  "noaa"),   # Swedes Bay (25km to station)
    ("swift-beach",                           "9413450",  "noaa"),   # Swift Beach (40km to station)
    ("swift-st-beach",                        "8465705",  "noaa"),   # Swift St. Beach (9km to station)
    ("swifts-beach",                          "8447930",  "noaa"),   # Swifts Beach (24km to station)
    ("swifts-neck-association",               "8447930",  "noaa"),   # Swifts Neck Association (24km to station)
    ("swimming-area",                         "9446484",  "noaa"),   # Swimming Area (19km to station)
    ("swimming-beach",                        "9440422",  "noaa"),   # Swimming Beach (37km to station)
    ("sycamore-beach",                        "8594900",  "noaa"),   # Sycamore Beach (22km to station)
    ("sycamore-cove",                         "8452660",  "noaa"),   # Sycamore Cove (22km to station)
    ("sykes-cove",                            "9450460",  "noaa"),   # Sykes Cove (38km to station)
    ("sylburn-harbor",                        "9450460",  "noaa"),   # Sylburn Harbor (16km to station)
    ("symonds-bay",                           "9451600",  "noaa"),   # Symonds Bay (24km to station)
    ("taachix",                               "9462620",  "noaa"),   # Taachix̂ (18km to station)
    ("tabbs-bay",                             "8770613",  "noaa"),   # Tabbs Bay (2km to station)
    ("table-bay",                             "9451054",  "noaa"),   # Table Bay (27km to station)
    ("tabletops",                             "9410230",  "noaa"),   # Tabletops (15km to station)
    ("tague-bay",                             "9751364",  "noaa"),   # Tague Bay (10km to station)
    ("taiya-inlet",                           "9452400",  "noaa"),   # Taiya Inlet (9km to station)
    ("taiyasanka-harbor",                     "9452400",  "noaa"),   # Taiyasanka Harbor (17km to station)
    ("takanis-bay",                           "9452634",  "noaa"),   # Takanis Bay (32km to station)
    ("takatz-bay",                            "9451600",  "noaa"),   # Takatz Bay (32km to station)
    ("taku-harbor",                           "9452210",  "noaa"),   # Taku Harbor (34km to station)
    ("taku-inlet",                            "9452210",  "noaa"),   # Taku Inlet (21km to station)
    ("tall-timbers-cove",                     "8577330",  "noaa"),   # Tall Timbers Cove (17km to station)
    ("tallow-rock-bay",                       "8311062",  "noaa"),   # Tallow Rock Bay (25km to station)
    ("tamarack-beach",                        "9410230",  "noaa"),   # Tamarack Beach (33km to station)
    ("tamarind-reef-beach",                   "9751364",  "noaa"),   # Tamarind Reef Beach (4km to station)
    ("tamgas-harbor",                         "9450460",  "noaa"),   # Tamgas Harbor (33km to station)
    ("tanani-bay",                            "9452400",  "noaa"),   # Tanani Bay (21km to station)
    ("tanaskan-bay",                          "9462620",  "noaa"),   # Tanaskan Bay (17km to station)
    ("tankards-beach",                        "8632200",  "noaa"),   # Tankards Beach (20km to station)
    ("tanner-creek",                          "8635750",  "noaa"),   # Tanner Creek (14km to station)
    ("tar-bay",                               "8631044",  "noaa"),   # Tar Bay (17km to station)
    ("tar-cove",                              "8575512",  "noaa"),   # Tar Cove (12km to station)
    ("tar-hill-cove",                         "8575512",  "noaa"),   # Tar Hill Cove (13km to station)
    ("tar-hole-inlet",                        "8654467",  "noaa"),   # Tar Hole Inlet (9km to station)
    ("tar-landing-bay",                       "8656483",  "noaa"),   # Tar Landing Bay (3km to station)
    ("tarkill-cove",                          "8635750",  "noaa"),   # Tarkill Cove (17km to station)
    ("tarkiln-bay",                           "8729840",  "noaa"),   # Tarkiln Bay (21km to station)
    ("tarkiln-bayou",                         "8729840",  "noaa"),   # Tarkiln Bayou (20km to station)
    ("tarpaulin-cove",                        "8447930",  "noaa"),   # Tarpaulin Cove (9km to station)
    ("tarpon-bay",                            "8725520",  "noaa"),   # Tarpon Bay (30km to station)
    ("tarpon-cove",                           "8537121",  "noaa"),   # Tarpon Cove (9km to station)
    ("tasaitsat-angayukangak-lagoon",         "9491094",  "noaa"),   # Tasaitsat Angayukangak Lagoon (1km to station)
    ("tasaitsat-lagoons",                     "9491094",  "noaa"),   # Tasaitsat Lagoons (1km to station)
    ("taunton-bay",                           "8413320",  "noaa"),   # Taunton Bay (20km to station)
    ("tautog-cove",                           "8452660",  "noaa"),   # Tautog Cove (30km to station)
    ("taylor-bay",                            "9452634",  "noaa"),   # Taylor Bay (18km to station)
    ("taylor-cove",                           "8635750",  "noaa"),   # Taylor Cove (16km to station)
    ("taylor-creek",                          "8635750",  "noaa"),   # Taylor Creek (34km to station)
    ("taylor-park-beach",                     "8311030",  "noaa"),   # Taylor Park Beach (30km to station)
    ("taylor-sound",                          "8536110",  "noaa"),   # Taylor Sound (9km to station)
    ("taylors-bay",                           "9751381",  "noaa"),   # Taylors Bay (34km to station)
    ("taylors-point-beach",                   "8447930",  "noaa"),   # Taylors Point Beach (25km to station)
    ("te-don-pond",                           "8760721",  "noaa"),   # Te Don Pond (8km to station)
    ("tea-creek",                             "8721604",  "noaa"),   # Tea Creek (16km to station)
    ("teachers-beach",                        "9415020",  "noaa"),   # Teachers Beach (16km to station)
    ("tebenkof-bay",                          "9451054",  "noaa"),   # Tebenkof Bay (39km to station)
    ("teddy-beach",                           "8447386",  "noaa"),   # Teddy Beach (10km to station)
    ("tee-harbor",                            "9452210",  "noaa"),   # Tee Harbor (25km to station)
    ("tektite-bay",                           "9751381",  "noaa"),   # Tektite Bay (1km to station)
    ("temple-bay",                            "8762482",  "noaa"),   # Temple Bay (15km to station)
    ("temple-beach",                          "1612480",  "noaa"),   # Temple Beach (28km to station)
    ("templeton-arm",                         "9432780",  "noaa"),   # Templeton Arm (28km to station)
    ("tennessee-beach",                       "9414290",  "noaa"),   # Tennessee Beach (8km to station)
    ("tennessee-cove",                        "9414290",  "noaa"),   # Tennessee Cove (8km to station)
    ("tenney-cove",                           "8411060",  "noaa"),   # Tenney Cove (26km to station)
    ("tennison-bay",                          "9087088",  "noaa"),   # Tennison Bay (29km to station)
    ("tenthouse-creek",                       "8575512",  "noaa"),   # Tenthouse Creek (16km to station)
    ("terra-ceia-bay",                        "8726384",  "noaa"),   # Terra Ceia Bay (10km to station)
    ("terrapin-creek-bay",                    "8652587",  "noaa"),   # Terrapin Creek Bay (12km to station)
    ("terrapin-sand-cove",                    "8571421",  "noaa"),   # Terrapin Sand Cove (24km to station)
    ("terrill-beach",                         "9449880",  "noaa"),   # Terrill Beach (21km to station)
    ("terry-cove",                            "8729840",  "noaa"),   # Terry Cove (35km to station)
    ("tessiers-bend",                         "8760721",  "noaa"),   # Tessiers Bend (16km to station)
    ("thachers-beach",                        "8447435",  "noaa"),   # Thachers Beach (23km to station)
    ("the-anchorage",                         "8447930",  "noaa"),   # The Anchorage (17km to station)
    ("the-arbors-private-beach",              "9446484",  "noaa"),   # The Arbors Private Beach (39km to station)
    ("the-basin",                             "8658120",  "noaa"),   # The Basin (30km to station)
    ("the-baths",                             "9751381",  "noaa"),   # The Baths (32km to station)
    ("the-bight",                             "9751381",  "noaa"),   # The Bight (11km to station)
    ("the-branch",                            "8418150",  "noaa"),   # The Branch (33km to station)
    ("the-camber",                            "2695540",  "noaa"),   # The Camber (13km to station)
    ("the-canal",                             "8418150",  "noaa"),   # The Canal (4km to station)
    ("the-cove",                              "8447386",  "noaa"),   # The Cove (10km to station)
    ("the-cove-at-lake-lenape",               "8534720",  "noaa"),   # The Cove at Lake Lenape (29km to station)
    ("the-cows-yard",                         "8411060",  "noaa"),   # The Cows Yard (31km to station)
    ("the-crack",                             "2695535",  "noaa"),   # The Crack (4km to station)
    ("the-crawl",                             "2695540",  "noaa"),   # The Crawl (15km to station)
    ("the-creek-beach",                       "8516945",  "noaa"),   # The Creek Beach (17km to station)
    ("the-dock",                              "8418150",  "noaa"),   # The Dock (24km to station)
    ("the-drain",                             "8654467",  "noaa"),   # The Drain (30km to station)
    ("the-dredge",                            "8534720",  "noaa"),   # The Dredge (17km to station)
    ("the-flying-place",                      "8411060",  "noaa"),   # The Flying Place (36km to station)
    ("the-four-mouths",                       "8631044",  "noaa"),   # The Four Mouths (36km to station)
    ("the-glimmer-glass",                     "8531680",  "noaa"),   # The Glimmer Glass (39km to station)
    ("the-gut",                               "8461490",  "noaa"),   # The Gut (9km to station)
    ("the-hobbit-hole",                       "9452634",  "noaa"),   # The Hobbit Hole (6km to station)
    ("the-inkwell-beach",                     "8447930",  "noaa"),   # The Inkwell Beach (13km to station)
    ("the-inlet",                             "8411060",  "noaa"),   # The Inlet (9km to station)
    ("the-kitchen",                           "8726674",  "noaa"),   # The Kitchen (12km to station)
    ("the-knobbs",                            "8419870",  "noaa"),   # The Knobbs (39km to station)
    ("the-lagoon",                            "8741533",  "noaa"),   # The Lagoon (35km to station)
    ("the-landing",                           "9449880",  "noaa"),   # The Landing (18km to station)
    ("the-let",                               "8452660",  "noaa"),   # The Let (24km to station)
    ("the-mix",                               "9759394",  "noaa"),   # The Mix (29km to station)
    ("the-narrows",                           "8570283",  "noaa"),   # The Narrows (18km to station)
    ("the-nook",                              "8413320",  "noaa"),   # The Nook (21km to station)
    ("the-pit",                               "9413450",  "noaa"),   # The Pit (10km to station)
    ("the-pocket",                            "8570283",  "noaa"),   # The Pocket (11km to station)
    ("the-point-2-beach",                     "8534720",  "noaa"),   # The Point 2 Beach (12km to station)
    ("the-pool",                              "8413320",  "noaa"),   # The Pool (17km to station)
    ("the-pots",                              "8452660",  "noaa"),   # The Pots (18km to station)
    ("the-prong",                             "8571421",  "noaa"),   # The Prong (35km to station)
    ("the-punchbowl",                         "8635750",  "noaa"),   # The Punchbowl (32km to station)
    ("the-river",                             "8447435",  "noaa"),   # The River (8km to station)
    ("the-run",                               "8516945",  "noaa"),   # The Run (30km to station)
    ("the-sag",                               "9087031",  "noaa"),   # The Sag (34km to station)
    ("the-sand-hole",                         "8516945",  "noaa"),   # The Sand Hole (27km to station)
    ("the-sands",                             "8635027",  "noaa"),   # The Sands (21km to station)
    ("the-scaur",                             "2695540",  "noaa"),   # The Scaur (19km to station)
    ("the-strand",                            "8447930",  "noaa"),   # The Strand (34km to station)
    ("the-swash",                             "8656483",  "noaa"),   # The Swash (26km to station)
    ("the-thorfare",                          "8570283",  "noaa"),   # The Thorfare (3km to station)
    ("the-tidepond",                          "8571421",  "noaa"),   # The Tidepond (8km to station)
    ("the-trench",                            "8652587",  "noaa"),   # The Trench (9km to station)
    ("the-widows-cove",                       "8447930",  "noaa"),   # The Widows Cove (22km to station)
    ("thea-foss-waterway",                    "9446484",  "noaa"),   # Thea Foss Waterway (2km to station)
    ("theos-cove",                            "2695540",  "noaa"),   # Theo's Cove (15km to station)
    ("theos-cove-beach",                      "2695540",  "noaa"),   # Theo's Cove Beach (15km to station)
    ("thetis-bay",                            "9451054",  "noaa"),   # Thetis Bay (35km to station)
    ("thicket-point-bay",                     "8635750",  "noaa"),   # Thicket Point Bay (6km to station)
    ("thimble-island-harbor",                 "8465705",  "noaa"),   # Thimble Island Harbor (14km to station)
    ("thimbleberry-bay",                      "9451600",  "noaa"),   # Thimbleberry Bay (5km to station)
    ("thinpoint-cove",                        "9459881",  "noaa"),   # Thinpoint Cove (22km to station)
    ("third-cove",                            "8577330",  "noaa"),   # Third Cove (3km to station)
    ("third-lagoon",                          "9449880",  "noaa"),   # Third Lagoon (10km to station)
    ("thistle-cove",                          "9452634",  "noaa"),   # Thistle Cove (36km to station)
    ("thomas-bay",                            "8413320",  "noaa"),   # Thomas Bay (12km to station)
    ("thomassin-pond",                        "8760721",  "noaa"),   # Thomassin Pond (13km to station)
    ("thompson-creek",                        "8575512",  "noaa"),   # Thompson Creek (15km to station)
    ("thompsons-bay",                         "9052000",  "noaa"),   # Thompsons Bay (20km to station)
    ("thompsons-beach",                       "8536110",  "noaa"),   # Thompsons Beach (25km to station)
    ("thompsons-harbor",                      "9075065",  "noaa"),   # Thompsons Harbor (34km to station)
    ("thompsons-lake-state-park-beach",       "8518979",  "noaa"),   # Thompsons Lake State Park Beach (39km to station)
    ("thoms-cove",                            "8574680",  "noaa"),   # Thoms Cove (7km to station)
    ("thorne-arm",                            "9450460",  "noaa"),   # Thorne Arm (24km to station)
    ("thorofare-bay",                         "8656483",  "noaa"),   # Thorofare Bay (39km to station)
    ("thorofare-cove",                        "8571421",  "noaa"),   # Thorofare Cove (25km to station)
    ("thoroughgood-cove",                     "8638610",  "noaa"),   # Thoroughgood Cove (20km to station)
    ("three-entrance-bay",                    "9451600",  "noaa"),   # Three Entrance Bay (8km to station)
    ("three-falls-harbor",                    "8411060",  "noaa"),   # Three Falls Harbor (37km to station)
    ("three-island-bay",                      "9462620",  "noaa"),   # Three Island Bay (36km to station)
    ("three-mile-bay",                        "8747437",  "noaa"),   # Three Mile Bay (32km to station)
    ("thrive-beach",                          "8779280",  "noaa"),   # Thrive Beach (10km to station)
    ("thrush-cove",                           "8461490",  "noaa"),   # Thrush Cove (31km to station)
    ("thukkie-beach",                         "1612340",  "noaa"),   # Thukkie Beach (10km to station)
    ("thumb-cove",                            "8447930",  "noaa"),   # Thumb Cove (18km to station)
    ("thunder-cove",                          "9449880",  "noaa"),   # Thunder Cove (21km to station)
    ("thunder-hole",                          "8413320",  "noaa"),   # Thunder Hole (8km to station)
    ("thurston-basin",                        "8516945",  "noaa"),   # Thurston Basin (19km to station)
    ("tiahs-cove",                            "8447930",  "noaa"),   # Tiah's Cove (18km to station)
    ("tichenor-cove",                         "9431647",  "noaa"),   # Tichenor Cove (0km to station)
    ("tide-mill-cove",                        "8571892",  "noaa"),   # Tide Mill Cove (28km to station)
    ("tide-pool-beach",                       "9416841",  "noaa"),   # Tide Pool Beach (29km to station)
    ("tigs-cove",                             "8571421",  "noaa"),   # Tigs Cove (2km to station)
    ("tilghman-creek",                        "8575512",  "noaa"),   # Tilghman Creek (24km to station)
    ("tilitie-pond",                          "8760721",  "noaa"),   # Tilitie Pond (10km to station)
    ("tillets-cove",                          "8651370",  "noaa"),   # Tillets Cove (15km to station)
    ("tillette-bayou",                        "8726384",  "noaa"),   # Tillette Bayou (8km to station)
    ("tilson-cove",                           "8510560",  "noaa"),   # Tilson Cove (37km to station)
    ("timbalier-bay",                         "8761724",  "noaa"),   # Timbalier Bay (40km to station)
    ("timberlake-residents-beach",            "9063053",  "noaa"),   # Timberlake Residents Beach (18km to station)
    ("timmons-cove",                          "8557380",  "noaa"),   # Timmons Cove (25km to station)
    ("tims-cove",                             "8447930",  "noaa"),   # Tims Cove (24km to station)
    ("tin-house-cove",                        "9415102",  "noaa"),   # Tin House Cove (13km to station)
    ("tisbury-town-beach",                    "8447930",  "noaa"),   # Tisbury Town Beach (9km to station)
    ("titlow-beach",                          "9446484",  "noaa"),   # Titlow Beach (11km to station)
    ("toad-hole",                             "9052000",  "noaa"),   # Toad Hole (17km to station)
    ("tobacco-bay",                           "2695535",  "noaa"),   # Tobacco Bay (2km to station)
    ("tobaccolot-bay",                        "8510560",  "noaa"),   # Tobaccolot Bay (11km to station)
    ("tobay-heading",                         "8516945",  "noaa"),   # Tobay Heading (36km to station)
    ("toby-island-bay",                       "8570283",  "noaa"),   # Toby Island Bay (38km to station)
    ("todd-bay",                              "8418150",  "noaa"),   # Todd Bay (40km to station)
    ("todd-cove",                             "8571421",  "noaa"),   # Todd Cove (1km to station)
    ("todds-bay",                             "8571892",  "noaa"),   # Todds Bay (15km to station)
    ("toledo-harbor",                         "9451054",  "noaa"),   # Toledo Harbor (14km to station)
    ("toll-plaza-beach",                      "9414750",  "noaa"),   # Toll Plaza Beach (6km to station)
    ("tolson-creek",                          "8575512",  "noaa"),   # Tolson Creek (15km to station)
    ("tom-bay",                               "8725520",  "noaa"),   # Tom Bay (31km to station)
    ("tom-cove",                              "8571421",  "noaa"),   # Tom Cove (14km to station)
    ("tom-woods-bay",                         "2695540",  "noaa"),   # Tom Wood's Bay (13km to station)
    ("tomales-beach",                         "9415020",  "noaa"),   # Tomales Beach (20km to station)
    ("toms-gut",                              "8631044",  "noaa"),   # Toms Gut (37km to station)
    ("toms-harbor",                           "8723970",  "noaa"),   # Toms Harbor (20km to station)
    ("tongore-park-beach",                    "8518962",  "noaa"),   # Tongore Park Beach (23km to station)
    ("tongue-shoal",                          "8410140",  "noaa"),   # Tongue Shoal (18km to station)
    ("tonys-pond",                            "8760721",  "noaa"),   # Tonys Pond (12km to station)
    ("toothacher-cove",                       "8413320",  "noaa"),   # Toothacher Cove (33km to station)
    ("toothacker-bay",                        "8413320",  "noaa"),   # Toothacker Bay (37km to station)
    ("topanga-county-beach",                  "9410840",  "noaa"),   # Topanga County Beach (8km to station)
    ("topsail-sound",                         "8658163",  "noaa"),   # Topsail Sound (17km to station)
    ("torch-bay",                             "9452634",  "noaa"),   # Torch Bay (30km to station)
    ("torrey-pines-city-beach",               "9410230",  "noaa"),   # Torrey Pines City Beach (1km to station)
    ("totem-bight",                           "9450460",  "noaa"),   # Totem Bight (14km to station)
    ("tottman-cove",                          "8418150",  "noaa"),   # Tottman Cove (34km to station)
    ("touglaalek-bay",                        "9455500",  "noaa"),   # Touglaalek Bay (38km to station)
    ("tourist-park",                          "9087088",  "noaa"),   # Tourist Park (1km to station)
    ("town-beach",                            "8447930",  "noaa"),   # Town Beach (12km to station)
    ("town-cove",                             "8447435",  "noaa"),   # Town Cove (14km to station)
    ("town-creek",                            "8577330",  "noaa"),   # Town Creek (3km to station)
    ("towner-cove",                           "8573364",  "noaa"),   # Towner Cove (18km to station)
    ("townsend-sound",                        "8536110",  "noaa"),   # Townsend Sound (28km to station)
    ("toy-harbor",                            "9451600",  "noaa"),   # Toy Harbor (40km to station)
    ("trading-bay",                           "9455760",  "noaa"),   # Trading Bay (29km to station)
    ("trails-end-bay",                        "9075080",  "noaa"),   # Trails End Bay (7km to station)
    ("traitors-inlet",                        "9441102",  "noaa"),   # Traitors Inlet (8km to station)
    ("travis-cove",                           "8551910",  "noaa"),   # Travis Cove (13km to station)
    ("trellis-bay",                           "9751381",  "noaa"),   # Trellis Bay (25km to station)
    ("trent-hall-creek",                      "8577330",  "noaa"),   # Trent Hall Creek (27km to station)
    ("trespass-pond",                         "8760721",  "noaa"),   # Trespass Pond (10km to station)
    ("trestle-beach",                         "9440422",  "noaa"),   # Trestle Beach (25km to station)
    ("triangle-beach",                        "8447930",  "noaa"),   # Triangle Beach (26km to station)
    ("trickys-cove",                          "8419870",  "noaa"),   # Trickys Cove (8km to station)
    ("trinidad-state-beach",                  "9418767",  "noaa"),   # Trinidad State Beach (34km to station)
    ("trippe-bay",                            "8571892",  "noaa"),   # Trippe Bay (20km to station)
    ("triton-beach",                          "8575512",  "noaa"),   # Triton Beach (11km to station)
    ("trollers-cove",                         "9450460",  "noaa"),   # Trollers Cove (37km to station)
    ("tropicana-beach",                       "8534720",  "noaa"),   # Tropicana Beach (2km to station)
    ("trotsky-inlet",                         "9446484",  "noaa"),   # Trotsky Inlet (31km to station)
    ("trotts-bay",                            "2695535",  "noaa"),   # Trott's Bay (5km to station)
    ("trouble-creek",                         "8726724",  "noaa"),   # Trouble Creek (29km to station)
    ("trout-creek",                           "8570283",  "noaa"),   # Trout Creek (2km to station)
    ("truman-beach",                          "8724580",  "noaa"),   # Truman Beach (1km to station)
    ("trumans-beach",                         "8461490",  "noaa"),   # Truman's Beach (32km to station)
    ("trunk-beach",                           "9751381",  "noaa"),   # Trunk Beach (6km to station)
    ("tsa-cove",                              "9450460",  "noaa"),   # Tsa Cove (21km to station)
    ("tubbs-cove",                            "8570283",  "noaa"),   # Tubbs Cove (15km to station)
    ("tubby-cove",                            "8573364",  "noaa"),   # Tubby Cove (19km to station)
    ("tuckers-bay",                           "2695540",  "noaa"),   # Tucker's Bay (6km to station)
    ("tuckers-cove",                          "8419870",  "noaa"),   # Tuckers Cove (3km to station)
    ("tudors-bay",                            "2695540",  "noaa"),   # Tudor's Bay (21km to station)
    ("tugboat-beach",                         "9449880",  "noaa"),   # Tugboat Beach (26km to station)
    ("tulalip-shores",                        "9444900",  "noaa"),   # Tulalip Shores (33km to station)
    ("tulcan-slough",                         "9455500",  "noaa"),   # Tulcan Slough (12km to station)
    ("tullytown-cove",                        "8548989",  "noaa"),   # Tullytown Cove (5km to station)
    ("tumbledown-cove",                       "8413320",  "noaa"),   # Tumbledown Cove (8km to station)
    ("tump-gut",                              "8656483",  "noaa"),   # Tump Gut (36km to station)
    ("tunitas-beach",                         "9414523",  "noaa"),   # Tunitas Beach (24km to station)
    ("tunnel-bay",                            "8311030",  "noaa"),   # Tunnel Bay (19km to station)
    ("turbats-creek",                         "8418150",  "noaa"),   # Turbats Creek (37km to station)
    ("turkey-basin",                          "8724580",  "noaa"),   # Turkey Basin (25km to station)
    ("turkey-swamp-park",                     "8548989",  "noaa"),   # Turkey Swamp Park (39km to station)
    ("turkeyland-cove",                       "8447930",  "noaa"),   # Turkeyland Cove (20km to station)
    ("turnagain-bay",                         "8656483",  "noaa"),   # Turnagain Bay (34km to station)
    ("turner-bay",                            "9751381",  "noaa"),   # Turner Bay (8km to station)
    ("turner-beach",                          "8725520",  "noaa"),   # Turner Beach (36km to station)
    ("turner-cove",                           "8452660",  "noaa"),   # Turner Cove (19km to station)
    ("turner-hole",                           "9751364",  "noaa"),   # Turner Hole (10km to station)
    ("turner-pond-beach",                     "8454000",  "noaa"),   # Turner Pond Beach (40km to station)
    ("turners-beach",                         "8725520",  "noaa"),   # Turner's Beach (35km to station)
    ("turpin-cove",                           "8570283",  "noaa"),   # Turpin Cove (22km to station)
    ("turquoise-beach",                       "9751381",  "noaa"),   # Turquoise Beach (12km to station)
    ("turtle-cove",                           "8516945",  "noaa"),   # Turtle Cove (6km to station)
    ("turtle-creek-bay",                      "9063085",  "noaa"),   # Turtle Creek Bay (29km to station)
    ("turwar-riffle",                         "9419750",  "noaa"),   # Turwar Riffle (32km to station)
    ("tutka-bay",                             "9455500",  "noaa"),   # Tutka Bay (16km to station)
    ("tutu-bay",                              "9751381",  "noaa"),   # Tutu Bay (18km to station)
    ("tutu-beach",                            "9751381",  "noaa"),   # Tutu Beach (18km to station)
    ("twentyseven-pond",                      "8760721",  "noaa"),   # Twentyseven Pond (10km to station)
    ("twilight-harbor",                       "8761305",  "noaa"),   # Twilight Harbor (40km to station)
    ("twin-river-surf-beach",                 "9444090",  "noaa"),   # Twin River Surf Beach (38km to station)
    ("twin-rivers-beach-east",                "8454000",  "noaa"),   # Twin Rivers Beach East (9km to station)
    ("twirly-hole",                           "8577330",  "noaa"),   # Twirly Hole (32km to station)
    ("twitch-cove",                           "8571421",  "noaa"),   # Twitch Cove (26km to station)
    ("twixt-hills-beach",                     "8467150",  "noaa"),   # Twixt Hills Beach (32km to station)
    ("two-mile-beach",                        "8536110",  "noaa"),   # Two Mile Beach (9km to station)
    ("tybee-roads",                           "8670870",  "noaa"),   # Tybee Roads (8km to station)
    ("tyler-bayou",                           "9087031",  "noaa"),   # Tyler Bayou (14km to station)
    ("tyler-cove",                            "8577330",  "noaa"),   # Tyler Cove (20km to station)
    ("tyler-creek",                           "8571421",  "noaa"),   # Tyler Creek (28km to station)
    ("tylers-cove",                           "8465705",  "noaa"),   # Tylers Cove (35km to station)
    ("tynes-bay",                             "2695540",  "noaa"),   # Tynes Bay (9km to station)
    ("ufo-beach-clothing-optional",           "8779280",  "noaa"),   # UFO Beach (clothing optional) (10km to station)
    ("uaoa-bay",                              "1615680",  "noaa"),   # Uaoa Bay (21km to station)
    ("udagak-bay",                            "9462620",  "noaa"),   # Udagak Bay (22km to station)
    ("udamak-cove",                           "9462620",  "noaa"),   # Udamak Cove (31km to station)
    ("udamat-bay",                            "9462620",  "noaa"),   # Udamat Bay (22km to station)
    ("ugadaga-bay",                           "9462620",  "noaa"),   # Ugadaga Bay (10km to station)
    ("ukumehame-beach-park",                  "1615680",  "noaa"),   # Ukumehame Beach Park (16km to station)
    ("ulster-landing-beach",                  "8518962",  "noaa"),   # Ulster Landing Beach (1km to station)
    ("ulumalu",                               "1615680",  "noaa"),   # Ulumalu (19km to station)
    ("uncas-point-beach",                     "8516945",  "noaa"),   # Uncas Point Beach (28km to station)
    ("uncle-georges-cove",                    "8447930",  "noaa"),   # Uncle Georges Cove (21km to station)
    ("uncle-roberts-cove",                    "8447435",  "noaa"),   # Uncle Roberts Cove (27km to station)
    ("undercliff-beach",                      "8516945",  "noaa"),   # Undercliff Beach (17km to station)
    ("uniktali-bay",                          "9462620",  "noaa"),   # Uniktali Bay (11km to station)
    ("united-states-coast-guard-yards-and-docks", "9076070",  "noaa"),   # United States Coast Guard Yards and Docks (3km to station)
    ("university-beach",                      "8775792",  "noaa"),   # University Beach (12km to station)
    ("unulau",                                "1611400",  "noaa"),   # Unulau (2km to station)
    ("upper-beach",                           "8510560",  "noaa"),   # Upper Beach (31km to station)
    ("upper-big-bay",                         "8311030",  "noaa"),   # Upper Big Bay (19km to station)
    ("upper-deep-bay",                        "8311030",  "noaa"),   # Upper Deep Bay (28km to station)
    ("upper-deep-hole",                       "8452944",  "noaa"),   # Upper Deep Hole (37km to station)
    ("upper-goose-bayou",                     "8729108",  "noaa"),   # Upper Goose Bayou (10km to station)
    ("upper-greens-cove",                     "8571421",  "noaa"),   # Upper Greens Cove (19km to station)
    ("upper-harvey-cove",                     "8418150",  "noaa"),   # Upper Harvey Cove (33km to station)
    ("upper-herring-cove",                    "8411060",  "noaa"),   # Upper Herring Cove (32km to station)
    ("upper-mccotter-bay",                    "8656483",  "noaa"),   # Upper McCotter Bay (36km to station)
    ("upper-sag-harbor-cove",                 "8510560",  "noaa"),   # Upper Sag Harbor Cove (30km to station)
    ("upper-san-jacinto-bay",                 "8770613",  "noaa"),   # Upper San Jacinto Bay (6km to station)
    ("upper-sugarloaf-sound",                 "8724580",  "noaa"),   # Upper Sugarloaf Sound (29km to station)
    ("upper-thirty-six-bay",                  "8725520",  "noaa"),   # Upper Thirty-six Bay (26km to station)
    ("upper-turning-basin",                   "9446484",  "noaa"),   # Upper Turning Basin (29km to station)
    ("upshur-bay",                            "8631044",  "noaa"),   # Upshur Bay (10km to station)
    ("urann-cove",                            "8413320",  "noaa"),   # Urann Cove (16km to station)
    ("urie-bay",                              "9075099",  "noaa"),   # Urie Bay (34km to station)
    ("usher-cove",                            "8452944",  "noaa"),   # Usher Cove (7km to station)
    ("vor-beach",                             "1615680",  "noaa"),   # VOR Beach (5km to station)
    ("vaca-key-bight",                        "8723970",  "noaa"),   # Vaca Key Bight (4km to station)
    ("vaill-beach",                           "8510560",  "noaa"),   # Vaill Beach (34km to station)
    ("vajo-de-manglar",                       "9755371",  "noaa"),   # Vajo de Manglar (1km to station)
    ("valdez-arm",                            "9454240",  "noaa"),   # Valdez Arm (29km to station)
    ("valdez-marine-terminal",                "9454240",  "noaa"),   # Valdez Marine Terminal (4km to station)
    ("valdez-small-boat-harbor",              "9454240",  "noaa"),   # Valdez Small Boat Harbor (1km to station)
    ("valentiers-pond",                       "8760721",  "noaa"),   # Valentiers Pond (11km to station)
    ("valentine-creek",                       "8575512",  "noaa"),   # Valentine Creek (12km to station)
    ("vallenar-bay",                          "9450460",  "noaa"),   # Vallenar Bay (15km to station)
    ("valley-cove",                           "8413320",  "noaa"),   # Valley Cove (13km to station)
    ("van-damme-beach",                       "9416841",  "noaa"),   # Van Damme Beach (40km to station)
    ("vanderburgh-cove",                      "8518962",  "noaa"),   # Vanderburgh Cove (15km to station)
    ("vaughans-bay",                          "2695535",  "noaa"),   # Vaughan's Bay (4km to station)
    ("veazey-cove",                           "8573927",  "noaa"),   # Veazey Cove (11km to station)
    ("venetian-bayou",                        "8534720",  "noaa"),   # Venetian Bayou (18km to station)
    ("venetian-shores-beach",                 "8516945",  "noaa"),   # Venetian Shores Beach (38km to station)
    ("vernam-basin",                          "8518750",  "noaa"),   # Vernam Basin (21km to station)
    ("vessup-bay",                            "9751381",  "noaa"),   # Vessup Bay (13km to station)
    ("vickers-bay",                           "2695540",  "noaa"),   # Vickers Bay (10km to station)
    ("villa-angela-beach",                    "9063063",  "noaa"),   # Villa Angela Beach (8km to station)
    ("villa-beach",                           "9063063",  "noaa"),   # Villa Beach (6km to station)
    ("villa-marina-yacht-basin",              "9753216",  "noaa"),   # Villa Marina Yacht Basin (1km to station)
    ("villa-rosa-terrace-beach",              "8465705",  "noaa"),   # Villa Rosa Terrace Beach (10km to station)
    ("village-of-ephraim-public-beach",       "9087088",  "noaa"),   # Village of Ephraim Public Beach (33km to station)
    ("virgin-bay",                            "9454240",  "noaa"),   # Virgin Bay (32km to station)
    ("voight-bay",                            "9075080",  "noaa"),   # Voight Bay (32km to station)
    ("volcano-bay",                           "9462620",  "noaa"),   # Volcano Bay (39km to station)
    ("voyageurs-bay",                         "9075080",  "noaa"),   # Voyageurs Bay (13km to station)
    ("waccasassa-bay",                        "8727520",  "noaa"),   # Waccasassa Bay (19km to station)
    ("wadding-cove",                          "9450460",  "noaa"),   # Wadding Cove (36km to station)
    ("waddington-beach",                      "8311030",  "noaa"),   # Waddington Beach (26km to station)
    ("wade-creek",                            "8656483",  "noaa"),   # Wade Creek (16km to station)
    ("wades-bayou",                           "9087031",  "noaa"),   # Wade's Bayou (14km to station)
    ("wades-beach",                           "8510560",  "noaa"),   # Wade's Beach (31km to station)
    ("wades-cove",                            "8447930",  "noaa"),   # Wades Cove (19km to station)
    ("wading-creek",                          "8656483",  "noaa"),   # Wading Creek (4km to station)
    ("wading-river-landing",                  "8465705",  "noaa"),   # Wading River Landing (36km to station)
    ("wadmalaw-sound",                        "8665530",  "noaa"),   # Wadmalaw Sound (27km to station)
    ("wagosh-bay",                            "9075099",  "noaa"),   # Wagosh Bay (36km to station)
    ("wahiawa-bay",                           "1611400",  "noaa"),   # Wahiawa Bay (24km to station)
    ("waiakailio-bay",                        "1617433",  "noaa"),   # Waiakailio Bay (5km to station)
    ("waialae-beach",                         "1612340",  "noaa"),   # Waialae Beach (10km to station)
    ("waialea-bay",                           "1617433",  "noaa"),   # Waialea Bay (6km to station)
    ("waialee-beach",                         "1612480",  "noaa"),   # Waialee Beach (38km to station)
    ("waikk-beach",                           "1612340",  "noaa"),   # Waikīkī Beach (5km to station)
    ("wailua-nui-bay",                        "1615680",  "noaa"),   # Wailua Nui Bay (36km to station)
    ("wailuaiki-bay",                         "1615680",  "noaa"),   # Wailuaiki Bay (36km to station)
    ("waimanu-bay",                           "1617433",  "noaa"),   # Waimanu Bay (24km to station)
    ("waimnalo-bay",                          "1612480",  "noaa"),   # Waimānalo Bay (14km to station)
    ("wainanalii-pond",                       "1617433",  "noaa"),   # Wainanalii Pond (22km to station)
    ("wainiha-bay",                           "1611400",  "noaa"),   # Wainiha Bay (35km to station)
    ("waiohue-bay",                           "1615680",  "noaa"),   # Waiohue Bay (38km to station)
    ("waipio-bay",                            "1617433",  "noaa"),   # Waipio Bay (27km to station)
    ("waiska-bay",                            "9076070",  "noaa"),   # Waiska Bay (18km to station)
    ("waites-island-beach",                   "8661070",  "noaa"),   # Waites Island Beach (38km to station)
    ("waiulua-bay",                           "1617433",  "noaa"),   # Waiulua Bay (14km to station)
    ("wake-beach",                            "8637689",  "noaa"),   # Wake Beach (40km to station)
    ("wakeby-lake-at-ryder-conservation-beach", "8447930",  "noaa"),   # Wakeby lake at Ryder Conservation Beach (23km to station)
    ("wakeman-beach",                         "9431647",  "noaa"),   # Wakeman Beach (29km to station)
    ("waleback-cove",                         "8411060",  "noaa"),   # Waleback Cove (12km to station)
    ("walk-on-beach",                         "9416841",  "noaa"),   # Walk On Beach (28km to station)
    ("walker-cove",                           "8452944",  "noaa"),   # Walker Cove (9km to station)
    ("walkters-harbor",                       "9075099",  "noaa"),   # Walkters Harbor (22km to station)
    ("wall-beach",                            "9415020",  "noaa"),   # Wall Beach (22km to station)
    ("wall-cove",                             "8574680",  "noaa"),   # Wall Cove (14km to station)
    ("wallabout-bay",                         "8518750",  "noaa"),   # Wallabout Bay (3km to station)
    ("wallabout-channel",                     "8518750",  "noaa"),   # Wallabout Channel (4km to station)
    ("wallace-beach",                         "9063063",  "noaa"),   # Wallace Beach (27km to station)
    ("wallops-beach",                         "8631044",  "noaa"),   # Wallops Beach (33km to station)
    ("walsingham-bay",                        "2695535",  "noaa"),   # Walsingham Bay (3km to station)
    ("waltz-key-basin",                       "8724580",  "noaa"),   # Waltz Key Basin (19km to station)
    ("waquoit-bay",                           "8447930",  "noaa"),   # Waquoit Bay (13km to station)
    ("ward-cove",                             "9450460",  "noaa"),   # Ward Cove (10km to station)
    ("ware-cove",                             "8557380",  "noaa"),   # Ware Cove (23km to station)
    ("ware-point-cove",                       "8571421",  "noaa"),   # Ware Point Cove (8km to station)
    ("warehouse-cove",                        "8637689",  "noaa"),   # Warehouse Cove (34km to station)
    ("warehouse-creek",                       "8575512",  "noaa"),   # Warehouse Creek (8km to station)
    ("warm-spring-bay",                       "9451600",  "noaa"),   # Warm Spring Bay (34km to station)
    ("warm-springs-bay",                      "9451600",  "noaa"),   # Warm Springs Bay (32km to station)
    ("warners-cove",                          "9075099",  "noaa"),   # Warners Cove (14km to station)
    ("warren-bayou",                          "8729108",  "noaa"),   # Warren Bayou (16km to station)
    ("warren-town-beach",                     "8452944",  "noaa"),   # Warren Town Beach (5km to station)
    ("warwick-long-bay",                      "2695540",  "noaa"),   # Warwick Long Bay (16km to station)
    ("warwick-long-bay-beach",                "2695540",  "noaa"),   # Warwick Long Bay Beach (16km to station)
    ("washaway-beach",                        "9440910",  "noaa"),   # Washaway Beach (10km to station)
    ("washing-pond-beach",                    "8449130",  "noaa"),   # Washing Pond Beach (4km to station)
    ("washington-lake-beach",                 "8545240",  "noaa"),   # Washington Lake Beach (22km to station)
    ("washington-pond",                       "8760721",  "noaa"),   # Washington Pond (11km to station)
    ("wassaw-sound",                          "8670870",  "noaa"),   # Wassaw Sound (12km to station)
    ("watchemoket-cove",                      "8454000",  "noaa"),   # Watchemoket Cove (2km to station)
    ("water-bay",                             "9751381",  "noaa"),   # Water Bay (15km to station)
    ("water-bay-beach",                       "9751381",  "noaa"),   # Water Bay Beach (15km to station)
    ("water-cove",                            "8418150",  "noaa"),   # Water Cove (23km to station)
    ("water-creek",                           "9751381",  "noaa"),   # Water Creek (5km to station)
    ("water-lemon-cay-beach",                 "9751381",  "noaa"),   # Water Lemon Cay Beach (5km to station)
    ("water-ski-beach",                       "9449880",  "noaa"),   # Water Ski Beach (29km to station)
    ("water-tank-bay",                        "1615680",  "noaa"),   # Water Tank Bay (35km to station)
    ("water-turkey-bayou",                    "8725520",  "noaa"),   # Water Turkey Bayou (32km to station)
    ("waterfall-cove",                        "9451600",  "noaa"),   # Waterfall Cove (35km to station)
    ("waterfront",                            "8725520",  "noaa"),   # Waterfront (22km to station)
    ("waterhole-cove",                        "8575512",  "noaa"),   # Waterhole Cove (28km to station)
    ("waterlemon-bay",                        "9751381",  "noaa"),   # Waterlemon Bay (5km to station)
    ("waterlily-bay",                         "8311062",  "noaa"),   # Waterlily Bay (19km to station)
    ("watermelon-bay",                        "8767816",  "noaa"),   # Watermelon Bay (9km to station)
    ("watermill-beach",                       "8510560",  "noaa"),   # Watermill Beach (37km to station)
    ("waters-bay",                            "8658163",  "noaa"),   # Waters Bay (34km to station)
    ("waterway-harbor",                       "9075080",  "noaa"),   # Waterway Harbor (23km to station)
    ("watson-bayou",                          "8729108",  "noaa"),   # Watson Bayou (2km to station)
    ("watts-bay",                             "8631044",  "noaa"),   # Watts Bay (38km to station)
    ("watts-cove",                            "8413320",  "noaa"),   # Watts Cove (34km to station)
    ("waverly-cove",                          "8635750",  "noaa"),   # Waverly Cove (34km to station)
    ("wawaion-bay",                           "1617433",  "noaa"),   # Wawaionū Bay (14km to station)
    ("weaver-cove",                           "8452660",  "noaa"),   # Weaver Cove (9km to station)
    ("weavers-cove",                          "8447386",  "noaa"),   # Weavers Cove (3km to station)
    ("webber-cove",                           "8413320",  "noaa"),   # Webber Cove (24km to station)
    ("webers-cove",                           "8516945",  "noaa"),   # Webers Cove (31km to station)
    ("webster-bay",                           "8311062",  "noaa"),   # Webster Bay (27km to station)
    ("webster-cove",                          "8571421",  "noaa"),   # Webster Cove (18km to station)
    ("weeburn-beach",                         "8467150",  "noaa"),   # Weeburn Beach (25km to station)
    ("weed-beach",                            "8467150",  "noaa"),   # Weed Beach (30km to station)
    ("weir-cove",                             "8413320",  "noaa"),   # Weir Cove (16km to station)
    ("weir-creek",                            "8516945",  "noaa"),   # Weir Creek (4km to station)
    ("weirs-beach",                           "9444090",  "noaa"),   # Weir's Beach (26km to station)
    ("welcome-cove",                          "8452660",  "noaa"),   # Welcome Cove (18km to station)
    ("well-bay",                              "2695535",  "noaa"),   # Well Bay (4km to station)
    ("well-bay-beach",                        "2695535",  "noaa"),   # Well Bay Beach (4km to station)
    ("wellridge-creek",                       "8571421",  "noaa"),   # Wellridge Creek (26km to station)
    ("wells-creek",                           "8651370",  "noaa"),   # Wells Creek (14km to station)
    ("welsh-cove",                            "8419870",  "noaa"),   # Welsh Cove (9km to station)
    ("wemps-bay",                             "9052000",  "noaa"),   # Wemps Bay (36km to station)
    ("wendt-beach",                           "9063020",  "noaa"),   # Wendt Beach (26km to station)
    ("wequaquet-estates-beach",               "8447930",  "noaa"),   # Wequaquet Estates Beach (32km to station)
    ("wequaquet-lake-beach",                  "8447930",  "noaa"),   # Wequaquet Lake Beach (32km to station)
    ("wequetequock-cove",                     "8461490",  "noaa"),   # Wequetequock Cove (18km to station)
    ("wes-cove",                              "8770613",  "noaa"),   # Wes Cove (32km to station)
    ("wescoat-cove",                          "8632200",  "noaa"),   # Wescoat Cove (17km to station)
    ("wescott-beach",                         "8454000",  "noaa"),   # Wescott Beach (26km to station)
    ("wescott-cove",                          "8631044",  "noaa"),   # Wescott Cove (16km to station)
    ("west-arm-port-dick",                    "9455500",  "noaa"),   # West Arm Port Dick (35km to station)
    ("west-bay",                              "9063079",  "noaa"),   # West Bay (8km to station)
    ("west-bayou",                            "8728690",  "noaa"),   # West Bayou (12km to station)
    ("west-branch-little-kennebec-bay",       "8411060",  "noaa"),   # West Branch Little Kennebec Bay (18km to station)
    ("west-canal-marina",                     "9063020",  "noaa"),   # West Canal Marina (20km to station)
    ("west-carrying-place-cove",              "8413320",  "noaa"),   # West Carrying Place Cove (37km to station)
    ("west-champagne-bay",                    "8761724",  "noaa"),   # West Champagne Bay (9km to station)
    ("west-cove",                             "8452660",  "noaa"),   # West Cove (4km to station)
    ("west-cove-beach",                       "8518962",  "noaa"),   # West Cove Beach (21km to station)
    ("west-crawfish-inlet",                   "9451600",  "noaa"),   # West Crawfish Inlet (28km to station)
    ("west-denny-way-street-end",             "9446484",  "noaa"),   # West Denny Way Street End (39km to station)
    ("west-end-bay",                          "9751401",  "noaa"),   # West End Bay (14km to station)
    ("west-gulf-place",                       "8735180",  "noaa"),   # West Gulf Place (37km to station)
    ("west-harbor",                           "8461490",  "noaa"),   # West Harbor (14km to station)
    ("west-harbor-beach",                     "8516945",  "noaa"),   # West Harbor Beach (21km to station)
    ("west-jetty",                            "8729840",  "noaa"),   # West Jetty (36km to station)
    ("west-karako-bay",                       "8747437",  "noaa"),   # West Karako Bay (35km to station)
    ("west-landing",                          "8518962",  "noaa"),   # West Landing (4km to station)
    ("west-moran-bay",                        "9075080",  "noaa"),   # West Moran Bay (12km to station)
    ("west-neck-bay",                         "8510560",  "noaa"),   # West Neck Bay (34km to station)
    ("west-neck-beach",                       "8516945",  "noaa"),   # West Neck Beach (26km to station)
    ("west-neck-harbor",                      "8510560",  "noaa"),   # West Neck Harbor (32km to station)
    ("west-pond",                             "8413320",  "noaa"),   # West Pond (12km to station)
    ("west-prong",                            "8721604",  "noaa"),   # West Prong (20km to station)
    ("west-river",                            "8575512",  "noaa"),   # West River (13km to station)
    ("west-shore-sandy-beach",                "8418150",  "noaa"),   # West Shore Sandy Beach (3km to station)
    ("west-silver-sands-beach",               "8465705",  "noaa"),   # West Silver Sands Beach (5km to station)
    ("west-thomas-street-end",                "9446484",  "noaa"),   # West Thomas Street End (40km to station)
    ("west-thorofare-bay",                    "8656483",  "noaa"),   # West Thorofare Bay (36km to station)
    ("west-twin-beach",                       "9444090",  "noaa"),   # West Twin Beach (38km to station)
    ("west-whale-bay",                        "2695540",  "noaa"),   # West Whale Bay (21km to station)
    ("westcott-cove",                         "8467150",  "noaa"),   # Westcott Cove (32km to station)
    ("western-bay",                           "8413320",  "noaa"),   # Western Bay (16km to station)
    ("western-beach",                         "8418150",  "noaa"),   # Western Beach (15km to station)
    ("western-branch-corrotoman-river",       "8635750",  "noaa"),   # Western Branch Corrotoman River (32km to station)
    ("western-cove",                          "8413320",  "noaa"),   # Western Cove (38km to station)
    ("westhaven-cove",                        "9441102",  "noaa"),   # Westhaven Cove (1km to station)
    ("westmouth-bay",                         "8656483",  "noaa"),   # Westmouth Bay (11km to station)
    ("weston-beach",                          "9413450",  "noaa"),   # Weston Beach (12km to station)
    ("westport-beach",                        "9440422",  "noaa"),   # Westport Beach (33km to station)
    ("wetzler-cove",                          "8516945",  "noaa"),   # Wetzler Cove (29km to station)
    ("whale-bone-beach",                      "9414523",  "noaa"),   # Whale Bone Beach (22km to station)
    ("whale-cove",                            "9435380",  "noaa"),   # Whale Cove (18km to station)
    ("whale-creek",                           "8656483",  "noaa"),   # Whale Creek (9km to station)
    ("whale-head-bay",                        "8651370",  "noaa"),   # Whale Head Bay (22km to station)
    ("whale-point-bay",                       "9751364",  "noaa"),   # Whale Point Bay (14km to station)
    ("whalebone-bay",                         "2695540",  "noaa"),   # Whalebone Bay (1km to station)
    ("whalen-bay",                            "9454240",  "noaa"),   # Whalen Bay (35km to station)
    ("whalers-cove",                          "9414523",  "noaa"),   # Whaler's Cove (39km to station)
    ("wharf-bay",                             "8651370",  "noaa"),   # Wharf Bay (28km to station)
    ("wharf-cove",                            "8418150",  "noaa"),   # Wharf Cove (5km to station)
    ("wharf-creek",                           "8575512",  "noaa"),   # Wharf Creek (15km to station)
    ("wharton-bayou",                         "8771972",  "noaa"),   # Wharton Bayou (10km to station)
    ("wheatfield-cove",                       "8452660",  "noaa"),   # Wheatfield Cove (18km to station)
    ("wheatley-point-cove",                   "8571421",  "noaa"),   # Wheatley Point Cove (18km to station)
    ("whiskey-bay",                           "8761305",  "noaa"),   # Whiskey Bay (40km to station)
    ("whiskey-cove",                          "9454050",  "noaa"),   # Whiskey Cove (19km to station)
    ("whiskey-harbor",                        "9075014",  "noaa"),   # Whiskey Harbor (18km to station)
    ("whisky-cove",                           "9450460",  "noaa"),   # Whisky Cove (0km to station)
    ("whisky-run-beach",                      "9432780",  "noaa"),   # Whisky Run Beach (16km to station)
    ("whistle-beach",                         "8410140",  "noaa"),   # Whistle Beach (20km to station)
    ("whistler-cove",                         "8413320",  "noaa"),   # Whistler Cove (17km to station)
    ("whitakers-bayou",                       "8773701",  "noaa"),   # Whitakers Bayou (9km to station)
    ("whitcomb-bayou",                        "8726724",  "noaa"),   # Whitcomb Bayou (20km to station)
    ("white-bay",                             "9751381",  "noaa"),   # White Bay (14km to station)
    ("white-bay-beach",                       "9751381",  "noaa"),   # White Bay Beach (23km to station)
    ("white-boulder-cove",                    "8418150",  "noaa"),   # White Boulder Cove (4km to station)
    ("white-cove",                            "8573364",  "noaa"),   # White Cove (17km to station)
    ("white-goose-bay",                       "9075080",  "noaa"),   # White Goose Bay (30km to station)
    ("white-goose-cove",                      "8449130",  "noaa"),   # White Goose Cove (8km to station)
    ("white-grunt-hole",                      "2695540",  "noaa"),   # White Grunt Hole (12km to station)
    ("white-gulch-beach",                     "9415020",  "noaa"),   # White Gulch Beach (22km to station)
    ("white-marsh-creek",                     "8571892",  "noaa"),   # White Marsh Creek (19km to station)
    ("white-oak-bay",                         "9412110",  "noaa"),   # White Oak Bay (31km to station)
    ("white-perch-cove",                      "8631044",  "noaa"),   # White Perch Cove (10km to station)
    ("white-sand-beach",                      "8461490",  "noaa"),   # White Sand Beach (20km to station)
    ("whitehall-bay",                         "8575512",  "noaa"),   # Whitehall Bay (4km to station)
    ("whitehall-creek",                       "8575512",  "noaa"),   # Whitehall Creek (4km to station)
    ("whitehouse-bay",                        "8311030",  "noaa"),   # Whitehouse Bay (24km to station)
    ("whitehouse-creek",                      "8635750",  "noaa"),   # Whitehouse Creek (38km to station)
    ("whitehurst-creek",                      "8656483",  "noaa"),   # Whitehurst Creek (11km to station)
    ("whitemarsh-creek",                      "8575512",  "noaa"),   # Whitemarsh Creek (10km to station)
    ("whites-bay",                            "9052000",  "noaa"),   # Whites Bay (31km to station)
    ("whites-cove",                           "8574680",  "noaa"),   # Whites Cove (15km to station)
    ("whitesand-bay",                         "9751381",  "noaa"),   # Whitesand Bay (5km to station)
    ("whitesboro-cove",                       "9416841",  "noaa"),   # Whitesboro Cove (34km to station)
    ("whitewood-cove",                        "8577330",  "noaa"),   # Whitewood Cove (17km to station)
    ("whitfield-bight",                       "8747437",  "noaa"),   # Whitfield Bight (5km to station)
    ("whitings-pond-beach",                   "8454000",  "noaa"),   # Whiting's Pond Beach (22km to station)
    ("whitney-bay",                           "9075099",  "noaa"),   # Whitney Bay (4km to station)
    ("whitneys-bay",                          "2695540",  "noaa"),   # Whitney's Bay (21km to station)
    ("wianno-beach",                          "8447930",  "noaa"),   # Wianno Beach (27km to station)
    ("wickes-beach",                          "8573364",  "noaa"),   # Wickes Beach (20km to station)
    ("wicomico-beach",                        "8635027",  "noaa"),   # Wicomico Beach (15km to station)
    ("wide-bay",                              "9462620",  "noaa"),   # Wide Bay (9km to station)
    ("widgeon-bay",                           "8534720",  "noaa"),   # Widgeon Bay (11km to station)
    ("widgeon-cove",                          "8418150",  "noaa"),   # Widgeon Cove (27km to station)
    ("wiggins-pass",                          "8725520",  "noaa"),   # Wiggins Pass (40km to station)
    ("wightman-lane-beach",                   "8725520",  "noaa"),   # Wightman Lane Beach (35km to station)
    ("wild-rose-shores",                      "8575512",  "noaa"),   # Wild Rose Shores (6km to station)
    ("wildcat-beach",                         "9415020",  "noaa"),   # Wildcat Beach (16km to station)
    ("wilderness-beach-base-ramey",           "9759394",  "noaa"),   # Wilderness Beach, Base Ramey (29km to station)
    ("wiley-park-beach",                      "8447435",  "noaa"),   # Wiley Park Beach (16km to station)
    ("wilkies-beach",                         "8418150",  "noaa"),   # Wilkies Beach (31km to station)
    ("wilkins-beach",                         "8632200",  "noaa"),   # Wilkins Beach (21km to station)
    ("will-rogers-state-beach",               "9410840",  "noaa"),   # Will Rogers State Beach (6km to station)
    ("willanch-inlet",                        "9432780",  "noaa"),   # Willanch Inlet (12km to station)
    ("willard-bay",                           "8461490",  "noaa"),   # Willard Bay (26km to station)
    ("willard-beach",                         "8418150",  "noaa"),   # Willard Beach (2km to station)
    ("willett-cove",                          "8637689",  "noaa"),   # Willett Cove (8km to station)
    ("william-morrow-beach",                  "8534720",  "noaa"),   # William Morrow Beach (16km to station)
    ("williams-bayou",                        "8729108",  "noaa"),   # Williams Bayou (15km to station)
    ("williams-beach",                        "8461490",  "noaa"),   # Williams Beach (12km to station)
    ("willis-creek",                          "8656483",  "noaa"),   # Willis Creek (4km to station)
    ("willow-cove",                           "8764044",  "noaa"),   # Willow Cove (22km to station)
    ("willow-pond",                           "8760721",  "noaa"),   # Willow Pond (12km to station)
    ("wills-cove",                            "8638610",  "noaa"),   # Wills Cove (19km to station)
    ("wilson-creek-beach",                    "9419750",  "noaa"),   # Wilson Creek Beach (17km to station)
    ("wilsons-beach",                         "8410140",  "noaa"),   # Wilsons Beach (5km to station)
    ("winans-cove",                           "8574680",  "noaa"),   # Winans Cove (2km to station)
    ("winchester-arm",                        "8575512",  "noaa"),   # Winchester Arm (5km to station)
    ("winchester-bay",                        "9432780",  "noaa"),   # Winchester Bay (39km to station)
    ("winchester-pond",                       "8575512",  "noaa"),   # Winchester Pond (3km to station)
    ("winders-landing",                       "8419870",  "noaa"),   # Winder's Landing (32km to station)
    ("windmill-cove",                         "8571421",  "noaa"),   # Windmill Cove (11km to station)
    ("windy-bay",                             "9455500",  "noaa"),   # Windy Bay (28km to station)
    ("windy-cove",                            "9412110",  "noaa"),   # Windy Cove (22km to station)
    ("windy-hill-beach",                      "8661070",  "noaa"),   # Windy Hill Beach (24km to station)
    ("wingate-cove",                          "8557380",  "noaa"),   # Wingate Cove (24km to station)
    ("wingate-creek",                         "8571421",  "noaa"),   # Wingate Creek (10km to station)
    ("wings-cove",                            "8447930",  "noaa"),   # Wings Cove (20km to station)
    ("winkumpaugh-cove",                      "8413320",  "noaa"),   # Winkumpaugh Cove (40km to station)
    ("winnegance-bay",                        "8418150",  "noaa"),   # Winnegance Bay (36km to station)
    ("winnies-boat-basin",                    "9063079",  "noaa"),   # Winnies Boat Basin (1km to station)
    ("winslow-cove",                          "9414863",  "noaa"),   # Winslow Cove (7km to station)
    ("wintucket-cove",                        "8447930",  "noaa"),   # Wintucket Cove (19km to station)
    ("wipeout-beach",                         "9410230",  "noaa"),   # Wipeout Beach (3km to station)
    ("wire-pond",                             "8570283",  "noaa"),   # Wire Pond (3km to station)
    ("wishin-wells",                          "9759394",  "noaa"),   # Wishin Wells (28km to station)
    ("witch-duck-bay",                        "8638610",  "noaa"),   # Witch Duck Bay (20km to station)
    ("withers-swash",                         "8661070",  "noaa"),   # Withers Swash (4km to station)
    ("withlacoochee-bay",                     "8727520",  "noaa"),   # Withlacoochee Bay (27km to station)
    ("wohoa-bay",                             "8411060",  "noaa"),   # Wohoa Bay (40km to station)
    ("wolftrap-creek",                        "8571421",  "noaa"),   # Wolftrap Creek (23km to station)
    ("womans-bay",                            "8631044",  "noaa"),   # Womans Bay (30km to station)
    ("wonsqueak-harbor",                      "8413320",  "noaa"),   # Wonsqueak Harbor (14km to station)
    ("wood-island-harbor",                    "8418150",  "noaa"),   # Wood Island Harbor (24km to station)
    ("wood-pond-cove",                        "8413320",  "noaa"),   # Wood Pond Cove (25km to station)
    ("woodbury-cove",                         "8410140",  "noaa"),   # Woodbury Cove (31km to station)
    ("woodcottage-bay",                       "9751364",  "noaa"),   # Woodcottage Bay (9km to station)
    ("woodman-bay",                           "9052000",  "noaa"),   # Woodman Bay (9km to station)
    ("woodmans-cove",                         "8516945",  "noaa"),   # Woodmans Cove (30km to station)
    ("woodruff-cove",                         "8411060",  "noaa"),   # Woodruff Cove (15km to station)
    ("woods-bayou",                           "8735180",  "noaa"),   # Woods Bayou (5km to station)
    ("woods-cove",                            "8447435",  "noaa"),   # Woods Cove (14km to station)
    ("woodstock-bay",                         "9099064",  "noaa"),   # Woodstock Bay (8km to station)
    ("woodward-cove",                         "8418150",  "noaa"),   # Woodward Cove (36km to station)
    ("woodway-beach-club",                    "8516945",  "noaa"),   # Woodway Beach Club (32km to station)
    ("woodyard-pond",                         "8760721",  "noaa"),   # Woodyard Pond (6km to station)
    ("worton-creek",                          "8573364",  "noaa"),   # Worton Creek (10km to station)
    ("wreck-bay",                             "2695540",  "noaa"),   # Wreck Bay (20km to station)
    ("wreck-cove",                            "8577330",  "noaa"),   # Wreck Cove (17km to station)
    ("wreck-creek",                           "8652587",  "noaa"),   # Wreck Creek (16km to station)
    ("wright-bay",                            "9052000",  "noaa"),   # Wright Bay (30km to station)
    ("wright-cove",                           "8546252",  "noaa"),   # Wright Cove (9km to station)
    ("wrights-cove",                          "8635750",  "noaa"),   # Wrights Cove (4km to station)
    ("wychmere-harbor",                       "8447435",  "noaa"),   # Wychmere Harbor (10km to station)
    ("wyman-bay",                             "8418150",  "noaa"),   # Wyman Bay (38km to station)
    ("wysocking-bay",                         "8654467",  "noaa"),   # Wysocking Bay (38km to station)
    ("xatacyan-lagoon-margarets-bay",         "9462620",  "noaa"),   # Xatacyan Lagoon (Margarets Bay) (1km to station)
    ("ywca-beach",                            "8454000",  "noaa"),   # YWCA Beach (30km to station)
    ("yacht-basin",                           "8720219",  "noaa"),   # Yacht Basin (20km to station)
    ("yantz-creek",                           "8575512",  "noaa"),   # Yantz Creek (12km to station)
    ("yaquina-bay",                           "9435380",  "noaa"),   # Yaquina Bay (0km to station)
    ("yates-bayou",                           "8770971",  "noaa"),   # Yates Bayou (8km to station)
    ("yates-cove",                            "8770971",  "noaa"),   # Yates Cove (8km to station)
    ("yaupon-hammock-gut",                    "8656483",  "noaa"),   # Yaupon Hammock Gut (29km to station)
    ("yeaton-cove",                           "8413320",  "noaa"),   # Yeaton Cove (22km to station)
    ("yellow-cotton-bay",                     "8760721",  "noaa"),   # Yellow Cotton Bay (19km to station)
    ("yellowcliff-bay",                       "9751364",  "noaa"),   # Yellowcliff Bay (8km to station)
    ("yelper-cove",                           "9454050",  "noaa"),   # Yelper Cove (36km to station)
    ("yeo-point-beach",                       "9449880",  "noaa"),   # Yeo Point Beach (39km to station)
    ("yoho-creek",                            "8411060",  "noaa"),   # Yoho Creek (17km to station)
    ("yopps-cove",                            "8635750",  "noaa"),   # Yopps Cove (39km to station)
    ("york-harbor-entrance",                  "8419870",  "noaa"),   # York Harbor Entrance (11km to station)
    ("young-bay",                             "9452210",  "noaa"),   # Young Bay (18km to station)
    ("youngs-bay",                            "8413320",  "noaa"),   # Youngs Bay (14km to station)
    ("zachs-bay",                             "8516945",  "noaa"),   # Zach's Bay (33km to station)
    ("zachary-bay",                           "9459450",  "noaa"),   # Zachary Bay (8km to station)
    ("zeb-cove",                              "8418150",  "noaa"),   # Zeb Cove (7km to station)
    ("zekes-bay",                             "8311062",  "noaa"),   # Zekes Bay (20km to station)
    ("zhilo-cove",                            "9452634",  "noaa"),   # Zhilo Cove (40km to station)
    ("ziegler-cove",                          "8467150",  "noaa"),   # Ziegler Cove (28km to station)
    ("zieglers-cove",                         "8467150",  "noaa"),   # Zieglers Cove (28km to station)
    ("zinzin-bay",                            "8760721",  "noaa"),   # Zinzin Bay (8km to station)
    ("zipperian-bayou",                       "8773146",  "noaa"),   # Zipperian Bayou (14km to station)
    ("zippy-creek",                           "8570283",  "noaa"),   # Zippy Creek (12km to station)
    ("zoar-beach",                            "8467150",  "noaa"),   # Zoar Beach (23km to station)
    ("umiwai-bay",                            "1617433",  "noaa"),   # ‘Umiwai Bay (25km to station)
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
        "ALTER TABLE water_cache ADD COLUMN temp_f_min REAL DEFAULT NULL",
        "ALTER TABLE water_cache ADD COLUMN temp_f_max REAL DEFAULT NULL",
        # bait_shop_cache and api_call_log are created by executescript(schema) above
        # for new DBs; existing DBs get them on next schema run automatically.
    ]
    for sql in migrations:
        try:
            conn.execute(sql)
        except Exception:
            pass  # column already exists

    # fishing_logic has no natural unique key (id is autoincrement-only), so
    # INSERT OR IGNORE never had anything to conflict against — every rerun
    # of this script (which happens on every deploy) silently appended a
    # fresh duplicate copy of the whole seed set. Clear and reseed instead,
    # matching the delete-then-insert pattern already used for tide_cache.
    # Nothing else has a foreign key into fishing_logic.id, so this is safe.
    conn.execute("DELETE FROM fishing_logic")

    conn.executemany(
        """INSERT INTO fishing_logic
           (temp_min_f, temp_max_f, fish_behavior, recommended_gear, asin, water_type)
           VALUES (?, ?, ?, ?, ?, ?)""",
        FISHING_LOGIC_SEED,
    )

    conn.executemany(
        """INSERT INTO fishing_logic
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
