"""EmoDetect dashboard API — serve static UI and /api/analyze."""

from __future__ import annotations

import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from backend.emotion_service import run_fusion, warmup_backend

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "web" / "static"
FONTS_WEB_DIR = BASE_DIR / "Fonts" / "Webfont"

ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_AUDIO = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}
MAX_UPLOAD_BYTES = 35 * 1024 * 1024

_log = logging.getLogger("emodet")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        warmup_backend()
        _log.info("Warmup: audio + DeepFace detector + emotion models loaded.")
    except Exception as e:
        _log.warning("Warmup incomplete (first request may be slower): %s", e)
    yield


app = FastAPI(title="EmoDetect Dashboard", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def static_cache_headers(request: Request, call_next):
    """Ask browsers and CDNs to revalidate HTML/CSS/JS after deploy (bump ?v= in index.html too)."""
    response = await call_next(request)
    path = request.url.path
    if (
        path == "/"
        or path.startswith("/assets/")
        or path.startswith("/fonts/")
    ):
        response.headers["Cache-Control"] = "no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


@app.get("/api/health")
def health():
    from backend.emotion_service import LABELS_PATH, MODEL_PATH

    return {
        "ok": True,
        "audio_model": MODEL_PATH.is_file(),
        "audio_labels": LABELS_PATH.is_file(),
        "tips": "Server preloads TensorFlow + DeepFace on startup. Use opencv detector (default).",
    }


@app.post("/api/analyze")
async def analyze(
    photo: UploadFile | None = File(None, description="Face image (optional if audio provided)"),
    audio: UploadFile | None = File(None, description="Audio clip (optional if image provided)"),
):
    has_photo = photo is not None and bool((photo.filename or "").strip())
    has_audio = audio is not None and bool((audio.filename or "").strip())
    if not has_photo and not has_audio:
        raise HTTPException(
            400,
            "Upload at least one file: an image (JPG/PNG/WebP) and/or an audio clip (WAV/MP3/…).",
        )

    ps = Path(photo.filename or "").suffix.lower() if has_photo else ""
    au = Path(audio.filename or "").suffix.lower() if has_audio else ""
    if has_photo and ps not in ALLOWED_IMAGE:
        raise HTTPException(400, f"Unsupported image type {ps!r}. Use {ALLOWED_IMAGE}.")
    if has_audio and au not in ALLOWED_AUDIO:
        raise HTTPException(400, f"Unsupported audio type {au!r}. Use {ALLOWED_AUDIO}.")

    photo_bytes = await photo.read() if has_photo else None
    audio_bytes = await audio.read() if has_audio else None
    if photo_bytes is not None and len(photo_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image file too large (max 35 MB).")
    if audio_bytes is not None and len(audio_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Audio file too large (max 35 MB).")

    tmpdir = tempfile.mkdtemp(prefix="emodet_")
    try:
        img_path: str | None = None
        aud_path: str | None = None
        if has_photo and photo_bytes is not None:
            img_path = os.path.join(tmpdir, f"upload{ps or '.jpg'}")
            with open(img_path, "wb") as f:
                f.write(photo_bytes)
        if has_audio and audio_bytes is not None:
            aud_path = os.path.join(tmpdir, f"upload{au or '.wav'}")
            with open(aud_path, "wb") as f:
                f.write(audio_bytes)

        try:
            result = run_fusion(img_path, aud_path)
        except FileNotFoundError as e:
            raise HTTPException(503, str(e)) from e
        except Exception as e:
            raise HTTPException(500, f"Analysis failed: {e!s}") from e

        return {"success": True, **result}
    finally:
        for name in os.listdir(tmpdir):
            try:
                os.unlink(os.path.join(tmpdir, name))
            except OSError:
                pass
        try:
            os.rmdir(tmpdir)
        except OSError:
            pass


if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")
if FONTS_WEB_DIR.is_dir():
    app.mount("/fonts", StaticFiles(directory=FONTS_WEB_DIR), name="fonts")


@app.get("/")
def root():
    index = STATIC_DIR / "index.html"
    if not index.is_file():
        return {"message": "Place web/static/index.html to enable the dashboard UI."}
    return FileResponse(
        index,
        headers={
            "Cache-Control": "no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


def main():
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )


if __name__ == "__main__":
    main()
