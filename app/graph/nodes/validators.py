import re
from datetime import datetime
from typing import Optional
import dateparser

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_REGEX = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')

# Filler words Whisper sometimes inserts when transcribing spoken "@" as
# "at" — e.g. "abc at the gmail dot com" instead of "abc at gmail dot com".
_AT_FILLER_WORDS = r'(?:the|a|uh|um)\s+'


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def is_valid_name(name: str) -> bool:
    name = name.strip()
    if len(name.split()) < 2:
        return False
    return bool(re.match(r"^[A-Za-z\s\-']+$", name))


def is_valid_age(age_text: str) -> bool:
    match = re.search(r"\d{1,3}", str(age_text))
    if not match:
        return False
    age = int(match.group())
    return 0 < age <= 120


def is_valid_reason(reason: str) -> bool:
    return len(reason.strip()) >= 3


def _normalize_spoken_email(message: str) -> str:
    """
    Converts common spoken-email patterns (from voice transcription) into
    real email syntax before regex extraction. E.g. "jamshed at gmail dot
    com" -> "jamshed@gmail.com". Safe to run on typed text too, since it
    only fires on the specific "word at word dot word" pattern.
    """
    text = message

    # Strip filler words directly after "at" — "at the gmail" -> "at gmail"
    text = re.sub(rf'\bat\s+{_AT_FILLER_WORDS}', 'at ', text, flags=re.IGNORECASE)

    # Whisper sometimes transcribes a spoken "@" as a literal @ symbol but
    # with spaces around it (e.g. "jamshed @ gmail.com") — collapse that
    # first, since EMAIL_REGEX requires no whitespace around the @.
    text = re.sub(r'\s*@\s*', '@', text)

    # "word at word dot/." -> word@word.word
    pattern = re.compile(
        r'\b([a-zA-Z0-9._%+-]+)\s+at\s+([a-zA-Z0-9-]+)(?:\s+dot\s+|\.)([a-zA-Z]{2,})\b',
        re.IGNORECASE,
    )
    text = pattern.sub(lambda m: f"{m.group(1)}@{m.group(2)}.{m.group(3)}", text)

    # Standalone " at " / " dot " inside something that already looks
    # like it's forming an email attempt (has an @ or a recognizable
    # domain word nearby) — normalize remaining loose "dot"/"at" words.
    text = re.sub(r'\s+at\s+', '@', text) if '@' not in text and re.search(r'\bat\b.*(?:\bdot\b|\.[a-zA-Z]{2,})', text, re.IGNORECASE) else text
    text = re.sub(r'\s+dot\s+', '.', text, flags=re.IGNORECASE)
    return text


def _extract_email(message: str) -> Optional[str]:
    """Extracts an email address via regex — deterministic, no LLM guessing.
    Normalizes spoken patterns (e.g. 'at'/'dot') first, since voice
    transcription doesn't produce literal @ and . symbols."""
    normalized = _normalize_spoken_email(message)
    match = EMAIL_REGEX.search(normalized)
    return match.group(0) if match else None


def normalize_spoken_email(text: str) -> str:
    """
    Public entry point used by booking_node — tries deterministic regex
    extraction first (handles 'X at Y dot Z' voice patterns reliably),
    falls back to lightly cleaning the raw text if no pattern matches.
    """
    extracted = _extract_email(text)
    if extracted:
        return extracted.lower()
    return re.sub(r'\s+', '', text.strip().lower())