'use strict';

// ── USA ───────────────────────────────────────────────────────────────────────
module.exports = {
  // Great Lakes
  'lake-michigan':        ['walleye','coho-salmon','chinook-salmon','smallmouth-bass','yellow-perch','lake-trout','steelhead','brown-trout'],
  'lake-superior':        ['lake-trout','walleye','northern-pike','yellow-perch','coho-salmon','steelhead','lake-whitefish'],
  'lake-erie':            ['walleye','yellow-perch','smallmouth-bass','steelhead','crappie','channel-catfish','sauger'],
  'lake-ontario':         ['walleye','chinook-salmon','coho-salmon','lake-trout','smallmouth-bass','steelhead'],
  'lake-huron':           ['walleye','smallmouth-bass','northern-pike','lake-trout','yellow-perch','muskellunge','lake-whitefish'],

  // Western US lakes
  'lake-tahoe':           ['rainbow-trout','lake-trout','brown-trout','smallmouth-bass'],
  'flathead-lake':        ['lake-trout','rainbow-trout','walleye','yellow-perch','lake-whitefish','smallmouth-bass'],
  'yellowstone-lake':     ['cutthroat-trout','lake-trout'],
  'lake-havasu':          ['largemouth-bass','smallmouth-bass','striped-bass','channel-catfish','rainbow-trout'],
  'lake-mead':            ['largemouth-bass','smallmouth-bass','striped-bass','channel-catfish'],
  'lake-powell':          ['largemouth-bass','smallmouth-bass','striped-bass','walleye','channel-catfish'],

  // Southern / reservoir lakes
  'lake-okeechobee':      ['largemouth-bass','bluegill','crappie','channel-catfish','carp'],
  'lake-lanier':          ['largemouth-bass','striped-bass','crappie','bluegill','channel-catfish'],
  'lake-norman':          ['largemouth-bass','striped-bass','crappie','bluegill','channel-catfish'],
  'kentucky-lake':        ['crappie','largemouth-bass','smallmouth-bass','striped-bass','walleye','channel-catfish'],
  'lake-barkley':         ['crappie','largemouth-bass','striped-bass','channel-catfish'],
  'lake-texoma':          ['striped-bass','largemouth-bass','smallmouth-bass','channel-catfish','crappie','sauger'],
  'sam-rayburn-reservoir':['largemouth-bass','crappie','channel-catfish','striped-bass'],
  'toledo-bend-reservoir':['largemouth-bass','crappie','channel-catfish','striped-bass'],
  'lake-travis':          ['largemouth-bass','smallmouth-bass','striped-bass','white-bass'],
  'lake-of-the-ozarks':   ['largemouth-bass','smallmouth-bass','striped-bass','walleye','crappie','channel-catfish'],
  'lake-pontchartrain':   ['largemouth-bass','crappie','channel-catfish','spotted-sea-trout','black-drum'],
  'lake-george':          ['largemouth-bass','smallmouth-bass','walleye','rainbow-trout','yellow-perch'],
  'lake-champlain':       ['walleye','smallmouth-bass','largemouth-bass','northern-pike','yellow-perch'],
  'lake-winnebago':       ['walleye','yellow-perch','white-bass','channel-catfish'],
  'lake-of-the-woods':    ['walleye','northern-pike','muskellunge','lake-trout','yellow-perch','smallmouth-bass'],

  // US rivers
  'mississippi-river':    ['largemouth-bass','smallmouth-bass','walleye','channel-catfish','flathead-catfish','northern-pike','carp','crappie','sauger'],
  'columbia-river':       ['chinook-salmon','steelhead','smallmouth-bass','walleye','rainbow-trout','cutthroat-trout'],
  'missouri-river':       ['walleye','channel-catfish','flathead-catfish','smallmouth-bass','northern-pike','sauger'],
  'colorado-river':       ['largemouth-bass','smallmouth-bass','striped-bass','channel-catfish','rainbow-trout'],
  'ohio-river':           ['largemouth-bass','smallmouth-bass','walleye','channel-catfish','flathead-catfish','crappie','sauger'],
  'tennessee-river':      ['largemouth-bass','smallmouth-bass','walleye','crappie','channel-catfish','striped-bass'],
  'hudson-river':         ['striped-bass','largemouth-bass','smallmouth-bass','channel-catfish','yellow-perch'],
  'delaware-river':       ['striped-bass','walleye','smallmouth-bass','channel-catfish','yellow-perch'],
  'potomac-river':        ['striped-bass','largemouth-bass','smallmouth-bass','channel-catfish','flathead-catfish','yellow-perch'],
  'susquehanna-river':    ['smallmouth-bass','walleye','channel-catfish','yellow-perch','sauger'],
  'st-johns-river':       ['largemouth-bass','crappie','bluegill','snook','striped-bass'],

  // US coastal / bays
  'chesapeake-bay':       ['striped-bass','flounder','red-drum','bluefish','weakfish','spotted-sea-trout','black-drum','cobia'],
  'delaware-bay':         ['striped-bass','flounder','weakfish','bluefish','red-drum'],
  'long-island-sound':    ['striped-bass','bluefish','flounder','weakfish'],
  'narragansett-bay':     ['striped-bass','bluefish','flounder','weakfish'],
  'buzzards-bay':         ['striped-bass','bluefish','flounder','weakfish'],
  'cape-cod-bay':         ['striped-bass','bluefin-tuna','bluefish','flounder','atlantic-cod'],
  'pamlico-sound':        ['red-drum','spotted-sea-trout','flounder','striped-bass','bluefish'],
  'albemarle-sound':      ['striped-bass','largemouth-bass','crappie','yellow-perch'],
  'mobile-bay':           ['red-drum','spotted-sea-trout','flounder','bluefish','spanish-mackerel'],
  'pensacola-bay':        ['red-drum','spotted-sea-trout','flounder','bluefish','cobia'],
  'apalachicola-bay':     ['red-drum','spotted-sea-trout','flounder','cobia'],
  'charlotte-harbor':     ['snook','red-drum','spotted-sea-trout','tarpon','cobia','flounder'],
  'tampa-bay':            ['spotted-sea-trout','red-drum','snook','flounder','cobia','spanish-mackerel'],
  'galveston-bay':        ['spotted-sea-trout','red-drum','flounder','black-drum','cobia'],
  'biscayne-bay':         ['snook','red-drum','spotted-sea-trout','bonefish','tarpon'],
  'florida-bay':          ['snook','tarpon','red-drum','spotted-sea-trout','bonefish'],
  'san-francisco-bay':    ['striped-bass','pacific-halibut','chinook-salmon','flounder'],
  'puget-sound':          ['chinook-salmon','coho-salmon','pacific-halibut','steelhead'],
  'green-bay':            ['walleye','yellow-perch','smallmouth-bass','northern-pike'],

  // US open waters
  'gulf-of-mexico':       ['red-drum','spotted-sea-trout','snook','tarpon','red-grouper','red-snapper','cobia','king-mackerel','spanish-mackerel','mahi-mahi','amberjack'],
  'gulf-of-alaska':       ['pacific-halibut','chinook-salmon','coho-salmon','atlantic-cod','pollock'],
  'pacific-ocean':        ['pacific-halibut','chinook-salmon','coho-salmon','yellowfin-tuna','mahi-mahi','striped-marlin','wahoo'],
  'atlantic-ocean':       ['striped-bass','bluefin-tuna','yellowfin-tuna','mahi-mahi','wahoo','king-mackerel','bluefish','atlantic-cod','haddock'],
  'caribbean-sea':        ['mahi-mahi','yellowfin-tuna','wahoo','king-mackerel','red-snapper','amberjack','tarpon','atlantic-sailfish'],
  'bering-sea':           ['pacific-halibut','atlantic-cod','pollock'],
  'cook-inlet':           ['chinook-salmon','coho-salmon','pacific-halibut','steelhead'],

  // ── Canada ────────────────────────────────────────────────────────────────────
  'georgian-bay':         ['walleye','northern-pike','smallmouth-bass','lake-trout','yellow-perch','lake-whitefish'],
  'lake-simcoe':          ['lake-trout','walleye','yellow-perch','lake-whitefish','northern-pike'],
  'lake-winnipeg':        ['walleye','northern-pike','lake-whitefish','yellow-perch','sauger'],
  'lake-manitoba':        ['walleye','northern-pike','yellow-perch','channel-catfish','lake-whitefish'],
  'lake-athabasca':       ['lake-trout','walleye','northern-pike','arctic-char','lake-whitefish','burbot'],
  'great-bear-lake':      ['lake-trout','arctic-char','northern-pike','lake-whitefish','burbot'],
  'great-slave-lake':     ['lake-trout','walleye','northern-pike','arctic-char','lake-whitefish'],
  'st-lawrence-river':    ['walleye','northern-pike','smallmouth-bass','muskellunge','lake-trout','atlantic-salmon'],
  'fraser-river':         ['chinook-salmon','coho-salmon','steelhead','rainbow-trout','cutthroat-trout'],
  'gulf-of-st-lawrence':  ['atlantic-cod','atlantic-mackerel','bluefin-tuna','striped-bass','atlantic-salmon','haddock'],
  'bay-of-fundy':         ['striped-bass','atlantic-cod','pollock','haddock','atlantic-salmon'],
  'strait-of-georgia':    ['chinook-salmon','coho-salmon','pacific-halibut','steelhead','cutthroat-trout'],
  'hudson-bay':           ['arctic-char','lake-trout','brook-trout','burbot','lake-whitefish'],
};
