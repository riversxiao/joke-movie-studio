#!/usr/bin/env python3
"""
Assemble 9:16 Joke Movie YouTube Short with:
  - Concatenated 1080x1920 24fps clips (with optional animated keyframe fallback)
  - Loudness normalization (-14 LUFS)
  - High-retention kinetic ASS subtitles (bold white + yellow punch-word highlight,
    matching and upgrading @based-xlily's u7xgfuToF7I top-center aesthetic, inside Shorts safe margins)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def fmt_ass_time(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def extract_chunks_from_transcribe_json(json_path: Path, offset_sec: float, chunk_size: int = 3):
    """Parse gemini-api transcribe --format json output into (chunk_text, start, end) tuples."""
    raw = json.loads(json_path.read_text(encoding="utf-8"))
    # Format A: {"segments": [{"start_time": "00:00.1", "end_time": "00:03.1", "content": "..."}]}
    if isinstance(raw, dict) and isinstance(raw.get("segments"), list):
        out = []
        for seg in raw["segments"]:
            content = str(seg.get("content", "")).strip()
            if not content:
                continue
            st = parse_ts(seg.get("start_time", seg.get("start", 0))) + offset_sec
            en = parse_ts(seg.get("end_time", seg.get("end", st))) + offset_sec
            dur = max(0.25, en - st)
            out.extend(fallback_chunk_timings(content, st, dur, chunk_size=chunk_size))
        return out

    # Format B: nested word-level objects
    words = []
    def walk(node):
        if isinstance(node, dict):
            if "word" in node and ("start_offset" in node or "start" in node or "start_time" in node):
                w = str(node["word"]).strip()
                s = node.get("start_offset", node.get("start", node.get("start_time", 0)))
                e = node.get("end_offset", node.get("end", node.get("end_time", 0)))
                words.append((w, parse_ts(s) + offset_sec, parse_ts(e) + offset_sec))
                return
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(raw)
    out = []
    for j in range(0, len(words), chunk_size):
        grp = words[j : j + chunk_size]
        out.append((" ".join(w[0] for w in grp), grp[0][1], grp[-1][2]))
    return out


def parse_ts(val) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s.endswith("s"):
        return float(s[:-1])
    if ":" in s:
        parts = s.replace(",", ".").split(":")
        parts = [float(p) for p in parts]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
    return float(s)


def fallback_chunk_timings(text: str, start_sec: float, duration_sec: float, chunk_size: int = 3):
    tokens = text.split()
    if not tokens:
        return []
    chunks = [" ".join(tokens[i : i + chunk_size]) for i in range(0, len(tokens), chunk_size)]
    per = duration_sec / len(chunks)
    out = []
    for idx, ch in enumerate(chunks):
        out.append((ch, start_sec + idx * per, start_sec + (idx + 1) * per))
    return out


def build_ass(events, hook_title: str, ass_path: Path, highlight_phrases):
    """Build 1080x1920 ASS file with kinetic Shorts captions + subtle top hook badge."""
    hl_upper = [p.upper() for p in highlight_phrases]
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,DejaVu Sans,58,&H0000EAFF,&H00FFFFFF,&H00000000,&H90000000,-1,0,0,0,96,100,1,0,1,7,3,8,70,70,210,1
Style: Caption,DejaVu Sans,90,&H00FFFFFF,&H0000EAFF,&H00000000,&H80000000,-1,0,0,0,92,100,1,0,1,9,4,8,70,70,380,1
Style: Punch,DejaVu Sans,98,&H0000EAFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,96,100,1,0,1,10,5,8,70,70,375,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    if hook_title:
        lines.append(
            f"Dialogue: 0,0:00:00.00,0:00:03.60,Hook,,0,0,0,,{{\\fad(120,250)}}{hook_title.upper()}\n"
        )

    for text, st, en in events:
        clean = re.sub(r"\s+", " ", text).strip().upper()
        if not clean:
            continue
        is_punch = any(h in clean for h in hl_upper)
        style = "Punch" if is_punch else "Caption"
        # Subtle pop-in scale animation matching viral stand-up Shorts feel
        anim = r"{\fscx86\fscy86\t(0,90,\fscx103\fscy103)\t(90,150,\fscx100\fscy100)}"
        lines.append(
            f"Dialogue: 1,{fmt_ass_time(st)},{fmt_ass_time(en)},{style},,0,0,0,,{anim}{clean}\n"
        )

    ass_path.write_text("".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True, help="Episode directory containing ep001_script.json")
    parser.add_argument("--clips", nargs="+", required=True, help="Ordered MP4 clip files")
    parser.add_argument("--subs-json", nargs="*", default=[], help="Optional transcribe JSON files matching clips")
    parser.add_argument("--out", required=True, help="Final output MP4 path")
    args = parser.parse_args()

    proj = Path(args.project_dir)
    script = json.loads((proj / "ep001_script.json").read_text(encoding="utf-8"))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = proj / "output" / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Normalize every clip to 1080x1920 @ 24fps, 48kHz stereo
    norm_clips = []
    durations = []
    for i, clip in enumerate(args.clips):
        cpath = Path(clip)
        norm = tmp_dir / f"norm_{i:02d}.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(cpath),
                "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=24,setsar=1",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-ar",
                "48000",
                "-ac",
                "2",
                "-b:a",
                "192k",
                str(norm),
            ]
        )
        norm_clips.append(norm)
        durations.append(probe_duration(norm))

    # 2. Concatenate normalized clips
    concat_list = tmp_dir / "concat.txt"
    concat_list.write_text("".join(f"file '{c.resolve()}'\n" for c in norm_clips), encoding="utf-8")
    merged = tmp_dir / "merged_raw.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(merged),
        ]
    )

    # 3. Build kinetic ASS subtitles
    events = []
    highlights = []
    offset = 0.0
    for idx, dur in enumerate(durations):
        shot = script["shots"][idx] if idx < len(script["shots"]) else {}
        highlights.extend(shot.get("highlight_words", []))
        sub_json = Path(args.subs_json[idx]) if idx < len(args.subs_json) and args.subs_json[idx] else None
        if sub_json and sub_json.exists():
            chunks = extract_chunks_from_transcribe_json(sub_json, offset, chunk_size=3)
            if chunks:
                events.extend(chunks)
            elif shot.get("dialogue"):
                events.extend(fallback_chunk_timings(shot["dialogue"], offset + 0.15, max(0.5, dur - 0.3)))
        elif shot.get("dialogue"):
            events.extend(fallback_chunk_timings(shot["dialogue"], offset + 0.15, max(0.5, dur - 0.3)))
        offset += dur

    ass_path = proj / "subs" / "ep001_kinetic.ass"
    ass_path.parent.mkdir(parents=True, exist_ok=True)
    build_ass(events, script.get("title", "").replace("💀", "").strip(), ass_path, highlights)

    # 4. Burn captions + loudness normalize (-14 LUFS) + slight film polish
    ass_escaped = str(ass_path.resolve()).replace("\\", "/").replace(":", "\\:")
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(merged),
            "-vf",
            f"ass='{ass_escaped}'",
            "-af",
            "loudnorm=I=-14:TP=-1.5:LRA=11",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(out_path),
        ]
    )
    print(f"\nDONE: {out_path} ({probe_duration(out_path):.2f}s)")


if __name__ == "__main__":
    main()
