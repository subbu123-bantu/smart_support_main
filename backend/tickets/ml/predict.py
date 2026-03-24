import os
import json
import re
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Constants
CATEGORIES = ["technical", "billing", "authentication", "network", "account", "other"]
PRIORITIES = ["low", "medium", "high", "urgent"]
CONFIDENCE_THRESHOLD = 0.8


def preprocess(text):
    return text.lower().strip()

#RULE-BASED CLASSIFICATION
def rule_based_classification(text):
    text_lower = preprocess(text)

    if any(word in text_lower for word in ["crash", "error 500", "server down", "data loss", "security breach"]):
        return build_response("technical", "urgent", 0.95, 0.95)
    
    if any(w in text_lower for w in ["deducted", "charged", "debited", "refund", "payment failed"]):
        return build_response("billing", "high", 0.95, 0.95)
    
    if any(word in text_lower for word in ["login", "password", "otp", "authentication", "2fa", "mfa", "access denied", "account locked"]):
        return build_response("authentication", "high", 0.9, 0.85)

    if any(word in text_lower for word in ["slow", "internet", "wifi", "network", "connection", "latency", "disconnect"]):
        return build_response("network", "medium", 0.85, 0.75)

    if any(word in text_lower for word in ["account", "profile", "update details", "change email","delete account", "account locked", "account blocked","account suspended", "account issue"]):
        return build_response("account", "medium", 0.9, 0.75)
    
    if any(w in text_lower for w in ["price", "cost", "plan"]) and not any(w in text_lower for w in ["not working", "failed", "error"]):
        return build_response("billing", "low", 0.8, 0.6)


    return None  # fallback to AI



#AI CLASSIFICATION (GROQ)

def ai_classification(text):
    prompt = f"""
Return STRICT JSON ONLY. No explanation.

Format:
{{
  "category": "...",
  "priority": "..."
}}

Valid categories: {CATEGORIES}
Valid priorities: {PRIORITIES}

Ticket: {text}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        # Clean possible formatting issues
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError("Invalid JSON")

        category = data.get("category", "other")
        priority = data.get("priority", "medium")

        # Safety check
        if category not in CATEGORIES:
            category = "other"
        if priority not in PRIORITIES:
            priority = "medium"

    except Exception as e:
        print("AI Error:", e)
        category = "other"
        priority = "medium"

    return category, priority


#CONFIDENCE CALCULATION

def calculate_confidence(category, priority):
    priority_scores = {
        "urgent": 0.95,
        "high": 0.85,
        "medium": 0.7,
        "low": 0.6
    }

    if category == "account":
        category_score = 0.85
    elif category != "other":
        category_score = 0.8
    else:
        category_score = 0.6
    priority_score = priority_scores.get(priority, 0.6)

    return category_score, priority_score



#RESPONSE BUILDER
def build_response(category, priority, cat_score, pri_score,source="rule"):
    auto_assign = cat_score >= CONFIDENCE_THRESHOLD and pri_score >= CONFIDENCE_THRESHOLD

    return {
        "predicted_category": category,
        "predicted_priority": priority,
        "category_confidence": round(cat_score, 2),
        "priority_confidence": round(pri_score, 2),
        "auto_assign": auto_assign,
        "source": source
    }

#MAIN FUNCTION
def predict_ticket(text):
    if not text:
        return build_response("other", "low", 0.5, 0.5)

    # Step 1: Rule-based
    rule_result = rule_based_classification(text)
    if rule_result:
        print("Rule-based classification used")
        return rule_result

    # Step 2: AI fallback
    category, priority = ai_classification(text)

    # Step 3: Confidence scoring
    cat_score, pri_score = calculate_confidence(category, priority)

    # Step 4: Build final response
    result = build_response(category, priority, cat_score, pri_score,source="AI")

    if result["source"] == "ai":
        result["category_confidence"] -= 0.1
        result["priority_confidence"] -= 0.1

    # Debug logs
    print("\n--- AI Prediction ---")
    print(f"Text: {text}")
    print(f"Category: {category} ({cat_score})")
    print(f"Priority: {priority} ({pri_score})")
    print(f"Auto Assign: {result['auto_assign']}")
    print("--------------------\n")

    return result