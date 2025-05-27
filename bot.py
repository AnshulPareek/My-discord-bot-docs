from keep_alive import keep_alive
import discord
from discord.ext import commands, tasks
import random
import asyncio
import datetime
import aiohttp
import json
import os
import time
from dotenv import load_dotenv
import asyncpg
load_dotenv()
keep_alive()  # Starts the web server


intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# === CHANNEL and ROLE IDS ===
WELCOME_CHANNEL_ID = 1373980307170004994
ANNOUNCE_CHANNEL_ID = 1373980682719858689
AUDIT_LOG_CHANNEL_ID = 1374257739018272769
LEVEL_CHANNEL_ID = 1374243868572254298
SEARCH_CHANNEL_ID = 1374258522564591697
AUTHORIZED_ROLE_ID = 1373962365019750411  # Role required for mod/admin commands
VERIFIED_ROLE_ID = 1373989096992800840    # Role to assign on captcha success
MUTED_ROLE_NAME = "Muted"

# === for authorized role ===
def is_authorized():
    def predicate(ctx):
        # Check if the user has the authorized role
        role = discord.utils.get(ctx.author.roles, id=AUTHORIZED_ROLE_ID)
        return role is not None
    return commands.check(predicate)
    
# === Welcome gifs and Anime gifs for UI ---
welcome_gifs = [
    "https://media.giphy.com/media/hvRJCLFzcasrR4ia7z/giphy.gif",
    "https://media.giphy.com/media/ASd0Ukj0y3qMM/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/hvRJCLFzcasrR4ia7z/giphy.gif",
    "https://media.giphy.com/media/ASd0Ukj0y3qMM/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/giphy.gif",
    "https://media.giphy.com/media/3oEduSbSGpGaRX2Vri/giphy.gif",
    "https://media.giphy.com/media/26xBwdIuRJiAIqHwA/giphy.gif",
    "https://media.giphy.com/media/3ohhwytHcusSCXXOUg/giphy.gif",
    "https://media.giphy.com/media/3o85xnoIXebk3xYxG4/giphy.gif",
    "https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/giphy.gif",
    "https://media.giphy.com/media/hvRJCLFzcasrR4ia7z/giphy.gif",
    "https://media.giphy.com/media/ASd0Ukj0y3qMM/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/giphy.gif",
    "https://media.giphy.com/media/3oEduSbSGpGaRX2Vri/giphy.gif",
    "https://media.giphy.com/media/26xBwdIuRJiAIqHwA/giphy.gif",
    "https://media.giphy.com/media/3ohhwytHcusSCXXOUg/giphy.gif",
    "https://media.giphy.com/media/3o85xnoIXebk3xYxG4/giphy.gif",
    "https://media.giphy.com/media/111ebonMs90YLu/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/5GoVLqeAOo6PK/giphy.gif",
    "https://media.giphy.com/media/OkJat1YNdoD3W/giphy.gif",
    "https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif",
    "https://media.giphy.com/media/12NUbkX6p4xOO4/giphy.gif",
    "https://media.giphy.com/media/26gsspfKLB9jNx2EU/giphy.gif",
    "https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif",
    "https://media.giphy.com/media/3o7TKtnuHOHHUjR38Y/giphy.gif",
    "https://media.giphy.com/media/xUOxf48vTrk26URB7i/giphy.gif"
]
anime_gifs = [
    "https://media.giphy.com/media/10SvWCbt1ytWCc/giphy.gif",
    "https://media.giphy.com/media/3o85xI5t4h1vZR0xyk/giphy.gif",
    "https://media.giphy.com/media/xT0BKiaM2VGJ4111l6/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/giphy.gif",
    "https://media.giphy.com/media/3o6ZtaO9BZHcOjmErm/giphy.gif",
    "https://media.giphy.com/media/11sBLVxNs7v6WA/giphy.gif",
    "https://media.giphy.com/media/5xtDarqCp0Tf7zG1p1e/giphy.gif",
    "https://media.giphy.com/media/l1J3preURPiwjRPvG/giphy.gif",
    "https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif",
    "https://media.giphy.com/media/3o7TKMt1VVNkHV2PaE/giphy.gif",
    "https://media.giphy.com/media/xUOxf48vTrk26URB7i/giphy.gif",
    "https://media.giphy.com/media/l4pTfx2qLszoacZRS/giphy.gif",
    "https://media.giphy.com/media/3o85xnoIXebk3xYxG4/giphy.gif",
    "https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif",
    "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
    "https://media.giphy.com/media/1BXa2alBjrCXC/giphy.gif",
    "https://media.giphy.com/media/10SvWCbt1ytWCc/giphy.gif",
    "https://media.giphy.com/media/l4Hn6uPjEVP46/giphy.gif",
    "https://media.giphy.com/media/O5NzDnjq0ElTy/giphy.gif",
    "https://media.giphy.com/media/3oKIPwoeGErMmaI43C/giphy.gif",
    "https://media.giphy.com/media/26tOZ42Mg6pbTUPHW/giphy.gif",
    "https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif"
]

# === User XP and leveling data (in-memory) ===
db = None
async def connect_db():
    global db
    db = await asyncpg.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST"),
        port=5432
    )
    await db.execute('''
        CREATE TABLE IF NOT EXISTS levels (
            user_id BIGINT PRIMARY KEY,
            xp INTEGER NOT NULL,
            level INTEGER NOT NULL
        )
    ''')
async def get_user_data(user_id):
    try:
        row = await db.fetchrow("SELECT xp, level FROM levels WHERE user_id = $1", user_id)
        return dict(row) if row else {"xp": 0, "level": 0}
    except Exception as e:
        print(f"DB error in get_user_data: {e}")
        return {"xp": 0, "level": 0}
async def update_user_data(user_id, xp, level):
    await db.execute('''
        INSERT INTO levels (user_id, xp, level)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id)
        DO UPDATE SET xp = EXCLUDED.xp, level = EXCLUDED.level
    ''', user_id, xp, level)

# === Bot online checking ===
@bot.event
async def on_ready():
    await connect_db()
    print(f"Logged in as {bot.user}")


# === Audit log ===
async def send_channel_message(channel_id, content=None, embed=None):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(content=content, embed=embed)
async def audit_log(ctx, action, member=None, reason=None):
    reason_text = f" | Reason: {reason}" if reason else ""
    member_text = f" | Member: {member}" if member else ""
    msg = f"🛠️ **{action}** by {ctx.author}{member_text}{reason_text}"
    await send_channel_message(AUDIT_LOG_CHANNEL_ID, msg)

# === WELCOME + CAPTCHA ===
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    gif_url = random.choice(welcome_gifs)
    embed = discord.Embed(
        title=f"Welcome to {member.guild.name}, {member.display_name}!",
        description=f"👋 Hey {member.mention}, please verify yourself by completing the captcha in DMs to get full access.",
        color=discord.Color.blue(),
        timestamp=datetime.datetime.now(datetime.UTC)
    )
    embed.set_image(url=gif_url)
    embed.set_footer(text="Verification Required")
    await channel.send(embed=embed)

    captcha = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
    try:
        await member.send(f"🛡️ Please type this code to verify yourself (2 minutes): **{captcha}**")

        def check(m):
            return m.author == member and isinstance(m.channel, discord.DMChannel)

        msg = await bot.wait_for('message', check=check, timeout=120)
        if msg.content.strip().upper() == captcha:
            role = member.guild.get_role(VERIFIED_ROLE_ID)
            if role:
                await member.add_roles(role)
            await member.send("✅ Verified! Enjoy the server.")
            await send_channel_message(AUDIT_LOG_CHANNEL_ID, f"✅ {member} passed captcha verification.")
        else:
            await member.send("❌ Incorrect code. You will be kicked.")
            await member.kick(reason="Failed captcha verification")
            await send_channel_message(AUDIT_LOG_CHANNEL_ID, f"⚠️ {member} kicked for failing captcha.")
    except asyncio.TimeoutError:
        await send_channel_message(AUDIT_LOG_CHANNEL_ID, f"⚠️ {member} did not respond to captcha verification.")
    except discord.Forbidden:
        await send_channel_message(AUDIT_LOG_CHANNEL_ID, f"⚠️ Couldn't DM {member} for verification.")

# === MODERATION COMMANDS ===
@bot.command()
@is_authorized()
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        return await ctx.send("❌ Please specify a member to ban.")
    try:
        await member.ban(reason=reason)
        await ctx.send(f"✅ Banned {member}!")
        await audit_log(ctx, "Ban", member, reason)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to ban that user.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@is_authorized()
async def tempban(ctx, member: discord.Member = None, time: int = None, *, reason=None):
    if not member or not time:
        return await ctx.send("❌ Usage: !tempban @user minutes [reason]")
    try:
        await member.ban(reason=reason)
        await ctx.send(f"✅ Temporarily banned {member} for {time} minutes.")
        await audit_log(ctx, "Tempban", member, reason)

        async def unban_later():
            await asyncio.sleep(time * 60)
            bans = await ctx.guild.bans()
            for ban_entry in bans:
                if ban_entry.user.id == member.id:
                    await ctx.guild.unban(ban_entry.user, reason="Tempban expired")
                    await send_channel_message(AUDIT_LOG_CHANNEL_ID, f"♻️ Tempban expired: Unbanned {member}")
                    break

        bot.loop.create_task(unban_later())
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to ban that user.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@is_authorized()
async def kick(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        return await ctx.send("❌ Please specify a member to kick.")
    try:
        await member.kick(reason=reason)
        await ctx.send(f"✅ Kicked {member}!")
        await audit_log(ctx, "Kick", member, reason)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to kick that user.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@is_authorized()
async def mute(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send("❌ Please specify a member to mute.")
    role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE_NAME)
    if not role:
        perms = discord.Permissions(send_messages=False, speak=False)
        try:
            role = await ctx.guild.create_role(name=MUTED_ROLE_NAME, permissions=perms)
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, send_messages=False, speak=False)
        except Exception as e:
            return await ctx.send(f"❌ Failed to create Muted role: {e}")
    if role in member.roles:
        return await ctx.send(f"⚠️ {member} is already muted.")
    try:
        await member.add_roles(role)
        await ctx.send(f"✅ Muted {member}.")
        await audit_log(ctx, "Mute", member)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to add roles.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@is_authorized()
async def unmute(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send("❌ Please specify a member to unmute.")
    role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE_NAME)
    if not role or role not in member.roles:
        return await ctx.send(f"⚠️ {member} is not muted.")
    try:
        await member.remove_roles(role)
        await ctx.send(f"✅ Unmuted {member}.")
        await audit_log(ctx, "Unmute", member)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to remove roles.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@is_authorized()
async def nick(ctx, member: discord.Member = None, *, nickname=None):
    if not member or nickname is None:
        return await ctx.send("❌ Usage: !nick @user new_nickname")
    try:
        await member.edit(nick=nickname)
        await ctx.send(f"✅ Changed nickname of {member} to `{nickname}`.")
        await audit_log(ctx, "Nickname Change", member, f"New nickname: {nickname}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to change nicknames.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@is_authorized()
async def clear(ctx, arg1=None, arg2=None):
    try:
        # Determine what arguments are passed
        target = None
        amount = 100  # default amount

        if arg1 is None:
            # No args: clear 100 messages from everyone
            pass
        elif arg2 is None:
            # Only one argument
            # Could be amount or target
            if arg1.isdigit():
                amount = int(arg1)
            else:
                target = arg1
        else:
            # Two arguments: target and amount
            target = arg1
            if arg2.isdigit():
                amount = int(arg2)
            else:
                return await ctx.send("❌ Amount must be a valid number.")

        if amount < 1:
            return await ctx.send("❌ Amount must be greater than 0.")

        if target is None:
            # Delete recent amount messages from everyone
            deleted = await ctx.channel.purge(limit=amount)
        
        elif target.lower() == "bots":
            def check(m):
                return m.author.bot
            deleted = await ctx.channel.purge(limit=amount, check=check)
        
        else:
            # Try to get a member from target
            member = None
            if len(ctx.message.mentions) > 0:
                member = ctx.message.mentions[0]
            else:
                try:
                    member = await commands.MemberConverter().convert(ctx, target)
                except commands.BadArgument:
                    return await ctx.send("❌ Invalid user specified.")
            
            def check(m):
                return m.author == member
            deleted = await ctx.channel.purge(limit=amount, check=check)

        await ctx.send(f"🧹 Deleted {len(deleted)} message(s).", delete_after=5)
        await audit_log(ctx, "Clear Messages", reason=f"Deleted {len(deleted)} messages in #{ctx.channel} by {target or 'everyone'}")

    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
@is_authorized()
async def role(ctx, member: discord.Member = None, role_id: int = None):
    if member is None or role_id is None:
        return await ctx.send("❌ Usage: `!role <user> <role_id>`")

    role = ctx.guild.get_role(role_id)
    if role is None:
        return await ctx.send("❌ Invalid role ID.")

    # Check if the bot can manage this role
    if role >= ctx.guild.me.top_role:
        return await ctx.send("❌ I can't assign that role. It's higher than my highest role.")

    # Check if the command user has a high enough role
    if ctx.author.top_role <= role and ctx.author != ctx.guild.owner:
        return await ctx.send("❌ You can't assign a role that is equal to or higher than your top role.")
    
    # Check if member already have that role
    if role in member.roles:
        return await ctx.send(f"ℹ️ {member.mention} already has the role `{role.name}`.")

    try:
        await member.add_roles(role)
        await ctx.send(f"✅ Successfully added {role.name} to {member.mention}.")
        await audit_log(ctx, f"Gave role {role.name}", member=member)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to assign that role.")
    except discord.HTTPException:
        await ctx.send("❌ Something went wrong. Failed to assign the role.")

@bot.command()
@is_authorized()
async def removerole(ctx, member: discord.Member = None, role_id: int = None):
    if member is None or role_id is None:
        return await ctx.send("❌ Usage: `!removerole <user> <role_id>`")

    role = ctx.guild.get_role(role_id)
    if role is None:
        return await ctx.send("❌ Invalid role ID.")

    if role not in member.roles:
        return await ctx.send(f"ℹ️ {member.mention} does not have the role `{role.name}`.")

    # Check if the bot can manage this role
    if role >= ctx.guild.me.top_role:
        return await ctx.send("❌ I can't remove that role. It's higher than my highest role.")

    # Check if the user has permission to manage this role
    if ctx.author.top_role <= role and ctx.author != ctx.guild.owner:
        return await ctx.send("❌ You can't remove a role that is equal to or higher than your top role.")

    try:
        await member.remove_roles(role)
        await ctx.send(f"✅ Successfully removed {role.name} from {member.mention}.")
        await audit_log(ctx, f"Removed role {role.name}", member=member)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to remove that role.")
    except discord.HTTPException:
        await ctx.send("❌ Something went wrong. Failed to remove the role.")

@bot.command()
@is_authorized()
async def offline(ctx):
    await ctx.send("🛑 Bot is going offline now...")
    await audit_log(ctx, "Bot Shutdown", reason="Shutdown via !offline command.")
    await bot.close()

    # Exit cleanly without traceback
    raise SystemExit(0)

# === ANNOUNCE ===
@bot.command()
@is_authorized()
async def announce(ctx, *, message=None):
    if not message:
        return await ctx.send("❌ Usage: !announce Your message here")
    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.orange(),
        timestamp=datetime.datetime.now(datetime.UTC)
    )
    embed.set_footer(text=f"By {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty)
    await send_channel_message(ANNOUNCE_CHANNEL_ID, embed=embed)
    await send_channel_message(AUDIT_LOG_CHANNEL_ID, f"📢 Announcement sent by {ctx.author}")

# === LEVEL & LEADERBOARD ===
# Replace usage of `user_xp` with direct DB access

def calculate_level(xp):
    return int((xp // 50) ** 0.5)

@bot.command()
async def level(ctx, member: discord.Member = None):
    if ctx.channel.id != LEVEL_CHANNEL_ID:
        return await ctx.send(f"❌ Please use this command in <#{LEVEL_CHANNEL_ID}> only.")
    
    member = member or ctx.author
    data = await get_user_data(member.id)
    if data is None:
        return await ctx.send(f"🚫 No level data for {member.display_name}.")

    rows = await db.fetch("SELECT user_id, xp, level FROM levels")
    sorted_users = sorted(rows, key=lambda r: (r["level"], r["xp"]), reverse=True)
    rank = next((i + 1 for i, row in enumerate(sorted_users) if row["user_id"] == member.id), None)

    embed = discord.Embed(
        title=f"🌟 Level for {member.display_name}",
        description=f"Level: `{data['level']}`\nXP: `{data['xp']}`\n🏆 Rank: `#{rank}`",
        color=discord.Color.purple(),
        timestamp=datetime.datetime.now(datetime.UTC)
    )
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    embed.set_image(url=random.choice(anime_gifs))
    await ctx.send(embed=embed)

@bot.command(aliases=["leaderboard", "rank" , "lb"])
async def ranks(ctx):
    if ctx.channel.id != LEVEL_CHANNEL_ID:
        return await ctx.send(f"❌ Please use this command in <#{LEVEL_CHANNEL_ID}> only.")

    rows = await db.fetch("SELECT user_id, xp, level FROM levels")
    if not rows:
        return await ctx.send("⚠️ No level data found.")

    top = sorted(rows, key=lambda r: (r["level"], r["xp"]), reverse=True)[:10]

    embed = discord.Embed(
        title="🏆 Leaderboard",
        color=discord.Color.gold(),
        timestamp=datetime.datetime.now(datetime.UTC)
    )

    for i, row in enumerate(top, 1):
        try:
            user = await bot.fetch_user(row["user_id"])
            name = user.name
        except discord.NotFound:
            name = f"User {row['user_id']}"

        embed.add_field(
            name=f"#{i} - {name}",
            value=f"Level {row['level']} | XP {row['xp']}",
            inline=False
        )

    embed.set_image(url=random.choice(anime_gifs))
    await ctx.send(embed=embed)


# === ROLE ASSIGNMENT BASED ON LEVEL (example) ===
level_roles = {
    10: 1374263528403374190,  # Example role ID for level 10
}
async def assign_level_roles(member, level):
    guild = member.guild
    for lvl, role_id in level_roles.items():
        role = guild.get_role(role_id)
        if not role:
            continue
        if level >= lvl and role not in member.roles:
            await member.add_roles(role)
        elif level < lvl and role in member.roles:
            await member.remove_roles(role)

# Keep track of last XP gain time per user (user_id -> timestamp)
last_xp_time = {}
@bot.event
async def on_message(message):
    if message.author == bot.user or message.guild is None:
        return

    if message.channel.id == AUDIT_LOG_CHANNEL_ID and not message.author.bot:
        await message.delete(delay=1)
        return

    user_id = message.author.id
    now = time.time()

    if user_id not in last_xp_time or now - last_xp_time[user_id] >= 3:
        last_xp_time[user_id] = now
        data = await get_user_data(user_id)
        data["xp"] += 3
        new_level = calculate_level(data["xp"])

        if new_level > data["level"]:
            data["level"] = new_level
            await assign_level_roles(message.author, new_level)

            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"Congratulations {message.author.mention}, you reached **Level {new_level}**!",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            if message.author.avatar:
                embed.set_thumbnail(url=message.author.avatar.url)
            embed.set_image(url=random.choice(anime_gifs))
            channel = bot.get_channel(LEVEL_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)

        await update_user_data(user_id, data["xp"], data["level"])

    await bot.process_commands(message)

# === SEARCH COMMAND (using Wikipedia API for example) ===
@bot.command()
async def search(ctx, *, query=None):
    if ctx.channel.id != SEARCH_CHANNEL_ID:
        return await ctx.send(f"❌ Please use this command in <#{SEARCH_CHANNEL_ID}> only.")
    if not query:
        return await ctx.send("❌ Please provide a search query.")

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 404:
                    return await ctx.send(f"❌ No Wikipedia page found for '{query}'.")
                elif resp.status != 200:
                    return await ctx.send("❌ Wikipedia search failed, try again later.")

                data = await resp.json()

                extract = data.get("extract")
                if not extract:
                    return await ctx.send("❌ No summary available on Wikipedia for this query.")

                embed = discord.Embed(
                    title=f"Wikipedia results for: {query}",
                    description=extract[:2048],  # max embed description length
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.now(datetime.UTC)
                )
                embed.set_footer(text="Search powered by Wikipedia")
                await ctx.send(embed=embed)

    except aiohttp.ClientError:
        await ctx.send("❌ Network error occurred while searching Wikipedia. Please try again later.")
    except Exception as e:
        await ctx.send(f"❌ An unexpected error occurred: {e}")

# === SERVERINFO AND USERINFO ===
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    embed = discord.Embed(
        title=f"User Info - {member}",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.now(datetime.UTC)
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Display Name", value=member.display_name, inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "Unknown", inline=True)
    embed.add_field(name="Roles", value=", ".join(roles) if roles else "No roles", inline=False)
    embed.add_field(name="Top Role", value=member.top_role.name, inline=True)
    embed.add_field(name="Bot?", value=member.bot, inline=True)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    roles = [role.name for role in guild.roles if role.name != "@everyone"]
    embed = discord.Embed(
        title=f"Server Info - {guild.name}",
        color=discord.Color.green(),
        timestamp=datetime.datetime.now(datetime.UTC)
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=str(guild.owner), inline=True)
    # Removed region line because it's deprecated in discord.py
    # embed.add_field(name="Region", value=str(guild.region), inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Roles", value=len(roles), inline=True)
    embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
    embed.add_field(name="Created On", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)

# === HELP COMMAND ===
@bot.command()
async def help(ctx):
    prefix = "!"
    embed = discord.Embed(
        title="🤖 Bot Commands Help",
        description=f"Use `{prefix}command` to run a command.\n\n"
                    f"Commands accessible to everyone:\n"
                    f"`level [user]` - Show your or user's level\n"
                    f"`leaderboard , rank , lb` - Show top users by level\n"
                    f"`search <query>` - Search something on internet (use in <#{SEARCH_CHANNEL_ID}>)\n\n"
                    f"Moderator/Admin Commands (Require Mod role):\n"
                    f"`ban <user> [reason]` - Ban a user\n"
                    f"`tempban <user> <minutes> [reason]` - Temporary ban a user\n"
                    f"`kick <user> [reason]` - Kick a user\n"
                    f"`mute <user>` - Mute a user\n"
                    f"`unmute <user>` - Unmute a user\n"
                    f"`nick <user> <nickname>` - Change user's nickname\n"
                    f"`clear [user] <amount> ` - Clear messages\n"
                    f"`announce <message>` - Send announcement\n"
                    f"`userinfo [user]` - Show info about user\n"
                    f"`serverinfo` - Show server info\n"
                    f"`role [user] [role-id]` - Assigns the mentioned role to the user\n"
                    f"`removerole [user] [role-id]` - Removes the mentioned role to the user\n"
                    f"`offline` - Forces the bot to go offline\n"
                    ,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)

# === ERROR HANDLING ===
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: {error.param}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument type.")
    else:
        await ctx.send(f"❌ An error occurred: {error}")

# === RUN BOT ===
# Put your bot token here
if __name__ == "__main__":
    try:
        bot.run(os.getenv("TOKEN"))
    except SystemExit:
        pass  # Do nothing; allows clean shutdown
