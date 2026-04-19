import re
from dataclasses import dataclass


ADDRESS_CONTEXT_PATTERN = re.compile(
    r"(?:адрес|живу|проживаю|нахожусь по адресу)\s+(.+?)(?:$|[.!?])",
    re.IGNORECASE,
)

STRONG_ADDRESS_KEYWORDS = [
    "улица",
    "ул",
    "проспект",
    "пр-кт",
    "переулок",
    "пер",
    "шоссе",
    "проезд",
    "бульвар",
    "площадь",
    "дом",
    "д",
    "квартира",
    "кв",
    "корпус",
    "строение",
]

SETTLEMENT_KEYWORDS = [
    "город",
    "г",
    "поселок",
    "посёлок",
    "село",
    "деревня",
]


@dataclass
class AddressCandidate:
    raw: str
    start_char: int
    end_char: int


def extract_address_candidates(text: str) -> list[AddressCandidate]:
    candidates: list[AddressCandidate] = []

    for match in ADDRESS_CONTEXT_PATTERN.finditer(text):
        raw = match.group(1).strip()
        candidates.append(
            AddressCandidate(
                raw=raw,
                start_char=match.start(1),
                end_char=match.end(1),
            )
        )

    return dedupe_address_candidates(candidates)


def dedupe_address_candidates(candidates: list[AddressCandidate]) -> list[AddressCandidate]:
    result: list[AddressCandidate] = []
    seen = set()

    for c in candidates:
        key = (c.start_char, c.end_char, c.raw)
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result


def normalize_address_candidate(raw: str) -> str | None:
    s = raw.strip()
    s = re.sub(r"\s+", " ", s)

    if len(s) < 8:
        return None

    lower = s.lower()

    has_strong = any(_contains_keyword(lower, kw) for kw in STRONG_ADDRESS_KEYWORDS)
    has_settlement = any(_contains_keyword(lower, kw) for kw in SETTLEMENT_KEYWORDS)

    if not has_strong:
        return None

    s = trim_address_tail(s)

    if len(s) < 8:
        return None

    lower = s.lower()
    has_strong = any(_contains_keyword(lower, kw) for kw in STRONG_ADDRESS_KEYWORDS)
    has_settlement = any(_contains_keyword(lower, kw) for kw in SETTLEMENT_KEYWORDS)

    if has_strong or (has_settlement and has_strong):
        return s

    return None


def is_valid_address_like(value: str) -> bool:
    lower = value.lower()

    has_strong = any(_contains_keyword(lower, kw) for kw in STRONG_ADDRESS_KEYWORDS)
    has_settlement = any(_contains_keyword(lower, kw) for kw in SETTLEMENT_KEYWORDS)

    return len(value) >= 8 and (has_strong or (has_settlement and has_strong))


def trim_address_tail(value: str) -> str:
    stop_patterns = [
        r"\.\s*замечательн",
        r"\.\s*моя почта",
        r"\.\s*можете",
        r"\.\s*также",
        r"\.\s*если",
        r"\.\s*мне очень",
        r"\.\s*вот",
    ]

    result = value
    lower = value.lower()

    cut_positions = []
    for pattern in stop_patterns:
        m = re.search(pattern, lower)
        if m:
            cut_positions.append(m.start())

    if cut_positions:
        result = value[:min(cut_positions)].strip(" ,.")

    return result


def _contains_keyword(text: str, keyword: str) -> bool:
    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None
