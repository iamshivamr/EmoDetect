"""Photo + audio emotion fusion — shared by the notebook logic and the web API."""

from __future__ import annotations

import os
import pickle
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import librosa
import numpy as np

# Quieter TF logs before any deepface import (main process should set earlier too)
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "audio_model.pkl"
LABELS_PATH = BASE_DIR / "audio_labels.pkl"

SR = 22050
N_MFCC = 40

REGULATION_MAP = {
    "happy": "Gratitude: list three good things happening right now.",
    "sad": "Breathing: inhale 4s, hold 4s, exhale 6s (five reps).",
    "angry": "Pause: count to ten, then plan one constructive next step.",
    "fearful": "Grounding: name five things you can see around you.",
    "neutral": "Body scan: notice tension and add a gentle stretch.",
    "calm": "Maintain steady breathing and a relaxed posture.",
    "disgust": "Take a short break and shift to neutral surroundings.",
    "surprised": "Label the feeling, then return to a calm baseline.",
}

_audio_model = None
_audio_le = None

# Default matches DeepFace docs; opencv is the fastest detector (same default as analyze()).
DETECTOR_BACKEND = os.environ.get("EMODETECT_DETECTOR_BACKEND", "opencv")

# Set EMODETECT_PARALLEL=0 to force serial photo+audio (debug if threads cause issues on your OS).
_USE_PARALLEL = os.environ.get("EMODETECT_PARALLEL", "1") != "0"


def warmup_backend() -> None:
    """Preload sklearn + DeepFace face detector + emotion model so the first user request is fast.

    Same models the notebook uses; this only avoids cold-start delay after the server boots.
    """
    load_models()
    from deepface import DeepFace

    try:
        DeepFace.build_model("opencv", task="face_detector")
    except Exception:
        pass
    try:
        DeepFace.build_model("Emotion", task="facial_attribute")
    except Exception:
        pass


def extract_audio_features(path: str) -> np.ndarray | None:
    try:
        y, sr = librosa.load(path, sr=SR, mono=True, duration=3.0)
        if len(y) < 512:
            return None
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC, n_fft=2048, hop_length=512)
        d1 = librosa.feature.delta(mfcc)
        d2 = librosa.feature.delta(mfcc, order=2)

        def stats(m: np.ndarray) -> np.ndarray:
            return np.concatenate([np.mean(m, axis=1), np.std(m, axis=1)])

        return np.concatenate([stats(mfcc), stats(d1), stats(d2)]).astype(np.float32)
    except Exception:
        return None


def load_models() -> None:
    global _audio_model, _audio_le
    if _audio_model is not None:
        return
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Missing {MODEL_PATH.name}. Train the notebook and save audio_model.pkl in the project root."
        )
    if not LABELS_PATH.is_file():
        raise FileNotFoundError(f"Missing {LABELS_PATH.name}.")
    with open(MODEL_PATH, "rb") as f:
        _audio_model = pickle.load(f)
    with open(LABELS_PATH, "rb") as f:
        _audio_le = pickle.load(f)


def fuse_emotions(audio_emo: str, photo_emo: str) -> str:
    neg = {"sad", "angry", "fearful"}
    a, f = audio_emo.lower(), photo_emo.lower()
    if a == f:
        return a
    if a in neg:
        return a
    if f in neg:
        return f
    return a


def run_fusion(
    image_path: str | None,
    audio_path: str | None,
) -> dict[str, Any]:
    """Run DeepFace and/or sklearn audio pipeline. Pass one path or both; fusion when both."""
    if not image_path and not audio_path:
        raise ValueError("Provide at least one of image_path or audio_path.")

    has_img = bool(image_path and os.path.isfile(image_path))
    has_aud = bool(audio_path and os.path.isfile(audio_path))
    if not has_img and not has_aud:
        raise ValueError("No valid image or audio file on disk.")

    if has_aud:
        load_models()

    audio_model = _audio_model
    audio_le = _audio_le

    from deepface import DeepFace

    photo_path_abs = os.path.abspath(image_path) if has_img else ""
    wav_path_abs = os.path.abspath(audio_path) if has_aud else ""

    def _face_branch():
        return DeepFace.analyze(
            photo_path_abs,
            actions=["emotion"],
            enforce_detection=False,
            detector_backend=DETECTOR_BACKEND,
            align=True,
            silent=True,
        )

    def _audio_branch() -> str:
        feat = extract_audio_features(wav_path_abs)
        if feat is None:
            return "audio_error"
        idx = audio_model.predict(feat.reshape(1, -1))[0]
        return str(audio_le.inverse_transform([idx])[0]).lower()

    photo_emo: str | None = None
    audio_emo: str | None = None
    photo_scores: dict[str, float] | None = None

    if has_img and has_aud:
        if _USE_PARALLEL:
            try:
                with ThreadPoolExecutor(max_workers=2) as pool:
                    fut_face = pool.submit(_face_branch)
                    fut_audio = pool.submit(_audio_branch)
                    photo_res = fut_face.result()
                    audio_emo = fut_audio.result()
            except Exception:
                photo_res = _face_branch()
                audio_emo = _audio_branch()
        else:
            photo_res = _face_branch()
            audio_emo = _audio_branch()

        photo_emo = str(photo_res[0]["dominant_emotion"]).lower()
        em = photo_res[0].get("emotion")
        if isinstance(em, dict):
            photo_scores = {k.lower(): float(v) for k, v in em.items()}
        final_emotion = fuse_emotions(audio_emo, photo_emo)
    elif has_img:
        photo_res = _face_branch()
        photo_emo = str(photo_res[0]["dominant_emotion"]).lower()
        em = photo_res[0].get("emotion")
        if isinstance(em, dict):
            photo_scores = {k.lower(): float(v) for k, v in em.items()}
        final_emotion = photo_emo
    else:
        audio_emo = _audio_branch()
        final_emotion = audio_emo

    regulation = REGULATION_MAP.get(
        str(final_emotion).lower(),
        "Nice — keep observing how you feel and adjust gently.",
    )

    return {
        "photo_emotion": photo_emo,
        "audio_emotion": audio_emo,
        "final_emotion": final_emotion,
        "regulation": regulation,
        "photo_scores": photo_scores,
        "photo_filename": os.path.basename(photo_path_abs) if has_img else None,
        "audio_filename": os.path.basename(wav_path_abs) if has_aud else None,
    }
