import discord
from discord.ext import commands
import json
import os
import logging

logger = logging.getLogger(__name__)
DATA_FILE = "data/starboard.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def get_config(self, guild_id):
        gid = str(guild_id)
        if gid not in self.data:
            self.data[gid] = {"channel": None, "threshold": 3, "posted": {}}
        return self.data[gid]

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) not in ["⭐", "🌟", "✨"]:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        cfg = self.get_config(guild.id)
        if not cfg.get("channel"):
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return

        if message.author.bot:
            return

        star_count = 0
        for reaction in message.reactions:
            if str(reaction.emoji) in ["⭐", "🌟", "✨"]:
                star_count += reaction.count

        threshold = cfg.get("threshold", 3)
        msg_id = str(message.id)

        if star_count < threshold:
            return

        sb_channel = guild.get_channel(int(cfg["channel"]))
        if not sb_channel:
            return

        if msg_id in cfg.get("posted", {}):
            try:
                sb_msg = await sb_channel.fetch_message(int(cfg["posted"][msg_id]))
                embed = sb_msg.embeds[0] if sb_msg.embeds else None
                if embed:
                    embed.set_footer(text=f"⭐ {star_count} stars | #{channel.name}")
                    await sb_msg.edit(embed=embed)
            except Exception:
                pass
            return

        embed = discord.Embed(
            description=message.content or "*[No text — see attachment]*",
            color=0xfbbf24,
            timestamp=message.created_at
        )
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url
        )

        if message.attachments:
            embed.set_image(url=message.attachments[0].url)

        embed.add_field(name="Original", value=f"[Jump to message]({message.jump_url})", inline=False)
        embed.set_footer(text=f"⭐ {star_count} stars | #{channel.name}")

        sb_msg = await sb_channel.send(
            content=f"⭐ **{star_count}** | {channel.mention}",
            embed=embed
        )
        cfg["posted"][msg_id] = str(sb_msg.id)
        save_data(self.data)

    @commands.command(name="setstarboard")
    @commands.has_permissions(administrator=True)
    async def set_starboard(self, ctx, channel: discord.TextChannel = None, threshold: int = 3):
        channel = channel or ctx.channel
        cfg = self.get_config(ctx.guild.id)
        cfg["channel"] = str(channel.id)
        cfg["threshold"] = threshold
        save_data(self.data)
        embed = discord.Embed(
            description=f"⭐ Starboard set to {channel.mention} with threshold **{threshold} stars**!",
            color=0xfbbf24
        )
        await ctx.send(embed=embed)

    @commands.command(name="starboardinfo")
    async def starboard_info(self, ctx):
        cfg = self.get_config(ctx.guild.id)
        ch_id = cfg.get("channel")
        ch = ctx.guild.get_channel(int(ch_id)) if ch_id else None
        embed = discord.Embed(title="⭐﹒ Starboard Info", color=0xfbbf24)
        embed.add_field(name="Channel", value=ch.mention if ch else "Not set", inline=True)
        embed.add_field(name="Threshold", value=f"**{cfg.get('threshold', 3)}** stars", inline=True)
        embed.add_field(name="Posts", value=f"**{len(cfg.get('posted', {}))}** messages starred", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Starboard(bot))
