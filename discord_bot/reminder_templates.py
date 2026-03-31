import random

REMINDER_TEMPLATES = [
    "Halo {username}! 👋 Kayaknya kamu belum sempat kenalan nih 😆 Yuk sempetin intro biar makin akrab!",
    "Hai {username}! 💫 Jangan lupa kenalan dulu di channel ya, biar kita bisa saling kenal!",
    "Halo {username}! 🚀 Masih nunggu intro kamu nih 😆 Yuk kenalan dulu!",
    "{username}, jangan jadi silent reader dong 😜 Yuk kenalan dulu di channel!",
    "Hai {username}! 🎉 Belum sempat intro ya? Yuk kenalan dulu biar makin seru!",

    "Halo {username}! 😎 Intro dulu yuk, biar gak asing di sini!",
    "{username}! 👀 Kita masih nunggu kenalan dari kamu nih 😆",
    "Hai {username}! 🚀 Yuk mulai dengan intro dulu ya!",
    "{username}, jangan lupa kenalan dulu yaa 😁",
    "Halo {username}! 🎊 Intro dulu yuk biar makin akrab!",

    "Hai {username}! 💬 Yuk kenalan dulu di channel!",
    "{username}! 😆 Drop intro kamu ya!",
    "Halo {username}! 🎉 Jangan lupa intro dulu ya!",
    "Hai hai {username}! 👋 Kita tunggu kenalan kamu!",
    "{username}! 🚀 Yuk mulai dengan kenalan dulu!",

    "Halo {username}! 💫 Kenalan dulu yuk!",
    "Hai {username}! 😁 Intro dulu ya!",
    "{username}! 🎉 Yuk kenalan biar makin seru!",
    "Halo {username}! 👀 Jangan lupa intro ya!",
    "{username}! 💬 Yuk kenalan dulu ya!"
]

def get_random_reminder(username):
    return random.choice(REMINDER_TEMPLATES).replace("{username}", username)