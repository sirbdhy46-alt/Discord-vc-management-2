import discord
from discord.ext import commands
import json
import os
import random
import logging
import time

logger = logging.getLogger(__name__)

DATA_FILE = "data/levels.json"
CONFIG_FILE = "data/levels_config.json"

LEVEL_ROLES = {
    1: "░ newbie",
    5: "◌ wanderer",
    10: "✦ regular",
    15: "⟡ vibe member",
    20: "✿ bloomer",
    30: "◎ known face",
    40: "★ rising star",
    50: "❀ legend",
    75: "✸ elite",
    100: "⊹ immortal",
}

def xp_for_level(level):
    return int(100 * (level ** 1.5))

def level_from_xp(xp):
    level = 0
    while xp >= xp_for_level(level + 1):
        level += 1
    return level

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.config = load_config()
        self.vc_join_times = {}

    def get_member_data(self, guild_id, member_id):
        gid = str(guild_id)
        mid = str(member_id)
        if gid not in self.data:
            self.data[gid] = {}
        if mid not in self.data[gid]:
            self.data[gid][mid] = {"xp": 0, "level": 0, "vc_minutes": 0}
        if "vc_minutes" not in self.data[gid][mid]:
            self.data[gid][mid]["vc_minutes"] = 0
        return self.data[gid][mid]

    def get_level_channel(self, guild_id):
        gid = str(guild_id)
        channel_id = self.config.get(gid, {}).get("level_channel")
        if channel_id:
            return self.bot.get_channel(int(channel_id))
        return None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        key = f"{member.guild.id}:{member.id}"

        # User joined a VC
        if after.channel and not before.channel:
            self.vc_join_times[key] = time.time()

        # User left a VC
        elif before.channel and not after.channel:
            if key in self.vc_join_times:
                seconds = time.time() - self.vc_join_times.pop(key)
                minutes = int(seconds / 60)
                if minutes < 1:
                    return
                xp_gain = minutes * random.randint(4, 8)
                member_data = self.get_member_data(member.guild.id, member.id)
                old_level = member_data["level"]
                member_data["xp"] += xp_gain
                member_data["vc_minutes"] += minutes
                new_level = level_from_xp(member_data["xp"])
                member_data["level"] = new_level
                save_data(self.data)

                if new_level > old_level:
                    await self.handle_level_up(member.guild, member, new_level)

        # User switched channels
        elif before.channel and after.channel and before.channel != after.channel:
            if key not in self.vc_join_times:
                self.vc_join_times[key] = time.time()

    async def handle_level_up(self, guild, member, new_level):
        embed = discord.Embed(
            title="⟡﹒ Level Up!",
            description=f"✿ **{member.display_name}** reached **Level {new_level}**!",
            color=0xb5a8d5
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        role_reward = None
        for level_req in sorted(LEVEL_ROLES.keys(), reverse=True):
            if new_level >= level_req:
                role_reward = LEVEL_ROLES[level_req]
                break

        if role_reward:
            role = discord.utils.get(guild.roles, name=role_reward)
            if role and role not in member.roles:
                try:
                    for old_role_name in LEVEL_ROLES.values():
                        old_role = discord.utils.get(guild.roles, name=old_role_name)
                        if old_role and old_role in member.roles and old_role != role:
                            await member.remove_roles(old_role)
                    await member.add_roles(role)
                    embed.add_field(name="New Role!", value=f"You earned **{role_reward}**! ✿")
                except Exception as e:
                    logger.error(f"Error assigning level role: {e}")

        channel = self.get_level_channel(guild.id)
        if not channel:
            channel = discord.utils.find(
                lambda c: any(k in c.name.lower() for k in ["level", "rank", "general", "chat"]),
                guild.text_channels
            )
        if channel:
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

    @commands.command(name="setlevelchannel")
    @commands.has_permissions(administrator=True)
    async def set_level_channel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gid = str(ctx.guild.id)
        if gid not in self.config:
            self.config[gid] = {}
        self.config[gid]["level_channel"] = str(channel.id)
        save_config(self.config)
        embed = discord.Embed(
            description=f"✿ Level-up notifications will now go to {channel.mention}!",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        member_data = self.get_member_data(ctx.guild.id, member.id)
        level = member_data["level"]
        xp = member_data["xp"]
        vc_mins = member_data.get("vc_minutes", 0)
        xp_needed = xp_for_level(level + 1)
        progress = int((xp / xp_needed) * 20) if xp_needed > 0 else 0
        bar = "█" * progress + "░" * (20 - progress)

        hours = vc_mins // 60
        mins = vc_mins % 60
        vc_time = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

        embed = discord.Embed(
            title=f"⟡﹒ {member.display_name}'s Rank",
            color=0xb5a8d5
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp}** / {xp_needed}", inline=True)
        embed.add_field(name="VC Time", value=f"**{vc_time}**", inline=True)
        embed.add_field(name="Progress", value=f"`[{bar}]`", inline=False)

        role_name = None
        for level_req in sorted(LEVEL_ROLES.keys(), reverse=True):
            if level >= level_req:
                role_name = LEVEL_ROLES[level_req]
                break
        if role_name:
            embed.add_field(name="Role", value=f"**{role_name}**")

        next_role = None
        for level_req in sorted(LEVEL_ROLES.keys()):
            if level < level_req:
                next_role = (level_req, LEVEL_ROLES[level_req])
                break
        if next_role:
            embed.add_field(name="Next Role At", value=f"Level **{next_role[0]}** → **{next_role[1]}**")

        embed.set_footer(text="﹒✶﹒⊹﹒ Spend time in VC to level up! ﹒⊹﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard(self, ctx):
        gid = str(ctx.guild.id)
        if gid not in self.data:
            return await ctx.send("No level data yet!")

        members_data = self.data[gid]
        sorted_members = sorted(members_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]

        embed = discord.Embed(
            title="✶﹒ Leaderboard ﹒✶",
            description="Top 10 most active VC members!",
            color=0xb5a8d5
        )

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        rows = []
        for i, (mid, mdata) in enumerate(sorted_members):
            member = ctx.guild.get_member(int(mid))
            name = member.display_name if member else f"User {mid}"
            vc_mins = mdata.get("vc_minutes", 0)
            hours = vc_mins // 60
            mins = vc_mins % 60
            vc_time = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            rows.append(f"{medals[i]} **{name}** — Lv.**{mdata['level']}** ({mdata['xp']} XP) ﹒ {vc_time} in VC")

        embed.description = "\n".join(rows) if rows else "No data yet!"
        embed.set_footer(text="﹒✶﹒⊹﹒ Keep chilling in VC to climb the ranks! ﹒⊹﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="setxp")
    @commands.has_permissions(administrator=True)
    async def set_xp(self, ctx, member: discord.Member, xp: int):
        member_data = self.get_member_data(ctx.guild.id, member.id)
        member_data["xp"] = xp
        member_data["level"] = level_from_xp(xp)
        save_data(self.data)
        embed = discord.Embed(
            description=f"✿ Set **{member.display_name}**'s XP to **{xp}** (Level {member_data['level']})!",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Levels(bot))
