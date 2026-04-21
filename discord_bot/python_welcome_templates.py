import random

PYTHON_WELCOME_TEMPLATES = [
    "Halo {username}! 👋 Selamat datang di kelas Python. Yuk mulai dengan perkenalan singkat di sini ya.",
    "Hai {username}! 🚀 Welcome to Python class. Silakan kenalan dulu biar makin nyaman belajar bareng.",
    "Halo {username}! 🐍 Senang kamu sudah bergabung. Coba intro dulu di channel ini ya.",
    "Hai {username}! 💻 Selamat datang di Python Lounge. Yuk mulai dengan perkenalan singkat.",
    "Halo {username}! ✨ Welcome aboard. Jangan lupa kenalan dulu di sini ya.",

    "Hai {username}! 🎯 Kamu sudah masuk kelas Python. Silakan mulai dengan intro ya.",
    "Halo {username}! 👋 Senang kamu join. Yuk perkenalan dulu supaya lebih akrab.",
    "Hai {username}! 🚀 Selamat datang. Coba kenalan dulu di channel ini ya.",
    "Halo {username}! 🐍 Yuk mulai perjalanan Python kamu dengan intro singkat.",
    "Hai {username}! 💡 Welcome to the class. Perkenalan dulu yuk.",

    "Halo {username}! 👋 Selamat bergabung di Python Class. Yuk kenalan dulu.",
    "Hai {username}! 🎉 Senang kamu di sini. Mulai dengan perkenalan ya.",
    "Halo {username}! 💻 Yuk perkenalan dulu supaya teman-teman bisa kenal kamu.",
    "Hai {username}! 🚀 Welcome! Jangan lupa intro dulu di sini.",
    "Halo {username}! 🐍 Mulai dari perkenalan dulu ya, biar makin nyaman.",

    "Hai {username}! ✨ Selamat datang di Python Lounge. Yuk kenalan dulu.",
    "Halo {username}! 🎯 Silakan intro dulu ya, biar makin akrab.",
    "Hai {username}! 👋 Jangan lupa perkenalan dulu di channel ini.",
    "Halo {username}! 💡 Yuk mulai dengan kenalan singkat.",
    "Hai {username}! 🚀 Welcome to Python. Intro dulu ya."
]


def get_python_welcome(username):
    return random.choice(PYTHON_WELCOME_TEMPLATES).replace("{username}", username)