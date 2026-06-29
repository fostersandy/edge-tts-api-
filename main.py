import asyncio
import io
import os

import edge_tts
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI(title="Edge TTS API")

# Good default neural voices. Full list: run `edge-tts --list-voices`
DEFAULT_VOICE = "en-US-GuyNeural"


@app.get("/")
def root():
    return {"status": "ok", "message": "Edge TTS API is running"}


@app.get("/voices")
async def list_voices():
    voices = await edge_tts.list_voices()
    # Trim to just the useful fields
    simplified = [
        {"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
        for v in voices
    ]
    return JSONResponse(simplified)


@app.post("/tts")
async def text_to_speech(
    text: str = Query(..., description="Text to convert to speech"),
    voice: str = Query(DEFAULT_VOICE, description="Voice name, e.g. en-US-GuyNeural"),
):
    if not text.strip():
        return JSONResponse({"error": "text is required"}, status_code=400)

    communicate = edge_tts.Communicate(text, voice)
    audio_buffer = io.BytesIO()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])

    audio_buffer.seek(0)

    return StreamingResponse(
        audio_buffer,
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=voiceover.mp3"},
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
