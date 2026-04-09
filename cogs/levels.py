import discord
from discord.ext import commands
import json
import os
import random
import logging
import time

logger = logging.getLogger(__name__)

DATA_FILE = "data/levels.json"

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

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.cooldowns = {}

    def get_member_data(self, guild_id, member_id):
        gid = str(guild_id)
        mid = str(member_id)
        if gid not in self.data:
            self.data[gid] = {}
        if mid not in self.data[gid]:
            self.data[gid][mid] = {"xp": 0, "level": 0, "messages": 0}
        return self.data[gid][mid]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        key = f"{message.guild.id}:{message.author.id}"
        now = time.time()
        if key in self.cooldowns and now - self.cooldowns[key] < 60:
            return
        self.cooldowns[key] = now

        member_data = self.get_member_data(message.guild.id, message.author.id)
        xp_gain = random.randint(15, 40)
        old_level = member_data["level"]
        member_data["xp"] += xp_gain
        member_data["messages"] += 1
        new_level = level_from_xp(member_data["xp"])
        member_data["level"] = new_level
        save_data(self.data)

        if new_level > old_level:
            await self.handle_level_up(message, message.author, new_level)

    async def handle_level_up(self, message, member, new_level):
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
            role = discord.utils.get(message.guild.roles, name=role_reward)
            if role and role not in member.roles:
                try:
                    for old_role_name in LEVEL_ROLES.values():
                        old_role = discord.utils.get(message.guild.roles, name=old_role_name)
                        if old_role and old_role in member.roles and old_role != role:
                            await member.remove_roles(old_role)
                    await member.add_roles(role)
                    embed.add_field(name="New Role!", value=f"You earned **{role_reward}**! ✿")
                except Exception as e:
                    logger.error(f"Error assigning level role: {e}")

        try:
            await message.channel.send(embed=embed)
        except Exception:
            pass

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        member_data = self.get_member_data(ctx.guild.id, member.id)
        level = member_data["level"]
        xp = member_data["xp"]
        msgs = member_data["messages"]
        xp_needed = xp_for_level(level + 1)
        progress = int((xp / xp_needed) * 20)
        bar = "█" * progress + "░" * (20 - progress)

        embed = discord.Embed(
            title=f"⟡﹒ {member.display_name}'s Rank",
            color=0xb5a8d5
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp}** / {xp_needed}", inline=True)
        embed.add_field(name="Messages", value=f"**{msgs}**", inline=True)
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

        embed.set_footer(text="﹒✶﹒⊹﹒ Keep chatting to level up! ﹒⊹﹒✶﹒")
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
            description="Top 10 most active members!",
            color=0xb5a8d5
        )

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        rows = []
        for i, (mid, mdata) in enumerate(sorted_members):
            member = ctx.guild.get_member(int(mid))
            name = member.display_name if member else f"User {mid}"
            rows.append(f"{medals[i]} **{name}** — Lv.**{mdata['level']}** ({mdata['xp']} XP)")

        embed.description = "\n".join(rows) if rows else "No data yet!"
        embed.set_footer(text="﹒✶﹒⊹﹒ Keep chatting to climb the ranks! ﹒⊹﹒✶﹒")
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
