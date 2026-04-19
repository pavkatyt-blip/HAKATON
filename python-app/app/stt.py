import whisper

from config import MODEL_NAME
from models import WordToken

_model = None


def get_model():
    global _model
    if _model is None:
        # для CPU лучше small или base
        name = MODEL_NAME if MODEL_NAME in {"tiny", "base", "small", "medium", "large"} else "small"
        _model = whisper.load_model(name)
    return _model


def transcribe_audio(audio_path: str, language: str = "ru") -> dict:
    model = get_model()

    result = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
        verbose=False,
    )

    transcript, words = flatten_words(result["segments"])

    return {
        "transcript": transcript,
        "words": words,
    }


def flatten_words(segments) -> tuple[str, list[WordToken]]:
    transcript_parts = []
    words_out: list[WordToken] = []
    cursor = 0

    for segment in segments:
        for word_info in segment.get("words", []):
            word = (word_info.get("word") or "").strip()
            start = word_info.get("start")
            end = word_info.get("end")

            if not word or start is None or end is None:
                continue

            if transcript_parts:
                transcript_parts.append(" ")
                cursor += 1

            idx_start = cursor
            transcript_parts.append(word)
            cursor += len(word)
            idx_end = cursor

            words_out.append(
                WordToken(
                    word=word,
                    start=float(start),
                    end=float(end),
                    idx_start=idx_start,
                    idx_end=idx_end,
                )
            )

    transcript = "".join(transcript_parts)
    return transcript, words_out
