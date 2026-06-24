'use strict';

// Maps an ambiguous slug (what the user said, slugified) to a list of specific
// seatemperature.info paths and their display names.
// URL format for state-qualified US locations: /united-states/{state}/{slug}-water-temperature.html
// Extend this table as new ambiguous locations are discovered.

module.exports = {
  'ocean-city': [
    { path: '/united-states/maryland/ocean-city-water-temperature.html',   name: 'Ocean City, Maryland' },
    { path: '/united-states/new-jersey/ocean-city-water-temperature.html', name: 'Ocean City, New Jersey' }
  ],
  'newport': [
    { path: '/united-states/rhode-island/newport-water-temperature.html', name: 'Newport, Rhode Island' },
    { path: '/united-states/oregon/newport-water-temperature.html',        name: 'Newport, Oregon' }
  ],
  'long-beach': [
    { path: '/united-states/california/long-beach-water-temperature.html', name: 'Long Beach, California' },
    { path: '/united-states/washington/long-beach-water-temperature.html', name: 'Long Beach, Washington' }
  ],
  'portland': [
    { path: '/united-states/maine/portland-water-temperature.html',   name: 'Portland, Maine' },
    { path: '/united-states/oregon/portland-water-temperature.html',  name: 'Portland, Oregon' }
  ],
  'venice': [
    { path: '/united-states/florida/venice-water-temperature.html', name: 'Venice, Florida' },
    { path: '/italy/venice-water-temperature.html',                 name: 'Venice, Italy' }
  ],
  'naples': [
    { path: '/united-states/florida/naples-water-temperature.html', name: 'Naples, Florida' },
    { path: '/italy/naples-water-temperature.html',                 name: 'Naples, Italy' }
  ],
  'gloucester': [
    { path: '/united-states/massachusetts/gloucester-water-temperature.html', name: 'Gloucester, Massachusetts' },
    { path: '/united-kingdom/gloucester-water-temperature.html',              name: 'Gloucester, United Kingdom' }
  ],
  'clearwater': [
    { path: '/united-states/florida/clearwater-water-temperature.html',    name: 'Clearwater, Florida' },
    { path: '/united-states/washington/clearwater-water-temperature.html', name: 'Clearwater, Washington' }
  ],
  'cambridge': [
    { path: '/united-states/massachusetts/cambridge-water-temperature.html', name: 'Cambridge, Massachusetts' },
    { path: '/united-kingdom/cambridge-water-temperature.html',              name: 'Cambridge, United Kingdom' }
  ],
};
