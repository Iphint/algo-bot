import discord
from config import COURSE_ROLE_MAP

async def assign_course_role(member, course_name):
    course_name = course_name.lower().strip()
    guild = member.guild

    assigned_role = None

    for keyword, role_name in COURSE_ROLE_MAP.items():
        role = discord.utils.get(guild.roles, name=role_name)

        if not role:
            continue

        if keyword in course_name:
            await member.add_roles(role)
            assigned_role = role
        else:
            if role in member.roles:
                await member.remove_roles(role)

    return assigned_role