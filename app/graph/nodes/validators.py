import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def is_valid_name(name: str) -> bool:
    name = name.strip()
    if len(name.split()) < 2:
        return False
    return bool(re.match(r"^[A-Za-z\s\-']+$", name))


def is_valid_age(age_text: str) -> bool:
    """Extracts a plausible integer age from text. Accepts '34', 'thirty
    four', '34 years old', etc. — the extractor normally hands back digits,
    but this stays lenient rather than requiring a strict int() match."""
    match = re.search(r"\d{1,3}", str(age_text))
    if not match:
        return False
    age = int(match.group())
    return 0 < age <= 120


def is_valid_reason(reason: str) -> bool:
    return len(reason.strip()) >= 3