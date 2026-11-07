# Start Here — Deploy Clip Notes

You do not need to write code. Use the attached ZIPs and follow these steps.

## 1. Upload the project to GitHub

1. Download and **extract** `clip-notes-agent.zip` on your computer.
2. Sign in to GitHub and create a new repository named `clip-notes-agent`. Choose **Private** if you do not want the source code to be public. Do not add a separate README or `.gitignore` during repository creation; this project already includes them.
3. Open the empty repository. Choose **Add file → Upload files**.
4. Drag the *contents inside* the extracted `clip-notes-agent` folder into the upload page. The repository’s top level must show `render.yaml`, `README.md`, `.gitignore`, `backend/`, and `frontend/`.
5. Commit the upload to the default branch. Do not upload or create a `.env` file; it can contain secrets.

## 2. Connect the repository to Render

1. Sign in to Render and choose **New → Blueprint**.
2. Connect your GitHub account if prompted, then select the `clip-notes-agent` repository.
3. Render will read the root `render.yaml`. It creates the web service using `backend/` as its service directory.
4. When prompted, set these values:
   - `APP_PASSWORD`: create a strong password you can remember; this is what you type into the website.
   - `OPENAI_API_KEY`: your private OpenAI API key.
   - `OPENAI_MODEL`: a model name enabled for that API key.
   - `SESSION_SECRET`: let the Blueprint generate it automatically.
5. Apply the Blueprint and wait until deployment finishes. Never send these secrets in chat or commit them to GitHub.

## 3. Confirm the backend

1. Open the Render service URL and add `/api/health` to the end.
2. Check that `login_configured`, `summary_configured`, and `yt_dlp_available` are `true`. `lark_configured` will be `false` until you add Lark settings.
3. Copy the base Render URL (without `/api/health`); you will enter it in the website.

## 4. Publish the website on HTMLSpace

1. Open HTMLSpace's Community publishing page.
2. Upload `clip-notes-htmlspace-upload.zip` as a ZIP package. It contains `index.html` at the ZIP root.
3. Publish and save the claim token if you want to manage the page later. Copy the published website's origin (the scheme and host only).
4. In Render's service settings, change `FRONTEND_ORIGINS` from `*` to that exact website origin, then save and deploy the change.

## 5. Use the site

1. Open the published HTMLSpace page.
2. Paste the Render base URL into **Backend URL** and click **Check connection**.
3. Enter your `APP_PASSWORD` and sign in.
4. Paste a YouTube or Shorts link and click **Retrieve transcript & summarize**.
5. Review the summary. If Lark is configured, check the approval box and press **Approve & send to Lark**. If it is not configured, use **Copy summary**.

## Optional Lark setup

Lark sending is not configured by default. The current integration sends the approved summary as a Lark **text message** to one configured user or chat; it does not create a document. To enable it, create and publish/install a Lark custom app with bot messaging permission, then add `LARK_APP_ID`, `LARK_APP_SECRET`, `LARK_RECEIVE_ID`, and `LARK_RECEIVE_ID_TYPE` to the Render service environment. Set `LARK_BASE` to the correct API host for your Lark/Feishu tenant. Keep these values private.

## If something fails

- `login_configured: false`: set `APP_PASSWORD` and `SESSION_SECRET` in Render.
- `summary_configured: false`: set `OPENAI_API_KEY` and `OPENAI_MODEL` in Render.
- Browser says it cannot connect: verify the Render base URL and exact `FRONTEND_ORIGINS` value.
- No readable captions or HTTP 429: that video may have no captions or YouTube may be rate-limiting retrieval. The app will not invent a summary.
- Lark button stays disabled: configure all Lark variables, permissions, and recipient details in Render.
