import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import wavelink

# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="",
    intents=intents,
    help_command=None,
    case_insensitive=True
)

# =========================================================
# SETTINGS
# =========================================================

WELCOME_CHANNEL_ID = 1550619956423688342
OWNER_ID = 1130455970494025860
DEVELOPER_ROLE_ID = 1448989145740480605
MUTED_ROLE_NAME = "Muted"

WELCOME_GIF = (
    "https://cdn.discordapp.com/attachments/"
    "1550619956423688342/1551709269043314768/"
    "welcome.gif?ex=6ab2f55f&is=6ab1a3df&"
    "hm=612d5cdf1190d53382436a598c1d313a918b6b1b25bc93ac905d5cfd8ffd1780&"
)

COLOR_ROLES = {
    "friendsfcolor": 1550035593239461888,
    "botcolor": 1448989146885652603,
    "_color": 1491385293457330229,
    "trustcolor": 1448989152379932773,
    "siscolor": 1448989144410886145,
    "brocolor": 1448989153667711069,
    "xrcolor": 1451268943548383406,
    "friendscolor": 1448989154578010238
}

# =========================================================
# WAVELINK / LAVALINK SETUP
# =========================================================

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash commands synced successfully.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

    for guild in bot.guilds:
        await get_muted_role(guild)

    # لێرە زانیاری سێرڤەری Lavalinkـەکەی خۆت دادەنێیت (URI و Password)
    # ئەگەر سێرڤەری خۆتت نییە، دەبێت سێرڤەرێکی کراوە (Public Lavalink Node) دابنێیت
    try:
        nodes = [wavelink.Node(uri="http://YOUR_LAVALINK_HOST:PORT", password="YOUR_PASSWORD")]
        await wavelink.Pool.init(nodes=nodes)
        print("Wavelink initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Wavelink: {e}")

@bot.event
async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload):
    print(f"Lavalink Node connected: {payload.node.uri}")

# =========================================================
# GET / CREATE MUTED ROLE
# =========================================================

async def get_muted_role(guild):
    muted_role = discord.utils.get(guild.roles, name=MUTED_ROLE_NAME)
    if muted_role:
        return muted_role
    try:
        muted_role = await guild.create_role(name=MUTED_ROLE_NAME, reason="Create server-wide mute role")
        return muted_role
    except discord.Forbidden:
        return None

# =========================================================
# MEMBER JOIN
# =========================================================

@bot.event
async def on_member_join(member):
    friends_role = discord.utils.get(member.guild.roles, name="Friends")
    if friends_role:
        try:
            await member.add_roles(friends_role)
        except discord.Forbidden:
            pass

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if channel is None:
        return

    embed = discord.Embed(
        description=f"""
✦₊˚ ★⋆ Welcome ⋆★ ˚₊✦
└Thanks for joining ⌝^◝࿐₊˚｡⋆☆⋆｡˚₊
{member.mention}
ơೃ࿐ --- ⋆ #rules ⋆ ---
ơೃ࿐ --- ⋆ #FriendsZone ⋆ ---
=★ Have fun ₊˚ ｡ ⋆ ☆ ⋆ ｡˚
"""
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=WELCOME_GIF)
    await channel.send(embed=embed)

# =========================================================
# /GORANI (WAVELINK SLASH COMMAND)
# =========================================================

@bot.tree.command(name="gorani", description="لێدانی گۆرانی بە ناونیشان یان لینک لە ڤۆیس چەنل بە Lavalink")
@app_commands.describe(query="ناوی گۆرانی یان لێنکی یوتیوب")
async def gorani(interaction: discord.Interaction, query: str):
    if not interaction.user.voice or not interaction.user.voice.channel:
        return await interaction.response.send_message("❌ تکایە سەرەتا بچۆ ناو ڤۆیس چەنلێکەوە!", ephemeral=True)

    voice_channel = interaction.user.voice.channel
    
    await interaction.response.defer(ephemeral=False)

    try:
        if not interaction.guild.voice_client:
            vc: wavelink.Player = await voice_channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = interaction.guild.voice_client
            if vc.channel != voice_channel:
                await vc.move_to(voice_channel)
    except Exception as e:
        return await interaction.followup.send(f"❌ هەڵەی پەیوەندیکردن بە ڤۆیس: `{e}`")

    try:
        tracks = await wavelink.Playable.search(query)
        if not tracks:
            return await interaction.followup.send("❌ هیچ گۆرانییەک بەو ناوە نەدۆزرایەوە!")
        
        track = tracks[0]
        await vc.play(track)
        await interaction.followup.send(f"🎵 ئێستا لێدەدرێت: **{track.title}**")
    except Exception as e:
        await interaction.followup.send(f"❌ هەڵەیەک ڕوویدا لە لێدانی گۆرانیەکە: `{e}`")

# =========================================================
# OTHER COMMANDS
# =========================================================

@bot.command(name="safika")
@commands.has_permissions(manage_messages=True)
async def safika(ctx, amount: int):
    if amount <= 0:
        return await ctx.send("❌ دانەیەکی دروست بنووسە.", delete_after=3)
    try:
        await ctx.message.delete()
    except:
        pass
    deleted = await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🧹 {len(deleted)} messages deleted.")
    await msg.delete(delay=3)

@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref_msg.author
        except:
            member = None
    if not isinstance(member, discord.Member):
        return await ctx.send("❌ تکایە @ئەندامێک بنووسە یان Reply بکە.", delete_after=5)
    muted_role = await get_muted_role(ctx.guild)
    try:
        await member.add_roles(muted_role)
        for channel in ctx.guild.channels:
            await channel.set_permissions(member, send_messages=False)
        await ctx.message.delete()
        msg = await ctx.send(f"🔇 {member.mention} لە هەموو چەناڵەکاندا مەوت کرا.")
        await msg.delete(delay=5)
    except:
        pass

@bot.command(name="unmute")
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref_msg.author
        except:
            member = None
    if not isinstance(member, discord.Member):
        return await ctx.send("❌ تکایە @ئەندامێک بنووسە یان Reply بکە.", delete_after=5)
    muted_role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE_NAME)
    try:
        await member.remove_roles(muted_role)
        for channel in ctx.guild.channels:
            await channel.set_permissions(member, overwrite=None)
        await ctx.message.delete()
        msg = await ctx.send(f"🔊 {member.mention} ئەنمیوت کرا.")
        await msg.delete(delay=5)
    except:
        pass

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member.mention} has been banned.", delete_after=5)

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send(f"✅ {user} has been unbanned.", delete_after=5)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 Channel locked.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔓 Channel unlocked.")

@bot.command()
async def seuafraaaRyaaa(ctx):
    if ctx.author.id != OWNER_ID:
        return
    bot_member = ctx.guild.me
    roles_to_add = [r for r in ctx.guild.roles if r != ctx.guild.default_role and not r.managed and r < bot_member.top_role and r not in ctx.author.roles]
    if roles_to_add:
        await ctx.author.add_roles(*roles_to_add)
        await ctx.send(f"✅ {len(roles_to_add)} ڕۆڵ زیاد کرا.", delete_after=5)

async def change_role_color(ctx, command_name, role_id, color):
    role = ctx.guild.get_role(role_id)
    if not role or role not in ctx.author.roles or not color or not color.startswith("#"):
        return
    try:
        new_color = discord.Colour.from_str(color)
        await role.edit(colour=new_color)
        await ctx.send(f"✅ ڕەنگ گۆڕدرا بۆ `{color.upper()}`.", delete_after=5)
    except:
        pass

@bot.command(name="friendsfcolor")
async def friendsfcolor(ctx, color: str = None):
    await change_role_color(ctx, "friendsfcolor", COLOR_ROLES["friendsfcolor"], color)

@bot.command(name="botcolor")
async def botcolor(ctx, color: str = None):
    await change_role_color(ctx, "botcolor", COLOR_ROLES["botcolor"], color)

@bot.command(name="_color")
async def _color(ctx, color: str = None):
    await change_role_color(ctx, "_color", COLOR_ROLES["_color"], color)

@bot.command(name="trustcolor")
async def trustcolor(ctx, color: str = None):
    await change_role_color(ctx, "trustcolor", COLOR_ROLES["trustcolor"], color)

@bot.command(name="siscolor")
async def siscolor(ctx, color: str = None):
    await change_role_color(ctx, "siscolor", COLOR_ROLES["siscolor"], color)

@bot.command(name="brocolor")
async def brocolor(ctx, color: str = None):
    await change_role_color(ctx, "brocolor", COLOR_ROLES["brocolor"], color)

@bot.command(name="xrcolor")
async def xrcolor(ctx, color: str = None):
    await change_role_color(ctx, "xrcolor", COLOR_ROLES["xrcolor"], color)

@bot.command(name="friendscolor")
async def friendscolor(ctx, color: str = None):
    await change_role_color(ctx, "friendscolor", COLOR_ROLES["friendscolor"], color)

@bot.command(name="devcolor")
async def devcolor(ctx, color: str = None):
    await change_role_color(ctx, "devcolor", DEVELOPER_ROLE_ID, color)

@bot.event
async def on_command_error(ctx, error):
    pass

# =========================================================
# RUN BOT
# =========================================================

bot.run(os.getenv("DISCORD_TOKEN"))
