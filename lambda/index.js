'use strict';

const Alexa = require('ask-sdk-core');
const { scrapeWaterTemperature, scrapeTides, getDisambiguation, formatWaterBodyUrl, extractSlugFromPath } = require('./waterScraper');
const { getFishingGuide, getRegionFish } = require('./fishData');
const { t } = require('./i18n');

// ── Shared response builder ───────────────────────────────────────────────────

async function fetchAndBuildFishingResponse(handlerInput, waterBodyName, slugOrPath, locale) {
  const fishSlug = slugOrPath.startsWith('/') ? extractSlugFromPath(slugOrPath) : slugOrPath;

  const [tempData, tides] = await Promise.all([
    scrapeWaterTemperature(slugOrPath),
    scrapeTides(slugOrPath),
  ]);

  if (!tempData) {
    return handlerInput.responseBuilder
      .speak(t(locale, 'NOT_FOUND', { waterBody: waterBodyName }))
      .reprompt(t(locale, 'REPROMPT'))
      .getResponse();
  }

  const { tempF, tempC } = tempData;
  const guide = getFishingGuide(fishSlug, tempF);
  const isAre = n => n === 1 ? t(locale, 'IS') : t(locale, 'ARE');

  let speak = t(locale, 'TEMPERATURE_INTRO', { waterBody: waterBodyName, tempF, tempC }) + ' ';

  if (guide.total > 0) {
    const knownKey = guide.isKnownRegion ? 'ACTIVE_KNOWN' : 'ACTIVE_GENERIC';

    if (guide.activeFish.length === 0) {
      speak += t(locale, guide.isKnownRegion ? 'ALL_INACTIVE' : 'ALL_INACTIVE_GENERIC', { total: guide.total }) + ' ';
    } else {
      speak += t(locale, knownKey, {
        total:  guide.total,
        n:      guide.activeFish.length,
        isAre:  isAre(guide.activeFish.length),
        list:   listify(guide.activeFish),
      }) + ' ';

      if (guide.peakFish.length > 0) {
        speak += t(locale, 'PEAK', {
          list:   listify(guide.peakFish),
          isAre:  isAre(guide.peakFish.length),
        }) + ' ';
      }

      if (guide.isKnownRegion && guide.inactiveFish.length > 0) {
        speak += t(locale, 'INACTIVE_REGION', {
          list:   listify(guide.inactiveFish),
          isAre:  isAre(guide.inactiveFish.length),
        }) + ' ';
      }
    }
  }

  if (guide.tip) speak += guide.tip + ' ';
  if (tides && tides.length > 0) speak += buildTideSpeech(tides, locale);

  return handlerInput.responseBuilder.speak(speak).getResponse();
}

// ── Intent handlers ───────────────────────────────────────────────────────────

const LaunchRequestHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'LaunchRequest';
  },
  handle(handlerInput) {
    const locale = Alexa.getLocale(handlerInput.requestEnvelope);
    return handlerInput.responseBuilder
      .speak(t(locale, 'WELCOME'))
      .reprompt(t(locale, 'REPROMPT'))
      .getResponse();
  },
};

const FishingGuideIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
      && Alexa.getIntentName(handlerInput.requestEnvelope) === 'GetFishingGuideIntent';
  },
  async handle(handlerInput) {
    const locale        = Alexa.getLocale(handlerInput.requestEnvelope);
    const slot          = Alexa.getSlot(handlerInput.requestEnvelope, 'WaterBody');
    const waterBodyName = slot && slot.value;

    if (!waterBodyName) {
      return handlerInput.responseBuilder
        .speak(t(locale, 'SLOT_MISSING_GUIDE'))
        .reprompt(t(locale, 'REPROMPT'))
        .getResponse();
    }

    try {
      const urlSlug  = formatWaterBodyUrl(waterBodyName);
      const tempData = await scrapeWaterTemperature(urlSlug);

      if (!tempData) {
        const options = getDisambiguation(urlSlug);
        if (options) {
          const attrs = handlerInput.attributesManager.getSessionAttributes();
          attrs.disambiguationOptions = options;
          handlerInput.attributesManager.setSessionAttributes(attrs);

          const numbered = options.map((o, i) => `${i + 1}. ${o.name}`).join(', ');
          return handlerInput.responseBuilder
            .speak(t(locale, 'DISAMBIG_PROMPT', { n: options.length, name: waterBodyName, options: numbered }))
            .reprompt(t(locale, 'DISAMBIG_INVALID', { max: options.length, options: numbered }))
            .getResponse();
        }
        return handlerInput.responseBuilder
          .speak(t(locale, 'NOT_FOUND', { waterBody: waterBodyName }))
          .reprompt(t(locale, 'REPROMPT'))
          .getResponse();
      }

      return fetchAndBuildFishingResponse(handlerInput, waterBodyName, urlSlug, locale);

    } catch (err) {
      console.error('FishingGuideIntent error:', err);
      return handlerInput.responseBuilder
        .speak(t(locale, 'FETCH_ERROR', { waterBody: waterBodyName }))
        .reprompt(t(locale, 'REPROMPT'))
        .getResponse();
    }
  },
};

const ChoiceIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
      && Alexa.getIntentName(handlerInput.requestEnvelope) === 'ChoiceIntent';
  },
  async handle(handlerInput) {
    const locale = Alexa.getLocale(handlerInput.requestEnvelope);
    const attrs  = handlerInput.attributesManager.getSessionAttributes();
    const options = attrs.disambiguationOptions;

    if (!options) {
      return handlerInput.responseBuilder
        .speak(t(locale, 'DISAMBIG_NONE'))
        .reprompt(t(locale, 'REPROMPT'))
        .getResponse();
    }

    const slot   = Alexa.getSlot(handlerInput.requestEnvelope, 'Choice');
    const choice = slot && slot.value ? parseInt(slot.value, 10) : NaN;

    if (isNaN(choice) || choice < 1 || choice > options.length) {
      const numbered = options.map((o, i) => `${i + 1}. ${o.name}`).join(', ');
      return handlerInput.responseBuilder
        .speak(t(locale, 'DISAMBIG_INVALID', { max: options.length, options: numbered }))
        .reprompt(t(locale, 'DISAMBIG_INVALID', { max: options.length, options: numbered }))
        .getResponse();
    }

    const chosen = options[choice - 1];
    delete attrs.disambiguationOptions;
    handlerInput.attributesManager.setSessionAttributes(attrs);

    try {
      return await fetchAndBuildFishingResponse(handlerInput, chosen.name, chosen.path, locale);
    } catch (err) {
      console.error('ChoiceIntent error:', err);
      return handlerInput.responseBuilder
        .speak(t(locale, 'FETCH_ERROR', { waterBody: chosen.name }))
        .reprompt(t(locale, 'REPROMPT'))
        .getResponse();
    }
  },
};

const FishSpeciesIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
      && Alexa.getIntentName(handlerInput.requestEnvelope) === 'GetFishSpeciesIntent';
  },
  handle(handlerInput) {
    const locale        = Alexa.getLocale(handlerInput.requestEnvelope);
    const slot          = Alexa.getSlot(handlerInput.requestEnvelope, 'WaterBody');
    const waterBodyName = slot && slot.value;

    if (!waterBodyName) {
      return handlerInput.responseBuilder
        .speak(t(locale, 'SLOT_MISSING_SPECIES'))
        .reprompt(t(locale, 'REPROMPT'))
        .getResponse();
    }

    const urlSlug = formatWaterBodyUrl(waterBodyName);
    const fish    = getRegionFish(urlSlug);

    if (fish.length === 0) {
      return handlerInput.responseBuilder
        .speak(t(locale, 'SPECIES_NOT_FOUND', { waterBody: waterBodyName }))
        .reprompt(t(locale, 'REPROMPT'))
        .getResponse();
    }

    const coldest = fish.reduce((a, b) => a.minTemp < b.minTemp ? a : b);
    const warmest = fish.reduce((a, b) => a.maxTemp > b.maxTemp ? a : b);

    const speak = t(locale, 'SPECIES_INTRO', { waterBody: waterBodyName, n: fish.length, list: listify(fish.map(f => f.name)) })
      + ' ' + t(locale, 'SPECIES_TEMPS', { min: coldest.minTemp, coldest: coldest.name, max: warmest.maxTemp, warmest: warmest.name })
      + ' ' + t(locale, 'SPECIES_PROMPT');

    return handlerInput.responseBuilder.speak(speak).getResponse();
  },
};

const HelpIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
      && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.HelpIntent';
  },
  handle(handlerInput) {
    const locale = Alexa.getLocale(handlerInput.requestEnvelope);
    const speak  = t(locale, 'HELP');
    return handlerInput.responseBuilder.speak(speak).reprompt(speak).getResponse();
  },
};

const CancelAndStopIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
      && ['AMAZON.CancelIntent', 'AMAZON.StopIntent']
        .includes(Alexa.getIntentName(handlerInput.requestEnvelope));
  },
  handle(handlerInput) {
    const locale = Alexa.getLocale(handlerInput.requestEnvelope);
    return handlerInput.responseBuilder.speak(t(locale, 'STOP')).getResponse();
  },
};

const FallbackIntentHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
      && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.FallbackIntent';
  },
  handle(handlerInput) {
    const locale = Alexa.getLocale(handlerInput.requestEnvelope);
    return handlerInput.responseBuilder
      .speak(t(locale, 'FALLBACK'))
      .reprompt(t(locale, 'REPROMPT'))
      .getResponse();
  },
};

const SessionEndedRequestHandler = {
  canHandle(handlerInput) {
    return Alexa.getRequestType(handlerInput.requestEnvelope) === 'SessionEndedRequest';
  },
  handle(handlerInput) {
    return handlerInput.responseBuilder.getResponse();
  },
};

const ErrorHandler = {
  canHandle() { return true; },
  handle(handlerInput, error) {
    console.error('Unhandled error:', error.message);
    const locale = Alexa.getLocale(handlerInput.requestEnvelope);
    return handlerInput.responseBuilder
      .speak(t(locale, 'ERROR'))
      .reprompt(t(locale, 'REPROMPT'))
      .getResponse();
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function listify(items) {
  if (items.length === 0) return '';
  if (items.length === 1) return items[0];
  return items.slice(0, -1).join(', ') + ', and ' + items[items.length - 1];
}

function buildTideSpeech(tides, locale) {
  const highs = tides.filter(t => t.type === 'high');
  const lows  = tides.filter(t => t.type === 'low');

  function describeTide(td) {
    return td.heightFt !== null ? `${td.time} at ${td.heightFt} feet` : td.time;
  }

  const tideSingular = t(locale, 'TIDE_SINGULAR');
  const tidePlural   = t(locale, 'TIDE_PLURAL');

  const parts = [];
  if (highs.length > 0) parts.push(t(locale, 'TIDES_HIGH', { tideWord: tideSingular, tidePlural: highs.length > 1 ? tidePlural : '', times: listify(highs.map(describeTide)) }));
  if (lows.length  > 0) parts.push(t(locale, 'TIDES_LOW',  { tideWord: tideSingular, tidePlural: lows.length  > 1 ? tidePlural : '', times: listify(lows.map(describeTide)) }));

  return t(locale, 'TIDES_INTRO') + ' ' + parts.join(', and ') + '. ' + t(locale, 'TIDES_TIP');
}

// ── Skill builder ─────────────────────────────────────────────────────────────

exports.handler = Alexa.SkillBuilders.custom()
  .addRequestHandlers(
    LaunchRequestHandler,
    FishingGuideIntentHandler,
    ChoiceIntentHandler,
    FishSpeciesIntentHandler,
    HelpIntentHandler,
    CancelAndStopIntentHandler,
    FallbackIntentHandler,
    SessionEndedRequestHandler,
  )
  .addErrorHandlers(ErrorHandler)
  .lambda();
