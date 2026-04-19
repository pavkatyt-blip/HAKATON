import re
from dataclasses import dataclass


EMAIL_KEYWORDS = ["почта", "email", "e-mail", "емейл", "имейл"]

NORMAL_EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


@dataclass
class EmailCandidate:
    raw: str
    start_char: int
    end_char: int


def extract_email_candidates(text: str) -> list[EmailCandidate]:
    candidates: list[EmailCandidate] = []

    for match in NORMAL_EMAIL_PATTERN.finditer(text):
        candidates.append(
            EmailCandidate(
                raw=match.group().strip(),
                start_char=match.start(),
                end_char=match.end(),
            )
        )

    lower = text.lower()

    for keyword in EMAIL_KEYWORDS:
        start = 0
        while True:
            idx = lower.find(keyword, start)
            if idx == -1:
                break

            value_start = idx + len(keyword)
            while value_start < len(text) and text[value_start].isspace():
                value_start += 1

            value_end = value_start
            while value_end < len(text):
                ch = text[value_end]

                if ch in "!?":
                    break

                if ch == ".":
                    tail = text[value_end:value_end + 8].lower()
                    if re.match(r"\.\s*(ru|com|org|net|rf|рф)", tail):
                        value_end += 1
                        continue
                    break

                value_end += 1

            raw = text[value_start:value_end].strip()
            if raw:
                candidates.append(
                    EmailCandidate(
                        raw=raw,
                        start_char=value_start,
                        end_char=value_end,
                    )
                )

            start = idx + len(keyword)

    return dedupe_email_candidates(candidates)


def dedupe_email_candidates(candidates: list[EmailCandidate]) -> list[EmailCandidate]:
    result: list[EmailCandidate] = []
    seen = set()

    for c in candidates:
        key = (c.start_char, c.end_char, c.raw)
        if key not in seen:
            seen.add(key)
            result.append(c)

    return result


def normalize_email_candidate(raw: str) -> str | None:
    s = raw.lower().strip()

    direct = re.search(NORMAL_EMAIL_PATTERN, s)
    if direct:
        return direct.group().lower()

    replacements = {
        "собака": "@",
        "sobaka": "@",
        "sabaka": "@",
        "sabaca": "@",
        "сабака": "@",
        "точка": ".",
        "dot": ".",
        "яндексру": "yandex.ru",
        "янбексру": "yandex.ru",
        "яндекс": "yandex",
        "янбекс": "yandex",
        "джимейл": "gmail",
        "гмейл": "gmail",
        "майл": "mail",
        "мэйл": "mail",
    }

    for old, new in replacements.items():
        s = s.replace(old, new)

    s = s.replace(",", " ")
    s = re.sub(r"\s*\.\s*", ".", s)
    s = re.sub(r"\s+", " ", s).strip()

    if "@" in s:
        s = s.replace(" ", "")
        s = s.replace("..", ".")
        s = s.replace("@.", "@")
        s = s.replace(".@", "@")

        if is_valid_email_like(s):
            return s

    tokens = s.split()
    if "@" in tokens:
        at_idx = tokens.index("@")
        local = "".join(tokens[:at_idx]).replace("..", ".")
        domain = "".join(tokens[at_idx + 1:]).replace("..", ".")
        candidate = f"{local}@{domain}".replace("@.", "@").replace(".@", "@")

        if is_valid_email_like(candidate):
            return candidate

    compact = s.replace(" ", "")
    compact = re.sub(
        r"([a-z0-9._%+-]+)(?:sobaka|sabaka|sabaca|собака|сабака)([a-z0-9.-]+\.[a-z]{2,})",
        r"\1@\2",
        compact,
        flags=re.IGNORECASE,
    )

    if is_valid_email_like(compact):
        return compact

    return None


def is_valid_email_like(value: str) -> bool:
    if "@" not in value:
        return False

    local, _, domain = value.partition("@")
    if not local or not domain:
        return False

    if "." not in domain:
        return False

    return bool(
        re.fullmatch(
            r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}",
            value,
            flags=re.IGNORECASE,
        )
    )
