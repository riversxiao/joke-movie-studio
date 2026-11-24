#!/usr/bin/env bash
# End-to-end, resume-safe Joke Movie EP001 builder using google-gemini/gemini-api-cli (v0.5.0+).
# Requires a Paid Tier GEMINI_API_KEY (for gemini-nano-banana-2.1 and gemini-omni-1.2-flash).
set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ="$SCRIPT_DIR"
RES="${1:-720p}"   # Pass "1080p" after approving 720p draft (~$1.70 total at 720p)

for bin in gemini-api ffmpeg ffprobe jq python3; do
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "ERROR: required command '$bin' not found on PATH." >&2
    exit 1
  fi
done

mkdir -p "$PROJ"/{keyframes,clips,subs,output}

echo "=== STEP 1: Generate 9:16 Keyframes with gemini-nano-banana-2.1 ==="
if [[ ! -f "$PROJ/keyframes/s01_stage_main.jpg" ]]; then
  gemini-api image \
    --aspect-ratio 9:16 --image-size 2K \
    --out "$PROJ/keyframes/s01_stage_main.jpg" \
    "$(jq -r '.shots[0].keyframe_prompt' "$PROJ/ep001_script.json")"
else
  echo "[skip] keyframes/s01_stage_main.jpg already exists"
fi

if [[ ! -f "$PROJ/keyframes/s02_stage_closeup.jpg" ]]; then
  gemini-api image \
    --aspect-ratio 9:16 --image-size 2K \
    -i "$PROJ/keyframes/s01_stage_main.jpg" \
    --out "$PROJ/keyframes/s02_stage_closeup.jpg" \
    "$(jq -r '.shots[1].keyframe_prompt' "$PROJ/ep001_script.json")"
else
  echo "[skip] keyframes/s02_stage_closeup.jpg already exists"
fi

if [[ ! -f "$PROJ/keyframes/s03_audience_reaction.jpg" ]]; then
  gemini-api image \
    --aspect-ratio 9:16 --image-size 2K \
    -i "$PROJ/keyframes/s01_stage_main.jpg" \
    --out "$PROJ/keyframes/s03_audience_reaction.jpg" \
    "$(jq -r '.shots[2].keyframe_prompt' "$PROJ/ep001_script.json")"
else
  echo "[skip] keyframes/s03_audience_reaction.jpg already exists"
fi

echo "=== STEP 2: Generate 4 Native Audio-Video Clips with gemini-omni-1.2-flash ($RES) ==="
if [[ ! -f "$PROJ/clips/s01_setup.mp4" ]]; then
  gemini-api video \
    -i "$PROJ/keyframes/s01_stage_main.jpg" \
    --body "{\"response_format\":{\"type\":\"video\",\"aspect_ratio\":\"9:16\",\"resolution\":\"$RES\",\"duration\":\"10s\"}}" \
    --out "$PROJ/clips/s01_setup.mp4" \
    "$(jq -r '.shots[0].video_prompt_gemini' "$PROJ/ep001_script.json")"
else
  echo "[skip] clips/s01_setup.mp4 already exists"
fi

if [[ ! -f "$PROJ/clips/s02_punchline.mp4" ]]; then
  gemini-api video \
    -i "$PROJ/keyframes/s02_stage_closeup.jpg" \
    -i "$PROJ/keyframes/s01_stage_main.jpg" \
    --body "{\"response_format\":{\"type\":\"video\",\"aspect_ratio\":\"9:16\",\"resolution\":\"$RES\",\"duration\":\"8s\"}}" \
    --out "$PROJ/clips/s02_punchline.mp4" \
    "$(jq -r '.shots[1].video_prompt_gemini' "$PROJ/ep001_script.json")"
else
  echo "[skip] clips/s02_punchline.mp4 already exists"
fi

if [[ ! -f "$PROJ/clips/s03_audience.mp4" ]]; then
  gemini-api video \
    -i "$PROJ/keyframes/s03_audience_reaction.jpg" \
    --body "{\"response_format\":{\"type\":\"video\",\"aspect_ratio\":\"9:16\",\"resolution\":\"$RES\",\"duration\":\"3s\"}}" \
    --out "$PROJ/clips/s03_audience.mp4" \
    "$(jq -r '.shots[2].video_prompt_gemini' "$PROJ/ep001_script.json")"
else
  echo "[skip] clips/s03_audience.mp4 already exists"
fi

if [[ ! -f "$PROJ/clips/s04_closer.mp4" ]]; then
  gemini-api video \
    -i "$PROJ/keyframes/s02_stage_closeup.jpg" \
    -i "$PROJ/keyframes/s01_stage_main.jpg" \
    --body "{\"response_format\":{\"type\":\"video\",\"aspect_ratio\":\"9:16\",\"resolution\":\"$RES\",\"duration\":\"3s\"}}" \
    --out "$PROJ/clips/s04_closer.mp4" \
    "$(jq -r '.shots[3].video_prompt_gemini' "$PROJ/ep001_script.json")"
else
  echo "[skip] clips/s04_closer.mp4 already exists"
fi

echo "=== STEP 3: Extract Timestamps via gemini-3.5-transcribe ==="
for name in s01_setup s02_punchline s04_closer; do
  if [[ ! -f "$PROJ/subs/${name}.json" ]]; then
    ffmpeg -y -v error -i "$PROJ/clips/${name}.mp4" -vn -ac 1 -ar 24000 "$PROJ/subs/${name}.wav"
    gemini-api transcribe -m gemini-3.5-transcribe \
      -i "$PROJ/subs/${name}.wav" --format json --no-speakers \
      --out "$PROJ/subs/${name}.json"
  else
    echo "[skip] subs/${name}.json already exists"
  fi
done

echo "=== STEP 4: Stitch + Burn Kinetic Shorts Captions + -14 LUFS ==="
python3 "$PROJ/post_edit.py" \
  --project-dir "$PROJ" \
  --clips "$PROJ/clips/s01_setup.mp4" "$PROJ/clips/s02_punchline.mp4" "$PROJ/clips/s03_audience.mp4" "$PROJ/clips/s04_closer.mp4" \
  --subs-json "$PROJ/subs/s01_setup.json" "$PROJ/subs/s02_punchline.json" "" "$PROJ/subs/s04_closer.json" \
  --out "$PROJ/output/EP001_how_to_teach_kids_about_taxes_9x16.mp4"
