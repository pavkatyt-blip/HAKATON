import re
from dataclasses import dataclass


SNILS_DIRECT_PATTERN = re.compile(
    r"\b\d{3}[- ]?\d{3}[- ]?\d{3}[- ]?\d{2}\b"
)

SNILS_CONTEXT_PATTERN = re.compile(
    r"(?:снилс|снил)\s+(.+?)(?:$|[.!?])",
    re.IGNORECASE,
)


@dataclass
class SnilsCandidate:
    raw: str
    start_char: int
    end_char: int


def extract_snils_candidates(text: str) -> list[SnilsCandidate]:
    candidates: list[SnilsCandidate] = []

    for match in SNILS_DIRECT_PATTERN.finditer(text):
        candidates.append(
            SnilsCandidate(
                raw=match.group().strip(),
                start_char=match.start(),
                end_char=match.end(),
            )
        )

    for match in SNILS_CONTEXT_PATTERN.finditer(text):
        raw = match.group(1).strip()
        candidates.append(
            SnilsCandidate(
                raw=raw,
                start_char=match.start(1),
                end_char=match.end(1),
            )
        )

    return dedupe_snils_candidates(candidates)


def dedupe_snils_candidates(candidates: list[SnilsCandidate]) -> list[SnilsCandidate]:
    result: list[SnilsCandidate] = []
    seen = set()

    for c in candidates:
        key = (c.start_char, c.end_char, c.raw)
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result


def normalize_snils_candidate(raw: str) -> str | None:
    digits = re.findall(r"\d+", raw)
    if not digits:
        return None

    joined = "".join(digits)

    if len(joined) == 11:
        return joined

    if len(joined) > 11:
        return joined[:11]

    return None


def is_valid_snils(value: str) -> bool:
    return bool(re.fullmatch(r"\d{11}", value))
