import re

from .ai_constants import GENERIC_WEAK_WORDS, SUPPORT_HINTS


def preprocess(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text


def contains_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def phrase_score(text: str, phrases: list[str]) -> tuple[int, list[str]]:
    score = 0
    matches = []

    for phrase in phrases:
        if phrase in text:
            score += 3 if " " in phrase else 1
            matches.append(phrase)

    return score, matches


def count_generic_only(words: list[str]) -> bool:
    if not words:
        return True
    return all(word in GENERIC_WEAK_WORDS for word in words)


def is_weak_input(words: list[str], clean: str) -> bool:
    return len(words) < 3 and not contains_any(clean, SUPPORT_HINTS)


def is_generic_input(words: list[str], clean: str) -> bool:
    return count_generic_only(words[:6]) and not contains_any(clean, SUPPORT_HINTS)