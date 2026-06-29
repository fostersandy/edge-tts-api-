# Edge TTS API

A tiny free wrapper around Microsoft Edge's neural text-to-speech voices,
exposed as a simple REST API for use in n8n (or anywhere else).

No API key. No quota. No billing account. Genuinely free, unlimited.

## Endpoints

- `GET /` — health check
- `GET /voices` — list all available voices
- `POST /tts?text=YOUR_TEXT&voice=en-US-GuyNeural` — returns an MP3 file

## Deploy on Railway

1. Push this folder to a new GitHub repo (or use Railway's "Deploy from local" CLI option)
2. In Railway: New Project → Deploy from GitHub repo → select this repo
3. Railway will detect the Dockerfile automatically and build it
4. Once deployed, Railway gives you a public URL like:
   `https://edge-tts-api-production-xxxx.up.railway.app`
5. Test it: visit `https://YOUR-URL/` in a browser — you should see
   `{"status":"ok","message":"Edge TTS API is running"}`

## Use in n8n

Replace your ElevenLabs HTTP Request node with:

- **Method:** POST
- **URL:** `https://YOUR-RAILWAY-URL/tts`
- **Query Parameters:**
  - `text` = `{{ $json.scriptChunk }}` (or whatever field has your script text)
  - `voice` = `en-US-GuyNeural` (or any voice from `/voices`)
- **Response Format:** set to "File" / binary (it returns raw MP3 bytes)

Pipe that binary output straight into your "Save MP3 to Google Drive" node,
same as before.

## Good voice options

- `en-US-GuyNeural` — male, US, energetic (good for sports content)
- `en-US-AriaNeural` — female, US, natural
- `en-GB-RyanNeural` — male, British
- `en-US-ChristopherNeural` — male, deep/authoritative

Run `GET /voices` on your deployed URL for the full list.

## Local testing (optional)

```bash
pip install -r requirements.txt
python main.py
```

Then test with:

```bash
curl -X POST "http://localhost:8000/tts?text=Hello%20world&voice=en-US-GuyNeural" --output test.mp3
```
