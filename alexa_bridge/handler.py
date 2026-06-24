"""
Alexa Skills Kit Lambda adapter — thin bridge between ASK request/response
format and the FastAPI backend.

Handles two-turn cart flow:
  Turn 1: fetch water temp → speak recommendation → "Want me to add to cart?"
  Turn 2: YesIntent → fire Connections.SendRequest directive
  Turn 3: Connections.Response → confirm cart result

Environment variables:
  FASTAPI_URL   public URL of the hosted FastAPI (e.g. https://your-app.railway.app)

Handler path (set in AWS Lambda console): handler.lambda_handler
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
    intent_name = event["request"]["intent"]["name"]
    session_attrs = event.get("session", {}).get("attributes", {})

    if intent_name == "GetWaterTempIntent":
        slots = event["request"]["intent"].get("slots", {})
        location = slots.get("location", {}).get("value")
        if not location:
            return speak(
                "Which lake, river, or coastal area would you like water temperature for?",
                end_session=False,
            )
        return fetch_and_respond(location, session_attrs)

    if intent_name == "AMAZON.YesIntent":
        # State 1 — user said yes to "Need any gear?"
        if session_attrs.get("awaiting_gear_question"):
            gear_name = session_attrs.get("pending_gear_name", "some gear")
            return speak(
                f"Based on the conditions, I'd suggest the {gear_name}. "
                "Want me to add it to your Amazon cart?",
                end_session=False,
                session_attributes={
                    **session_attrs,
                    "awaiting_gear_question": False,
                    "awaiting_cart_confirm": True,
                },
            )

        # State 2 — user confirmed the cart add
        if session_attrs.get("awaiting_cart_confirm"):
            asin          = session_attrs.get("pending_asin")
            associates_id = session_attrs.get("pending_associates_id")
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
                    "pending_asin": secondary_asin,
                    "pending_secondary_asin": None,
                    "pending_secondary_gear": None,
                    "awaiting_cart_confirm": True,
                }
            return response

        return speak(
            "I'm not sure what you're saying yes to. "
            "Try asking for water temperature at a location first.",
            end_session=False,
        )

    if intent_name == "AMAZON.NoIntent":
        return speak("No problem. Good luck on the water!", end_session=True)

    if intent_name == "AMAZON.HelpIntent":
        return speak(
            "Ask me for the water temperature at any lake, river, or coastal location. "
            "I'll tell you the temperature, how the fish are behaving, and suggest gear. "
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
# FastAPI call
# ---------------------------------------------------------------------------

def fetch_and_respond(location, session_attrs):
    params = urllib.parse.urlencode({"location": location})
    url = f"{FASTAPI_URL}/fishing-guide?{params}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return speak(
                f"I couldn't find water temperature data for {location}. "
                "Try a nearby location or check the spelling."
            )
        return speak(
            "I'm having trouble reaching the water temperature service right now. "
            "Please try again in a moment."
        )
    except Exception:
        return speak(
            "Something went wrong fetching the water temperature. Please try again."
        )

    # Disambiguation — FastAPI found multiple locations with this name
    if data.get("disambiguation"):
        return speak(data["spoken_response"], end_session=False)

    spoken        = data["spoken_response"]
    directive     = data.get("alexa_directive")
    gear_name     = data.get("recommended_gear")
    secondary     = data.get("secondary_directive")
    secondary_asin = secondary["payload"]["items"][0]["asin"] if secondary else None
    secondary_gear = data.get("secondary_gear")

    if directive and gear_name and data.get("temp_f") is not None:
        asin          = directive["payload"]["items"][0]["asin"]
        associates_id = directive["payload"]["associatedId"]
        return speak(
            spoken + " Need any gear for today?",
            end_session=False,
            session_attributes={
                **session_attrs,
                "awaiting_gear_question": True,
                "awaiting_cart_confirm":  False,
                "pending_gear_name":      gear_name,
                "pending_asin":           asin,
                "pending_associates_id":  associates_id,
                "pending_secondary_asin": secondary_asin,
                "pending_secondary_gear": secondary_gear,
            },
        )

    return speak(spoken, end_session=True)


# ---------------------------------------------------------------------------
# Cart directives
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
                        "type": "BuyShoppingProducts",
                        "items": [{"asin": asin, "quantity": 1}],
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
        "I wasn't able to add that to your cart right now. "
        "You can find it in the Amazon app.",
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
