import os
import re
import tempfile
from pathlib import Path

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
SUPPORTED_SUBTITLE_EXTENSIONS = {".srt", ".ass", ".ssa"}
TIMESTAMP_PATTERN = re.compile(
    r"\[(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})\]\s*(.*)"
)


def validate_video_file(path: str) -> bool:
    p = Path(path)
    return p.is_file() and p.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS


def validate_text_file(path: str) -> bool:
    p = Path(path)
    return p.is_file() and p.suffix.lower() == ".txt"


def get_temp_wav_path() -> str:
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    return path


def cleanup_temp_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def parse_timestamp(ts: str) -> float:
    """Parse HH:MM:SS.mmm into seconds."""
    parts = ts.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    sec_parts = parts[2].split(".")
    seconds = int(sec_parts[0])
    millis = int(sec_parts[1]) if len(sec_parts) > 1 else 0
    return hours * 3600 + minutes * 60 + seconds + millis / 1000.0


def segments_to_text(segments: list[dict]) -> str:
    """Convert list of {start, end, text} dicts to the intermediate text format."""
    lines = []
    for seg in segments:
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        lines.append(f"[{start} --> {end}] {seg['text']}")
    return "\n".join(lines)


def parse_text_to_segments(text: str) -> list[dict]:
    """Parse the intermediate text format back into segment dicts."""
    segments = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        match = TIMESTAMP_PATTERN.match(line)
        if match:
            start_ts, end_ts, content = match.groups()
            segments.append({
                "start": parse_timestamp(start_ts),
                "end": parse_timestamp(end_ts),
                "text": content.strip(),
            })
    return segments


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
