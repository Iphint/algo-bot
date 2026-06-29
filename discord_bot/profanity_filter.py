import re

PROFANITY_LIST_ID = [
    "anjing", "bajingan", "bangsat", "bodoh", "brengsek", "babi", "bangke",
    "setan", "kampret", "sinting", "tolol", "goblok", "kontol", "memek",
    "jancok", "asu", "bejat", "sialan", "kampungan", "keparat", "bego",
    "jalang", "pelacur", "edan", "perek", "banci", "anjim", "kontlok",
    "geje", "ngenes", "bacot",
]

PROFANITY_LIST_EN = [
    "fuck", "shit", "bitch", "bastard", "asshole", "dick", "pussy", "crap",
    "slut", "prick", "cunt", "dumbass", "motherfucker", "ass", "cock",
    "whore", "faggot", "jackass", "idiot", "loser", "stupid", "moron",
    "douche", "retard", "twat", "shithead", "asswipe", "dickhead", "wanker",
    "bitchass", "craphead", "cockhead", "dumbfuck", "dipshit", "cocksucker",
    "fuckface", "prickface", "arsehole", "shitty", "slutface", "bastardface",
    "dumbhead", "fuckboy", "shitbag", "asshat", "twatwaffle",
    # Additional from CSV analysis
    "bitches", "hoes", "hoe", "nigga", "niggas", "niggah", "nigger", "niggers",
    "fag", "fags", "retarded", "fuckin", "tranny", "beaner", "queer", "gaywad",
    "spook", "ghetto", "dumb",
]

ALL_PROFANITY = set(PROFANITY_LIST_ID + PROFANITY_LIST_EN)


def contains_profanity(text: str) -> list[str]:
    words = re.findall(r"[\w\u00C0-\u024F]+", text.lower())
    found = [w for w in words if w in ALL_PROFANITY]
    return list(set(found))


def censor_text(text: str) -> str:
    def replace_word(match):
        word = match.group(0)
        if word.lower() in ALL_PROFANITY:
            return word[0] + "*" * (len(word) - 1)
        return word
    return re.sub(r"[\w\u00C0-\u024F]+", replace_word, text)
