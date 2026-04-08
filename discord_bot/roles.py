import discord # type: ignore
from config import COURSE_ROLE_MAP

async def assign_course_role(member, course_name):
    guild = member.guild
    course_name = course_name.lower().strip()

    assigned_role = None

    for keyword, role_name in COURSE_ROLE_MAP:
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            continue
        if keyword in course_name:
            await member.add_roles(role)
            assigned_role = role
            break

    for _, role_name in COURSE_ROLE_MAP:
        role = discord.utils.get(guild.roles, name=role_name)
        if role and role != assigned_role and role in member.roles:
            await member.remove_roles(role)

    return assigned_role