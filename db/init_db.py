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
