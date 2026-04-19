import re
from dataclasses import dataclass


PERSON_CONTEXT_PATTERNS = [
    re.compile(r"(?:меня зовут|моё имя|мое имя)\s+([А-ЯЁA-Z][а-яёa-z]+(?:\s+[А-ЯЁA-Z][а-яёa-z]+){0,2})"),
    re.compile(r"(?:я)\s+([А-ЯЁA-Z][а-яёa-z]+(?:\s+[А-ЯЁA-Z][а-яёa-z]+){0,2})"),
]

FULLNAME_PATTERN = re.compile(
    r"\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?\b"
)


@dataclass
class PersonCandidate:
    raw: str
    start_char: int
    end_char: int


def extract_person_candidates(text: str) -> list[PersonCandidate]:
    candidates: list[PersonCandidate] = []

    for pattern in PERSON_CONTEXT_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(1).strip()
            candidates.append(
                PersonCandidate(
                    raw=raw,
                    start_char=match.start(1),
                    end_char=match.end(1),
                )
            )

    for match in FULLNAME_PATTERN.finditer(text):
        raw = match.group().strip()
        candidates.append(
            PersonCandidate(
                raw=raw,
                start_char=match.start(),
                end_char=match.end(),
            )
        )

    return dedupe_person_candidates(candidates)


def dedupe_person_candidates(candidates: list[PersonCandidate]) -> list[PersonCandidate]:
    result: list[PersonCandidate] = []
    seen = set()

    for c in candidates:
        key = (c.start_char, c.end_char, c.raw)
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result


def normalize_person_candidate(raw: str) -> str | None:
    s = raw.strip()
    s = re.sub(r"\s+", " ", s)

    parts = s.split()
    if not 1 <= len(parts) <= 3:
        return None

    cleaned = []
    for part in parts:
        if not re.fullmatch(r"[А-ЯЁA-Z][а-яёa-z\-]+", part):
            return None
        cleaned.append(part)

    return " ".join(cleaned)


def is_valid_person_like(value: str) -> bool:
    parts = value.split()
    if not 1 <= len(parts) <= 3:
        return False

    return all(re.fullmatch(r"[А-ЯЁA-Z][а-яёa-z\-]+", p) for p in parts)
