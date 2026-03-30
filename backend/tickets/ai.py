import re
import os
import json
import requests
from dotenv import load_dotenv
from .models import TicketPredictionLog

#CONFIG#

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

CONFIDENCE_THRESHOLD = 0.8

#PATTERNS #

PATTERNS = {
    "billing": ["payment", "transaction", "refund", "charged", "money", "pricing"],
    "technical": ["error", "bug", "crash", "not working", "freeze", "broken"],
    "authentication": ["login", "otp", "password", "verify", "session"],
    "network": ["internet", "wifi", "connection", "slow", "network"],
    "account": ["profile", "account", "settings", "delete account"],
}

#  PREPROCESS  #

def preprocess(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text

#  PRIORITY  #

def get_priority(text):
    text = text.lower()

    if any(w in text for w in ["urgent", "asap", "blocked", "down"]):
        return "urgent"
    if any(w in text for w in ["crash", "failed", "error"]):
        return "high"
    if any(w in text for w in ["slow", "lag"]):
        return "medium"
    return "low"

# RULE ENGINE #

def rule_engine(text):

    # PRIORITY ORDER (very important)
    text = text.lower()
    if len(text.split()) < 3 and not any(w in text for w in [
        "login", "payment", "error", "network"
    ]):
        return {"category": "other", "confidence": 0.5, "source": "rule"}

    if "password" in text:
        return {"category": "authentication", "confidence": 0.95, "source": "rule"}
    
    #  1. AUTH ONLY if pure auth (no bug words)
    if any(w in text for w in ["login", "otp", "password", "verify", "session"]):
        if not any(w in text for w in ["error", "fail", "crash", "bug", "not working", "freeze"]):
            return {"category": "authentication", "confidence": 0.9, "source": "rule"}

    #  2. NETWORK (higher priority than technical)
    if any(w in text for w in ["network", "internet", "wifi", "connection"]):
        return {"category": "network", "confidence": 0.9, "source": "rule"}

    #  3. BILLING (expand keywords)
    if any(w in text for w in ["payment", "money", "refund", "charged", "upi", "pricing", "deducted"]):
        return {"category": "billing", "confidence": 0.9, "source": "rule"}

    #  4. ACCOUNT (new category fix)
    if any(w in text for w in ["profile", "account", "settings", "delete"]):
        return {"category": "account", "confidence": 0.9, "source": "rule"}

    #  5. TECHNICAL (fallback)
    if any(w in text for w in ["error", "bug", "crash", "not working", "freeze", "broken", "fails"]):
        return {"category": "technical", "confidence": 0.9, "source": "rule"}
    
    

    return None
#  AI  #

def call_groq(prompt):
    if not GROQ_API_KEY:
        return None

    try:
        res = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "Return ONLY JSON"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            timeout=10,
        )

        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        else:
            print("GROQ ERROR:", res.status_code, res.text)

    except Exception as e:
        print("GROQ ERROR:", e)

    return None


def ai_classification(text):
    prompt = f"""
Classify ticket into:
billing, technical, authentication, network

Return JSON:
{{"category":"...", "priority":"..."}}

Ticket: "{text}"
"""

    result = call_groq(prompt)

    try:
        return json.loads(result)
    except:
        print("JSON ERROR:", result)
        return None

#  LOGGING  #

def log_prediction(text, result):
    TicketPredictionLog.objects.create(
        text=text,
        predicted_category=result["category"],
        predicted_priority=result["priority"],
        source=result["source"],
        confidence=result.get("confidence", 0)
    )

# MAIN PIPELINE  #

def predict_ticket(text):
    clean = preprocess(text)

    # STEP 1: RULE
    rule = rule_engine(clean)

    if rule:
        final = rule

    else:
        # STEP 2: AI
        ai = ai_classification(text)

        if ai:
            final = {
                "category": ai.get("category", "other"),
                "confidence": 0.7,
                "source": "AI"
            }
        else:
            final = {
                "category": "other",
                "confidence": 0.5,
                "source": "fallback"
            }

    if final["category"] not in ["billing", "technical", "authentication", "network", "account"]:
        final["category"] = "other"
    final["priority"] = get_priority(text)

    log_prediction(text, final)

    return final