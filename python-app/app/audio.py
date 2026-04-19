import subprocess
from uuid import uuid4

from config import TMP_OUTPUT_DIR
from models import AudioPIISpan

FFMPEG_BIN = "ffmpeg"


def normalize_audio(input_path: str) -> str:
    TMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TMP_OUTPUT_DIR / f"normalized_{uuid4().hex}.wav"

    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i",
        input_path,
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)

    return str(output_path)


def mute_segments(input_path: str, spans: list[AudioPIISpan]) -> str:
    TMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TMP_OUTPUT_DIR / f"redacted_{uuid4().hex}.wav"

    if not spans:
        cmd = [FFMPEG_BIN, "-y", "-i", input_path, str(output_path)]
        subprocess.run(cmd, check=True)
        return str(output_path)

    filters = []
    for span in spans:
        filters.append(
            f"volume=enable='between(t,{span.start_time:.3f},{span.end_time:.3f})':volume=0"
        )

    filter_chain = ",".join(filters)

    cmd = [
        FFMPEG_BIN,
        "-y",
        "-i",
        input_path,
        "-af",
        filter_chain,
        str(output_path),
    ]
    subprocess.run(cmd, check=True)

    return str(output_path)
