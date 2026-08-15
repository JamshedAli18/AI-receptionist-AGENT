import time
from datetime import datetime
import dateparser
from instructor.v2.core.errors import IncompleteOutputException


def call_with_retry(fn, max_retries=4, base_wait=8):
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn()
        except IncompleteOutputException as e:
            # Transient generation cutoff — the model's structured output got
            # truncated before instructor could parse it. Usually resolves
            # on retry, sometimes needs a moment.
            last_exc = e
            wait = 3 * (attempt + 1)
            print(f"[llm] incomplete output, retrying in {wait}s... (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)
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


NEGATION_OVERRIDE_PHRASES = {
    "didn't work", "doesn't work", "does not work", "did not work",
    "not work", "won't work", "will not work", "not correct", "not right",
    "isn't right", "isn't correct", "that's wrong",
}


def detect_confirmation_fallback(text: str) -> bool | None:
    # Strip trailing punctuation before matching, so "Yes." / "Yes!" match
    # the same as "Yes" — this was silently failing before.
    normalized = text.strip().lower().rstrip(".!?")

    # A negation phrase anywhere in the message overrides a leading "yes" —
    # e.g. "yes, that didn't work for me" must be treated as a decline, not
    # a confirmation. Check this BEFORE the positive-word check.
    if any(phrase in normalized for phrase in NEGATION_OVERRIDE_PHRASES):
        return False

    if any(normalized == w or normalized.startswith(w + " ") or normalized.startswith(w + ",") for w in POSITIVE_WORDS):
        return True
    if any(normalized == w or normalized.startswith(w + " ") or normalized.startswith(w + ",") for w in NEGATIVE_WORDS):
        return False
    return None


ABANDON_PHRASES = {
    "bye", "goodbye", "never mind", "nevermind", "forget it", "leave it",
    "cancel that", "stop", "no thanks", "not interested", "i don't want",
    "i dont want", "i changed my mind", "actually no", "skip it",
}


def detect_abandonment_fallback(text: str) -> bool:
    """
    Hardcoded safety net for callers trying to exit a flow (booking,
    reschedule, cancel) — LLM extraction can fail to notice this across
    several turns, leaving the caller stuck. Checked as a fallback when the
    LLM's own abandonment signal comes back false/null.
    """
    normalized = text.strip().lower()
    return any(phrase in normalized for phrase in ABANDON_PHRASES)