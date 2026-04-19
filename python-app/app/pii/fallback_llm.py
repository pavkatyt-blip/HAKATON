import os
import json
import re
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI


@dataclass
class LLMEmailResult:
    normalized_email: Optional[str]
    confidence: float
    reason: str


@dataclass
class LLMPersonResult:
    normalized_person: Optional[str]
    confidence: float
    reason: str


@dataclass
class LLMAddressResult:
    normalized_address: Optional[str]
    confidence: float
    reason: str


def _get_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def is_valid_email_like(value: str) -> bool:
    if "@" not in value:
        return False

    local, _, domain = value.partition("@")
    if not local or not domain or "." not in domain:
        return False

    return bool(
        re.fullmatch(
            r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}",
            value,
            flags=re.IGNORECASE,
        )
    )


def is_valid_person_like(value: str) -> bool:
    parts = value.split()
    if not 1 <= len(parts) <= 3:
        return False

    return all(re.fullmatch(r"[А-ЯЁA-Z][а-яёa-z\-]+", p) for p in parts)


def is_valid_address_like(value: str) -> bool:
    if not value or len(value.strip()) < 8:
        return False

    lower = value.lower()
    keywords = [
        "улица", "ул", "проспект", "пр-кт", "переулок", "пер", "дом", "д",
        "квартира", "кв", "город", "г", "поселок", "посёлок", "село", "деревня",
        "шоссе", "проезд", "бульвар", "площадь", "корпус", "строение",
    ]
    return any(k in lower for k in keywords)


def _safe_parse_json(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except Exception:
        return None


def recover_email_with_llm(
    candidate: str,
    model: str = "gpt-5.4-mini",
) -> Optional[LLMEmailResult]:
    client = _get_client()
    if client is None:
        return None

    system_prompt = """Ты восстанавливаешь email из шумной ASR-расшифровки.
Правила:
1. Верни только JSON.
2. Если это похоже на проговоренный email, восстанови его в каноническом виде.
3. Если уверенности мало, верни normalized_email = null.
4. Не выдумывай, если данных не хватает.

Подсказки:
- "собака", "sobaka", "sabaka", "sabaca" часто означают "@"
- "точка" часто означает "."
- "яндекс", "янбекс" часто означают "yandex"
- "джимейл", "гмейл" часто означают "gmail"
- "майл", "мэйл" часто означают "mail"
"""

    user_prompt = f"""Кандидат из ASR:
{candidate}

Верни JSON вида:
{{
  "normalized_email": "user@example.com" | null,
  "confidence": 0.0,
  "reason": "short explanation"
}}"""

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "email_recovery",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "normalized_email": {"type": ["string", "null"]},
                            "confidence": {"type": "number"},
                            "reason": {"type": "string"},
                        },
                        "required": ["normalized_email", "confidence", "reason"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
        )
    except Exception:
        return None

    data = _safe_parse_json(response.output_text)
    if data is None:
        return None

    normalized_email = data.get("normalized_email")
    confidence = float(data.get("confidence", 0.0))
    reason = data.get("reason", "")

    if normalized_email is not None:
        normalized_email = normalized_email.strip().lower()
        if not is_valid_email_like(normalized_email):
            normalized_email = None

    return LLMEmailResult(
        normalized_email=normalized_email,
        confidence=confidence,
        reason=reason,
    )


def recover_person_with_llm(
    candidate: str,
    model: str = "gpt-5.4-mini",
) -> Optional[LLMPersonResult]:
    client = _get_client()
    if client is None:
        return None

    system_prompt = """Ты определяешь, является ли фрагмент ФИО человека.
Правила:
1. Верни только JSON.
2. Если это похоже на ФИО, верни нормализованную форму.
3. Если уверенности мало, верни normalized_person = null.
4. Не выдумывай лишние слова и не расширяй имя без оснований.
"""

    user_prompt = f"""Кандидат из ASR:
{candidate}

Верни JSON вида:
{{
  "normalized_person": "Иван Петров" | null,
  "confidence": 0.0,
  "reason": "short explanation"
}}"""

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "person_recovery",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "normalized_person": {"type": ["string", "null"]},
                            "confidence": {"type": "number"},
                            "reason": {"type": "string"},
                        },
                        "required": ["normalized_person", "confidence", "reason"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
        )
    except Exception:
        return None

    data = _safe_parse_json(response.output_text)
    if data is None:
        return None

    normalized_person = data.get("normalized_person")
    confidence = float(data.get("confidence", 0.0))
    reason = data.get("reason", "")

    if normalized_person is not None:
        normalized_person = re.sub(r"\s+", " ", normalized_person.strip())
        if not is_valid_person_like(normalized_person):
            normalized_person = None

    return LLMPersonResult(
        normalized_person=normalized_person,
        confidence=confidence,
        reason=reason,
    )


def recover_address_with_llm(
    candidate: str,
    model: str = "gpt-5.4-mini",
) -> Optional[LLMAddressResult]:
    client = _get_client()
    if client is None:
        return None

    system_prompt = """Ты определяешь, является ли фрагмент адресом.
Правила:
1. Верни только JSON.
2. Если это похоже на адрес, верни нормализованную форму.
3. Если уверенности мало, верни normalized_address = null.
4. Не выдумывай недостающие части адреса.
"""

    user_prompt = f"""Кандидат из ASR:
{candidate}

Верни JSON вида:
{{
  "normalized_address": "Москва, улица Ленина, дом 5" | null,
  "confidence": 0.0,
  "reason": "short explanation"
}}"""

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "address_recovery",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "normalized_address": {"type": ["string", "null"]},
                            "confidence": {"type": "number"},
                            "reason": {"type": "string"},
                        },
                        "required": ["normalized_address", "confidence", "reason"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
        )
    except Exception:
        return None

    data = _safe_parse_json(response.output_text)
    if data is None:
        return None

    normalized_address = data.get("normalized_address")
    confidence = float(data.get("confidence", 0.0))
    reason = data.get("reason", "")

    if normalized_address is not None:
        normalized_address = re.sub(r"\s+", " ", normalized_address.strip())
        if not is_valid_address_like(normalized_address):
            normalized_address = None

    return LLMAddressResult(
        normalized_address=normalized_address,
        confidence=confidence,
        reason=reason,
    )
