import re
from dataclasses import dataclass


PASSPORT_DIRECT_PATTERNS = [
    re.compile(r"\b\d{2}\s?\d{2}\s?\d{6}\b"),
    re.compile(r"\b\d{2}\s\d{2}\s\d{2}\s\d{2}\s\d{2}\b"),
]

PASSPORT_CONTEXT_PATTERN = re.compile(
    r"(?:паспорт|паспорта|серия|номер паспорта|данные паспорта)\s+(.+?)(?:$|[.!?])",
    re.IGNORECASE,
)


@dataclass
class PassportCandidate:
    raw: str
    start_char: int
    end_char: int


def extract_passport_candidates(text: str) -> list[PassportCandidate]:
    candidates: list[PassportCandidate] = []

    for pattern in PASSPORT_DIRECT_PATTERNS:
        for match in pattern.finditer(text):
            candidates.append(
                PassportCandidate(
                    raw=match.group().strip(),
                    start_char=match.start(),
                    end_char=match.end(),
                )
            )

    for match in PASSPORT_CONTEXT_PATTERN.finditer(text):
        raw = match.group(1).strip()
        candidates.append(
            PassportCandidate(
                raw=raw,
                start_char=match.start(1),
                end_char=match.end(1),
            )
        )

    return dedupe_passport_candidates(candidates)


def dedupe_passport_candidates(candidates: list[PassportCandidate]) -> list[PassportCandidate]:
    result: list[PassportCandidate] = []
    seen = set()

    for c in candidates:
        key = (c.start_char, c.end_char, c.raw)
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result


def normalize_passport_candidate(raw: str) -> str | None:
    digits = re.findall(r"\d+", raw)
    if not digits:
        return None

    joined = "".join(digits)

    if len(joined) == 10:
        return joined

    if len(joined) > 10:
        return joined[:10]

    return None


def is_valid_passport(value: str) -> bool:
    return bool(re.fullmatch(r"\d{10}", value))
