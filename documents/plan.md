# Create Subtitle - Project Plan

## Overview

A Python desktop application with a simple GUI that:
1. Extracts audio from video files and generates subtitles (text) via speech-to-text.
2. Converts plain-text subtitles into standard subtitle formats (.srt, .ass, .ssa).

---

## Features

### Feature 1: Video → Subtitle Text
- **Input:** Video file (`.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`)
- **Process:**
  1. Extract audio from the video using `ffmpeg` (via `pydub` or direct subprocess call).
  2. Save the extracted audio as a temporary `.wav` file.
  3. Run speech-to-text on the audio using `faster-whisper` (CTranslate2-based, lightweight, offline).
  4. Faster-whisper returns timestamped segments (start, end, text).
  5. Primary language: **Japanese** (configurable, but defaulting to `ja`).
- **Output:** A `.txt` file containing the transcribed subtitle text with timestamps.

### Feature 2: Text → Subtitle File
- **Input:** A plain-text subtitle file (the `.txt` from Feature 1, or user-provided).
- **Process:**
  1. Parse the text file (expected format: one line per segment with timestamp + text).
  2. Convert parsed data into the chosen subtitle format.
- **Output:** Subtitle file in one of these formats:
  - `.srt` (SubRip — most common)
  - `.ass` (Advanced SubStation Alpha)
  - `.ssa` (SubStation Alpha)

---

## Tech Stack

| Component           | Library / Tool                        |
|----------------------|---------------------------------------|
| GUI                 | `tkinter` (built-in, simple, no extra install) |
| Audio extraction    | `pydub` + `ffmpeg` (system dependency) |
| Speech-to-text      | `faster-whisper` (CTranslate2-based, lightweight, offline) |
| Subtitle formatting | Custom Python module (no extra lib needed) |
| File dialogs        | `tkinter.filedialog`                  |

---

## Project Structure

```
create_subtitle/
├── main.py                  # Entry point — launches the GUI
├── gui/
│   ├── __init__.py
│   └── app.py               # Tkinter GUI layout and event handlers
├── core/
│   ├── __init__.py
│   ├── audio_extractor.py   # Video → Audio extraction (pydub/ffmpeg)
│   ├── transcriber.py       # Audio → Text transcription (faster-whisper)
│   └── subtitle_converter.py # Text → .srt / .ass / .ssa conversion
├── utils/
│   ├── __init__.py
│   └── file_helpers.py      # File I/O, temp file management, validation
├── documents/
│   └── plan.md              # This file
├── requirements.txt         # Python dependencies
└── README.md                # Usage instructions
```

---

## GUI Layout (Tkinter)

Simple tabbed or sectioned window:

### Tab 1: Video → Subtitle
- **[Browse]** button to select a video file.
- Display selected file path.
- Dropdown to select Whisper model size (`tiny`, `base`, `small`, `medium`, `large`).
- Language selector (default: Japanese `ja`; can switch to English, etc.).
- **[Generate Subtitle]** button to start processing.
- Progress indicator (label or progress bar).
- **[Save]** button to export the `.txt` result.

### Tab 2: Text → Subtitle File
- **[Browse]** button to select a `.txt` subtitle file.
- Display file preview (first few lines).
- Radio buttons to choose output format: `.srt` / `.ass` / `.ssa`.
- **[Convert]** button.
- **[Save As]** button to export the subtitle file.

---

## Processing Pipeline

### Pipeline 1: Video → Subtitle Text

```
Video File (.mp4/.mkv/...)
        │
        ▼
  [Extract Audio]  ──► Temporary .wav file
        │
        ▼
  [Whisper STT]    ──► List of segments: [{start, end, text}, ...]
        │
        ▼
  [Format as Text] ──► Plain text with timestamps
        │
        ▼
  Save .txt file
```

### Pipeline 2: Text → Subtitle File

```
Text File (.txt)
        │
        ▼
  [Parse Segments]  ──► List of segments: [{start, end, text}, ...]
        │
        ▼
  [Convert Format]  ──► .srt / .ass / .ssa content string
        │
        ▼
  Save subtitle file
```

---

## Text File Format (Intermediate)

Each line follows this pattern:

```
[HH:MM:SS.mmm --> HH:MM:SS.mmm] Subtitle text here
```

Example:
```
[00:00:01.200 --> 00:00:04.500] Hello and welcome to this video.
[00:00:05.000 --> 00:00:08.300] Today we will talk about Python.
```

---

## Implementation Steps

### Phase 1: Core Logic
1. **Audio extraction** — Write `audio_extractor.py`: accept video path, return audio `.wav` path.
2. **Transcription** — Write `transcriber.py`: accept audio path, return list of timed segments.
3. **Subtitle conversion** — Write `subtitle_converter.py`: accept segments, return `.srt`/`.ass`/`.ssa` string.
4. **File helpers** — Write `file_helpers.py`: read/write text files, validate paths, manage temp files.

### Phase 2: GUI
5. **Build GUI** — Write `app.py` with two tabs using `tkinter.ttk.Notebook`.
6. **Wire up** — Connect GUI buttons to core functions.
7. **Threading** — Run long tasks (extraction, transcription) in background threads to keep GUI responsive.

### Phase 3: Polish
8. **Error handling** — Friendly error messages for missing ffmpeg, bad files, etc.
9. **Progress feedback** — Show progress/status during transcription.
10. **Testing** — Test with various video formats and lengths.

---

## Dependencies

```
faster-whisper
pydub
```

**Why `faster-whisper` over `openai-whisper`:**
- No PyTorch dependency (~150 MB–2 GB saved).
- Uses CTranslate2 — up to 4x faster, lower RAM usage.
- Same Whisper models, same accuracy, same Japanese support.
- Total install ~200 MB with `base` model vs 500 MB+ with standard Whisper.

System requirement: **ffmpeg** must be installed and available in PATH.

---

## Notes

- Faster-whisper runs locally — no API key or internet required (after model download).
- Model sizes trade speed for accuracy: `tiny` is fast but less accurate, `large` is slow but most accurate.
- For Japanese, `base` or `small` is recommended as a good speed/accuracy balance. (I choose `small`)
- Default language is set to Japanese (`ja`) but user can change it in the GUI.
- The app should handle errors gracefully (e.g., missing ffmpeg, unsupported file, corrupted audio).
- Threading is essential so the GUI doesn't freeze during transcription.
