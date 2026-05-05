from faster_whisper import WhisperModel


AVAILABLE_MODELS = ["tiny", "base", "small", "medium"]

LANGUAGE_OPTIONS = {
    "Japanese": "ja",
    "English": "en",
    "Chinese": "zh",
    "Korean": "ko",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Auto-detect": None,
}


def transcribe_audio(
    audio_path: str,
    model_size: str = "small",
    language: str = "ja",
    progress_callback=None,
) -> list[dict]:
    """
    Transcribe audio using faster-whisper.
    Returns a list of dicts: [{start, end, text}, ...]
    """
    if progress_callback:
        progress_callback(f"Loading Whisper model ({model_size})... This may take a moment on first run.")

    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    if progress_callback:
        progress_callback("Transcribing audio... Please wait.")

    segments_gen, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,
    )

    if progress_callback:
        progress_callback(f"Detected language: {info.language} (probability {info.language_probability:.2f})")

    segments = []
    for seg in segments_gen:
        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        if progress_callback:
            progress_callback(f"Transcribed: {seg.start:.1f}s - {seg.end:.1f}s")

    if progress_callback:
        progress_callback(f"Transcription complete. {len(segments)} segments found.")

    return segments
