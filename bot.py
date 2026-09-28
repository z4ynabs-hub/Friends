import os
import discord
from discord import app_commands
from discord.ext import commands

# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

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
MUTED_ROLE_NAME = "Muted"

WELCOME_GIF = (
    "https://cdn.discordapp.com/attachments/"
    "1550619956423688342/1551709269043314768/"
    "welcome.gif?ex=6ab2f55f&is=6ab1a3df&"
    "hm=612d5cdf1190d53382436a598c1d313a918b6b1b25bc93ac905d5cfd8ffd1780&"
)

# =========================================================
# GET / CREATE MUTED ROLE
# =========================================================

async def get_muted_role(guild):
    muted_role = discord.utils.get(
        guild.roles,
        name=MUTED_ROLE_NAME
    )

    if muted_role:
        return muted_role

    try:
        muted_role = await guild.create_role(
            name=MUTED_ROLE_NAME,
            reason="Create server-wide mute role"
        )
        print(f"Created Muted role in {guild.name}")
        return muted_role

    except discord.Forbidden:
        print(f"Bot cannot create Muted role in {guild.name}")
        return None

# =========================================================
# BOT READY
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

# =========================================================
# MEMBER JOIN
# =========================================================

@bot.event
async def on_member_join(member):
    friends_role = discord.utils.get(
        member.guild.roles,
        name="Friends"
    )

    if friends_role:
        try:
            await member.add_roles(friends_role)
        except discord.Forbidden:
            print("Bot cannot give Friends role.")

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
# TEST WELCOME
# =========================================================

@bot.command()
async def test(ctx):
    embed = discord.Embed(
        description=f"""
✦₊˚ ★⋆ Welcome ⋆★ ˚₊✦
└Thanks for joining ⌝^◝࿐₊˚｡⋆☆⋆｡˚₊
{ctx.author.mention}
ơೃ࿐ --- ⋆ #rules ⋆ ---
ơೃ࿐ --- ⋆ #FriendsZone ⋆ ---
=★ Have fun ₊˚ ｡ ⋆ ☆ ⋆ ｡˚
"""
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_image(url=WELCOME_GIF)
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete()
    except:
        pass

# =========================================================
# SAFIKA
# =========================================================

@bot.command(name="safika")
@commands.has_permissions(manage_messages=True)
async def safika(ctx, amount: int):
    if amount <= 0:
        return await ctx.send("❌ دانەیەکی دروست بنووسە.", delete_after=3)

    try:
        try:
            await ctx.message.delete()
        except:
            pass

        deleted = await ctx.channel.purge(limit=amount)
        msg = await ctx.send(f"🧹 {len(deleted)} messages deleted.")
        await msg.delete(delay=3)

    except discord.Forbidden:
        await ctx.send("❌ بۆتەکە دەسەڵاتی سڕینەوەی نامەکانی نییە.", delete_after=5)
    except discord.HTTPException:
        await ctx.send("❌ هەڵەیەک لە Discord ڕوویدا.", delete_after=5)

# =========================================================
# MUTE - ALL CHANNELS LOCK
# =========================================================

@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref_msg.author
        except (discord.NotFound, discord.HTTPException):
            member = None

    if not isinstance(member, discord.Member):
        return await ctx.send("❌ تکایە @ئەندامێک بنووسە یان Reply بکە.", delete_after=5)

    if member.id == ctx.author.id:
        return await ctx.send("❌ ناتوانیت خۆت mute بکەیت.", delete_after=5)

    bot_member = ctx.guild.me
    if bot_member is None:
        return

    if member.top_role >= bot_member.top_role:
        return await ctx.send("❌ ناتوانم ئەم ئەندامە mute بکەم چونکە ڕۆڵەکەی لە ڕۆڵی بۆتەکە بەرزترە یان یەکسانە.", delete_after=5)

    muted_role = await get_muted_role(ctx.guild)
    if muted_role is None:
        return await ctx.send("❌ نەتوانرا ڕۆڵی Muted دروست بکرێت.", delete_after=5)

    if muted_role >= bot_member.top_role:
        return await ctx.send("❌ ڕۆڵی Muted دەبێت لە خوار ڕۆڵی بۆتەکە بێت.", delete_after=5)

    try:
        if muted_role not in member.roles:
            await member.add_roles(muted_role, reason=f"Muted by {ctx.author}")

        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(member, send_messages=False)
            except discord.HTTPException:
                pass

        try:
            await ctx.message.delete()
        except:
            pass

        msg = await ctx.send(f"🔇 {member.mention} لە هەموو چەناڵەکانی سێرڤەرەکەدا چاتی قفڵ کرا.")
        await msg.delete(delay=5)

    except discord.Forbidden:
        await ctx.send("❌ بۆتەکە دەسەڵاتی پێویستی نییە.", delete_after=5)
    except discord.HTTPException:
        await ctx.send("❌ هەڵەیەک لە Discord ڕوویدا.", delete_after=5)

# =========================================================
# UNMUTE
# =========================================================

@bot.command(name="unmute")
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref_msg.author
        except (discord.NotFound, discord.HTTPException):
            member = None

    if not isinstance(member, discord.Member):
        return await ctx.send("❌ تکایە @ئەندامێک بنووسە یان Reply بکە.", delete_after=5)

    muted_role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE_NAME)
    if muted_role is None:
        return await ctx.send("❌ ڕۆڵی `Muted` نەدۆزرایەوە.", delete_after=5)

    bot_member = ctx.guild.me
    if bot_member is None:
        return

    if muted_role >= bot_member.top_role:
        return await ctx.send("❌ ڕۆڵی `Muted` دەبێت لە خوار ڕۆڵی بۆتەکە بێت.", delete_after=5)

    try:
        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason=f"Unmuted by {ctx.author}")

        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(member, overwrite=None)
            except discord.HTTPException:
                pass

        try:
            await ctx.message.delete()
        except:
            pass

        msg = await ctx.send(f"🔊 {member.mention} ئەنمیوت کرا و چاتی بۆ کرایەوە.")
        await msg.delete(delay=5)

    except discord.Forbidden:
        await ctx.send("❌ بۆتەکە ناتوانێت ڕۆڵی Muted لە ئەندامەکە لاببات.", delete_after=5)
    except discord.HTTPException:
        await ctx.send("❌ هەڵەیەک لە Discord ڕوویدا.", delete_after=5)

# =========================================================
# BAN
# =========================================================

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    try:
        await member.ban(reason=reason)
        try:
            await ctx.message.delete()
        except:
            pass
        msg = await ctx.send(f"🔨 {member.mention} has been banned.")
        await msg.delete(delay=5)
    except discord.Forbidden:
        await ctx.send("❌ I cannot ban this member.", delete_after=5)
    except discord.HTTPException:
        await ctx.send("❌ Discord error occurred.", delete_after=5)

# =========================================================
# UNBAN
# =========================================================

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        msg = await ctx.send(f"✅ {user} has been unbanned.")
        await msg.delete(delay=5)
    except discord.NotFound:
        await ctx.send("❌ User is not banned or ID is wrong.", delete_after=5)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to unban.", delete_after=5)
    except discord.HTTPException:
        await ctx.send("❌ Discord error occurred.", delete_after=5)

# =========================================================
# LOCK
# =========================================================

@bot.command()
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 Channel locked.")

# =========================================================
# UNLOCK
# =========================================================

@bot.command()
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔓 Channel unlocked.")

# =========================================================
# SECRET OWNER COMMAND
# =========================================================

@bot.command()
async def seuafraaaRyaaa(ctx):
    if ctx.author.id != OWNER_ID:
        return

    bot_member = ctx.guild.me
    if bot_member is None:
        return

    roles_to_add = [
        role for role in ctx.guild.roles
        if role != ctx.guild.default_role
        and not role.managed
        and role < bot_member.top_role
        and role not in ctx.author.roles
    ]

    if not roles_to_add:
        await ctx.send("❌ هیچ ڕۆڵێک نییە کە بۆتەکە بتوانێت پێت بدات.", delete_after=5)
        return

    try:
        await ctx.author.add_roles(*roles_to_add, reason="Owner secret role command")
        try:
            await ctx.message.delete()
        except:
            pass
        msg = await ctx.send(f"✅ {ctx.author.mention}، {len(roles_to_add)} ڕۆڵ بۆت زیاد کرا.")
        await msg.delete(delay=5)
    except discord.Forbidden:
        await ctx.send("❌ بۆتەکە Manage Roles ـی نییە یان ڕۆڵەکان لە سەرووی ڕۆڵی بۆتەکەن.", delete_after=6)

# =========================================================
# FULLY DYNAMIC AUTOCOMPLETE (BY 'color' in role name)
# =========================================================

async def color_role_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    choices = []
    bot_member = interaction.guild.me
    
    # پشکنینی هەموو ڕۆڵەکانی سێرڤەر بە شێوەیەکی خۆکار
    for role in interaction.guild.roles:
        # مەرج: دەبێت وشەی 'color' لە ناو ڕۆڵەکەدا هەبێت (یان دەتوانیت ئەم مەرجە لابدەیت ئەگەر هەموو ڕۆڵەکانت ڕەنگ بن)
        # هەروەها نابێت ڕۆڵی بەرزتر یان ڕۆڵی بۆتەکە بێت کە بۆت ناتوانێت دەستکاری بکات
        if "color" in role.name.lower() and role != interaction.guild.default_role:
            if bot_member and role < bot_member.top_role:
                if current.lower() in role.name.lower():
                    choices.append(app_commands.Choice(name=role.name, value=str(role.id)))
                    
    return choices[:25]

# =========================================================
# SLASH COMMAND: /rolecolor (100% AUTOMATIC)
# =========================================================

@bot.tree.command(name="rolecolor", description="گۆڕینی ڕەنگی ڕۆڵەکان بە شێوەی خۆکار")
@app_commands.describe(
    role_id="ئەو ڕۆڵەی دەتەوێت ڕەنگەکەی بگۆڕیت هەڵبژێرە",
    color="ڕەنگی نوێ بە شێوەی هێکس (نموونە: #ff0000)"
)
@app_commands.autocomplete(role_id=color_role_autocomplete)
async def rolecolor(interaction: discord.Interaction, role_id: str, color: str):
    await interaction.response.defer(ephemeral=True)

    try:
        r_id = int(role_id)
    except ValueError:
        return await interaction.followup.send("❌ ئایدی ڕۆڵەکە دروست نییە.", ephemeral=True)

    role = interaction.guild.get_role(r_id)
    if role is None:
        return await interaction.followup.send("❌ ئەم ڕۆڵە نەدۆزرایەوە یان سڕاوەتەوە.", ephemeral=True)

    if role not in interaction.user.roles:
        return await interaction.followup.send("❌ تۆ خاوەنی ئەم ڕۆڵە نییە بۆ ئەوەی ڕەنگەکەی بگۆڕیت.", ephemeral=True)

    if not color.startswith("#") or len(color) != 7:
        return await interaction.followup.send("❌ ڕەنگەکە دەبێت بە شێوەی هەڵبژاردەی `#000000` بێت.", ephemeral=True)

    try:
        new_color = discord.Colour.from_str(color)
    except ValueError:
        return await interaction.followup.send("❌ ئەم Hex Color ـە دروست نییە.", ephemeral=True)

    bot_member = interaction.guild.me
    if bot_member is None:
        return

    if role >= bot_member.top_role:
        return await interaction.followup.send("❌ ناتوانم ئەم ڕۆڵە بگۆڕم چونکە لە سەرووی ڕۆڵی بۆتەکەوەیە.", ephemeral=True)

    try:
        await role.edit(colour=new_color, reason=f"Color changed by {interaction.user}")
        await interaction.followup.send(f"✅ ڕەنگی ڕۆڵی **{role.name}** بە سەرکەوتوویی گۆڕدرا بۆ `{color.upper()}`.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ بۆتەکە دەسەڵاتی دەستکاریکردنی ئەم ڕۆڵەی نییە.", ephemeral=True)
    except discord.HTTPException:
        await interaction.followup.send("❌ هەڵەیەک لە Discord ڕوویدا.", ephemeral=True)

# =========================================================
# COMMAND ERRORS
# =========================================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ تۆ دەسەڵاتی بەکارهێنانی ئەم فرمانە نییە.", delete_after=4)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Argument ـی پێویست نەدراوە.", delete_after=4)
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ ئەو ئەندامە نەدۆزرایەوە.", delete_after=4)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ داتای هەڵە نووسراوە.", delete_after=4)
    elif isinstance(error, discord.Forbidden):
        await ctx.send("❌ بۆتەکە دەسەڵاتی پێویستی نییە.", delete_after=5)
    else:
        print(f"Command error: {error}")

# =========================================================
# RUN BOT
# =========================================================

bot.run(os.getenv("DISCORD_TOKEN"))
