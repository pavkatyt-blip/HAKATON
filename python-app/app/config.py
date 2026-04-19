from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_INPUT_DIR = BASE_DIR / "tmp" / "input"
TMP_OUTPUT_DIR = BASE_DIR / "tmp" / "output"

DEFAULT_LANGUAGE = "ru"
DEFAULT_REDACTION_MODE = "mute"

DEVICE = "cpu"
MODEL_NAME = "small"
