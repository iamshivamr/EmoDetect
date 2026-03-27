# EmoDetect

Dual-modality emotion analysis on **RAVDESS-style** speech and face data: an **audio** classifier (MFCC features + scikit-learn) and **DeepFace** facial emotion, with a **fusion** rule when both modalities are present. Includes a **Jupyter** training notebook and a **FastAPI** web dashboard for uploads.

## What it does

- **Audio**: MFCC + delta features → trained `audio_model.pkl` (labels in `audio_labels.pkl`).
- **Image**: [DeepFace](https://github.com/serengil/deepface) emotion on the uploaded face photo.
- **Fusion** (`backend/emotion_service.py`): When audio and photo disagree, negative emotions (sad, angry, fearful) are prioritized; identical modalities agree outright.
- **Web UI**: Static assets under `web/static/`; API at `/api/analyze` (multipart: optional `photo` + optional `audio`).

## Repository layout

| Path | Role |
|------|------|
| `RAVDESS_Dual_Emotion_Detection.ipynb` | Train/evaluate, export `audio_model.pkl` / `audio_labels.pkl` |
| `backend/main.py` | FastAPI app, static mounts, `/api/health`, `/api/analyze` |
| `backend/emotion_service.py` | Feature extraction, model load, DeepFace + fusion |
| `run_dashboard.py` | Local server on `http://127.0.0.1:8765` |
| `web/static/` | Dashboard HTML/CSS/JS |
| `requirements_web.txt` | Minimal deps for the API + UI only |
| `start_emodet.sh` | Optional: Jupyter Lab, dashboard, Cloudflare tunnel |
| `cloudflared/` | Tunnel config example and setup notes |

Large media folders (`audio_files/`, `video_files/`, `ravdess_data/`, etc.) are for training and demos; they are not required to *run* the dashboard if you already have the pickle models in the project root.

## Prerequisites

- Python 3.11+ recommended (matches typical local setups for TensorFlow / DeepFace).
- For the **notebook**, install the ML stack (see the notebook’s install cell): e.g. `deepface`, `tensorflow`, `librosa`, `scikit-learn`, `opencv-python` or `opencv-python-headless`, etc.
- For the **dashboard only**, a venv with `requirements_web.txt` **plus** the same runtime stack DeepFace needs (TensorFlow, OpenCV, etc.) — same as you use for inference in the notebook.

## Quick start (dashboard)

1. Create a virtual environment and install dependencies (at minimum `pip install -r requirements_web.txt`, and the packages that DeepFace / your notebook use for inference).

2. Place trained artifacts in the **project root** (train via the notebook or copy from `ravdess_data/models/` if you use that layout):

   - `audio_model.pkl`
   - `audio_labels.pkl`

3. From the repo root:

   ```bash
   python run_dashboard.py
   ```

4. Open **http://127.0.0.1:8765** — upload an image and/or audio (WAV, MP3, FLAC, M4A, OGG; images JPG/PNG/WebP/GIF). Max upload size per file: **35 MB**.

5. Check **http://127.0.0.1:8765/api/health** for model file presence and server status.

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | JSON: `ok`, whether `audio_model.pkl` / `audio_labels.pkl` exist |
| `POST` | `/api/analyze` | `multipart/form-data`: fields `photo` and/or `audio` |

## Environment variables (optional)

| Variable | Default | Purpose |
|----------|---------|---------|
| `EMODETECT_DETECTOR_BACKEND` | `opencv` | DeepFace face detector backend |
| `EMODETECT_PARALLEL` | `1` | Set to `0` to run photo and audio steps serially (debugging) |
| `TF_CPP_MIN_LOG_LEVEL` | often `2` | Quieter TensorFlow logs (set in `run_dashboard.py`) |

## Jupyter Lab + tunnel (optional)

- `./start_emodet.sh` — starts Jupyter (port **8888**), the dashboard (**8765**), and optionally `cloudflared` if `cloudflared/config.yml` exists.
- `./start_emodet.sh --no-tunnel` — local services only.
- `./start_emodet.sh stop` — stop using PID files under `logs/`.
- Detailed Cloudflare steps: **`cloudflared/SETUP.txt`**. Copy `cloudflared/config.yml.example` to `cloudflared/config.yml` and add your tunnel credentials (do not commit secrets).

## Dataset and training

The notebook expects **RAVDESS** (or compatible) **audio** and **video** under `audio_files/` and `video_files/`, with optional backup under `ravdess_data/`. Training and evaluation steps are documented in **`RAVDESS_Dual_Emotion_Detection.ipynb`**.

## License

Add a `LICENSE` file if you distribute this project publicly.
