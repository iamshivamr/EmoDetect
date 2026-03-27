/**
 * Dashboard copy & theme — edit this file to customize without touching HTML/CSS much.
 * Optional keys are skipped if omitted.
 */
window.EMO_DASHBOARD_CONFIG = {
  /** Optional; if omitted, document title is `${appName} — ${tagline}`. */
  // pageTitle: "custom tab title",

  appName: "emodetect",
  tagline: "Emotions from face and voice",
  logoGlyph: "🧠",

  uploadHeading: "Run analysis",
  resultsHeading: "Results",

  /** Shown under “Run analysis” — keep short or use hintHtml */
  hintText:
    "Upload a face image and/or a short speech clip. With both files, DeepFace and the trained audio model run and results are fused; with one file, only that modality is analyzed.",

  analyzeButton: "Analyze fusion",
  clearButton: "Clear",

  /** Shown while loading when both image and audio are uploaded */
  loadingMessage: "Running face + audio models…",
  /** Image only */
  loadingMessageImage: "Running face model…",
  /** Audio only */
  loadingMessageAudio: "Running audio model…",

  footerLeft: "Backend: FastAPI",
  footerRight: "POST /api/analyze",
  /** Shown next to footer (browser cannot read server port; set to match run_dashboard.py) */
  serverPort: "8765",

  /** Optional: set any --variable from theme.css at runtime (brand: #B298E7 #B8E3E9 #F5B8D5 #F9BEDD) */
  theme: {
    // "--lavender": "#b298e7",
    // "--radius": "20px",
  },
};
