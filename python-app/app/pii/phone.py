import re
from dataclasses import dataclass


PHONE_DIGIT_PATTERN = re.compile(
    r"(\+7|7|8)[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-()]*\d{2}[\s\-()]*\d{2}",
    re.IGNORECASE,
)

PHONE_CONTEXT_PATTERN = re.compile(
    r"(?:телефон|номер|номер телефона|мой номер)\s+"
    r"((?:плюс\s+)?(?:\+?\d+|ноль|один|одна|два|две|три|четыре|пять|шесть|семь|восемь|девять)"
    r"(?:[\s\-()]+(?:\d+|ноль|один|одна|два|две|три|четыре|пять|шесть|семь|восемь|девять))*)",
    re.IGNORECASE,
)

RUS_NUMBER_WORDS = {
    "ноль": "0",
    "один": "1",
    "одна": "1",
    "два": "2",
    "две": "2",
    "три": "3",
    "четыре": "4",
    "пять": "5",
    "шесть": "6",
    "семь": "7",
    "восемь": "8",
    "девять": "9",
}


@dataclass
class PhoneCandidate:
    raw: str
    start_char: int
    end_char: int


def extract_phone_candidates(text: str) -> list[PhoneCandidate]:
    candidates: list[PhoneCandidate] = []

    for match in PHONE_DIGIT_PATTERN.finditer(text):
        candidates.append(
            PhoneCandidate(
                raw=match.group().strip(),
                start_char=match.start(),
                end_char=match.end(),
            )
        )

    for match in PHONE_CONTEXT_PATTERN.finditer(text):
        candidates.append(
            PhoneCandidate(
                raw=match.group(1).strip(),
                start_char=match.start(1),
                end_char=match.end(1),
            )
        )

    return dedupe_phone_candidates(candidates)


def dedupe_phone_candidates(candidates: list[PhoneCandidate]) -> list[PhoneCandidate]:
    result: list[PhoneCandidate] = []
    seen = set()

    for c in candidates:
        key = (c.start_char, c.end_char, c.raw)
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result


def normalize_phone_candidate(raw: str) -> str | None:
    s = raw.lower().strip()
    s = s.replace("+", " + ")
    s = s.replace("-", " ")
    s = s.replace("(", " ")
    s = s.replace(")", " ")
    s = s.replace(",", " ")
    s = re.sub(r"\s+", " ", s).strip()

    tokens = s.split()
    digits_parts: list[str] = []

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok == "+" and i + 1 < len(tokens) and tokens[i + 1].isdigit():
            digits_parts.append(tokens[i + 1])
            i += 2
            continue

        if tok == "плюс" and i + 1 < len(tokens):
            nxt = tokens[i + 1]
            if nxt.isdigit():
                digits_parts.append(nxt)
                i += 2
                continue
            if nxt in RUS_NUMBER_WORDS:
                digits_parts.append(RUS_NUMBER_WORDS[nxt])
                i += 2
                continue

        if tok.isdigit():
            digits_parts.append(tok)
            i += 1
            continue

        if tok in RUS_NUMBER_WORDS:
            digits_parts.append(RUS_NUMBER_WORDS[tok])
            i += 1
            continue

        i += 1

    digits = "".join(digits_parts)
    digits = re.sub(r"\D", "", digits)

    if len(digits) == 11 and digits.startswith(("7", "8")):
        return digits
    if len(digits) == 10:
        return "7" + digits

    return None


def is_valid_phone(value: str) -> bool:
    return bool(re.fullmatch(r"[78]\d{10}", value))
