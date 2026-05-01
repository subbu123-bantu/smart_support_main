FEW_SHOT_EXAMPLES = [
    {
        "text": "My payment failed but money was deducted from my bank account",
        "category": "billing",
        "confidence": 0.88,
    },
    {
        "text": "I was charged twice for the same subscription renewal",
        "category": "billing",
        "confidence": 0.91,
    },
    {
        "text": "Refund is not showing in my account after cancellation",
        "category": "billing",
        "confidence": 0.89,
    },
    {
        "text": "Invoice generated with the wrong amount this month",
        "category": "billing",
        "confidence": 0.87,
    },
    {
        "text": "Server error 500 while submitting ticket",
        "category": "technical",
        "confidence": 0.9,
    },
    {
        "text": "App crashes every time I try to upload a document",
        "category": "technical",
        "confidence": 0.9,
    },
    {
        "text": "The dashboard page is blank after I log in",
        "category": "technical",
        "confidence": 0.87,
    },
    {
        "text": "File attachment button is not working in the browser",
        "category": "technical",
        "confidence": 0.85,
    },
    {
        "text": "I cannot login with my correct password",
        "category": "authentication",
        "confidence": 0.88,
    },
    {
        "text": "OTP is not arriving on my phone for sign in",
        "category": "authentication",
        "confidence": 0.9,
    },
    {
        "text": "My account keeps saying invalid credentials even though the password is correct",
        "category": "authentication",
        "confidence": 0.89,
    },
    {
        "text": "Password reset link expired immediately after I opened it",
        "category": "authentication",
        "confidence": 0.86,
    },
    {
        "text": "Unable to connect to server due to timeout",
        "category": "network",
        "confidence": 0.86,
    },
    {
        "text": "The app disconnects repeatedly when I am on office wifi",
        "category": "network",
        "confidence": 0.87,
    },
    {
        "text": "Request fails because of connection timeout and high latency",
        "category": "network",
        "confidence": 0.89,
    },
    {
        "text": "I cannot reach the service from my network but other websites work",
        "category": "network",
        "confidence": 0.85,
    },
    {
        "text": "Please change my registered mobile number",
        "category": "account",
        "confidence": 0.83,
    },
    {
        "text": "I need to update the email address linked to my account",
        "category": "account",
        "confidence": 0.86,
    },
    {
        "text": "Please delete my profile and all account information",
        "category": "account",
        "confidence": 0.88,
    },
    {
        "text": "How can I change my contact number and profile details",
        "category": "account",
        "confidence": 0.84,
    },
    {
        "text": "Good morning",
        "category": "other",
        "confidence": 0.25,
    },
    {
        "text": "Hello team",
        "category": "other",
        "confidence": 0.22,
    },
    {
        "text": "Can you help me",
        "category": "other",
        "confidence": 0.28,
    },
    {
        "text": "I have an issue",
        "category": "other",
        "confidence": 0.27,
    },
    {
        "text": "Thanks for the quick support yesterday",
        "category": "other",
        "confidence": 0.2,
    },
]


def format_examples_for_prompt() -> str:
    rendered = []
    for example in FEW_SHOT_EXAMPLES:
        rendered.append(
            "\n".join(
                [
                    f'Ticket: {example["text"]}',
                    "{",
                    f'  "category": "{example["category"]}",',
                    f'  "confidence": {example["confidence"]:.2f}',
                    "}",
                ]
            )
        )
    return "\n\n".join(rendered)
