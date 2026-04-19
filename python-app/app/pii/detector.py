from models import TextPIISpan
from pii.email import extract_email_candidates, normalize_email_candidate, is_valid_email_like
from pii.phone import extract_phone_candidates, normalize_phone_candidate, is_valid_phone
from pii.passport import extract_passport_candidates, normalize_passport_candidate, is_valid_passport
from pii.snils import extract_snils_candidates, normalize_snils_candidate, is_valid_snils
from pii.inn import extract_inn_candidates, normalize_inn_candidate, is_valid_inn
from pii.person import extract_person_candidates, normalize_person_candidate, is_valid_person_like
from pii.address import extract_address_candidates, normalize_address_candidate, is_valid_address_like
from pii.fallback_llm import (
    recover_email_with_llm,
    recover_person_with_llm,
    recover_address_with_llm,
)


def detect_pii(transcript: str, debug: bool = False) -> list[TextPIISpan]:
    spans: list[TextPIISpan] = []

    # PHONE
    phone_candidates = extract_phone_candidates(transcript)
    if debug:
        print("\nPHONE CANDIDATES:")
        for c in phone_candidates:
            print(c)

    for candidate in phone_candidates:
        normalized = normalize_phone_candidate(candidate.raw)
        if debug:
            print("PHONE RAW:", candidate.raw, "->", normalized)

        if normalized and is_valid_phone(normalized):
            spans.append(
                TextPIISpan(
                    entity_type="PHONE_NUMBER",
                    text=normalized,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.95,
                )
            )

    # EMAIL
    email_candidates = extract_email_candidates(transcript)
    if debug:
        print("\nEMAIL CANDIDATES:")
        for c in email_candidates:
            print(c)

    for candidate in email_candidates:
        normalized = normalize_email_candidate(candidate.raw)
        if debug:
            print("EMAIL RAW:", candidate.raw, "->", normalized)

        if normalized and is_valid_email_like(normalized):
            spans.append(
                TextPIISpan(
                    entity_type="EMAIL_ADDRESS",
                    text=normalized,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.90,
                )
            )
            continue

        try:
            llm_result = recover_email_with_llm(candidate.raw)
        except Exception:
            llm_result = None

        if debug and llm_result:
            print("EMAIL LLM:", candidate.raw, "->", llm_result)

        if llm_result and llm_result.normalized_email and llm_result.confidence >= 0.6:
            spans.append(
                TextPIISpan(
                    entity_type="EMAIL_ADDRESS",
                    text=llm_result.normalized_email,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=min(max(llm_result.confidence, 0.6), 0.95),
                )
            )
        else:
            spans.append(
                TextPIISpan(
                    entity_type="EMAIL_CANDIDATE",
                    text=candidate.raw,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.55,
                )
            )

    # PASSPORT
    passport_candidates = extract_passport_candidates(transcript)
    if debug:
        print("\nPASSPORT CANDIDATES:")
        for c in passport_candidates:
            print(c)

    for candidate in passport_candidates:
        normalized = normalize_passport_candidate(candidate.raw)
        if debug:
            print("PASSPORT RAW:", candidate.raw, "->", normalized)

        if normalized and is_valid_passport(normalized):
            spans.append(
                TextPIISpan(
                    entity_type="PASSPORT_RF",
                    text=normalized,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.95,
                )
            )
        else:
            context_text = candidate.raw.lower()
            if any(k in context_text for k in ["паспорт", "паспорта", "серия", "номер"]):
                spans.append(
                    TextPIISpan(
                        entity_type="PASSPORT_CANDIDATE",
                        text=candidate.raw,
                        start_char=candidate.start_char,
                        end_char=candidate.end_char,
                        score=0.55,
                    )
                )

    # SNILS
    snils_candidates = extract_snils_candidates(transcript)
    if debug:
        print("\nSNILS CANDIDATES:")
        for c in snils_candidates:
            print(c)

    for candidate in snils_candidates:
        normalized = normalize_snils_candidate(candidate.raw)
        if debug:
            print("SNILS RAW:", candidate.raw, "->", normalized)

        if normalized and is_valid_snils(normalized):
            spans.append(
                TextPIISpan(
                    entity_type="SNILS",
                    text=normalized,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.95,
                )
            )
        else:
            context_text = candidate.raw.lower()
            if any(k in context_text for k in ["снилс", "снил"]):
                spans.append(
                    TextPIISpan(
                        entity_type="SNILS_CANDIDATE",
                        text=candidate.raw,
                        start_char=candidate.start_char,
                        end_char=candidate.end_char,
                        score=0.55,
                    )
                )

    # INN
    inn_candidates = extract_inn_candidates(transcript)
    if debug:
        print("\nINN CANDIDATES:")
        for c in inn_candidates:
            print(c)

    for candidate in inn_candidates:
        normalized = normalize_inn_candidate(candidate.raw)
        if debug:
            print("INN RAW:", candidate.raw, "->", normalized)

        if normalized and is_valid_inn(normalized):
            spans.append(
                TextPIISpan(
                    entity_type="INN",
                    text=normalized,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.95,
                )
            )
        else:
            spans.append(
                TextPIISpan(
                    entity_type="INN_CANDIDATE",
                    text=candidate.raw,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.55,
                )
            )

    # PERSON
    person_candidates = extract_person_candidates(transcript)
    if debug:
        print("\nPERSON CANDIDATES:")
        for c in person_candidates:
            print(c)

    for candidate in person_candidates:
        normalized = normalize_person_candidate(candidate.raw)
        if debug:
            print("PERSON RAW:", candidate.raw, "->", normalized)

        if normalized and is_valid_person_like(normalized):
            spans.append(
                TextPIISpan(
                    entity_type="PERSON",
                    text=normalized,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.75,
                )
            )
            continue

        try:
            llm_result = recover_person_with_llm(candidate.raw)
        except Exception:
            llm_result = None

        if debug and llm_result:
            print("PERSON LLM:", candidate.raw, "->", llm_result)

        if llm_result and llm_result.normalized_person and llm_result.confidence >= 0.6:
            spans.append(
                TextPIISpan(
                    entity_type="PERSON",
                    text=llm_result.normalized_person,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=min(max(llm_result.confidence, 0.6), 0.90),
                )
            )
        else:
            spans.append(
                TextPIISpan(
                    entity_type="PERSON_CANDIDATE",
                    text=candidate.raw,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.50,
                )
            )

    # ADDRESS
    address_candidates = extract_address_candidates(transcript)
    if debug:
        print("\nADDRESS CANDIDATES:")
        for c in address_candidates:
            print(c)

    for candidate in address_candidates:
        normalized = normalize_address_candidate(candidate.raw)
        if debug:
            print("ADDRESS RAW:", candidate.raw, "->", normalized)

        if normalized and is_valid_address_like(normalized):
            spans.append(
                TextPIISpan(
                    entity_type="ADDRESS",
                    text=normalized,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.70,
                )
            )
            continue

        try:
            llm_result = recover_address_with_llm(candidate.raw)
        except Exception:
            llm_result = None

        if debug and llm_result:
            print("ADDRESS LLM:", candidate.raw, "->", llm_result)

        if llm_result and llm_result.normalized_address and llm_result.confidence >= 0.6:
            spans.append(
                TextPIISpan(
                    entity_type="ADDRESS",
                    text=llm_result.normalized_address,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=min(max(llm_result.confidence, 0.6), 0.90),
                )
            )
        else:
            spans.append(
                TextPIISpan(
                    entity_type="ADDRESS_CANDIDATE",
                    text=candidate.raw,
                    start_char=candidate.start_char,
                    end_char=candidate.end_char,
                    score=0.50,
                )
            )

    return dedupe_spans(spans)


def dedupe_spans(spans: list[TextPIISpan]) -> list[TextPIISpan]:
    spans = sorted(
        spans,
        key=lambda s: (s.start_char, -(s.end_char - s.start_char), s.entity_type),
    )

    result: list[TextPIISpan] = []

    for span in spans:
        skip = False
        for kept in result:
            same_type = span.entity_type == kept.entity_type
            inside = span.start_char >= kept.start_char and span.end_char <= kept.end_char
            same_text = span.text == kept.text

            if same_type and (inside or same_text):
                skip = True
                break

        if not skip:
            result.append(span)

    return result
