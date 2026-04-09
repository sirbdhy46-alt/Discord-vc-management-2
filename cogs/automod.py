import discord
from discord.ext import commands
import json
import os
import logging
import re
import time
from collections import defaultdict

logger = logging.getLogger(__name__)
DATA_FILE = "data/automod.json"
WARNS_FILE = "data/warnings.json"

BAD_WORDS = ["nigger", "nigga", "faggot", "retard", "kys", "kill yourself"]
SPAM_THRESHOLD = 5
SPAM_INTERVAL = 5
CAPS_THRESHOLD = 0.7
CAPS_MIN_LENGTH = 10
INVITE_PATTERN = re.compile(r"(discord\.gg|discord\.com\/invite)\/[a-zA-Z0-9]+")

def load_data(f):
    if os.path.exists(f):
        with open(f, "r") as fp:
            return json.load(fp)
    return {}

def save_data(data, f):
    os.makedirs("data", exist_ok=True)
    with open(f, "w") as fp:
        json.dump(data, fp, indent=2)

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_data(DATA_FILE)
        self.warns = load_data(WARNS_FILE)
        self.spam_tracker = defaultdict(list)
        self.muted_users = set()

    def get_config(self, guild_id):
        gid = str(guild_id)
        if gid not in self.config:
            self.config[gid] = {
                "anti_spam": True,
                "anti_caps": True,
                "anti_invite": True,
                "anti_badwords": True,
                "log_channel": None,
                "warn_threshold": 3,
            }
        return self.config[gid]

    def get_warns(self, guild_id, user_id):
        gid = str(guild_id)
        uid = str(user_id)
        if gid not in self.warns:
            self.warns[gid] = {}
        if uid not in self.warns[gid]:
            self.warns[gid][uid] = []
        return self.warns[gid][uid]

    async def log_action(self, guild, action, member, reason):
        cfg = self.get_config(guild.id)
        log_id = cfg.get("log_channel")
        if not log_id:
            log_ch = discord.utils.find(lambda c: any(k in c.name.lower() for k in ["mod-log", "logs", "mod-logs"]), guild.text_channels)
        else:
            log_ch = guild.get_channel(int(log_id))
        if not log_ch:
            return
        embed = discord.Embed(title=f"⚠️ AutoMod — {action}", color=0xff6b9d)
        embed.add_field(name="Member", value=f"{member.mention} (`{member}`)", inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.set_footer(text=f"User ID: {member.id}")
        try:
            await log_ch.send(embed=embed)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        if message.author.guild_permissions.manage_messages:
            return

        cfg = self.get_config(message.guild.id)
        content = message.content

        if cfg.get("anti_badwords"):
            lowered = content.lower()
            for word in BAD_WORDS:
                if word in lowered:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    await message.channel.send(
                        embed=discord.Embed(description=f"✗ {message.author.mention} Watch your language!", color=0xff6b9d),
                        delete_after=5
                    )
                    await self.add_warn(message.guild, message.author, "Bad language (automod)")
                    await self.log_action(message.guild, "Bad Word Detected", message.author, f"Used: `{word}`")
                    return

        if cfg.get("anti_invite") and INVITE_PATTERN.search(content):
            try:
                await message.delete()
            except Exception:
                pass
            await message.channel.send(
                embed=discord.Embed(description=f"✗ {message.author.mention} No invite links allowed!", color=0xff6b9d),
                delete_after=5
            )
            await self.add_warn(message.guild, message.author, "Sent invite link")
            await self.log_action(message.guild, "Invite Link", message.author, "Sent a Discord invite link")
            return

        if cfg.get("anti_caps") and len(content) >= CAPS_MIN_LENGTH:
            letters = [c for c in content if c.isalpha()]
            if letters and sum(1 for c in letters if c.isupper()) / len(letters) >= CAPS_THRESHOLD:
                try:
                    await message.delete()
                except Exception:
                    pass
                await message.channel.send(
                    embed=discord.Embed(description=f"✗ {message.author.mention} Too many caps!", color=0xff6b9d),
                    delete_after=5
                )
                return

        if cfg.get("anti_spam"):
            key = f"{message.guild.id}:{message.author.id}"
            now = time.time()
            self.spam_tracker[key] = [t for t in self.spam_tracker[key] if now - t < SPAM_INTERVAL]
            self.spam_tracker[key].append(now)
            if len(self.spam_tracker[key]) >= SPAM_THRESHOLD:
                self.spam_tracker[key] = []
                try:
                    await message.channel.purge(limit=10, check=lambda m: m.author == message.author)
                except Exception:
                    pass
                await message.channel.send(
                    embed=discord.Embed(description=f"✗ {message.author.mention} Slow down! Spam detected.", color=0xff6b9d),
                    delete_after=5
                )
                await self.add_warn(message.guild, message.author, "Spamming (automod)")
                await self.log_action(message.guild, "Spam Detected", message.author, "Sent messages too fast")

    async def add_warn(self, guild, member, reason):
        warns = self.get_warns(guild.id, member.id)
        warns.append({"reason": reason, "time": time.time()})
        save_data(self.warns, WARNS_FILE)
        cfg = self.get_config(guild.id)
        threshold = cfg.get("warn_threshold", 3)
        if len(warns) >= threshold:
            muted_role = discord.utils.get(guild.roles, name="muted")
            if muted_role and muted_role not in member.roles:
                try:
                    await member.add_roles(muted_role, reason="AutoMod: Too many warnings")
                    await self.log_action(guild, "Auto-Mute", member, f"Reached {threshold} warnings")
                except Exception:
                    pass

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason"):
        await self.add_warn(ctx.guild, member, reason)
        warns = self.get_warns(ctx.guild.id, member.id)
        embed = discord.Embed(
            title="⚠️﹒ Warning Issued",
            description=f"**{member.mention}** has been warned!\n**Reason:** {reason}\n**Total Warnings:** {len(warns)}",
            color=0xfbbf24
        )
        await ctx.send(embed=embed)
        try:
            await member.send(embed=discord.Embed(
                description=f"⚠️ You were warned in **{ctx.guild.name}**\n**Reason:** {reason}\n**Total:** {len(warns)} warning(s)",
                color=0xfbbf24
            ))
        except Exception:
            pass

    @commands.command(name="warnings", aliases=["warns"])
    async def warnings(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        warns = self.get_warns(ctx.guild.id, member.id)
        embed = discord.Embed(title=f"⚠️﹒ Warnings for {member.display_name}", color=0xfbbf24)
        if not warns:
            embed.description = "No warnings! Keep it up ✿"
        else:
            for i, w in enumerate(warns, 1):
                embed.add_field(
                    name=f"Warning {i}",
                    value=w["reason"],
                    inline=False
                )
        await ctx.send(embed=embed)

    @commands.command(name="clearwarns", aliases=["clearwarnings"])
    @commands.has_permissions(manage_messages=True)
    async def clear_warns(self, ctx, member: discord.Member):
        gid = str(ctx.guild.id)
        uid = str(member.id)
        if gid in self.warns and uid in self.warns[gid]:
            self.warns[gid][uid] = []
            save_data(self.warns, WARNS_FILE)
        embed = discord.Embed(description=f"✿ Cleared all warnings for **{member.display_name}**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @commands.command(name="automod")
    @commands.has_permissions(administrator=True)
    async def automod_settings(self, ctx, setting: str = None, value: str = None):
        cfg = self.get_config(ctx.guild.id)
        toggles = ["anti_spam", "anti_caps", "anti_invite", "anti_badwords"]

        if setting and setting in toggles:
            current = cfg.get(setting, True)
            cfg[setting] = not current
            save_data(self.config, DATA_FILE)
            status = "enabled" if cfg[setting] else "disabled"
            return await ctx.send(embed=discord.Embed(
                description=f"✿ **{setting}** is now **{status}**!",
                color=0xb5a8d5
            ))

        embed = discord.Embed(title="◎﹒ AutoMod Settings", color=0xb5a8d5)
        for toggle in toggles:
            status = "✅ On" if cfg.get(toggle, True) else "❌ Off"
            embed.add_field(name=toggle, value=status, inline=True)
        embed.set_footer(text="Use -automod <setting> to toggle")
        await ctx.send(embed=embed)

    @commands.command(name="setlogchannel")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        cfg = self.get_config(ctx.guild.id)
        cfg["log_channel"] = str(channel.id)
        save_data(self.config, DATA_FILE)
        await ctx.send(embed=discord.Embed(description=f"✿ Log channel set to {channel.mention}!", color=0xb5a8d5))

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
