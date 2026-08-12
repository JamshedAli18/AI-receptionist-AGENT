import time
import dateparser


def call_with_retry(fn, max_retries=4, base_wait=8):
    """
    Generic retry wrapper for any Groq/instructor call that can hit a
    rate limit under load. Groq's TPM cap resets on a rolling per-minute
    basis, not instantly, so backoff waits get longer each attempt.
    Catches by message content rather than a specific exception class,
    since instructor wraps the underlying groq.RateLimitError in its own
    InstructorRetryException after its internal retries are exhausted.
    """
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


def parse_datetime_robust(text: str, prefer_future: bool = True):
    """
    dateparser can silently return None for some 'next <weekday> at <time>'
    phrases depending on internal ambiguity resolution between its relative
    and absolute-weekday parsers. Try a few strategies before giving up.
    """
    primary_settings = {"PREFER_DATES_FROM": "future"} if prefer_future else {}

    parsed = dateparser.parse(text, settings=primary_settings) if primary_settings else dateparser.parse(text)
    if parsed:
        return parsed

    parsed = dateparser.parse(text)
    if parsed:
        return parsed

    try:
        from dateparser.search import search_dates
        results = search_dates(text, settings=primary_settings or None)
        if results:
            return results[0][1]
    except Exception:
        pass

    return None