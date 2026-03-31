import random

INTRO_TEMPLATES = [
    "🎉 WELCOME {username}! Akhirnya datang juga 😆\nYuk kenalan dulu di sini ya! 👇\nAbis itu langsung gas ke main chat 🔥 dan jangan lupa cek weekly quest 🎯",

    "👀 Eh ada {username} nih!\nJangan jadi misterius ya 😏 Kenalan dulu di sini!\nTerus lanjut nimbrung di main chat 💬 + cek weekly quest 🚀",

    "🔥 {username} JOINED THE SERVER!\nLangsung intro dulu biar kita kenal 😆\nHabis itu bebas ngobrol di main chat & ambil challenge di weekly quest 🎯",

    "✨ Halo {username}! Welcome to the chaos 😆\nDrop intro kamu di sini dulu ya 👇\nLanjut ke main chat 💬 atau cari seru di weekly quest 🚀",

    "🎊 {username} masukkk!\nSebelum jadi legend di sini 😎 wajib intro dulu ya!\nAbis itu gas ke main chat & weekly quest 🔥",

    "😆 Hai {username}! Jangan cuma lewat doang 👀\nKenalan dulu di sini ya biar kita kenal!\nTerus lanjut ngobrol santai di main chat 💬",

    "🚀 {username} has landed!\nIntro dulu di sini ya biar gak jadi silent reader 😏\nAbis itu langsung aktif di main chat + weekly quest 🎯",

    "👋 Halo {username}!\nCeritain dikit tentang kamu di sini ya 😆\nTerus lanjut seru-seruan di main chat 🔥",

    "🎉 Welcome {username}!\nStep 1: Intro dulu di sini 👇\nStep 2: Nimbrung di main chat 💬\nStep 3: Cek weekly quest 🎯\nGaskeun! 🚀",

    "😎 {username} join squad!\nJangan lupa perkenalan dulu ya ✨\nAbis itu langsung nyemplung ke main chat & weekly quest 🔥",

    "👀 {username} spotted!\nKenalan dulu dong di sini 😆\nTerus lanjut ngobrol di main chat + ikutan weekly quest 🚀",

    "🔥 Halo {username}!\nBiar makin akrab, intro dulu ya 👇\nHabis itu bebas ngobrol di main chat 💬",

    "🎊 {username} hadir!\nJangan skip intro ya 😏\nAbis itu langsung aktif di main chat & weekly quest 🎯",

    "💫 Hai {username}!\nIntro dulu yuk biar kita kenal 😆\nTerus lanjut ke main chat buat ngobrol santai 💬",

    "🚀 Welcome aboard {username}!\nKenalan dulu di sini ya 👇\nLanjut ke main chat & jangan lupa weekly quest 🔥",

    "😆 {username} masuk!\nDrop intro kamu di sini ya ✨\nAbis itu langsung seru-seruan di main chat 💬",

    "🎉 Halo {username}!\nIntro dulu biar gak asing 😏\nTerus lanjut ke main chat & weekly quest 🚀",

    "👋 {username}!\nYuk kenalan dulu di sini 😆\nHabis itu langsung join obrolan di main chat 🔥",

    "🔥 {username} detected!\nWajib intro dulu ya 😎\nTerus lanjut ke main chat + weekly quest 🎯",

    "🎊 Welcome {username}!\nPerkenalan dulu yuk di sini 👇\nAbis itu bebas explore main chat & weekly quest 🚀",

    "😏 {username} jangan malu-malu ya!\nIntro dulu di sini biar kita kenal 😆\nTerus lanjut ke main chat 💬",

    "🚀 {username} join!\nStep awal: intro dulu 👇\nStep selanjutnya: aktif di main chat & weekly quest 🔥",

    "✨ Halo {username}!\nKenalan dulu ya biar makin akrab 😆\nTerus lanjut ngobrol di main chat 💬",

    "👀 Ada {username} nih!\nIntro dulu yuk di sini 😆\nHabis itu langsung nimbrung di main chat 🚀",

    "🎉 {username} masuk!\nJangan lupa kenalan dulu ya 👇\nTerus lanjut ke weekly quest 🔥",

    "🔥 Welcome {username}!\nIntro dulu biar kita kenal 😎\nAbis itu langsung aktif di main chat 💬",

    "😆 Hai {username}!\nYuk intro dulu di sini 👇\nTerus lanjut seru-seruan di main chat 🚀",

    "🎊 {username} hadir!\nKenalan dulu yuk 😆\nAbis itu lanjut ke weekly quest & main chat 🔥",

    "🚀 {username} joined!\nIntro dulu ya biar gak asing 😏\nTerus lanjut ngobrol di main chat 💬",

    "✨ Welcome {username}!\nDrop intro kamu di sini 👇\nTerus lanjut ke main chat & weekly quest 🎯"
]

def get_random_intro(username):
    template = random.choice(INTRO_TEMPLATES)
    return template.replace("{username}", username)