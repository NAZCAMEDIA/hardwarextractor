"""Anti-bot detection utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class AntiBotResult:
    """Result of anti-bot detection.

    Attributes:
        blocked: Whether the request was blocked
        reason: Reason for blocking (if blocked)
        confidence: Confidence level of detection (0.0-1.0)
    """
    blocked: bool
    reason: Optional[str] = None
    confidence: float = 1.0


class AntiBotDetector:
    """Detects anti-bot protection in HTTP responses."""

    # Patterns to detect various anti-bot measures
    # (pattern, reason, confidence)
    CONTENT_PATTERNS = [
        # Cloudflare
        (r"checking your browser", "cloudflare_challenge", 0.95),
        (r"cf-browser-verification", "cloudflare_challenge", 0.95),
        (r"_cf_chl_opt", "cloudflare_challenge", 0.90),
        (r"cloudflare", "cloudflare_generic", 0.70),
        (r"ray id", "cloudflare_generic", 0.60),

        # Generic CAPTCHA
        (r"captcha", "captcha", 0.85),
        (r"robot.*check", "robot_check", 0.80),
        (r"verify.*human", "human_verification", 0.85),
        (r"are you a robot", "robot_check", 0.90),
        (r"prove.*human", "human_verification", 0.85),
        (r"recaptcha", "recaptcha", 0.95),
        (r"hcaptcha", "hcaptcha", 0.95),

        # Rate limiting
        (r"rate.?limit", "rate_limit", 0.90),
        (r"too many requests", "rate_limit", 0.95),
        (r"slow down", "rate_limit", 0.70),
        (r"try again later", "rate_limit", 0.60),

        # Access denied
        (r"access.?denied", "access_denied", 0.85),
        (r"403 forbidden", "access_denied", 0.95),
        (r"permission denied", "access_denied", 0.80),
        (r"blocked", "blocked", 0.70),

        # Bot detection
        (r"bot.?detected", "bot_detected", 0.95),
        (r"automated.?access", "bot_detected", 0.90),
        (r"suspicious.?activity", "bot_detected", 0.80),

        # JavaScript challenge
        (r"enable.?javascript", "js_required", 0.85),
        (r"javascript.?required", "js_required", 0.90),
        (r"please.?enable.?js", "js_required", 0.85),
    ]

    # HTTP status codes that indicate blocking
    BLOCKED_STATUS_CODES = {
        403: "http_forbidden",
        429: "http_rate_limit",
        503: "http_service_unavailable",
        520: "cloudflare_520",
        521: "cloudflare_521",
        522: "cloudflare_522",
        523: "cloudflare_523",
        524: "cloudflare_524",
    }

    @classmethod
    def detect(cls, html: str, status_code: int = 200) -> AntiBotResult:
        """Detect if a response indicates anti-bot blocking.

        Args:
            html: The HTML content of the response
            status_code: HTTP status code of the response

        Returns:
            AntiBotResult indicating if blocked and why
        """
        # Check status code first
        if status_code in cls.BLOCKED_STATUS_CODES:
            return AntiBotResult(
                blocked=True,
                reason=cls.BLOCKED_STATUS_CODES[status_code],
                confidence=0.95
            )

        # Check content patterns
        if not html:
            return AntiBotResult(blocked=False)

        html_lower = html.lower()

        # If this looks like a real product page, don't mark as blocked
        # even if it mentions cloudflare (many sites use CF as CDN)
        if cls.is_likely_product_page(html):
            return AntiBotResult(blocked=False)

        # Check for very short responses (likely blocked)
        if len(html.strip()) < 500:
            # Short response might be a challenge page
            for pattern, reason, confidence in cls.CONTENT_PATTERNS:
                if re.search(pattern, html_lower):
                    return AntiBotResult(
                        blocked=True,
                        reason=reason,
                        confidence=min(confidence + 0.1, 1.0)  # Boost for short response
                    )

        # Only check high-confidence patterns for longer pages
        # Skip generic patterns like "cloudflare" which cause false positives
        HIGH_CONFIDENCE_PATTERNS = [
            (r"checking your browser", "cloudflare_challenge", 0.95),
            (r"cf-browser-verification", "cloudflare_challenge", 0.95),
            (r"_cf_chl_opt", "cloudflare_challenge", 0.90),
            (r"recaptcha", "recaptcha", 0.95),
            (r"hcaptcha", "hcaptcha", 0.95),
            (r"are you a robot", "robot_check", 0.90),
            (r"bot.?detected", "bot_detected", 0.95),
            (r"too many requests", "rate_limit", 0.95),
            (r"403 forbidden", "access_denied", 0.95),
        ]

        for pattern, reason, confidence in HIGH_CONFIDENCE_PATTERNS:
            if re.search(pattern, html_lower):
                return AntiBotResult(
                    blocked=True,
                    reason=reason,
                    confidence=confidence
                )

        # Check for empty body with normal status
        if status_code == 200 and len(html.strip()) < 100:
            return AntiBotResult(
                blocked=True,
                reason="empty_response",
                confidence=0.70
            )

        return AntiBotResult(blocked=False)

    @classmethod
    def is_likely_product_page(cls, html: str) -> bool:
        """Check if the HTML looks like a product page (not a challenge).

        Args:
            html: The HTML content

        Returns:
            True if this looks like actual product content
        """
        if not html or len(html) < 1000:
            return False

        html_lower = html.lower()

        # Positive signals that this is a real product page
        product_signals = [
            r"specifications",
            r"spec[s]?\s*:",
            r"features",
            r"product",
            r"model",
            r"price",
            r"<table",
            r"data-spec",
            r"tech.?specs",
        ]

        signals_found = sum(
            1 for pattern in product_signals
            if re.search(pattern, html_lower)
        )

        return signals_found >= 2

    @classmethod
    def get_block_severity(cls, result: AntiBotResult) -> str:
        """Get the severity level of a block.

        Args:
            result: The anti-bot detection result

        Returns:
            "none", "soft", or "hard"
        """
        if not result.blocked:
            return "none"

        hard_blocks = {
            "cloudflare_challenge",
            "recaptcha",
            "hcaptcha",
            "http_forbidden",
            "bot_detected",
        }

        if result.reason in hard_blocks:
            return "hard"

        return "soft"

    @classmethod
    def is_antibot_error(cls, error_msg: str) -> bool:
        """Check if an error message indicates anti-bot protection.

        Args:
            error_msg: The error message string

        Returns:
            True if the error appears to be anti-bot related
        """
        if not error_msg:
            return False

        error_lower = error_msg.lower()

        antibot_keywords = [
            "cloudflare",
            "captcha",
            "rate limit",
            "rate-limit",
            "ratelimit",
            "too many requests",
            "bot detected",
            "access denied",
            "403 forbidden",
            "blocked",
            "challenge",
            "verify",
            "robot",
            "human verification",
        ]

        return any(keyword in error_lower for keyword in antibot_keywords)
