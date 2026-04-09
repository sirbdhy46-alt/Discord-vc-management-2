import discord
from discord.ext import commands
import json
import os
import logging
import random

logger = logging.getLogger(__name__)
DATA_FILE = "data/welcome.json"

WELCOME_MESSAGES = [
    "omg {mention} just walked in, everyone act natural 💀",
    "{mention} arrived!! the vibes just got 10x better ✿",
    "look who decided to show up — {mention} 👀",
    "a wild {mention} appeared!! 🌟",
    "welcome {mention}! we've been waiting for u ♡",
    "{mention} just joined! someone give them a cookie 🍪",
    "the legends say when {mention} joins, good vibes follow ⟡",
    "{mention} is here!! chaos level: activated 💫",
    "slay {mention} just entered the server ✿﹒⟡",
    "new member just dropped — {mention} 🔥",
]

LEAVE_MESSAGES = [
    "{name} left the server.. the void grows 🕳️",
    "{name} said bye bye 💀",
    "{name} dipped, they'll be missed ᶻz",
    "rip {name}, gone but not forgotten ◎",
    "{name} has left the building 👋",
]

AUTO_ROLES = ["◖ vc member"]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_data()

    def get_guild_config(self, guild_id):
        gid = str(guild_id)
        if gid not in self.config:
            self.config[gid] = {
                "welcome_channel": None,
                "leave_channel": None,
                "auto_roles": AUTO_ROLES,
            }
        return self.config[gid]

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        cfg = self.get_guild_config(guild.id)

        for role_name in cfg.get("auto_roles", []):
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                try:
                    await member.add_roles(role)
                except Exception as e:
                    logger.error(f"Auto-role error: {e}")

        channel_id = cfg.get("welcome_channel")
        if not channel_id:
            channel = discord.utils.find(
                lambda c: any(k in c.name.lower() for k in ["welcome", "general", "general-chat", "chat"]),
                guild.text_channels
            )
        else:
            channel = guild.get_channel(int(channel_id))

        if not channel:
            return

        msg = random.choice(WELCOME_MESSAGES).format(mention=member.mention, name=member.display_name)

        embed = discord.Embed(
            description=f"✿﹒ {msg}",
            color=0xb5a8d5
        )
        embed.set_author(name=f"Welcome to {guild.name}! ⟡", icon_url=guild.icon.url if guild.icon else None)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="◖ Member", value=member.mention, inline=True)
        embed.add_field(name="⟡ Account", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="◎ You are member", value=f"**#{guild.member_count}**", inline=True)
        embed.add_field(
            name="✶ Get started",
            value="✿ Read the rules\n⟡ Grab your roles\n◖ Introduce yourself\n★ Have fun!",
            inline=False
        )
        embed.set_image(url=member.display_avatar.with_size(512).url)
        embed.set_footer(text=f"﹒✶﹒⊹﹒ {guild.name} ﹒⊹﹒✶﹒")

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Welcome message error: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        cfg = self.get_guild_config(guild.id)

        channel_id = cfg.get("leave_channel") or cfg.get("welcome_channel")
        if not channel_id:
            channel = discord.utils.find(
                lambda c: any(k in c.name.lower() for k in ["welcome", "general", "general-chat"]),
                guild.text_channels
            )
        else:
            channel = guild.get_channel(int(channel_id))

        if not channel:
            return

        msg = random.choice(LEAVE_MESSAGES).format(name=member.display_name, mention=member.mention)
        embed = discord.Embed(
            description=f"ᶻz﹒ {msg}",
            color=0x94a3b8
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"We had {guild.member_count} members")
        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Leave message error: {e}")

    @commands.command(name="setwelcome")
    @commands.has_permissions(administrator=True)
    async def set_welcome(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        cfg = self.get_guild_config(ctx.guild.id)
        cfg["welcome_channel"] = str(channel.id)
        save_data(self.config)
        embed = discord.Embed(description=f"✿ Welcome channel set to {channel.mention}!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @commands.command(name="setleave")
    @commands.has_permissions(administrator=True)
    async def set_leave(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        cfg = self.get_guild_config(ctx.guild.id)
        cfg["leave_channel"] = str(channel.id)
        save_data(self.config)
        embed = discord.Embed(description=f"✿ Leave channel set to {channel.mention}!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @commands.command(name="testwelcome")
    @commands.has_permissions(administrator=True)
    async def test_welcome(self, ctx):
        await self.on_member_join(ctx.author)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
