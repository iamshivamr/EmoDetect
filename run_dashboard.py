#!/usr/bin/env python3
"""Start the EmoDetect web dashboard (FastAPI + static UI).

From the project root:
  python run_dashboard.py

Then open http://127.0.0.1:8765
Requires: pip install -r requirements_web.txt
          audio_model.pkl and audio_labels.pkl in the project root (from the notebook).

Performance: set reload=False (default below) so TensorFlow + DeepFace load once.
             reload=True reloads the process on every code change and is much slower to use.
"""

from __future__ import annotations

import os

# Before TensorFlow is imported (via DeepFace warmup)
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )
