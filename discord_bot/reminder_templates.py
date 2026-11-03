import random

REMINDER_TEMPLATES = [
    "Halo {username}! 👋 Santai aja yaa di sini, yuk langsung mampir nimbrung ngobrol di main-chat 😄",
    "Hai {username}! 💫 Lagi pada ngobrol seru nih di main-chat, yuk ikutan nimbrung bareng yang lain!",
    "Halo {username}! 🚀 Jangan sungkan yaa, langsung sapa teman-teman dan join chat di main-chat!",
    "{username}! 😜 Yuk mampir ke main-chat, teman-teman di sini ramah dan asik diajak ngobrol kok!",
    "Hai {username}! 🎉 Ditunggu kehadirannya di main-chat yaa, yuk santai bareng kita!",
    "Halo {username}! 😎 Kalau mau ngobrol atau tanya-tanya seputar kelas/coding, langsung gas ke main-chat yuk!",
    "{username}! 👀 Yuk langsung meluncur ke main-chat, kita kenalan dan ngobrol santai bareng 😆",
    "Hai {username}! 💬 Santai aja yaa, langsung nimbrung di main-chat kapan pun kamu sempat!",
]


def get_random_reminder(username):
    return random.choice(REMINDER_TEMPLATES).replace("{username}", username)
