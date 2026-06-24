'use strict';

const FISH_SPECIES = {
  ...require('./species/freshwater'),
  ...require('./species/saltwater'),
  ...require('./species/european'),
  ...require('./species/southAmerican'),
};

const WATER_BODY_FISH = {
  ...require('./regions/northAmerica'),
  ...require('./regions/europe'),
  ...require('./regions/southAmerica'),
};

const SALTWATER_KEYWORDS = ['ocean','sea','bay','gulf','sound','harbor','inlet','strait','estuary','cove','bight','channel','lagoon','pass','key','keys'];
const FRESHWATER_KEYWORDS = ['lake','river','creek','pond','reservoir','stream','brook','spring','falls','fork','bayou','slough','pantanal','loch','lough'];

function getWaterType(urlSlug) {
  for (const kw of SALTWATER_KEYWORDS) {
    if (urlSlug.includes(kw)) return 'saltwater';
  }
  for (const kw of FRESHWATER_KEYWORDS) {
    if (urlSlug.includes(kw)) return 'freshwater';
  }
  return 'unknown';
}

function getRegionFish(urlSlug) {
  if (WATER_BODY_FISH[urlSlug]) {
    return WATER_BODY_FISH[urlSlug]
      .map(key => FISH_SPECIES[key])
      .filter(Boolean);
  }
  const waterType = getWaterType(urlSlug);
  return Object.values(FISH_SPECIES).filter(f =>
    waterType === 'unknown' || f.type === waterType
  );
}

function getFishingGuide(urlSlug, tempF) {
  const regionFish    = getRegionFish(urlSlug);
  const isKnownRegion = !!WATER_BODY_FISH[urlSlug];

  const activeFish   = regionFish.filter(f => tempF >= f.minTemp && tempF <= f.maxTemp);
  const peakFish     = regionFish.filter(f => tempF >= f.peakMin && tempF <= f.peakMax);
  const inactiveFish = regionFish.filter(f => tempF < f.minTemp || tempF > f.maxTemp);

  const leadFish = peakFish[0] || activeFish[0];
  const tip = leadFish
    ? leadFish.tip
    : tempF < 45
      ? 'Water is very cold. Fish slowly with small presentations near the bottom.'
      : tempF < 60
        ? 'Cool water means slow metabolism. Downsize your bait and slow your retrieve.'
        : tempF < 75
          ? 'Excellent temperature window. Fish are active throughout the water column.'
          : tempF < 82
            ? 'Warm water keeps fish active but moving. Focus on early morning, evening, and shaded structure.'
            : 'Hot water pushes most fish deep or into current. Fish first and last light near cool inflows.';

  return {
    activeFish:    activeFish.map(f => f.name),
    peakFish:      peakFish.map(f => f.name),
    inactiveFish:  inactiveFish.map(f => f.name),
    total:         regionFish.length,
    isKnownRegion,
    tip,
  };
}

module.exports = { getFishingGuide, getRegionFish, getWaterType };
