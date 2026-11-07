# Clip Notes — YouTube Transcript & Summary Assistant

A real frontend + separate FastAPI backend based on the supplied showcase page. The page accepts a YouTube link, retrieves readable subtitle text on the backend, summarizes only that transcript, and waits for explicit review before optional Lark sending.

## What is included

- `START_HERE.md` — beginner-friendly GitHub, Render, and HTMLSpace setup steps.
- `frontend/index.html` — responsive UI adapted from the supplied visual style; no hard-coded demo examples.
- `backend/main.py` — password-gated API, direct YouTube caption retrieval with yt-dlp fallback, OpenAI Responses API summary, and optional approved Lark message delivery.
- `render.yaml` — Render Blueprint configuration.
- `backend/tests/test_app.py` — offline API tests using mocked network/model work.

The backend does not save video transcripts or summaries to a database. Lark delivery is disabled until the app credentials and recipient are configured. The user must review and check the explicit approval box before sending.

## Local preview

Requirements: Python 3.11+ and yt-dlp (including a supported JS runtime for full YouTube extraction). In a terminal:

1. `cd backend`
2. Create a virtual environment and install `requirements.txt`.
3. Copy `.env.example` to `.env`; set `APP_PASSWORD`, `SESSION_SECRET`, `OPENAI_API_KEY`, and `OPENAI_MODEL`.
4. Start the API: `uvicorn main:app --reload --port 8000`.
5. In a second terminal, serve the frontend: `python -m http.server 5500 --directory ../frontend`.
6. Open `http://127.0.0.1:5500`, check the backend URL, sign in, and submit a YouTube link.

The API's CORS configuration defaults to local preview origins in the example env file. For a hosted frontend, set `FRONTEND_ORIGINS` to the exact HTMLSpace origin (scheme + host, no path), or a comma-separated list. Avoid wildcard origins for a public deployment.

## Deploy the backend on Render

1. Create a new GitHub repository and upload the complete project folder (`README.md`, `render.yaml`, `backend/`, and `frontend/`). Do not upload `.env` or any secrets.
2. In Render, choose **New → Blueprint**, connect the GitHub repository, and apply the Blueprint. Render reads the root `render.yaml` and deploys the `backend/` folder as a web service. Alternatively, create a Web Service with root directory `backend`, build command `pip install -r requirements.txt`, and start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
3. In the Render service's environment settings, enter `OPENAI_API_KEY` and `OPENAI_MODEL`; set a strong `APP_PASSWORD`. The Blueprint prompts for the app password and generates a `SESSION_SECRET`. Keep all secrets on the backend.
4. Wait for deployment; open `/api/health` on the Render URL. `login_configured`, `summary_configured`, and `yt_dlp_available` should be true. `lark_configured` remains false until optional Lark settings are filled.
5. If YouTube extraction fails due to missing JavaScript challenge support, verify the deploy includes `yt-dlp[default,deno]` and its supported Deno runtime; YouTube may rate-limit or block some requests, and not every video has captions.

## Publish the frontend on HTMLSpace

1. Open `frontend/index.html` locally and check that it loads.
2. Publish the single `index.html` via HTMLSpace **Files & folders** (or place it at the root of a ZIP named with `index.html`). The Google Fonts link is optional; the page falls back to system fonts.
3. Copy the published origin, then set the backend's `FRONTEND_ORIGINS` to that exact origin and redeploy/restart the backend.
4. Open the published site, enter the Render API base URL (no trailing slash), click **Check connection**, and sign in with the configured app password.

HTMLSpace hosts the frontend only. The backend must stay deployed separately. Do not place API keys, Lark secrets, or the app password in the frontend.

## Optional Lark delivery

To enable sending, create/configure a Lark custom app, enable its bot, grant the required send-message permission, publish/install it for the intended user or chat, and configure these backend environment variables:

- `LARK_APP_ID`
- `LARK_APP_SECRET`
- `LARK_RECEIVE_ID` — the target open ID or chat ID
- `LARK_RECEIVE_ID_TYPE` — `open_id` or `chat_id`
- `LARK_BASE` — `https://open.larksuite.com` for Lark; use the appropriate Feishu API base for a Feishu tenant

The configured bot must be allowed to message the target. After the user reviews the result and checks approval, the frontend sends the summary to the backend; only then does the backend call Lark. This version sends a text message, not a document/file.

## Test

From `backend` run `python -m unittest discover -s tests -v`. These tests verify API behavior with transcript/model responses mocked; they do not claim live YouTube, model, Render, or Lark connectivity. A live summary requires valid OpenAI credentials, and Lark delivery requires a configured app and recipient.

## Security and limits

- Use HTTPS for hosted deployments; the app password and bearer session token protect API actions.
- The session expires after 12 hours; refresh the page and sign in again when needed.
- Configure exact allowed frontend origins for deployment.
- The app sends transcript text to the configured OpenAI API to generate the summary. Review your provider's data settings before use.
- yt-dlp retrieves subtitle files only; it does not download video. Retrieval can fail, captions may be absent or inaccurate, and HTTP 429 means retry later.
- Transcript text above the processing limit is rejected rather than silently truncated.
