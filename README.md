# Create Subtitle

A Python desktop app that generates subtitles from video files using offline speech-to-text (faster-whisper). It can also convert plain-text subtitles into `.srt`, `.ass`, or `.ssa` formats.

Default language is Japanese, but other languages are supported.

## Requirements

- Python 3.10+
- [ffmpeg](https://www.gyan.dev/ffmpeg/builds/) installed and available in PATH

## Run from Source

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

## Executable (.exe)

### Where is it?

After building, the exe is located at:

```
dist/CreateSubtitle/CreateSubtitle.exe
```

### How to build

Double-click `build.bat`, or run it in a terminal (requires venv with dependencies installed):

```bash
.\build.bat
```

### How to share

Zip the **entire** `dist/CreateSubtitle/` folder and send it. The folder contains the exe and all its required files — they must stay together.

### Notes

- **ffmpeg** is still required on the target machine.
- Whisper models are **not** bundled in the exe — they download automatically on first use (~480 MB for the default `small` model) and are cached locally after that.
- The exe uses `--windowed` mode, so no console window appears.
