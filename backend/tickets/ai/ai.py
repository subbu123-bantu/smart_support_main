from .ai_client import ai_classification_async
from .ai_constants import (
    AUTH_DEBOOST_PHRASES,
    CATEGORY_KEYWORDS,
    CATEGORY_THRESHOLDS,
    CATEGORIES,
    CANNOT_CONNECT,
    DELETE_ACCOUNT,
    SERVER_ERROR,
)
from .ai_helper import (
    contains_any,
    is_generic_input,
    is_weak_input,
    phrase_score,
    preprocess,
)
from .ai_overrides import apply_conflict_overrides
from .ai_priority import get_priority
from ..models import TicketPredictionLog


class TicketPredictor:
    review_sources = {
        "fallback",
        "threshold_reject",
        "soft_fallback",
        "weak_input_reject",
        "generic_input_reject",
    }

    def rule_engine(self, text: str):
        if len(text.split()) < 2:
            return {"category": "other", "confidence": 0.40, "source": "rule_short_input"}

        scores = {}
        matches = {}

        for category, keywords in CATEGORY_KEYWORDS.items():
            score, matched = phrase_score(text, keywords)
            scores[category] = score
            matches[category] = matched

        if contains_any(text, AUTH_DEBOOST_PHRASES):
            scores["authentication"] = max(0, scores["authentication"] - 3)

        if contains_any(text, ["payment", "refund", "charged", "invoice", "deducted"]):
            scores["billing"] += 2

        if contains_any(text, ["dashboard", SERVER_ERROR, "upload", "crash", "500"]):
            scores["technical"] += 2

        if contains_any(text, [CANNOT_CONNECT, "timeout", "latency", "disconnect"]):
            scores["network"] += 2

        if contains_any(text, ["change email", "change phone", "update profile", DELETE_ACCOUNT]):
            scores["account"] += 2

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        if best_score <= 0:
            return None

        confidence = min(0.78 + (best_score * 0.04), 0.95)

        return {
            "category": best_category,
            "confidence": round(confidence, 2),
            "source": "rule",
            "matches": matches.get(best_category, []),
            "scores": scores,
        }

    def best_keyword_category(self, text: str):
        scores = {}
        matches_by_category = {}

        for category, keywords in CATEGORY_KEYWORDS.items():
            score, matched = phrase_score(text, keywords)
            scores[category] = score
            matches_by_category[category] = matched

        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        if best_score <= 0:
            return None

        confidence = min(0.70 + (best_score * 0.05), 0.90)

        return {
            "category": best_category,
            "confidence": round(confidence, 2),
            "source": "keyword_fallback",
            "matches": matches_by_category.get(best_category, []),
        }

    def choose_final(self, rule_result, ai_result, keyword_result) -> dict:
        candidates = [result for result in [rule_result, ai_result, keyword_result] if result]

        if not candidates:
            return {"category": "other", "confidence": 0.35, "source": "fallback"}

        if rule_result and ai_result and rule_result["category"] == ai_result["category"]:
            boosted = round(
                min(max(rule_result["confidence"], ai_result["confidence"]) + 0.04, 0.97),
                2,
            )
            return {
                "category": rule_result["category"],
                "confidence": boosted,
                "source": "rule+AI",
            }

        if (
            rule_result
            and keyword_result
            and rule_result["category"] == keyword_result["category"]
        ):
            boosted = round(
                min(max(rule_result["confidence"], keyword_result["confidence"]) + 0.03, 0.95),
                2,
            )
            return {
                "category": rule_result["category"],
                "confidence": boosted,
                "source": "rule+keyword",
            }

        candidates.sort(key=lambda item: item.get("confidence", 0), reverse=True)
        return candidates[0]

    def log_prediction(self, text: str, result: dict, ticket=None) -> None:
        TicketPredictionLog.objects.create(
            ticket=ticket,
            text=text,
            predicted_category=result["category"],
            predicted_priority=result["priority"],
            source=result["source"],
            confidence=result["confidence"],
        )

    def resolve_low_confidence(self, category: str, confidence: float, final: dict, keyword_result):
        threshold = CATEGORY_THRESHOLDS.get(category, 0.78)

        if category == "other" or confidence >= threshold:
            return category, confidence

        if keyword_result and len(keyword_result.get("matches", [])) >= 2:
            final["source"] = "soft_fallback"
            return keyword_result["category"], max(keyword_result.get("confidence", 0.72), 0.72)

        final["source"] = "threshold_reject"
        return "other", 0.48

    def needs_manual_review(self, category: str, confidence: float, source: str) -> bool:
        return category == "other" or confidence < 0.85 or source in self.review_sources

    def _early_reject(self, text: str):
        clean = preprocess(text)
        words = clean.split()

        if is_weak_input(words, clean):
            return clean, {
                "category": "other",
                "confidence": 0.30,
                "source": "weak_input_reject",
                "priority": "low",
                "needs_manual_review": True,
            }

        if is_generic_input(words, clean):
            return clean, {
                "category": "other",
                "confidence": 0.32,
                "source": "generic_input_reject",
                "priority": "low",
                "needs_manual_review": True,
            }

        return clean, None

    def _predict_with_ai_result(self, text: str, ai_result) -> dict:
        clean, rejected = self._early_reject(text)
        if rejected:
            return rejected

        rule_result = self.rule_engine(clean)
        keyword_result = self.best_keyword_category(clean)
        final = self.choose_final(rule_result, ai_result, keyword_result)
        final = apply_conflict_overrides(clean, final)

        category = final.get("category", "other")
        confidence = final.get("confidence", 0.35)

        if category not in CATEGORIES and category != "other":
            category = "other"
            confidence = 0.35
            final["source"] = "fallback"

        category, confidence = self.resolve_low_confidence(
            category,
            confidence,
            final,
            keyword_result,
        )

        priority = get_priority(clean, category)
        source = final["source"]

        return {
            "category": category,
            "confidence": round(confidence, 2),
            "source": source,
            "priority": priority,
            "needs_manual_review": self.needs_manual_review(category, confidence, source),
        }

    async def predict_ticket(self, text: str, include_ai: bool = True) -> dict:
        _, rejected = self._early_reject(text)
        if rejected:
            return rejected

        ai_result = await ai_classification_async(text) if include_ai else None
        return self._predict_with_ai_result(text, ai_result)

PREDICTOR = TicketPredictor()


def rule_engine(text: str):
    return PREDICTOR.rule_engine(text)


def best_keyword_category(text: str):
    return PREDICTOR.best_keyword_category(text)


def choose_final(rule_result, ai_result, keyword_result) -> dict:
    return PREDICTOR.choose_final(rule_result, ai_result, keyword_result)


def log_prediction(text: str, result: dict, ticket=None) -> None:
    return PREDICTOR.log_prediction(text, result, ticket)


def resolve_low_confidence(category: str, confidence: float, final: dict, keyword_result):
    return PREDICTOR.resolve_low_confidence(category, confidence, final, keyword_result)


def needs_manual_review(category: str, confidence: float, source: str) -> bool:
    return PREDICTOR.needs_manual_review(category, confidence, source)


async def predict_ticket(text: str) -> dict:
    return await PREDICTOR.predict_ticket(text)


async def predict_ticket_without_ai(text: str) -> dict:
    return await PREDICTOR.predict_ticket(text, include_ai=False)
