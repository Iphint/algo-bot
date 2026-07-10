import time
import pytest
from discord_bot.spam_filter import (
    contains_suspicious_links,
    contains_shortened_links,
    is_all_caps,
    check_spam,
    SpamTracker,
    SCAM_DOMAINS,
    SPAM_PATTERNS,
)


class FakeMessage:
    def __init__(self, author_id=1, content="", mention_everyone=False, mentions=None, role_mentions=None):
        self.author = type("obj", (object,), {"id": author_id})
        self.content = content
        self.mention_everyone = mention_everyone
        self.mentions = mentions or []
        self.role_mentions = role_mentions or []


# ─── contains_suspicious_links ───────────────────────────────────────────────

class TestContainsSuspiciousLinks:
    def test_returns_scam_domains_found(self):
        result = contains_suspicious_links("Check this https://discord-nitro.xyz/free")
        assert "discord-nitro.xyz" in result

    def test_returns_multiple_domains(self):
        url = "https://discord-nitro.xyz and http://eth-giveaway.com"
        result = contains_suspicious_links(url)
        assert "discord-nitro.xyz" in result
        assert "eth-giveaway.com" in result

    def test_returns_empty_for_safe_url(self):
        result = contains_suspicious_links("https://google.com")
        assert result == []

    def test_returns_empty_for_no_url(self):
        result = contains_suspicious_links("hello world")
        assert result == []

    def test_returns_empty_for_empty_string(self):
        result = contains_suspicious_links("")
        assert result == []

    def test_every_scam_domain_is_detected(self):
        for domain in SCAM_DOMAINS:
            result = contains_suspicious_links(f"https://{domain}/xyz")
            assert domain in result, f"{domain} should be detected"

    def test_case_insensitive(self):
        result = contains_suspicious_links("HTTPS://DISCORD-NITRO.XYZ/free")
        assert "discord-nitro.xyz" in result

    def test_no_false_positive_for_safe_domain(self):
        result = contains_suspicious_links("https://discord.com/channels/123")
        assert result == []


# ─── contains_shortened_links ────────────────────────────────────────────────

class TestContainsShortenedLinks:
    def test_detects_bitly(self):
        result = contains_shortened_links("https://bit.ly/3xYz123")
        assert any("bit.ly" in r for r in result)

    def test_detects_tinyurl(self):
        result = contains_shortened_links("http://tinyurl.com/abc123")
        assert any("tinyurl" in r for r in result)

    def test_returns_empty_for_normal_url(self):
        result = contains_shortened_links("https://example.com/page")
        assert result == []

    def test_returns_empty_for_no_url(self):
        result = contains_shortened_links("just text")
        assert result == []

    def test_empty_string(self):
        result = contains_shortened_links("")
        assert result == []


# ─── is_all_caps ─────────────────────────────────────────────────────────────

class TestIsAllCaps:
    def test_all_caps_long(self):
        assert is_all_caps("HELLO THIS IS ALL CAPS") is True

    def test_mixed_case_below_threshold(self):
        assert is_all_caps("Hello This Is Normal") is False

    def test_too_short(self):
        assert is_all_caps("HI") is False

    def test_no_letters(self):
        assert is_all_caps("12345 67890 !!!") is False

    def test_empty_string(self):
        assert is_all_caps("") is False

    def test_custom_threshold(self):
        assert is_all_caps("ABCdef", min_length=3, caps_ratio=0.5) is True
        assert is_all_caps("ABCdef", min_length=3, caps_ratio=0.6) is False


# ─── SpamTracker ─────────────────────────────────────────────────────────────

class TestSpamTracker:
    def test_record_and_count(self):
        tracker = SpamTracker()
        tracker.record_message(1, "hello")
        assert tracker.get_recent_message_count(1, window=5.0) == 1

    def test_count_multiple_messages(self):
        tracker = SpamTracker()
        tracker.record_message(1, "a")
        tracker.record_message(1, "b")
        tracker.record_message(1, "c")
        assert tracker.get_recent_message_count(1, window=5.0) == 3

    def test_old_messages_not_counted(self):
        tracker = SpamTracker()
        tracker.record_message(1, "old")
        ts = list(tracker.message_times[1])[0]
        old_ts = ts - 10.0
        tracker.message_times[1].append(old_ts)
        assert tracker.get_recent_message_count(1, window=5.0) == 1

    def test_duplicate_count(self):
        tracker = SpamTracker()
        tracker.record_message(1, "spam")
        tracker.record_message(1, "spam")
        assert tracker.get_duplicate_count(1, "spam") == 2

    def test_duplicate_count_no_match(self):
        tracker = SpamTracker()
        tracker.record_message(1, "hello")
        assert tracker.get_duplicate_count(1, "world") == 0

    def test_duplicate_empty_content(self):
        tracker = SpamTracker()
        tracker.record_message(1, "")
        assert tracker.get_duplicate_count(1, "") == 0

    def test_is_duplicate_threshold(self):
        tracker = SpamTracker()
        tracker.record_message(1, "spam")
        tracker.record_message(1, "spam")
        assert tracker.is_duplicate(1, "spam", threshold=2) is True

    def test_separate_users(self):
        tracker = SpamTracker()
        tracker.record_message(1, "hello")
        tracker.record_message(2, "world")
        assert tracker.get_recent_message_count(1, window=5.0) == 1
        assert tracker.get_recent_message_count(2, window=5.0) == 1

    def test_get_consecutive_count(self):
        tracker = SpamTracker()
        now = time.time()
        tracker.message_times[1].append(now - 0.5)
        tracker.message_times[1].append(now - 0.3)
        tracker.message_times[1].append(now - 0.1)
        assert tracker.get_consecutive_count(1, window=2.0) == 3

    def test_consecutive_count_excludes_old(self):
        tracker = SpamTracker()
        now = time.time()
        tracker.message_times[1].append(now - 10.0)
        tracker.message_times[1].append(now - 9.0)
        assert tracker.get_consecutive_count(1, window=2.0) == 0

    def test_maxlen_50(self):
        tracker = SpamTracker()
        for i in range(60):
            tracker.record_message(1, str(i))
        assert len(tracker.message_times[1]) <= 50


# ─── check_spam ──────────────────────────────────────────────────────────────

class TestCheckSpam:
    def setup_method(self):
        from discord_bot.spam_filter import tracker as global_tracker
        global_tracker.message_times.clear()
        global_tracker.last_messages.clear()

    def test_no_violations_for_normal_message(self):
        msg = FakeMessage(author_id=99, content="hello, how are you?")
        violations = check_spam(msg)
        assert violations == []

    def test_detects_rapid_fire(self):
        msg = FakeMessage(author_id=100, content="msg")
        for _ in range(4):
            check_spam(msg)
        violations = check_spam(msg)
        types = [v["type"] for v in violations]
        assert "rapid_fire" in types

    def test_detects_duplicate(self):
        msg = FakeMessage(author_id=101, content="spam spam spam")
        for _ in range(4):
            check_spam(msg)
        violations = check_spam(msg)
        types = [v["type"] for v in violations]
        assert "duplicate" in types

    def test_detects_suspicious_link(self):
        msg = FakeMessage(author_id=102, content="free nitro at https://discord-nitro.xyz")
        violations = check_spam(msg)
        types = [v["type"] for v in violations]
        assert "suspicious_link" in types

    def test_detects_spam_pattern(self):
        msg = FakeMessage(author_id=103, content="free nitro click here")
        violations = check_spam(msg)
        types = [v["type"] for v in violations]
        assert "spam_pattern" in types

    def test_detects_mass_mention(self):
        msg = FakeMessage(
            author_id=104,
            content="@everyone look at this",
            mention_everyone=True,
        )
        violations = check_spam(msg)
        types = [v["type"] for v in violations]
        assert "mass_mention" in types

    def test_detects_all_caps(self):
        msg = FakeMessage(author_id=105, content="THIS IS VERY LOUD MESSAGE HERE")
        violations = check_spam(msg)
        types = [v["type"] for v in violations]
        assert "all_caps" in types

    def test_multiple_violations_at_once(self):
        msg = FakeMessage(
            author_id=106,
            content="FREE NITRO CLICK HERE https://discord-nitro.xyz",
            mention_everyone=True,
        )
        violations = check_spam(msg)
        types = {v["type"] for v in violations}
        assert "suspicious_link" in types
        assert "spam_pattern" in types
        assert "mass_mention" in types

    def test_rapid_fire_severity_medium_at_4(self):
        msg = FakeMessage(author_id=107, content="x")
        for _ in range(4):
            check_spam(msg)
        violations = check_spam(msg)
        rf = [v for v in violations if v["type"] == "rapid_fire"]
        assert rf
        assert rf[0]["severity"] == "medium"

    def test_rapid_fire_severity_high_at_8(self):
        msg = FakeMessage(author_id=108, content="x")
        for _ in range(8):
            check_spam(msg)
        violations = check_spam(msg)
        rf = [v for v in violations if v["type"] == "rapid_fire"]
        assert rf
        assert rf[0]["severity"] == "high"

    def test_mass_mention_severity_medium_at_5(self):
        mentions = [type("obj", (object,), {"id": i}) for i in range(5)]
        msg = FakeMessage(author_id=109, content="look", mentions=mentions)
        violations = check_spam(msg)
        mm = [v for v in violations if v["type"] == "mass_mention"]
        assert mm
        assert mm[0]["severity"] == "medium"

    def test_mass_mention_severity_high_at_10(self):
        mentions = [type("obj", (object,), {"id": i}) for i in range(10)]
        msg = FakeMessage(author_id=110, content="look", mentions=mentions)
        violations = check_spam(msg)
        mm = [v for v in violations if v["type"] == "mass_mention"]
        assert mm
        assert mm[0]["severity"] == "high"


# ─── SPAM_PATTERNS regex ─────────────────────────────────────────────────────

class TestSpamPatterns:
    @pytest.mark.parametrize("text", [
        "free nitro",
        "FREE NITRO",
        "Free Nitro Here",
        "gratis nitro",
        "click here free win",
        "klik sini gratis menang",
        "crypto giveaway",
        "bitcoin airdrop",
        "eth drop",
        "btc gratis",
        "claim your nitro",
        "ambil gratis hadiah",
        "check bit.ly/abc123",
        "tinyurl.com/xyz",
    ])
    def test_positive_matches(self, text):
        assert any(
            __import__("re").search(p, text) for p in SPAM_PATTERNS
        ), f"'{text}' should match a spam pattern"

    @pytest.mark.parametrize("text", [
        "hello world",
        "what is your name",
        "I like python",
        "how are you today",
        "check this out https://github.com",
    ])
    def test_negative_non_spam(self, text):
        assert not any(
            __import__("re").search(p, text) for p in SPAM_PATTERNS
        ), f"'{text}' should NOT match any spam pattern"
