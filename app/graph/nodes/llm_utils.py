import time
from datetime import datetime
import dateparser


def call_with_retry(fn, max_retries=4, base_wait=8):
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            msg = str(e).lower()
            if "rate_limit" not in msg and "429" not in msg:
                raise
            last_exc = e
            wait = base_wait * (attempt + 1)
            print(f"[llm] rate limited, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)
    raise last_exc


def parse_datetime_robust(text: str):
    """
    Pins RELATIVE_BASE to the actual current moment on every call, so
    "tomorrow"/"in two days"/etc. always resolve relative to *now*, not to
    some earlier date dateparser inferred from context. Without pinning
    this explicitly, dateparser can inconsistently anchor relative phrases
    within the same process run.
    """
    now = datetime.now()
    settings = {"PREFER_DATES_FROM": "future", "RELATIVE_BASE": now}

    parsed = dateparser.parse(text, settings=settings)
    if parsed:
        return parsed

    parsed = dateparser.parse(text, settings={"RELATIVE_BASE": now})
    if parsed:
        return parsed

    try:
        from dateparser.search import search_dates
        results = search_dates(text, settings=settings)
        if results:
            return results[0][1]
    except Exception:
        pass

    return None


POSITIVE_WORDS = {"yes", "yeah", "yep", "yup", "sure", "ok", "okay", "correct",
                   "works", "sounds good", "that works", "done", "confirmed",
                   "right", "perfect", "great", "good"}
NEGATIVE_WORDS = {"no", "nope", "not", "don't", "dont", "wait", "cancel that",
                   "incorrect", "wrong"}


def detect_confirmation_fallback(text: str) -> bool | None:
    """
    Hardcoded safety net for yes/no detection — LLM extraction can miss
    casual affirmatives like 'yeah'. Checked whenever the LLM's own
    confirms_action/wants_to_confirm field comes back null on a turn where
    a yes/no answer was expected.
    """
    normalized = text.strip().lower()
    if any(normalized == w or normalized.startswith(w + " ") or normalized.startswith(w + ",") for w in POSITIVE_WORDS):
        return True
    if any(normalized == w or normalized.startswith(w + " ") or normalized.startswith(w + ",") for w in NEGATIVE_WORDS):
        return False
    return None