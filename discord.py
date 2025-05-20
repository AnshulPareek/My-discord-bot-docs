import discord
from discord.ext import commands, tasks
import random
import asyncio
import datetime
import aiohttp

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}!")

# === CHANNEL and ROLE IDS ===
WELCOME_CHANNEL_ID = 1373980307170004994
ANNOUNCE_CHANNEL_ID = 1373980682719858689
AUDIT_LOG_CHANNEL_ID = 1374257739018272769
LEVEL_CHANNEL_ID = 1374243868572254298
SEARCH_CHANNEL_ID = 1374258522564591697

AUTHORIZED_ROLE_ID = 1373962365019750411  # Role required for mod/admin commands
VERIFIED_ROLE_ID = 1373989096992800840    # Role to assign on captcha success
MUTED_ROLE_NAME = "Muted"

# === Welcome gifs and Anime gifs for UI ---
welcome_gifs = [
    "https://media.giphy.com/media/hvRJCLFzcasrR4ia7z/giphy.gif",
    "https://media.giphy.com/media/ASd0Ukj0y3qMM/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/giphy.gif"
]

anime_gifs = [
    "https://media.giphy.com/media/10SvWCbt1ytWCc/giphy.gif",
    "https://media.giphy.com/media/3o85xI5t4h1vZR0xyk/giphy.gif",
    "https://media.giphy.com/media/xT0BKiaM2VGJ4111l6/giphy.gif"
]

# === User XP and leveling data (in-memory) ===
user_xp = {}

def calculate_level(xp):
    return int(xp ** 0.25)

def is_authorized():
    def predicate(ctx):
        role = discord.utils.get(ctx.author.roles, id=AUTHORIZED_ROLE_ID)
        return role is not None or ctx.author.guild_permissions.administrator
    return commands.check(predicate)

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
        timestamp=datetime.datetime.utcnow()
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

# === LEVELING SYSTEM ===
@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return

    data = user_xp.setdefault(message.author.id, {"xp": 0, "level": 0})
    data["xp"] += 5
    new_level = calculate_level(data["xp"])
    if new_level > data["level"]:
        data["level"] = new_level
        embed = discord.Embed(
            title="🎉 Level Up!",
            description=f"Congratulations {message.author.mention}, you reached **Level {new_level}**!",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else discord.Embed.Empty)
        embed.set_image(url=random.choice(anime_gifs))
        await send_channel_message(LEVEL_CHANNEL_ID, embed=embed)

    await bot.process_commands(message)

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
async def clear(ctx, amount: int = 10, member: discord.Member = None):
    if amount < 1:
        return await ctx.send("❌ Amount must be greater than 0.")
    try:
        if member:
            def check(m):
                return m.author == member
            deleted = await ctx.channel.purge(limit=amount, check=check)
        else:
            deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"🧹 Deleted {len(deleted)} message(s).", delete_after=5)
        await audit_log(ctx, "Clear Messages", reason=f"Deleted {len(deleted)} messages in #{ctx.channel}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages.")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

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
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_footer(text=f"By {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else discord.Embed.Empty)
    await send_channel_message(ANNOUNCE_CHANNEL_ID, embed=embed)
    await send_channel_message(AUDIT_LOG_CHANNEL_ID, f"📢 Announcement sent by {ctx.author}")

# === LEVEL & LEADERBOARD ===
@bot.command()
async def level(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = user_xp.get(member.id)
    if not data:
        return await ctx.send(f"🚫 No level data for {member.display_name}.")
    embed = discord.Embed(
        title=f"🌟 Level for {member.display_name}",
        description=f"Level: `{data['level']}`\nXP: `{data['xp']}`",
        color=discord.Color.purple(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else discord.Embed.Empty)
    embed.set_image(url=random.choice(anime_gifs))
    await send_channel_message(LEVEL_CHANNEL_ID, embed=embed)

@bot.command(aliases=["leaderboard", "rank"])
async def ranks(ctx):
    if not user_xp:
        return await ctx.send("⚠️ No data yet.")
    top = sorted(user_xp.items(), key=lambda x: x[1]["level"], reverse=True)[:10]
    embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold(), timestamp=datetime.datetime.utcnow())
    for i, (uid, d) in enumerate(top, 1):
        user = await bot.fetch_user(uid)
        embed.add_field(name=f"#{i} - {user.name}", value=f"Level {d['level']} | XP {d['xp']}", inline=False)
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

@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None:
        return

    data = user_xp.setdefault(message.author.id, {"xp": 0, "level": 0})
    data["xp"] += 5
    new_level = calculate_level(data["xp"])
    if new_level > data["level"]:
        data["level"] = new_level
        await assign_level_roles(message.author, new_level)
        embed = discord.Embed(
            title="🎉 Level Up!",
            description=f"Congratulations {message.author.mention}, you reached **Level {new_level}**!",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else discord.Embed.Empty)
        embed.set_image(url=random.choice(anime_gifs))
        await send_channel_message(LEVEL_CHANNEL_ID, embed=embed)

    await bot.process_commands(message)

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # If message is in the audit log channel and not from the bot
    if message.channel.id == AUDIT_LOG_CHANNEL_ID:
        await message.delete(delay=5)
        return  # Skip further processing for this message
    if message.channel.id == LEVEL_CHANNEL_ID:
        await message.delete(delay=5)
        return  # Skip further processing for this message

    await bot.process_commands(message)  # Allow command processing


# === SEARCH COMMAND (using DuckDuckGo API for example) ===
@bot.command()
async def search(ctx, *, query=None):
    if ctx.channel.id != SEARCH_CHANNEL_ID:
        return await ctx.send(f"❌ Please use this command in <#{SEARCH_CHANNEL_ID}> only.")
    if not query:
        return await ctx.send("❌ Please provide a search query.")
    url = f"https://api.duckduckgo.com/?q={query}&format=json&no_redirect=1&skip_disambig=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await ctx.send("❌ Search failed, try again later.")
            data = await resp.json(content_type=None)  # allow any content-type
            abstract = data.get("AbstractText")
            if not abstract:
                return await ctx.send("❌ No results found.")
            embed = discord.Embed(
                title=f"Search results for: {query}",
                description=abstract,
                color=discord.Color.blue(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text="Search powered by DuckDuckGo")
            embed.set_image(url=random.choice(anime_gifs))
            await ctx.send(embed=embed)

# === SERVERINFO AND USERINFO ===
@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    embed = discord.Embed(
        title=f"User Info - {member}",
        color=discord.Color.blurple(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else discord.Embed.Empty)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Display Name", value=member.display_name, inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S") if member.joined_at else "Unknown", inline=True)
    embed.add_field(name="Roles", value=", ".join(roles) if roles else "No roles", inline=False)
    embed.add_field(name="Top Role", value=member.top_role.name, inline=True)
    embed.add_field(name="Bot?", value=member.bot, inline=True)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
    embed.set_image(url=random.choice(anime_gifs))
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    roles = [role.name for role in guild.roles if role.name != "@everyone"]
    embed = discord.Embed(
        title=f"Server Info - {guild.name}",
        color=discord.Color.green(),
        timestamp=datetime.datetime.utcnow()
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
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
    embed.set_image(url=random.choice(anime_gifs))
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
                    f"`leaderboard` - Show top users by level\n"
                    f"`search <query>` - Search something on internet (use in <#{SEARCH_CHANNEL_ID}>)\n\n"
                    f"Moderator/Admin Commands (Require <@&{AUTHORIZED_ROLE_ID}> role):\n"
                    f"`ban <user> [reason]` - Ban a user\n"
                    f"`tempban <user> <minutes> [reason]` - Temporary ban a user\n"
                    f"`kick <user> [reason]` - Kick a user\n"
                    f"`mute <user>` - Mute a user\n"
                    f"`unmute <user>` - Unmute a user\n"
                    f"`nick <user> <nickname>` - Change user's nickname\n"
                    f"`clear <amount> [user]` - Clear messages\n"
                    f"`announce <message>` - Send announcement\n"
                    f"`userinfo [user]` - Show info about user\n"
                    f"`serverinfo` - Show server info\n",
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
    embed.set_image(url=random.choice(anime_gifs))
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
bot.run("Your bot token")