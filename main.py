import asyncio
import io
import logging
import os
import re

import edge_tts
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edge-tts-api")

app = FastAPI(title="Edge TTS API")

# Good default neural voices. Full list: run `edge-tts --list-voices`
DEFAULT_VOICE = "en-US-GuyNeural"

# Characters that break SSML / the edge-tts protocol if left raw
_SANITIZE_PATTERN = re.compile(r"[\*_#`]")


def sanitize_text(text: str) -> str:
    """Strip markdown symbols and XML-unsafe characters that can break TTS."""
    text = _SANITIZE_PATTERN.sub("", text)
    text = text.replace("&", "and")
    text = text.replace("<", "").replace(">", "")
    return text.strip()


class TTSRequest(BaseModel):
    text: str
    voice: str = DEFAULT_VOICE


@app.get("/")
def root():
    return {"status": "ok", "message": "Edge TTS API is running"}


@app.get("/voices")
async def list_voices():
    voices = await edge_tts.list_voices()
    simplified = [
        {"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]}
        for v in voices
    ]
    return JSONResponse(simplified)


async def generate_audio(text: str, voice: str):
    if not text.strip():
        return JSONResponse({"error": "text is required"}, status_code=400)

    clean_text = sanitize_text(text)
    logger.info(f"Generating TTS for {len(clean_text)} chars with voice={voice}")

    try:
        communicate = edge_tts.Communicate(clean_text, voice)
        audio_buffer = io.BytesIO()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        if audio_buffer.tell() == 0:
            logger.error("No audio data generated")
            return JSONResponse(
                {"error": "No audio data was generated. Check voice name and text content."},
                status_code=500,
            )

        audio_buffer.seek(0)

        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=voiceover.mp3"},
        )
    except Exception as e:
        logger.exception("TTS generation failed")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/tts")
async def text_to_speech_post(payload: TTSRequest):
    """Preferred: send text in JSON body to avoid URL length / encoding issues."""
    return await generate_audio(payload.text, payload.voice)


@app.get("/tts")
async def text_to_speech_get(
    text: str = Query(..., description="Text to convert to speech"),
    voice: str = Query(DEFAULT_VOICE, description="Voice name, e.g. en-US-GuyNeural"),
):
    """Kept for convenience/testing with short text via query params."""
    return await generate_audio(text, voice)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
