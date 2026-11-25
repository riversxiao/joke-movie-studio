# Joke Movie Studio

AI-acted English comedy Shorts (**YouTube Shorts / TikTok / Reels**, native `9:16`) production studio — designed to replicate and surpass viral AI stand-up & street-interview comedy channels (e.g., `@based-xlily`) with **multi-camera cinematography, expressive comedic timing, consistent recurring cast, original audience reaction cutaways, and kinetic Shorts captions**.

---

## Repository Structure

```text
joke-movie-studio/
├── AGENTS.md                        # Direct handoff instructions for AI coding/media agents
├── README.md                        # Project overview & quickstart
├── docs/
│   └── MASTER_PLAN.md               # Competitor teardown, 3 comedy formats, Colab G4 (Drama 3 + H3) architecture
└── episodes/
    └── ep001_taxes/                 # Pilot episode: "How to Teach Kids About Taxes 💀" (24s, 4 shots)
        ├── ep001_script.json        # Structured 4-shot storyboard, cast/set bible, Gemini & H3 prompts
        ├── run_gemini_pilot.sh      # One-click resume-safe gemini-api CLI pipeline (image -> video -> transcribe -> edit)
        ├── post_edit.py             # FFmpeg 1080x1920 stitcher + kinetic ASS subtitles + -14 LUFS loudness
        ├── audio/                   # Pre-generated expressive stand-up audition WAVs (gemini-3.8-flash-tts)
        └── subs/                    # Pre-generated segment timestamp JSONs (gemini-3.5-transcribe)
```

---

## Quickstart 1: Run EP001 via `gemini-api` CLI (Recommended for Fast Pilot)

Requires [google-gemini/gemini-api-cli](https://github.com/google-gemini/gemini-api-cli) (`v0.5.0+`), `ffmpeg`, `jq`, `python3`, and a **Paid Tier** `GEMINI_API_KEY` (Google AI Ultra subscribers can claim free monthly \$40–\$100 API credits directly inside Google AI Studio).

```bash
# 1. Install gemini-api CLI (Linux / macOS)
curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.sh | bash
export PATH="$HOME/.local/bin:$PATH"

# 2. Set your Paid Tier Gemini API key
export GEMINI_API_KEY="YOUR_PAID_GEMINI_API_KEY"
gemini-api whoami

# 3. Run the full 4-shot EP001 pilot (~$1.70 total at 720p, resume-safe)
cd episodes/ep001_taxes
./run_gemini_pilot.sh 720p

# Optional: once happy with timing/acting, re-render or upscale to 1080p
# ./run_gemini_pilot.sh 1080p
```

Output lands at:
`episodes/ep001_taxes/output/EP001_how_to_teach_kids_about_taxes_9x16.mp4`

---

## Quickstart 2: Assemble Clips Generated in Google Flow / AI Studio Web / Colab G4

If you generated the 4 shot clips in **Google Flow** (using Ultra credits), **AI Studio Web**, or **Colab G4 (Fish Audio Drama 3 + MiniMax H3-Image + MiniMax H3 Ref2VA `fully_copy`)**, place them at:
- `episodes/ep001_taxes/clips/s01_setup.mp4`
- `episodes/ep001_taxes/clips/s02_punchline.mp4`
- `episodes/ep001_taxes/clips/s03_audience.mp4`
- `episodes/ep001_taxes/clips/s04_closer.mp4`

Then run `run_gemini_pilot.sh` (it automatically skips existing keyframes/clips and runs `gemini-3.5-transcribe` + `post_edit.py`), or call `post_edit.py` directly:

```bash
python3 episodes/ep001_taxes/post_edit.py \
  --project-dir episodes/ep001_taxes \
  --clips episodes/ep001_taxes/clips/s01_setup.mp4 \
          episodes/ep001_taxes/clips/s02_punchline.mp4 \
          episodes/ep001_taxes/clips/s03_audience.mp4 \
          episodes/ep001_taxes/clips/s04_closer.mp4 \
  --subs-json episodes/ep001_taxes/subs/s01_setup.json \
              episodes/ep001_taxes/subs/s02_punchline.json \
              "" \
              episodes/ep001_taxes/subs/s04_closer.json \
  --out episodes/ep001_taxes/output/EP001_how_to_teach_kids_about_taxes_9x16.mp4
```

---

## Single-shot Talk Show: bilingual karaoke finishing

For an existing portrait clip with its original voice track, use the [bilingual karaoke post-production kit](tools/talkshow_karaoke/README.md). It adds large English and Simplified Chinese subtitles, word-synced gold highlighting, and a reusable comment cue after the reveal. It renders locally and does not call a video generator or touch EP001.

---

## Long-Term Production Architecture (Colab G4 96GB)

See [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) for the full scaled production plan combining:
- **Colab G4** (`1× NVIDIA RTX PRO 6000 Blackwell`, 96 GB VRAM)
- **Fish Audio Drama 3** (FP8 MoE, 37 GB VRAM — directable multi-speaker comedic voice acting)
- **MiniMax H3-Image** (up to 16 reference images for locked character & set continuity)
- **MiniMax H3 (`Ref2VA fully_copy` + `FL2VA`)** (exact lip-sync driven by Drama 3 stems + shared `Qwen3-VL-32B` encoder)
