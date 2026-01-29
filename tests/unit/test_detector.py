"""Tests for scrape/engines/detector.py - Anti-bot detection."""

import pytest
from hardwarextractor.scrape.engines.detector import AntiBotDetector, AntiBotResult


class TestAntiBotResult:
    """Test AntiBotResult dataclass."""

    def test_result_not_blocked(self):
        """Test creating a non-blocked result."""
        result = AntiBotResult(blocked=False)
        assert result.blocked is False
        assert result.reason is None
        assert result.confidence == 1.0

    def test_result_blocked(self):
        """Test creating a blocked result."""
        result = AntiBotResult(blocked=True, reason="cloudflare", confidence=0.95)
        assert result.blocked is True
        assert result.reason == "cloudflare"
        assert result.confidence == 0.95

    def test_result_defaults(self):
        """Test default values."""
        result = AntiBotResult(blocked=True)
        assert result.reason is None
        assert result.confidence == 1.0


class TestAntiBotDetector:
    """Test AntiBotDetector class."""

    def test_detect_cloudflare_challenge(self):
        """Test detecting Cloudflare challenge."""
        html = """
        <html>
        <head><title>Just a moment...</title></head>
        <body>
        <div id="cf-challenge-running">Checking your browser before accessing</div>
        </body>
        </html>
        """
        result = AntiBotDetector.detect(html)
        assert result.blocked is True
        assert "cloudflare" in result.reason.lower()

    def test_detect_captcha(self):
        """Test detecting CAPTCHA."""
        html = """
        <html>
        <body>
        <div class="g-recaptcha" data-sitekey="xxx">reCAPTCHA</div>
        </body>
        </html>
        """
        result = AntiBotDetector.detect(html)
        assert result.blocked is True
        assert "captcha" in result.reason.lower() or "recaptcha" in result.reason.lower()

    def test_detect_hcaptcha(self):
        """Test detecting hCaptcha."""
        html = """
        <html>
        <body>
        <div class="h-captcha" data-sitekey="xxx">hCaptcha here</div>
        </body>
        </html>
        """
        result = AntiBotDetector.detect(html)
        assert result.blocked is True
        assert "captcha" in result.reason.lower() or "hcaptcha" in result.reason.lower()

    def test_detect_access_denied(self):
        """Test detecting access denied page."""
        html = """
        <html>
        <head><title>Access Denied</title></head>
        <body>
        <h1>Access Denied</h1>
        <p>You don't have permission to access this resource.</p>
        </body>
        </html>
        """
        result = AntiBotDetector.detect(html)
        assert result.blocked is True
        assert "denied" in result.reason.lower() or "access" in result.reason.lower()

    def test_detect_403_status_code(self):
        """Test detecting 403 Forbidden status code."""
        html = "<html><body>Forbidden</body></html>"
        result = AntiBotDetector.detect(html, status_code=403)
        assert result.blocked is True
        assert "forbidden" in result.reason.lower()

    def test_detect_429_status_code(self):
        """Test detecting 429 rate limit status code."""
        html = "<html><body>Rate limited</body></html>"
        result = AntiBotDetector.detect(html, status_code=429)
        assert result.blocked is True
        assert "rate" in result.reason.lower()

    def test_detect_503_status_code(self):
        """Test detecting 503 service unavailable status code."""
        html = "<html><body>Service unavailable</body></html>"
        result = AntiBotDetector.detect(html, status_code=503)
        assert result.blocked is True

    def test_normal_content_not_detected(self):
        """Test that normal content is not flagged."""
        html = """
        <html>
        <head><title>Product Page - Corsair Vengeance</title></head>
        <body>
        <h1>Corsair Vengeance LPX 32GB</h1>
        <div class="specs">
            <p>Capacity: 32GB (2x16GB)</p>
            <p>Speed: 3200MHz</p>
            <p>Type: DDR4</p>
            <p>Latency: CL16</p>
        </div>
        <table>
            <tr><th>Feature</th><th>Value</th></tr>
            <tr><td>Voltage</td><td>1.35V</td></tr>
        </table>
        </body>
        </html>
        """
        result = AntiBotDetector.detect(html)
        assert result.blocked is False

    def test_detect_rate_limit(self):
        """Test detecting rate limit message."""
        html = """
        <html>
        <body>
        <h1>Too Many Requests</h1>
        <p>You have been rate limited. Please try again later.</p>
        </body>
        </html>
        """
        result = AntiBotDetector.detect(html)
        assert result.blocked is True
        assert "rate" in result.reason.lower()

    def test_detect_robot_check(self):
        """Test detecting robot check page."""
        html = """
        <html>
        <body>
        <h1>Are you a robot?</h1>
        <p>Please verify you are human to continue.</p>
        </body>
        </html>
        """
        result = AntiBotDetector.detect(html)
        assert result.blocked is True

    def test_empty_content(self):
        """Test with empty content."""
        result = AntiBotDetector.detect("")
        assert result.blocked is False

    def test_none_content(self):
        """Test with None content."""
        result = AntiBotDetector.detect(None)
        assert result.blocked is False

    def test_detect_cloudflare_status_codes(self):
        """Test Cloudflare-specific status codes."""
        for status in [520, 521, 522, 523, 524]:
            result = AntiBotDetector.detect("<html></html>", status_code=status)
            assert result.blocked is True
            assert "cloudflare" in result.reason.lower()

    def test_short_empty_response_200(self):
        """Test empty response with 200 status code."""
        result = AntiBotDetector.detect("<html></html>", status_code=200)
        assert result.blocked is True
        assert result.reason == "empty_response"


class TestIsLikelyProductPage:
    """Test is_likely_product_page method."""

    def test_product_page_with_specs(self):
        """Test detecting a product page with specifications."""
        html = """
        <html>
        <head><title>Intel Core i7-12700K Specifications</title></head>
        <body>
        <h1>Intel Core i7-12700K</h1>
        <div class="specifications">
            <h2>Technical Specifications</h2>
            <table class="specs-table" data-spec="true">
                <tr><th>Feature</th><th>Value</th></tr>
                <tr><td>Cores</td><td>12</td></tr>
                <tr><td>Threads</td><td>20</td></tr>
                <tr><td>Base Clock</td><td>3.6 GHz</td></tr>
                <tr><td>Boost Clock</td><td>5.0 GHz</td></tr>
                <tr><td>TDP</td><td>125W</td></tr>
            </table>
        </div>
        <div class="features">
            <h3>Key Features</h3>
            <ul>
                <li>Alder Lake Architecture</li>
                <li>DDR5 Support</li>
            </ul>
        </div>
        <div class="product-info">
            <p>Model: BX8071512700K</p>
            <p>Price: $409.99</p>
        </div>
        </body>
        </html>
        """
        assert AntiBotDetector.is_likely_product_page(html) is True

    def test_short_content_not_product_page(self):
        """Test that short content is not a product page."""
        html = "<html><body>Hello</body></html>"
        assert AntiBotDetector.is_likely_product_page(html) is False

    def test_empty_not_product_page(self):
        """Test that empty content is not a product page."""
        assert AntiBotDetector.is_likely_product_page("") is False
        assert AntiBotDetector.is_likely_product_page(None) is False

    def test_challenge_page_not_product(self):
        """Test that challenge page is not a product page."""
        html = """
        <html>
        <body>
        <div>Please verify you are human</div>
        <div class="challenge">Complete the CAPTCHA</div>
        </body>
        </html>
        """
        assert AntiBotDetector.is_likely_product_page(html) is False


class TestGetBlockSeverity:
    """Test get_block_severity method."""

    def test_not_blocked_severity(self):
        """Test severity for non-blocked result."""
        result = AntiBotResult(blocked=False)
        assert AntiBotDetector.get_block_severity(result) == "none"

    def test_hard_block_cloudflare(self):
        """Test hard block for Cloudflare challenge."""
        result = AntiBotResult(blocked=True, reason="cloudflare_challenge")
        assert AntiBotDetector.get_block_severity(result) == "hard"

    def test_hard_block_recaptcha(self):
        """Test hard block for reCAPTCHA."""
        result = AntiBotResult(blocked=True, reason="recaptcha")
        assert AntiBotDetector.get_block_severity(result) == "hard"

    def test_hard_block_hcaptcha(self):
        """Test hard block for hCaptcha."""
        result = AntiBotResult(blocked=True, reason="hcaptcha")
        assert AntiBotDetector.get_block_severity(result) == "hard"

    def test_hard_block_forbidden(self):
        """Test hard block for HTTP forbidden."""
        result = AntiBotResult(blocked=True, reason="http_forbidden")
        assert AntiBotDetector.get_block_severity(result) == "hard"

    def test_hard_block_bot_detected(self):
        """Test hard block for bot detected."""
        result = AntiBotResult(blocked=True, reason="bot_detected")
        assert AntiBotDetector.get_block_severity(result) == "hard"

    def test_soft_block_rate_limit(self):
        """Test soft block for rate limit."""
        result = AntiBotResult(blocked=True, reason="rate_limit")
        assert AntiBotDetector.get_block_severity(result) == "soft"

    def test_soft_block_js_required(self):
        """Test soft block for JS required."""
        result = AntiBotResult(blocked=True, reason="js_required")
        assert AntiBotDetector.get_block_severity(result) == "soft"

    def test_soft_block_empty_response(self):
        """Test soft block for empty response."""
        result = AntiBotResult(blocked=True, reason="empty_response")
        assert AntiBotDetector.get_block_severity(result) == "soft"


class TestAntiBotPatterns:
    """Test specific anti-bot patterns detection."""

    def test_cloudflare_browser_check(self):
        """Test Cloudflare browser verification pattern."""
        result = AntiBotDetector.detect("Checking your browser before accessing the site")
        assert result.blocked is True
        assert "cloudflare" in result.reason.lower()

    def test_cloudflare_cf_browser_verification(self):
        """Test cf-browser-verification pattern."""
        result = AntiBotDetector.detect('<div class="cf-browser-verification">Please wait</div>')
        assert result.blocked is True

    def test_robot_check_pattern(self):
        """Test robot check pattern."""
        result = AntiBotDetector.detect("Please complete the robot check to continue")
        assert result.blocked is True
        assert "robot" in result.reason.lower()

    def test_prove_human_pattern(self):
        """Test prove you are human pattern."""
        result = AntiBotDetector.detect("Please prove you are human")
        assert result.blocked is True
        assert "human" in result.reason.lower()

    def test_bot_detected_pattern(self):
        """Test bot detected pattern."""
        result = AntiBotDetector.detect("Bot detected - automated access is not allowed")
        assert result.blocked is True
        assert "bot" in result.reason.lower()

    def test_enable_javascript_pattern(self):
        """Test enable JavaScript pattern."""
        result = AntiBotDetector.detect("Please enable JavaScript to continue")
        assert result.blocked is True
        assert "js" in result.reason.lower()

    def test_blocked_pattern(self):
        """Test generic blocked pattern."""
        result = AntiBotDetector.detect("Your access has been blocked")
        assert result.blocked is True

    def test_suspicious_activity_pattern(self):
        """Test suspicious activity pattern."""
        result = AntiBotDetector.detect("Suspicious activity detected from your IP")
        assert result.blocked is True


class TestContentPatternConfidence:
    """Test confidence levels for different patterns."""

    def test_high_confidence_recaptcha(self):
        """Test high confidence for reCAPTCHA detection."""
        result = AntiBotDetector.detect("This page requires reCAPTCHA verification")
        assert result.blocked is True
        assert result.confidence >= 0.9

    def test_high_confidence_cloudflare(self):
        """Test high confidence for Cloudflare challenge."""
        result = AntiBotDetector.detect("Checking your browser before accessing")
        assert result.blocked is True
        assert result.confidence >= 0.9

    def test_medium_confidence_generic(self):
        """Test medium confidence for generic patterns."""
        result = AntiBotDetector.detect("Access denied - permission required")
        assert result.blocked is True
        assert result.confidence >= 0.7
