"""
Spam detection for comments.

Detects spam based on:
1. Keyword blacklist (Chinese + English spam keywords)
2. Link count (too many links = likely spam)
3. Excessive caps / special characters
4. Comment length anomalies
"""

import re

# ── Blacklists ──────────────────────────────────
SPAM_KEYWORDS = [
    "免费", "赚钱", "点击", "优惠", "折扣", "代购", "刷单",
    "buy now", "click here", "free money", "cheap", "discount",
    "casino", "loan", "viagra", "cialis", "crypto currency",
    "seo services", "web design services", "buy followers",
    "http://", "https://", "www.",
]

# Keywords that suggest spam when combined with links
SUSPICIOUS_PATTERNS = [
    r"(?i)(buy|purchase|order)\s+(now|today|online)",
    r"(?i)(click|visit)\s+(here|this|my)\s+(site|blog|website)",
    r"(?i)(make|earn|get)\s+(money|cash|dollars)\s+(online|fast|quick)",
    r"(?i)(free|cheap)\s+(shipping|offer|sample)",
    r"(?i)\d{1,3}\s*(day|week|month)\s*(trial|guarantee)",
]


def detect_spam(content: str) -> tuple[bool, str]:
    """
    Analyze comment content for spam indicators.

    Returns:
        (is_spam: bool, reason: str) — True if likely spam, with explanation.
    """
    reasons = []

    # 1. Keyword check
    keyword_hits = [kw for kw in SPAM_KEYWORDS if kw.lower() in content.lower()]
    if keyword_hits:
        reasons.append(f"Spam keywords detected: {', '.join(keyword_hits[:5])}")

    # 2. Link count
    urls = re.findall(r"https?://[^\s]+", content)
    if len(urls) >= 3:
        reasons.append(f"Too many links ({len(urls)} found, max 2 allowed)")

    # 3. Suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, content):
            reasons.append(f"Suspicious pattern matched: {pattern}")
            break

    # 4. Excessive caps (more than 60% uppercase for non-short messages)
    if len(content) > 30:
        alpha_chars = [c for c in content if c.isalpha()]
        if alpha_chars:
            caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
            if caps_ratio > 0.6:
                reasons.append(f"Excessive capitalization ({caps_ratio:.0%})")

    # 5. Repeated characters (e.g., "goooood!!!!!!!!")
    if re.search(r"([!?])\1{4,}", content):
        reasons.append("Excessive repeated punctuation")

    # 6. Too short with links
    if len(content.strip()) < 20 and urls:
        reasons.append("Very short content with links")

    is_spam = len(reasons) >= 1
    reason = "; ".join(reasons) if reasons else "No spam indicators"

    return is_spam, reason


def is_probable_spam(content: str, user_is_new: bool = False) -> bool:
    """
    Quick check — returns True if comment should be auto-flagged.

    New users (registered < 24h) get stricter filtering.
    """
    spam, reason = detect_spam(content)
    if spam:
        return True

    # New user + any link = flag for review
    if user_is_new and re.search(r"https?://", content):
        return True

    return False
