import re
from dataclasses import dataclass


INN_DIRECT_PATTERN = re.compile(
    r"\b\d{10}\b|\b\d{12}\b"
)

INN_CONTEXT_PATTERN = re.compile(
    r"(?:инн|нн|инэн|иэнэн|ннн|cnn|inn)\s+(.+?)(?:$|[.!?])",
    re.IGNORECASE,
)


@dataclass
class InnCandidate:
    raw: str
    start_char: int
    end_char: int


def extract_inn_candidates(text: str) -> list[InnCandidate]:
    candidates: list[InnCandidate] = []

    for match in INN_DIRECT_PATTERN.finditer(text):
        candidates.append(
            InnCandidate(
                raw=match.group().strip(),
                start_char=match.start(),
                end_char=match.end(),
            )
        )

    for match in INN_CONTEXT_PATTERN.finditer(text):
        raw = match.group(1).strip()
        candidates.append(
            InnCandidate(
                raw=raw,
                start_char=match.start(1),
                end_char=match.end(1),
            )
        )

    return dedupe_inn_candidates(candidates)


def dedupe_inn_candidates(candidates: list[InnCandidate]) -> list[InnCandidate]:
    result: list[InnCandidate] = []
    seen = set()

    for c in candidates:
        key = (c.start_char, c.end_char, c.raw)
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result


def normalize_inn_candidate(raw: str) -> str | None:
    digits = re.findall(r"\d+", raw)
    if not digits:
        return None

    joined = "".join(digits)

    if len(joined) in (10, 12):
        return joined

    if len(joined) > 12:
        if len(joined[:12]) == 12:
            return joined[:12]
        if len(joined[:10]) == 10:
            return joined[:10]

    return None


def is_valid_inn(value: str) -> bool:
    return bool(re.fullmatch(r"\d{10}|\d{12}", value))
