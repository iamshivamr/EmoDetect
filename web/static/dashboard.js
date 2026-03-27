(() => {
  const $ = (id) => document.getElementById(id);

  /** Emoji for photo/audio/fused labels — DeepFace + RAVDESS-style names (lowercase). */
  function emotionEmoji(raw) {
    if (raw == null || raw === "" || raw === "—") return "";
    const k = String(raw)
      .trim()
      .toLowerCase()
      .replace(/\s+/g, "_");
    const alias = {
      surprise: "surprised",
      fear: "fearful",
      joy: "happy",
      anger: "angry",
    };
    const key = alias[k] || k;
    const map = {
      happy: "😊",
      sad: "😢",
      angry: "😠",
      fearful: "😨",
      neutral: "😐",
      calm: "😌",
      disgust: "🤢",
      surprised: "😮",
      audio_error: "⚠️",
    };
    return map[key] || map[k] || "🎭";
  }

  function applyDashboardConfig() {
    const c = window.EMO_DASHBOARD_CONFIG;
    if (!c || typeof c !== "object") return;

    if (c.pageTitle) {
      document.title = c.pageTitle;
    } else if (c.appName != null && c.tagline) {
      document.title = `${c.appName} — ${c.tagline}`;
    }
    if (c.appName) {
      const el = $("appName");
      if (el) el.textContent = c.appName;
    }
    if (c.tagline) {
      const el = $("appTagline");
      if (el) el.textContent = c.tagline;
    }
    if (c.logoGlyph) {
      const el = $("logoGlyph");
      if (el) el.textContent = c.logoGlyph;
    }
    if (c.uploadHeading) {
      const el = $("upload-heading");
      if (el) el.textContent = c.uploadHeading;
    }
    if (c.resultsHeading) {
      const el = $("results-heading");
      if (el) el.textContent = c.resultsHeading;
    }
    if (c.hintText) {
      const el = $("hintText");
      if (el) el.textContent = c.hintText;
    }
    if (c.analyzeButton) {
      const el = $("analyzeLabel");
      if (el) el.textContent = c.analyzeButton;
    }
    if (c.clearButton) {
      const el = $("clearLabel");
      if (el) el.textContent = c.clearButton;
    }
    if (c.loadingMessage) {
      const el = $("loadingMessage");
      if (el) el.textContent = c.loadingMessage;
    }
    if (c.footerLeft) {
      const el = $("footerLeft");
      if (el) el.textContent = c.footerLeft;
    }
    if (c.footerRight) {
      const el = $("footerRight");
      if (el) el.textContent = c.footerRight;
    }
    if (c.serverPort) {
      const el = $("portHint");
      if (el) el.textContent = c.serverPort;
    }

    const theme = c.theme;
    if (theme && typeof theme === "object") {
      const root = document.documentElement;
      for (const [key, value] of Object.entries(theme)) {
        if (value == null || value === "") continue;
        if (key.startsWith("--")) {
          root.style.setProperty(key, String(value));
        } else if (key === "accent") {
          root.style.setProperty("--accent", String(value));
        } else {
          root.style.setProperty(`--${key}`, String(value));
        }
      }
    }
  }

  applyDashboardConfig();

  const inputPhoto = $("inputPhoto");
  const inputAudio = $("inputAudio");
  const dzPhoto = $("dzPhoto");
  const dzAudio = $("dzAudio");
  const photoName = $("photoName");
  const audioName = $("audioName");
  const btnAnalyze = $("btnAnalyze");
  const btnClear = $("btnClear");
  const errorBox = $("errorBox");
  const healthPill = $("healthPill");
  const healthText = $("healthText");
  const mainLayout = $("mainLayout");
  const resultsBody = $("resultsBody");
  const loadingOverlay = $("loadingOverlay");
  const loadingMessageEl = $("loadingMessage");
  const outPhoto = $("outPhoto");
  const outAudio = $("outAudio");
  const outPhotoEmoji = $("outPhotoEmoji");
  const outAudioEmoji = $("outAudioEmoji");
  const outFinal = $("outFinal");
  const outFinalEmoji = $("outFinalEmoji");
  const outRegulation = $("outRegulation");
  const outScores = $("outScores");
  const scoreList = $("scoreList");

  const THEME_KEY = "emodetect-theme";

  function getTheme() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function applyTheme(theme) {
    const next = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch (_) {
      /* ignore */
    }
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", next === "dark" ? "#17141f" : "#B298E7");
    const btn = $("themeToggle");
    if (btn) {
      btn.setAttribute("aria-pressed", next === "dark" ? "true" : "false");
      btn.setAttribute(
        "aria-label",
        next === "dark" ? "Switch to light mode" : "Switch to dark mode"
      );
      btn.title = next === "dark" ? "Light mode" : "Dark mode";
    }
  }

  const themeToggle = $("themeToggle");
  if (themeToggle) {
    applyTheme(getTheme());
    themeToggle.addEventListener("click", () => {
      applyTheme(getTheme() === "dark" ? "light" : "dark");
    });
  }

  let photoFile = null;
  let audioFile = null;

  function setError(msg) {
    if (!msg) {
      errorBox.hidden = true;
      errorBox.textContent = "";
      return;
    }
    errorBox.hidden = false;
    errorBox.textContent = msg;
  }

  function syncButton() {
    btnAnalyze.disabled = !(photoFile || audioFile);
    dzPhoto.classList.toggle("has-file", !!photoFile);
    dzAudio.classList.toggle("has-file", !!audioFile);
    photoName.textContent = photoFile ? photoFile.name : "";
    audioName.textContent = audioFile ? audioFile.name : "";
  }

  inputPhoto.addEventListener("change", () => {
    photoFile = inputPhoto.files?.[0] || null;
    syncButton();
  });
  inputAudio.addEventListener("change", () => {
    audioFile = inputAudio.files?.[0] || null;
    syncButton();
  });

  ["dragenter", "dragover"].forEach((ev) => {
    dzPhoto.addEventListener(ev, (e) => {
      e.preventDefault();
      dzPhoto.style.borderColor = "var(--accent)";
    });
    dzAudio.addEventListener(ev, (e) => {
      e.preventDefault();
      dzAudio.style.borderColor = "var(--accent)";
    });
  });
  ["dragleave", "drop"].forEach((ev) => {
    dzPhoto.addEventListener(ev, (e) => {
      e.preventDefault();
      dzPhoto.style.borderColor = "";
    });
    dzAudio.addEventListener(ev, (e) => {
      e.preventDefault();
      dzAudio.style.borderColor = "";
    });
  });
  dzPhoto.addEventListener("drop", (e) => {
    const f = e.dataTransfer.files?.[0];
    if (f && f.type.startsWith("image/")) {
      photoFile = f;
      syncButton();
    }
  });
  dzAudio.addEventListener("drop", (e) => {
    const f = e.dataTransfer.files?.[0];
    if (f && (f.type.startsWith("audio/") || /\.(wav|mp3|flac|m4a|ogg)$/i.test(f.name))) {
      audioFile = f;
      syncButton();
    }
  });

  btnClear.addEventListener("click", () => {
    photoFile = null;
    audioFile = null;
    inputPhoto.value = "";
    inputAudio.value = "";
    syncButton();
    setError("");
    resultsBody.hidden = true;
    if (outPhotoEmoji) outPhotoEmoji.textContent = "";
    if (outAudioEmoji) outAudioEmoji.textContent = "";
    if (outFinalEmoji) outFinalEmoji.textContent = "";
    if (mainLayout) mainLayout.classList.remove("layout--has-results");
  });

  async function checkHealth() {
    try {
      const r = await fetch("/api/health");
      const j = await r.json();
      if (j.audio_model && j.audio_labels) {
        healthPill.dataset.state = "ok";
        healthText.textContent = "Backend ready";
      } else {
        healthPill.dataset.state = "bad";
        healthText.textContent = "Missing model files (train notebook first)";
      }
    } catch {
      healthPill.dataset.state = "bad";
      healthText.textContent = "Backend unreachable";
    }
  }

  btnAnalyze.addEventListener("click", async () => {
    setError("");
    if (!photoFile && !audioFile) return;

    const fd = new FormData();
    if (photoFile) fd.append("photo", photoFile, photoFile.name);
    if (audioFile) fd.append("audio", audioFile, audioFile.name);

    loadingOverlay.hidden = false;
    const cfg = window.EMO_DASHBOARD_CONFIG;
    let msg = "Running…";
    if (photoFile && audioFile) {
      msg = (cfg && cfg.loadingMessage) || "Running face + audio models…";
    } else if (photoFile) {
      msg = (cfg && cfg.loadingMessageImage) || "Running face model…";
    } else {
      msg = (cfg && cfg.loadingMessageAudio) || "Running audio model…";
    }
    if (loadingMessageEl) loadingMessageEl.textContent = msg;
    try {
      const res = await fetch("/api/analyze", { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const d = data.detail;
        let msg = res.statusText || "Request failed";
        if (typeof d === "string") msg = d;
        else if (Array.isArray(d) && d[0]?.msg) msg = d.map((x) => x.msg).join("; ");
        else if (data.message) msg = data.message;
        throw new Error(msg);
      }

      const photo = data.photo_emotion || "—";
      const audio = data.audio_emotion || "—";
      outPhoto.textContent = photo;
      outAudio.textContent = audio;
      if (outPhotoEmoji) {
        outPhotoEmoji.textContent = photo !== "—" ? emotionEmoji(photo) : "";
      }
      if (outAudioEmoji) {
        outAudioEmoji.textContent = audio !== "—" ? emotionEmoji(audio) : "";
      }
      const fused = data.final_emotion || "—";
      outFinal.textContent = fused;
      if (outFinalEmoji) {
        outFinalEmoji.textContent = fused !== "—" ? emotionEmoji(fused) : "";
      }
      outRegulation.textContent = data.regulation || "";

      if (data.photo_scores && typeof data.photo_scores === "object") {
        outScores.hidden = false;
        scoreList.innerHTML = "";
        const entries = Object.entries(data.photo_scores).sort((a, b) => b[1] - a[1]);
        for (const [k, v] of entries) {
          const li = document.createElement("li");
          const num = Number(v);
          const pct = num <= 1 ? num * 100 : num;
          li.innerHTML = `<span>${k}</span><span>${pct.toFixed(1)}%</span>`;
          scoreList.appendChild(li);
        }
      } else {
        outScores.hidden = true;
      }

      resultsBody.hidden = false;
      if (mainLayout) mainLayout.classList.add("layout--has-results");
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      loadingOverlay.hidden = true;
    }
  });

  syncButton();
  if (loadingOverlay) {
    loadingOverlay.hidden = true;
  }
  checkHealth();
})();
