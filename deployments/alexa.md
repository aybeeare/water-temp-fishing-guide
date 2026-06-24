# Alexa Deployment

**Target:** Amazon Alexa Skills Kit + AWS Lambda + Railway.app

## Architecture

```
Alexa Device → Lambda (alexa_bridge/) → FastAPI (Railway) → SQLite + Ingest
```

## FastAPI (Railway)

Environment variables:
```
USGS_API_KEY           = <key>
GOOGLE_PLACES_API_KEY  = <key>
ASSOCIATES_TRACKING_ID = watertemperat-20
DAILY_PLACES_LIMIT     = 50
ENABLE_BAIT_SHOP       = true        ← Google Places active
```

Build command: `python db/init_db.py`
Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

## Lambda (AWS)

- Runtime: Python 3.12
- Handler: `handler.lambda_handler`
- Zip: `alexa_bridge/` folder contents
- Environment variables:
  ```
  FASTAPI_URL            = https://your-app.up.railway.app
  ASSOCIATES_TRACKING_ID = watertemperat-20
  ```
- Trigger: Alexa Skills Kit (paste Skill ID from Alexa console)

## Alexa Console

- Invocation name: "fishing water guide"
- Endpoint: AWS Lambda ARN
- Interaction model: `skill-package/`
- Distribution: US only

## Feature notes

- Bait shop lookup (Google Places) is active — spoken in response
- Amazon affiliate cart flow is active — Connections.SendRequest directive
- Sponsor script slot available for paid placements
