"""
Alexa Skills Kit Lambda adapter — multi-turn conversational state machine.

Turn flow:
  Turn 1: water temp only → "Want to know what fish are active?"
  Turn 2 (Yes): fish behavior → "Need fishing gear?"
  Turn 3 (Yes): "Local bait shop or Amazon?" (LocalShopIntent / AmazonGearIntent)
  Turn 4a (LocalShopIntent): speak shop info → optionally offer Amazon cart add
  Turn 4b (AmazonGearIntent): gear recommendation → "Add to cart?"
  Turn 5 (Yes): Connections.SendRequest cart directive

Environment variables:
  FASTAPI_URL   public URL of the hosted FastAPI (e.g. https://your-app.railway.app)
"""
import json
import os
import urllib.request
import urllib.parse
import urllib.error

FASTAPI_URL = os.environ.get("FASTAPI_URL", "https://your-api.railway.app")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    request_type = event["request"]["type"]

    if request_type == "LaunchRequest":
        return speak(
            "Welcome to the Water Temperature Fishing Guide. "
            "Ask me about water temperature at any lake, river, or coastal location. "
            "Try saying: what's the water temperature at Lake Michigan?",
            end_session=False,
        )

    if request_type == "SessionEndedRequest":
        return {"version": "1.0", "response": {}}

    if request_type == "IntentRequest":
        return handle_intent(event)

    if request_type == "Connections.Response":
        return handle_cart_response(event)

    return speak("Sorry, I didn't understand that request.")


# ---------------------------------------------------------------------------
# Intent routing
# ---------------------------------------------------------------------------

def handle_intent(event):
    intent_name   = event["request"]["intent"]["name"]
    session_attrs = event.get("session", {}).get("attributes", {})

    # ── GetFishingGuideIntent — fetch data, speak temp only ──────────────────
    if intent_name == "GetFishingGuideIntent":
        slots    = event["request"]["intent"].get("slots", {})
        location = slots.get("WaterBody", {}).get("value")
        if not location:
            return speak(
                "Which lake, river, or coastal area would you like conditions for?",
                end_session=False,
            )
        return fetch_and_open(location)

    # ── YesIntent — branch on current session state ──────────────────────────
    if intent_name == "AMAZON.YesIntent":

        # State 1: user wants fish info
        if session_attrs.get("awaiting_fish_info"):
            fish_speech = session_attrs.get("pending_fish_speech", "Fish are active in this area.")
            return speak(
                fish_speech + " Do you need fishing gear for these conditions?",
                end_session=False,
                session_attributes={
                    **session_attrs,
                    "awaiting_fish_info":     False,
                    "awaiting_gear_question": True,
                },
            )

        # State 2: user wants gear
        if session_attrs.get("awaiting_gear_question"):
            if session_attrs.get("pending_shop_speech"):
                return speak(
                    "I can point you to a local bait shop, or recommend gear from Amazon. "
                    "Which would you prefer?",
                    end_session=False,
                    session_attributes={
                        **session_attrs,
                        "awaiting_gear_question": False,
                        "awaiting_shop_choice":   True,
                    },
                )
            # No local shop available — go straight to Amazon
            return _offer_amazon_gear(session_attrs)

        # State 3: cart confirm
        if session_attrs.get("awaiting_cart_confirm"):
            return _do_cart_add(session_attrs)

        return speak(
            "I'm not sure what you're saying yes to. "
            "Try asking for water temperature at a location first.",
            end_session=False,
        )

    # ── NoIntent ─────────────────────────────────────────────────────────────
    if intent_name == "AMAZON.NoIntent":
        if session_attrs.get("awaiting_fish_info"):
            return speak("No problem. Good luck on the water!", end_session=True)
        if session_attrs.get("awaiting_gear_question"):
            return speak("No problem. Tight lines!", end_session=True)
        if session_attrs.get("awaiting_cart_confirm"):
            return speak("No worries. Good luck out there!", end_session=True)
        return speak("Come back anytime you need fishing conditions!", end_session=True)

    # ── LocalShopIntent ───────────────────────────────────────────────────────
    if intent_name == "LocalShopIntent":
        if not session_attrs.get("awaiting_shop_choice"):
            return speak("Try asking for water temperature at a location first.", end_session=False)
        shop_speech = session_attrs.get("pending_shop_speech")
        if not shop_speech:
            return speak(
                "I don't have a nearby shop for this location. "
                "Want me to recommend gear from Amazon instead?",
                end_session=False,
                session_attributes={
                    **session_attrs,
                    "awaiting_shop_choice":   False,
                    "awaiting_gear_question": True,
                },
            )
        gear_name = session_attrs.get("pending_gear_name")
        if gear_name:
            return speak(
                shop_speech + f" I can also recommend the {gear_name} from Amazon. "
                "Want me to add it to your cart?",
                end_session=False,
                session_attributes={
                    **session_attrs,
                    "awaiting_shop_choice":  False,
                    "awaiting_cart_confirm": True,
                },
            )
        return speak(shop_speech, end_session=True)

    # ── AmazonGearIntent ─────────────────────────────────────────────────────
    if intent_name == "AmazonGearIntent":
        if not session_attrs.get("awaiting_shop_choice"):
            return speak("Try asking for water temperature at a location first.", end_session=False)
        return _offer_amazon_gear(session_attrs)

    # ── Standard built-ins ────────────────────────────────────────────────────
    if intent_name == "AMAZON.HelpIntent":
        return speak(
            "Ask me for water temperature at any lake, river, or coastal location. "
            "I'll tell you the temperature, what fish are active, and help you find gear or a local shop. "
            "Try saying: what's the water temperature at Lake Michigan?",
            end_session=False,
        )

    if intent_name in ("AMAZON.CancelIntent", "AMAZON.StopIntent"):
        return speak("Tight lines!", end_session=True)

    return speak(
        "Sorry, I didn't catch that. "
        "Try asking for water temperature at a specific location.",
        end_session=False,
    )


# ---------------------------------------------------------------------------
# FastAPI call — speaks temp only, stores everything else in session
# ---------------------------------------------------------------------------

def fetch_and_open(location):
    params = urllib.parse.urlencode({"location": location})
    url    = f"{FASTAPI_URL}/fishing-guide?{params}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return speak(
                f"I couldn't find water temperature data for {location}. "
                "Try a nearby location or check the spelling."
            )
        return speak(
            "I'm having trouble reaching the water temperature service. Please try again."
        )
    except Exception:
        return speak("Something went wrong fetching the water temperature. Please try again.")

    if data.get("disambiguation"):
        return speak(data["spoken_response"], end_session=False)

    temp_f    = data.get("temp_f")
    temp_c    = data.get("temp_c")
    site_name = data.get("site_name", location)

    if temp_f is None:
        return speak(
            data.get("spoken_response", f"No temperature data is available for {location}.")
        )

    temp_speech = (
        f"The current water temperature at {site_name} is "
        f"{temp_f} degrees Fahrenheit, or {temp_c} degrees Celsius."
    )

    # Objective species report — no pre-written behavioral commentary
    species = data.get("species") or []
    if species:
        readable = [s.replace("_", " ") for s in species[:4]]
        if len(readable) == 1:
            fish_speech = (
                f"At {temp_f} degrees, {readable[0]} are among the likely active species here."
            )
        else:
            species_str = ", ".join(readable[:-1]) + f" and {readable[-1]}"
            fish_speech = (
                f"At {temp_f} degrees, species commonly active here include {species_str}."
            )
    else:
        fish_speech = (
            f"At {temp_f} degrees, check local reports for current activity — "
            "I don't have species data for this exact station yet."
        )

    # Shop speech
    shop        = data.get("nearby_shop")
    shop_speech = _format_shop_speech(shop) if shop else ""

    # Gear / cart info
    directive      = data.get("alexa_directive")
    secondary      = data.get("secondary_directive")
    gear_name      = data.get("recommended_gear")
    secondary_gear = data.get("secondary_gear")
    asin           = directive["payload"]["items"][0]["asin"] if directive else None
    associates_id  = directive["payload"]["associatedId"] if directive else None
    secondary_asin = secondary["payload"]["items"][0]["asin"] if secondary else None

    return speak(
        temp_speech + " Want to know what fish are active at this temperature?",
        end_session=False,
        session_attributes={
            "awaiting_fish_info":     True,
            "awaiting_gear_question": False,
            "awaiting_shop_choice":   False,
            "awaiting_cart_confirm":  False,
            "pending_fish_speech":    fish_speech,
            "pending_shop_speech":    shop_speech,
            "pending_gear_name":      gear_name,
            "pending_asin":           asin,
            "pending_associates_id":  associates_id,
            "pending_secondary_asin": secondary_asin,
            "pending_secondary_gear": secondary_gear,
        },
    )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _offer_amazon_gear(session_attrs):
    gear_name = session_attrs.get("pending_gear_name")
    if not gear_name:
        return speak(
            "I don't have a gear recommendation for these conditions. Tight lines!",
            end_session=True,
        )
    return speak(
        f"For these conditions I'd suggest the {gear_name}. "
        "Want me to add it to your Amazon cart?",
        end_session=False,
        session_attributes={
            **session_attrs,
            "awaiting_gear_question": False,
            "awaiting_shop_choice":   False,
            "awaiting_cart_confirm":  True,
        },
    )


def _do_cart_add(session_attrs):
    asin           = session_attrs.get("pending_asin")
    associates_id  = session_attrs.get("pending_associates_id")
    secondary_asin = session_attrs.get("pending_secondary_asin")
    secondary_gear = session_attrs.get("pending_secondary_gear")
    if not asin:
        return speak("Sorry, I lost track of what to add. Try asking again.", end_session=True)
    response = add_to_cart(asin, associates_id)
    if secondary_asin:
        response["response"]["outputSpeech"]["ssml"] = (
            f"<speak>Done! Added to your cart. "
            f"Would you also like the {secondary_gear} to round out your setup?</speak>"
        )
        response["response"]["shouldEndSession"] = False
        response["sessionAttributes"] = {
            **session_attrs,
            "pending_asin":           secondary_asin,
            "pending_secondary_asin": None,
            "pending_secondary_gear": None,
            "awaiting_cart_confirm":  True,
        }
    return response


def _format_shop_speech(shop):
    if not shop:
        return ""
    name    = shop.get("name", "a local shop")
    address = shop.get("address", "")
    is_open = shop.get("open_now")
    status  = "open right now" if is_open else "closed right now"
    parts   = [f"The nearest bait shop is {name}, {status}"]
    if address:
        parts.append(f"at {address}")
    return ", ".join(parts) + "."


# ---------------------------------------------------------------------------
# Cart directive
# ---------------------------------------------------------------------------

def add_to_cart(asin, associates_id):
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "SSML",
                "ssml": "<speak>Adding it to your cart now.</speak>",
            },
            "directives": [
                {
                    "type": "Connections.SendRequest",
                    "name": "AddToShoppingCart",
                    "payload": {
                        "type":         "BuyShoppingProducts",
                        "items":        [{"asin": asin, "quantity": 1}],
                        "associatedId": associates_id,
                    },
                    "token": "fishing-guide-cart-token",
                }
            ],
            "shouldEndSession": None,
        },
    }


def handle_cart_response(event):
    status = event["request"].get("status", {})
    if status.get("code") == "200":
        return speak("Done! I've added it to your cart. Good luck out there!", end_session=True)
    return speak(
        "I wasn't able to add that to your cart right now. You can find it in the Amazon app.",
        end_session=True,
    )


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------

def speak(text, end_session=True, session_attributes=None):
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "SSML",
                "ssml": f"<speak>{text}</speak>",
            },
            "shouldEndSession": end_session,
        },
    }
    if session_attributes is not None:
        response["sessionAttributes"] = session_attributes
    return response
