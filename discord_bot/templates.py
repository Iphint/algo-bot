import random

INTRO_TEMPLATES = [
    "🎉 Selamat datang {username}! 👋\nYuk kenalan dulu di #kenalan-dulu 😄\nSetelah itu lanjut ke #📜︱rules dan centang ✅ untuk verifikasi. Sampai ketemu di chat! 🚀",

    "✨ Halo {username}!\nKenalan dulu di #kenalan-dulu ya 👋\nTerus buka #📜︱rules dan cukup centang ✅ buat verifikasi. Gampang banget! 😆",

    "🚀 Welcome {username}!\nLangkah pertama: perkenalan di #kenalan-dulu 💬\nLangkah kedua: buka #📜︱rules lalu centang ✅ untuk membuka akses server.",

    "👋 Hai {username}!\nJangan lupa mampir ke #kenalan-dulu buat kenalan ya 😄\nHabis itu ke #📜︱rules dan centang ✅ untuk verifikasi.",

    "🎊 Welcome {username}!\nYuk mulai dengan kenalan di #kenalan-dulu ✨\nLalu buka #📜︱rules dan tekan centang ✅. Beres deh! 🚀",

    "😆 Halo {username}!\nPerkenalkan diri dulu di #kenalan-dulu ya!\nSetelah itu tinggal buka #📜︱rules dan centang ✅ untuk verifikasi.",

    "🔥 {username} baru bergabung!\nKenalan dulu di #kenalan-dulu 👋\nLalu ke #📜︱rules dan centang ✅ agar semua channel terbuka.",

    "💫 Hai {username}!\nDrop sedikit perkenalan di #kenalan-dulu 😊\nTerus buka #📜︱rules dan lakukan verifikasi dengan centang ✅.",

    "🎉 Selamat datang {username}!\n1️⃣ Kenalan di #kenalan-dulu\n2️⃣ Buka #📜︱rules\n3️⃣ Centang ✅ untuk verifikasi\nSelamat bergabung! 🚀",

    "👀 Halo {username}!\nMulai dulu dengan kenalan di #kenalan-dulu 😄\nSetelah itu cukup centang ✅ di #📜︱rules untuk verifikasi."
]

MULTI_INTRO_TEMPLATES = [
    "🎉 Selamat datang {mentions}! 👋\nYuk kenalan dulu di #kenalan-dulu 😄\nSetelah itu lanjut ke #📜︱rules dan centang ✅ untuk verifikasi.",

    "✨ Halo {mentions}!\nPerkenalkan diri dulu di #kenalan-dulu ya 👋\nLalu buka #📜︱rules dan centang ✅ agar akses server terbuka.",

    "🚀 Welcome {mentions}!\nLangkah pertama: kenalan di #kenalan-dulu 💬\nLangkah kedua: buka #📜︱rules lalu centang ✅ untuk verifikasi.",

    "👋 Hai {mentions}!\nJangan lupa mampir ke #kenalan-dulu buat kenalan ya 😄\nHabis itu ke #📜︱rules dan centang ✅.",

    "🎊 Selamat datang {mentions}!\nYuk mulai dengan kenalan di #kenalan-dulu ✨\nLalu buka #📜︱rules dan tekan centang ✅.",

    "😆 Halo {mentions}!\nPerkenalkan diri kalian dulu di #kenalan-dulu!\nSetelah itu tinggal buka #📜︱rules dan centang ✅.",

    "🔥 {mentions} baru bergabung!\nKenalan dulu di #kenalan-dulu 👋\nLalu ke #📜︱rules dan centang ✅ agar semua channel terbuka.",

    "💫 Hai {mentions}!\nDrop sedikit perkenalan di #kenalan-dulu 😊\nTerus buka #📜︱rules dan lakukan verifikasi dengan centang ✅.",

    "🎉 Selamat datang {mentions}!\n1️⃣ Kenalan di #kenalan-dulu\n2️⃣ Buka #📜︱rules\n3️⃣ Centang ✅ untuk verifikasi\nSelamat bergabung! 🚀",

    "👀 Halo {mentions}!\nMulai dulu dengan kenalan di #kenalan-dulu 😄\nSetelah itu cukup centang ✅ di #📜︱rules untuk verifikasi."
]
def get_random_intro(username):
    template = random.choice(INTRO_TEMPLATES)
    return template.replace("{username}", username)


def format_mentions(members):
    if not members:
        return ""
    if len(members) == 1:
        return members[0].mention
    mention_str = ", ".join(m.mention for m in members[:-1])
    return f"{mention_str}, dan {members[-1].mention}"


def get_intro_message(members):
    mention_str = format_mentions(members)
    if len(members) == 1:
        template = random.choice(INTRO_TEMPLATES)
        template = template.replace("{username}", mention_str)
        template = template.replace("{mentions}", mention_str)
    else:
        template = random.choice(MULTI_INTRO_TEMPLATES)
        template = template.replace("{mentions}", mention_str)
    return template