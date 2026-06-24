'use strict';

const locales = {
  en: require('./en'),
  es: require('./es'),
  fr: require('./fr'),
  de: require('./de'),
  it: require('./it'),
  pt: require('./pt'),
};

function getLang(locale) {
  if (!locale) return 'en';
  return locale.split('-')[0].toLowerCase();
}

// Retrieve a string for the given locale, falling back to English.
// Replaces {param} placeholders with values from the params object.
function t(locale, key, params = {}) {
  const lang = getLang(locale);
  const strings = locales[lang] || locales.en;
  let str = strings[key] !== undefined ? strings[key] : (locales.en[key] || key);
  return Object.entries(params).reduce(
    (acc, [k, v]) => acc.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v)),
    str
  );
}

module.exports = { t };
