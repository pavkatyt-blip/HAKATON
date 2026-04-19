from dataclasses import dataclass


@dataclass
class WordToken:
    word: str
    start: float
    end: float
    idx_start: int
    idx_end: int


@dataclass
class TextPIISpan:
    entity_type: str
    text: str
    start_char: int
    end_char: int
    score: float


@dataclass
class AudioPIISpan:
    entity_type: str
    text: str
    start_time: float
    end_time: float
    score: float
