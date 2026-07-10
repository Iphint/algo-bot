import re
import time
from collections import defaultdict, deque

SCAM_DOMAINS = [
    "discord-nitro.xyz", "discord.gift.free", "steamcommunity.ru",
    "nitro-discord.xyz", "free-nitro.xyz", "discord.steam-nitro.com",
    "discordairdrop.site", "discord-airdrop.com", "discordgift.site",
    "steam-nitro.ru", "steamnitro.ru", "nitro-free.xyz",
    "discordsafe.com", "discord-safe.com", "discord-verify.com",
    "discord-verification.com", "discord-verif.com", "airdrop-discord.com",
    "cryptogiveaway.xyz", "freecrypto.xyz", "eth-giveaway.com",
    "btc-giveaway.net", "click-me.xyz", "free-nitro.me",
    "discord-nitro.me", "nitro-giveaway.xyz", "gift-nitro.xyz",
    "discord.gift-nitro.xyz", "free-discord-nitro.xyz",
    "boost-discord.xyz", "discord-boost.xyz",
]

SPAM_PATTERNS = [
    r"(?i)\b(free|gratis)\s*(nitro|discord)\b",
    r"(?i)\b(click|klik)\s*(here|sini|link)\b.*\b(free|gratis|win|menang)\b",
    r"(?i)\b(crypto|bitcoin|eth|btc)\s*(giveaway|gratis|free|drop|airdrop)\b",
    r"(?i)\b(claim|ambil)\s*(your|kamu|free|gratis)\s*(nitro|prize|hadiah)\b",
    r"(?i)(?:https?:\/\/)?(?:www\.)?(?:bit\.ly|tinyurl|shorturl|cutly|rb\.gy)(?:\.\w+)?\/\S+",
]

class SpamTracker:
    def __init__(self):
        self.message_times = defaultdict(lambda: deque(maxlen=50))
        self.last_messages = defaultdict(lambda: deque(maxlen=5))
        self.cleanup_interval = 300
        self.last_cleanup = time.time()

    def record_message(self, user_id: int, content: str):
        now = time.time()
        self.message_times[user_id].append(now)
        if content:
            self.last_messages[user_id].append(content.lower().strip())
        self._cleanup()

    def _cleanup(self):
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return
        cutoff = now - 3600
        for uid in list(self.message_times.keys()):
            if self.message_times[uid] and self.message_times[uid][-1] < cutoff:
                del self.message_times[uid]
                if uid in self.last_messages:
                    del self.last_messages[uid]
        self.last_cleanup = now

    def get_recent_message_count(self, user_id: int, window: float = 5.0) -> int:
        now = time.time()
        cutoff = now - window
        return sum(1 for t in self.message_times[user_id] if t >= cutoff)

    def get_consecutive_count(self, user_id: int, window: float = 2.0) -> int:
        now = time.time()
        cutoff = now - window
        return sum(1 for t in self.message_times[user_id] if t >= cutoff)

    def get_duplicate_count(self, user_id: int, content: str) -> int:
        normalized = content.lower().strip()
        if not normalized:
            return 0
        return sum(1 for msg in self.last_messages[user_id] if msg == normalized)

    def is_duplicate(self, user_id: int, content: str, threshold: int = 2) -> bool:
        return self.get_duplicate_count(user_id, content) >= threshold

tracker = SpamTracker()

def contains_suspicious_links(text: str) -> list[str]:
    urls = re.findall(r'(?:https?://|www\.)\S+', text.lower())
    found = []
    for url in urls:
        for domain in SCAM_DOMAINS:
            if domain in url:
                found.append(domain)
    return list(set(found))

def contains_shortened_links(text: str) -> list[str]:
    matches = re.findall(r'(?:https?://)?(?:www\.)?(?:bit\.ly|tinyurl|shorturl|cutly|rb\.gy|shortlink|linkly)\b', text.lower())
    return list(set(matches))

def count_mentions(message) -> int:
    count = 0
    if message.mention_everyone:
        count += 20
    count += len(message.mentions)
    count += len(message.role_mentions)
    return count

def is_all_caps(text: str, min_length: int = 10, caps_ratio: float = 0.7) -> bool:
    if len(text) < min_length:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    caps_count = sum(1 for c in letters if c.isupper())
    return (caps_count / len(letters)) >= caps_ratio

def check_spam(message) -> list[dict]:
    violations = []
    user_id = message.author.id
    content = message.content

    tracker.record_message(user_id, content)

    rate_count = tracker.get_recent_message_count(user_id, window=5.0)
    if rate_count >= 4:
        violations.append({
            "type": "rapid_fire",
            "detail": f"Mengirim {rate_count} pesan dalam 5 detik",
            "severity": "high" if rate_count >= 8 else "medium",
        })
    elif rate_count >= 3:
        burst_count = tracker.get_consecutive_count(user_id, window=2.0)
        if burst_count >= 3:
            violations.append({
                "type": "rapid_fire",
                "detail": f"Mengirim {burst_count} pesan berturut-turut dalam 2 detik",
                "severity": "medium",
            })

    if content and tracker.get_duplicate_count(user_id, content) >= 3:
        violations.append({
            "type": "duplicate",
            "detail": "Mengirim pesan yang sama berulang kali",
            "severity": "medium",
        })

    mention_count = count_mentions(message)
    if mention_count >= 5:
        violations.append({
            "type": "mass_mention",
            "detail": f"Menyebut {mention_count} user/role dalam 1 pesan",
            "severity": "high" if mention_count >= 10 else "medium",
        })

    suspicious_domains = contains_suspicious_links(content)
    if suspicious_domains:
        violations.append({
            "type": "suspicious_link",
            "detail": f"Membagikan link mencurigakan: {', '.join(suspicious_domains)}",
            "severity": "high",
        })

    spam_pattern_match = any(
        re.search(p, content) for p in SPAM_PATTERNS
    ) if content else False
    if spam_pattern_match:
        violations.append({
            "type": "spam_pattern",
            "detail": "Pesan mengandung pola spam (giveaway palsu, link pendek, dll)",
            "severity": "high",
        })

    if is_all_caps(content):
        violations.append({
            "type": "all_caps",
            "detail": "Pesan menggunakan huruf kapital berlebihan",
            "severity": "low",
        })

    return violations
