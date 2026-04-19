from audio import mute_segments, normalize_audio
from models import AudioPIISpan, WordToken, TextPIISpan
from pii import detect_pii
from stt import transcribe_audio


TYPE_MAP = {
    "PHONE_NUMBER": "PHONE",
    "EMAIL_ADDRESS": "EMAIL",
    "EMAIL_CANDIDATE": "EMAIL",
    "PERSON": "PERSON",
    "PERSON_CANDIDATE": "PERSON",
    "ADDRESS": "ADDRESS",
    "ADDRESS_CANDIDATE": "ADDRESS",
    "PASSPORT_RF": "PASSPORT",
    "PASSPORT_CANDIDATE": "PASSPORT",
    "INN": "INN",
    "INN_CANDIDATE": "INN",
    "SNILS": "SNILS",
    "SNILS_CANDIDATE": "SNILS",
}

REPLACEMENT_MAP = {
    "PHONE": "[PHONE]",
    "EMAIL": "[EMAIL]",
    "PERSON": "[PERSON]",
    "ADDRESS": "[ADDRESS]",
    "PASSPORT": "[PASSPORT]",
    "INN": "[INN]",
    "SNILS": "[SNILS]",
}


def canonical_type(entity_type: str) -> str:
    return TYPE_MAP.get(entity_type, entity_type)


def replacement_for(entity_type: str) -> str:
    return REPLACEMENT_MAP.get(canonical_type(entity_type), "[REDACTED]")


def map_text_span_to_audio(words: list[WordToken], start_char: int, end_char: int):
    matched = []

    for word in words:
        intersects = not (word.idx_end <= start_char or word.idx_start >= end_char)
        if intersects:
            matched.append(word)

    if not matched:
        return None, []

    return (matched[0].start, matched[-1].end), matched


def merge_audio_spans(spans: list[AudioPIISpan], gap: float = 0.15) -> list[AudioPIISpan]:
    if not spans:
        return []

    spans = sorted(spans, key=lambda s: s.start_time)
    merged = [spans[0]]

    for span in spans[1:]:
        last = merged[-1]

        if span.start_time <= last.end_time + gap:
            merged[-1] = AudioPIISpan(
                entity_type=f"{last.entity_type}|{span.entity_type}",
                text=f"{last.text} {span.text}",
                start_time=last.start_time,
                end_time=max(last.end_time, span.end_time),
                score=max(last.score, span.score),
            )
        else:
            merged.append(span)

    return merged


def build_redacted_text(transcript: str, text_spans: list[TextPIISpan]) -> str:
    if not text_spans:
        return transcript

    spans = sorted(text_spans, key=lambda s: (s.start_char, s.end_char))
    result_parts = []
    cursor = 0

    for span in spans:
        if span.start_char < cursor:
            continue

        result_parts.append(transcript[cursor:span.start_char])
        result_parts.append(replacement_for(span.entity_type))
        cursor = span.end_char

    result_parts.append(transcript[cursor:])
    return "".join(result_parts)


def process_audio(input_path: str, request_id: str, language_hint: str = "ru") -> dict:
    normalized_path = normalize_audio(input_path)

    stt_result = transcribe_audio(normalized_path, language_hint)
    transcript = stt_result["transcript"]
    words = stt_result["words"]

    text_spans = detect_pii(transcript, debug=True)
    redacted_text = build_redacted_text(transcript, text_spans)

    print("\nTRANSCRIPT:")
    print(transcript)
    print("\nREDACTED TEXT:")
    print(redacted_text)
    print("\nTEXT SPANS:")
    for span in text_spans:
        print(span)

    raw_audio_spans: list[AudioPIISpan] = []
    response_pii_spans: list[dict] = []

    for span in text_spans:
        mapped, matched_words = map_text_span_to_audio(words, span.start_char, span.end_char)
        if not mapped:
            continue

        start_time, end_time = mapped

        print(f"\nSPAN: {span.text}")
        print(f"AUDIO: {start_time:.3f} -> {end_time:.3f}")
        print("WORDS:")
        for w in matched_words:
            print(f"  {w.word} [{w.start:.3f} - {w.end:.3f}]")

        audio_span = AudioPIISpan(
            entity_type=span.entity_type,
            text=span.text,
            start_time=max(0.0, start_time - 0.05),
            end_time=end_time + 0.05,
            score=span.score,
        )
        raw_audio_spans.append(audio_span)

        response_pii_spans.append(
            {
                "type": canonical_type(span.entity_type),
                "start_time": round(max(0.0, start_time - 0.05), 3),
                "end_time": round(end_time + 0.05, 3),
                "text": span.text,
                "replacement": replacement_for(span.entity_type),
            }
        )

    print("\nRAW AUDIO SPANS:")
    for span in raw_audio_spans:
        print(span)

    audio_spans_for_redaction = merge_audio_spans(raw_audio_spans)

    print("\nMERGED AUDIO SPANS:")
    for span in audio_spans_for_redaction:
        print(span)

    output_path = mute_segments(normalized_path, audio_spans_for_redaction)

    return {
        "request_id": request_id,
        "transcript": transcript,
        "redacted_text": redacted_text,
        "pii_spans": response_pii_spans,
        "output_path": output_path,
    }
