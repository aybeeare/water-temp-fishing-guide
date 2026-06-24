'use strict';

const axios    = require('axios');
const cheerio  = require('cheerio');
const DISAMBIG = require('./disambiguation');

const BASE_URL = 'https://seatemperature.info';

// ── URL helpers ───────────────────────────────────────────────────────────────

function formatWaterBodyUrl(waterBodyName) {
  return waterBodyName
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-{2,}/g, '-');
}

// Accept either a bare slug or an absolute path (starts with '/').
function buildUrl(slugOrPath, suffix) {
  return slugOrPath.startsWith('/')
    ? `${BASE_URL}${slugOrPath}`
    : `${BASE_URL}/${slugOrPath}${suffix}`;
}

// When we receive a full water-temp path, derive the tides path from it.
function tidesUrlFromWaterTempPath(path) {
  return path.replace('-water-temperature', '-tides');
}

// Extract the bare location slug from a full path for fish-DB lookups.
function extractSlugFromPath(path) {
  const filename = path.split('/').pop();
  return filename.replace('-water-temperature.html', '');
}

// ── Temperature parsing ───────────────────────────────────────────────────────

function parseTemperature(text) {
  if (!text) return null;
  const isFahrenheit = /°?\s*f\b/i.test(text);
  const match = text.match(/(\d+(?:\.\d+)?)/);
  if (!match) return null;
  const value = parseFloat(match[1]);
  if (isFahrenheit) {
    return { tempF: Math.round(value * 10) / 10, tempC: Math.round((value - 32) * 5 / 9 * 10) / 10 };
  }
  return { tempC: Math.round(value * 10) / 10, tempF: Math.round((value * 9 / 5 + 32) * 10) / 10 };
}

// ── Water temperature scraper ─────────────────────────────────────────────────

async function scrapeWaterTemperature(slugOrPath) {
  const url = buildUrl(slugOrPath, '-water-temperature.html');

  let html;
  try {
    const { data, status } = await axios.get(url, {
      timeout: 8000,
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; FishingGuideSkill/1.0)' },
      validateStatus: s => s < 500,
    });
    if (status === 404) return null;
    html = data;
  } catch (err) {
    if (err.response && err.response.status === 404) return null;
    throw err;
  }

  const $ = cheerio.load(html);

  // Strategy 1 – explicit CSS selectors
  for (const sel of ['.current-temp','#current-temp','.temperature','#temperature','.temp-value','.sea-temp','.water-temp','.today-temp']) {
    const el = $(sel).first();
    if (!el.length) continue;
    const result = parseTemperature(el.text());
    if (result) return result;
  }

  // Strategy 2 – degree symbols in body text
  const bodyText = $('body').text();
  const cMatch = bodyText.match(/(\d{1,3}(?:\.\d)?)\s*°\s*C/i);
  if (cMatch) {
    const tempC = parseFloat(cMatch[1]);
    return { tempC, tempF: Math.round((tempC * 9 / 5 + 32) * 10) / 10 };
  }
  const fMatch = bodyText.match(/(\d{2,3}(?:\.\d)?)\s*°\s*F/i);
  if (fMatch) {
    const tempF = parseFloat(fMatch[1]);
    return { tempF, tempC: Math.round((tempF - 32) * 5 / 9 * 10) / 10 };
  }

  // Strategy 3 – table row with "today / current"
  let found = null;
  $('table tr').each((_, row) => {
    if (found) return;
    if (!/today|current|now/i.test($(row).text())) return;
    $(row).find('td').each((_, td) => {
      if (found) return;
      const r = parseTemperature($(td).text());
      if (r) found = r;
    });
  });
  return found;
}

// ── Disambiguation ────────────────────────────────────────────────────────────

function getDisambiguation(slug) {
  return DISAMBIG[slug] || null;
}

// ── Tide scraper ──────────────────────────────────────────────────────────────

function parseTidesFromText(text) {
  const tides = [];
  const flat  = text.replace(/\r?\n/g, ' ').replace(/\s{2,}/g, ' ');

  const pattern = /(high|low)\s+tide[^0-9]{0,30}(\d{1,2}:\d{2}\s*[AP]M)[^H]{0,80}Height:\s*(\d+\.?\d*)\s*ft/gi;
  let match;
  while ((match = pattern.exec(flat)) !== null) {
    tides.push({ type: match[1].toLowerCase(), time: match[2].replace(/\s+/, ' ').trim(), heightFt: parseFloat(match[3]) });
  }

  if (tides.length === 0) {
    const simple = /(high|low)\s+tide[^0-9]{0,20}(\d{1,2}:\d{2}\s*[AP]M)/gi;
    while ((match = simple.exec(flat)) !== null) {
      tides.push({ type: match[1].toLowerCase(), time: match[2].trim(), heightFt: null });
    }
  }
  return tides;
}

async function scrapeTides(slugOrPath) {
  const url = slugOrPath.startsWith('/')
    ? `${BASE_URL}${tidesUrlFromWaterTempPath(slugOrPath)}`
    : `${BASE_URL}/${slugOrPath}-tides.html`;

  let html;
  try {
    const { data, status } = await axios.get(url, {
      timeout: 8000,
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; FishingGuideSkill/1.0)' },
      validateStatus: s => s < 500,
    });
    if (status === 404) return null;
    html = data;
  } catch (err) {
    if (err.response && err.response.status === 404) return null;
    throw err;
  }

  const $ = cheerio.load(html);
  const tides = parseTidesFromText($('body').text());
  return tides.length > 0 ? tides : null;
}

module.exports = {
  scrapeWaterTemperature,
  scrapeTides,
  getDisambiguation,
  formatWaterBodyUrl,
  extractSlugFromPath,
};
