# Agent Handoff Guide (`AGENTS.md`)

You are taking over **Joke Movie Studio** to produce the pilot 9:16 AI stand-up comedy Short **EP001 (`episodes/ep001_taxes/`)** inspired by and upgrading `https://www.youtube.com/shorts/u7xgfuToF7I`.

## 1. Prerequisites Check

Before running generation, verify:
1. `gemini-api` CLI (`v0.5.0+` from `https://github.com/google-gemini/gemini-api-cli`) is on `PATH`.
2. `ffmpeg`, `ffprobe`, `jq`, and `python3` are installed.
3. A **Paid Tier** `GEMINI_API_KEY` (or Vertex/AI Studio billing-enabled credential) is configured (`gemini-api whoami`).
   - Note: `gemini-nano-banana-2.1` (image) and `gemini-omni-1.2-flash` (video) require Paid Tier billing (`limit: 0` / `RESOURCE_EXHAUSTED` on Free Tier).
   - `gemini-3.8-flash-tts` and `gemini-3.5-transcribe` work on both Free and Paid tiers.

## 2. How to Run EP001 End-to-End

Execute:
```bash
cd episodes/ep001_taxes
./run_gemini_pilot.sh 720p
```

What `run_gemini_pilot.sh` does (and is **resume-safe** — existing files are skipped):
1. **Keyframes (`gemini-nano-banana-2.1`, `9:16`, `2K`)**:
   - `keyframes/s01_stage_main.jpg` (Chloe on wooden barstool, brick-wall Comedy Club, silhouetted audience heads)
   - `keyframes/s02_stage_closeup.jpg` (uses `s01_stage_main.jpg` as `-i` reference for exact identity/outfit/lighting match)
   - `keyframes/s03_audience_reaction.jpg` (uses `s01_stage_main.jpg` as lighting reference for original crowd laugh cutaway)
2. **Video + Native Audio (`gemini-omni-1.2-flash`, `9:16`, `720p`)**:
   - `clips/s01_setup.mp4` (`10s`, `-i keyframes/s01_stage_main.jpg`)
   - `clips/s02_punchline.mp4` (`8s`, `-i keyframes/s02_stage_closeup.jpg -i keyframes/s01_stage_main.jpg`)
   - `clips/s03_audience.mp4` (`3s`, `-i keyframes/s03_audience_reaction.jpg`)
   - `clips/s04_closer.mp4` (`3s`, `-i keyframes/s02_stage_closeup.jpg -i keyframes/s01_stage_main.jpg`)
3. **Transcription (`gemini-3.5-transcribe`)**:
   - Extracts mono 24 kHz WAV from `s01_setup.mp4`, `s02_punchline.mp4`, `s04_closer.mp4` and outputs `subs/*.json`.
4. **Post-Production (`post_edit.py`)**:
   - Scales/normalizes all 4 clips to `1080x1920 @ 24fps`, concatenates them, generates kinetic ASS captions (`subs/ep001_kinetic.ass`) highlighting punch words in bold yellow, applies `-14 LUFS` loudness normalization, and writes `output/EP001_how_to_teach_kids_about_taxes_9x16.mp4`.

## 3. Quality Acceptance Checks Before Delivering to User

After generating `output/EP001_how_to_teach_kids_about_taxes_9x16.mp4`:
1. Inspect keyframe images (`keyframes/*.jpg`) before spending video credits if iterating manually — verify Chloe's face, dusty-pink dress, wired mic, and `COMEDY CLUB` brick wall stay consistent across `s01` and `s02`.
2. Inspect each generated clip (`clips/*.mp4`) for clean lip-sync, zero garbled speech, and authentic laughter timing. If a single shot misses the comedic beat, delete ONLY that clip (or use `gemini-api video --previous-interaction-id <id>` to refine it) and re-run `./run_gemini_pilot.sh`.
3. Verify the final MP4 with `ffprobe` (1080×1920, 24fps, stereo audio, ~22–24s) and visually inspect 2–3 extracted frames to ensure subtitles sit cleanly in the upper-center safe zone without overlapping faces or YouTube Shorts UI edges.

## 4. Alternative: Pre-Generated Audio Stems (for MiniMax H3 / Colab G4)

`episodes/ep001_taxes/audio/` already includes expressive voice stems generated with `gemini-3.8-flash-tts`:
- `beat1_setup.wav` (11.24s)
- `beat2_punchline.wav` (8.88s)
- `beat3_closer.wav` (1.96s)
- `ep001_full_voice_audition.wav` (combined audition track)

These can be fed directly into **MiniMax H3 `Ref2VA` (`<Audio 1>: fully_copy`)** on Colab G4 (see `docs/MASTER_PLAN.md`) if bypassing Gemini video billing.
