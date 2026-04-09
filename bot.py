import discord
from discord.ext import commands, tasks
import os
import asyncio
import json
import logging
import random
import itertools
from keepalive import keep_alive

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
PREFIX = "-"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

STATUSES = [
    ("-help ﹒ ✿﹒⟡", discord.ActivityType.watching),
    ("over the server ﹒ ⊹﹒✶", discord.ActivityType.watching),
    ("your vibes ﹒ ♡﹒◎", discord.ActivityType.listening),
    ("the chaos ﹒ ◍﹒✦", discord.ActivityType.watching),
    ("you sleep ﹒ ᶻz﹒░", discord.ActivityType.watching),
    ("-invite ﹒ ⟡﹒❀", discord.ActivityType.playing),
    ("everyone's secrets ﹒ ◖﹒✸", discord.ActivityType.listening),
    ("the stars ﹒ ★﹒⿴", discord.ActivityType.watching),
]
status_cycle = itertools.cycle(STATUSES)

COGS = [
    "cogs.vc_manager",
    "cogs.roles",
    "cogs.setup",
    "cogs.levels",
    "cogs.invites",
    "cogs.welcome",
    "cogs.economy",
    "cogs.fun",
    "cogs.giveaway",
    "cogs.automod",
    "cogs.starboard",
    "cogs.events",
]

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded cog: {cog}")
        except Exception as e:
            logger.error(f"Failed to load cog {cog}: {e}")

@tasks.loop(seconds=30)
async def rotate_status():
    name, activity_type = next(status_cycle)
    await bot.change_presence(activity=discord.Activity(type=activity_type, name=name))

@bot.event
async def on_ready():
    logger.info(f"Bot logged in as {bot.user} (ID: {bot.user.id})")
    rotate_status.start()
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"Failed to sync: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(description="✗ You don't have permission to do that!", color=0xff6b9d)
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.MemberNotFound):
        embed = discord.Embed(description="✗ Member not found!", color=0xff6b9d)
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(description=f"✗ Missing argument: `{error.param.name}`", color=0xff6b9d)
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        logger.error(f"Command error in {ctx.command}: {error}")

@bot.command(name="help")
async def help_cmd(ctx, category: str = None):
    CATEGORIES = {
        "vc": ("◖﹒ Voice Channels", [
            "`-vc name <name>` — Rename your VC",
            "`-vc limit <n>` — Set user limit",
            "`-vc lock / unlock` — Lock/Unlock VC",
            "`-vc hide / show` — Hide/Show VC",
            "`-vc kick / ban @user` — Remove someone",
            "`-vc invite @user` — Invite to private VC",
            "`-vc transfer @user` — Give ownership",
        ]),
        "levels": ("⊹﹒ Levels", [
            "`-rank [@user]` — View rank card",
            "`-leaderboard` — Top 10 members",
            "`-setxp @user <xp>` — Set XP (admin)",
        ]),
        "economy": ("ıllı﹒ Economy", [
            "`-balance [@user]` — Check coins",
            "`-daily` — Claim daily coins",
            "`-work` — Work for coins",
            "`-crime` — Risk it for big coins",
            "`-rob @user` — Rob someone",
            "`-give @user <amount>` — Give coins",
            "`-shop` — View item shop",
            "`-buy <item>` — Buy an item",
            "`-inventory` — View your items",
            "`-richest` — Top 10 richest",
        ]),
        "fun": ("✿﹒ Fun", [
            "`-8ball <question>` — Ask the magic ball",
            "`-ship @user1 @user2` — Ship two people",
            "`-roast @user` — Roast someone 💀",
            "`-compliment @user` — Compliment someone",
            "`-confess <text>` — Anonymous confession",
            "`-hug @user` — Hug someone",
            "`-slap @user` — Slap someone",
            "`-rps <r/p/s>` — Rock paper scissors",
            "`-coinflip` — Flip a coin",
            "`-roll <sides>` — Roll a die",
            "`-wouldyourather` — Would you rather",
            "`-neverhaveiever` — Never have I ever",
            "`-dare` — Get a dare",
            "`-truth` — Get a truth question",
        ]),
        "invites": ("⟡﹒ Invites", [
            "`-invites [@user]` — Check invite count",
            "`-inviteleaderboard` — Top inviters",
            "`-inviteinfo @user` — Who invited who",
        ]),
        "events": ("★﹒ Events", [
            "`-poll <question>` — Create a poll",
            "`-giveaway <time> <prize>` — Start giveaway",
            "`-reroll` — Reroll last giveaway",
            "`-birthday set <dd/mm>` — Set your birthday",
            "`-birthday check [@user]` — Check birthday",
            "`-counting` — Check counting channel stats",
        ]),
        "mod": ("◎﹒ Moderation", [
            "`-kick @user [reason]` — Kick",
            "`-ban @user [reason]` — Ban",
            "`-unban <user>` — Unban",
            "`-mute @user` — Mute",
            "`-unmute @user` — Unmute",
            "`-purge <amount>` — Delete messages",
            "`-warn @user <reason>` — Warn member",
            "`-warnings @user` — View warnings",
            "`-clearwarns @user` — Clear warnings",
        ]),
        "setup": ("⿴﹒ Setup", [
            "`-setup` — Full server setup",
            "`-setuproles` — Create all roles",
            "`-setupvcs` — Register JTC channels",
            "`-starweek @user` — Set star of the week",
            "`-serverinfo` — Server info",
            "`-memberinfo [@user]` — Member info",
            "`-roles` — View all roles",
            "`-giverole @user <role>` — Give role (mod+)",
            "`-removerole @user <role>` — Remove role (mod+)",
        ]),
    }

    if category and category.lower() in CATEGORIES:
        cat_name, fields = CATEGORIES[category.lower()]
        embed = discord.Embed(title=f"✿﹒ {cat_name} Commands", description="\n".join(fields), color=0xb5a8d5)
        embed.set_footer(text=f"﹒✶﹒ Use -help for all categories ﹒✶﹒")
        return await ctx.send(embed=embed)

    embed = discord.Embed(
        title="✿﹒⟡﹒ Commands ﹒⟡﹒✿",
        description=(
            "Use `-help <category>` for detailed commands!\n\n"
            "◖﹒ `-help vc` — Voice channels\n"
            "⊹﹒ `-help levels` — Leveling system\n"
            "ıllı﹒ `-help economy` — Economy & coins\n"
            "✿﹒ `-help fun` — Fun & games\n"
            "⟡﹒ `-help invites` — Invite tracker\n"
            "★﹒ `-help events` — Polls, giveaways, birthdays\n"
            "◎﹒ `-help mod` — Moderation\n"
            "⿴﹒ `-help setup` — Server setup"
        ),
        color=0xb5a8d5
    )
    embed.set_footer(text="﹒✶﹒⊹﹒ Made with ♡ ﹒⊹﹒✶﹒")
    await ctx.send(embed=embed)

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    if not TOKEN:
        logger.error("DISCORD_BOT_TOKEN not set!")
        exit(1)
    keep_alive()
    asyncio.run(main())
