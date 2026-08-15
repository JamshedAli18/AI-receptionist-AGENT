import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.nodes.llm_utils import detect_confirmation_fallback

cases = [
    ("Yes.", True),
    ("yes", True),
    ("Yes, that works", True),
    ("Yes, that didn't work for me.", False),
    ("No, that doesn't work", False),
    ("that didn't work", False),
    ("no", False),
    ("maybe", None),
]

for text, expected in cases:
    result = detect_confirmation_fallback(text)
    status = "✅" if result == expected else "❌"
    print(f"{status} '{text}' -> {result} (expected {expected})")