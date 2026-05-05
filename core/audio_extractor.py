import subprocess
import shutil

from utils.file_helpers import get_temp_wav_path, validate_video_file


def check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def extract_audio(video_path: str, progress_callback=None) -> str:
    """
    Extract audio from a video file and save it as a temporary WAV file.
    Returns the path to the WAV file.
    Raises RuntimeError if ffmpeg is missing or extraction fails.
    """
    if not check_ffmpeg():
        raise RuntimeError(
            "ffmpeg is not installed or not found in PATH.\n"
            "Please install ffmpeg and make sure it is accessible from the command line."
        )

    if not validate_video_file(video_path):
        raise ValueError(
            f"Invalid or unsupported video file: {video_path}\n"
            "Supported formats: .mp4, .mkv, .avi, .mov, .webm"
        )

    wav_path = get_temp_wav_path()

    if progress_callback:
        progress_callback("Extracting audio from video...")

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        wav_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed with exit code {result.returncode}:\n"
                f"{result.stderr.decode(errors='replace')}"
            )
    except FileNotFoundError:
        raise RuntimeError("ffmpeg executable not found. Please install ffmpeg.")

    if progress_callback:
        progress_callback("Audio extraction complete.")

    return wav_path
