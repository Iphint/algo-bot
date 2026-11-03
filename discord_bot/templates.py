import random
import discord

INTRO_TEMPLATES = [
    "Halo {username}! 👋 Selamat datang yaa! Yuk langsung mampir dan nimbrung ngobrol bareng di {main_chat} 😄",
    "Hai {username}! Welcome di server! Santai aja yaa di sini, langsung join obrolan bareng yang lain di {main_chat} 🙌",
    "Welcome {username}! Salam kenal yaa. Jangan ragu buat sapa yang lain dan langsung nimbrung di {main_chat} ✨",
    "Halo {username}! Senang bisa ketemu di sini. Yuk langsung meluncur ke {main_chat} buat ngobrol-ngobrol santai 🚀",
    "Hai {username}! Selamat bergabung! Kalau mau ngobrol atau tanya-tanya, langsung gas ke {main_chat} yaa 😁",
    "Welcome {username}! Yuk langsung nongkrong di {main_chat}, teman-teman di sana asik-asik kok 👋",
    "Halo {username}! Salam kenal! Langsung nimbrung aja di {main_chat}, gak usah sungkan yaa 💬",
    "Hai hai {username}! Welcome to the server! Yuk cus ke {main_chat} buat ngobrol santai bareng teman-teman 🎉",
    "Selamat datang {username}! Langsung gabung di {main_chat} yaa, ditunggu obrolan serunya! 🔥",
    "Halo {username}! Welcome yaa! Langsung gas mampir ke {main_chat} buat kenalan dan ngobrol bareng 😄",
]

MULTI_INTRO_TEMPLATES = [
    "Halo {mentions}! 👋 Selamat datang yaa semuanya! Yuk langsung mampir dan nimbrung ngobrol di {main_chat} 😄",
    "Hai {mentions}! Welcome di server! Santai aja yaa di sini, langsung join obrolan bareng yang lain di {main_chat} 🙌",
    "Welcome {mentions}! Salam kenal yaa semuanya. Jangan ragu buat sapa yang lain dan langsung nimbrung di {main_chat} ✨",
    "Halo {mentions}! Senang banget kalian bisa gabung. Yuk langsung meluncur ke {main_chat} buat ngobrol santai bareng 🚀",
    "Hai {mentions}! Selamat datang semuanya! Kalau mau ngobrol santai atau tanya-tanya, langsung gas ke {main_chat} yaa 😁",
    "Welcome {mentions}! Yuk langsung nongkrong bareng di {main_chat}, teman-teman di sana asik-asik kok 👋",
    "Halo {mentions}! Salam kenal semuanya! Langsung nimbrung aja di {main_chat}, gak usah sungkan yaa 💬",
    "Hai hai {mentions}! Welcome! Yuk cus bareng ke {main_chat} buat ngobrol santai 🎉",
    "Selamat datang {mentions}! Langsung gabung di {main_chat} yaa, ditunggu obrolan serunya bareng-bareng! 🔥",
    "Halo {mentions}! Welcome yaa semuanya! Langsung gas mampir ke {main_chat} buat kenalan dan ngobrol bareng 😄",
]


def format_mentions(members):
    if not members:
        return ""
    if len(members) == 1:
        member = members[0]
        return getattr(member, "mention", str(member))
    mentions = [getattr(m, "mention", str(m)) for m in members]
    return f"{', '.join(mentions[:-1])}, dan {mentions[-1]}"


def get_main_chat_mention(members):
    if not members:
        return "#main-chat"
    first = members[0]
    guild = getattr(first, "guild", None)
    if not guild or not hasattr(guild, "text_channels"):
        return "#main-chat"

    main_chat = discord.utils.get(guild.text_channels, name="main-chat")
    if not main_chat:
        main_chat = discord.utils.find(
            lambda c: "main-chat" in c.name.lower() or "main_chat" in c.name.lower() or c.name.lower() == "mainchat",
            guild.text_channels
        )
    return main_chat.mention if main_chat else "#main-chat"


def get_random_intro(username):
    template = random.choice(INTRO_TEMPLATES)
    return template.replace("{username}", username).replace("{main_chat}", "#main-chat")


def get_intro_message(members):
    mention_str = format_mentions(members)
    main_chat_mention = get_main_chat_mention(members)

    if len(members) == 1:
        template = random.choice(INTRO_TEMPLATES)
        template = template.replace("{username}", mention_str)
        template = template.replace("{mentions}", mention_str)
    else:
        template = random.choice(MULTI_INTRO_TEMPLATES)
        template = template.replace("{mentions}", mention_str)
        template = template.replace("{username}", mention_str)

    template = template.replace("{main_chat}", main_chat_mention)
    return template
