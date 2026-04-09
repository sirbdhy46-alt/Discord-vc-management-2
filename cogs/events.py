import discord
from discord.ext import commands
from discord.ext import tasks
import json
import os
import logging
import asyncio
import random
import datetime

logger = logging.getLogger(__name__)
BIRTHDAY_FILE = "data/birthdays.json"
COUNTING_FILE = "data/counting.json"
POLL_FILE = "data/polls.json"

def load_json(f):
    if os.path.exists(f):
        with open(f, "r") as fp:
            return json.load(fp)
    return {}

def save_json(data, f):
    os.makedirs("data", exist_ok=True)
    with open(f, "w") as fp:
        json.dump(data, fp, indent=2)

POLL_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthdays = load_json(BIRTHDAY_FILE)
        self.counting = load_json(COUNTING_FILE)
        self.polls = load_json(POLL_FILE)
        self.birthday_check.start()

    def cog_unload(self):
        self.birthday_check.cancel()

    # ─── POLLS ─────────────────────────────────────────────────────────────────

    @commands.command(name="poll")
    async def poll(self, ctx, *, question: str):
        parts = [p.strip() for p in question.split("|")]
        question_text = parts[0]
        options = parts[1:] if len(parts) > 1 else None

        embed = discord.Embed(title=f"📊﹒ {question_text}", color=0xb5a8d5)
        embed.set_footer(text=f"Poll by {ctx.author.display_name} ﹒✶﹒ React to vote!")

        if options and len(options) >= 2:
            desc = []
            for i, opt in enumerate(options[:10]):
                desc.append(f"{POLL_EMOJIS[i]} {opt}")
            embed.description = "\n".join(desc)
            msg = await ctx.send(embed=embed)
            for i in range(len(options[:10])):
                await msg.add_reaction(POLL_EMOJIS[i])
        else:
            embed.description = "React with ✅ for Yes or ❌ for No!"
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

        await ctx.message.delete()

    @commands.command(name="quickpoll", aliases=["qp"])
    async def quickpoll(self, ctx, *, question: str):
        embed = discord.Embed(
            title=f"◎﹒ Quick Poll",
            description=f"**{question}**",
            color=0xb5a8d5
        )
        embed.set_footer(text=f"By {ctx.author.display_name}")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await msg.add_reaction("🤷")
        try:
            await ctx.message.delete()
        except Exception:
            pass

    # ─── BIRTHDAYS ─────────────────────────────────────────────────────────────

    @commands.group(name="birthday", aliases=["bday"], invoke_without_command=True)
    async def birthday(self, ctx):
        embed = discord.Embed(
            description="Use `-birthday set <dd/mm>` to set your birthday!\nUse `-birthday check [@user]` to view.",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @birthday.command(name="set")
    async def birthday_set(self, ctx, date: str):
        try:
            day, month = map(int, date.split("/"))
            assert 1 <= day <= 31 and 1 <= month <= 12
        except Exception:
            return await ctx.send(embed=discord.Embed(description="✗ Use format: `dd/mm` (e.g. 25/12)", color=0xff6b9d))

        gid = str(ctx.guild.id)
        uid = str(ctx.author.id)
        if gid not in self.birthdays:
            self.birthdays[gid] = {}
        self.birthdays[gid][uid] = {"day": day, "month": month}
        save_json(self.birthdays, BIRTHDAY_FILE)

        embed = discord.Embed(
            description=f"🎂 Birthday set to **{day:02d}/{month:02d}**! I'll celebrate when the day comes ♡",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @birthday.command(name="check")
    async def birthday_check(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        gid = str(ctx.guild.id)
        uid = str(member.id)
        bd = self.birthdays.get(gid, {}).get(uid)

        if not bd:
            return await ctx.send(embed=discord.Embed(
                description=f"✗ {member.display_name} hasn't set their birthday yet!",
                color=0xff6b9d
            ))

        now = datetime.datetime.now()
        bday = datetime.datetime(now.year, bd["month"], bd["day"])
        if bday < now.replace(hour=0, minute=0, second=0, microsecond=0):
            bday = bday.replace(year=now.year + 1)
        days_until = (bday - now).days

        embed = discord.Embed(
            title=f"🎂﹒ {member.display_name}'s Birthday",
            description=f"**{bd['day']:02d}/{bd['month']:02d}**\n{'🎉 TODAY!' if days_until == 0 else f'Coming up in **{days_until}** days!'}",
            color=0xf9a8d4
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @birthday.command(name="upcoming")
    async def birthday_upcoming(self, ctx):
        gid = str(ctx.guild.id)
        bdays = self.birthdays.get(gid, {})
        now = datetime.datetime.now()
        upcoming = []

        for uid, bd in bdays.items():
            member = ctx.guild.get_member(int(uid))
            if not member:
                continue
            bday = datetime.datetime(now.year, bd["month"], bd["day"])
            if bday < now.replace(hour=0, minute=0, second=0, microsecond=0):
                bday = bday.replace(year=now.year + 1)
            days_until = (bday - now).days
            upcoming.append((days_until, member.display_name, bd["day"], bd["month"]))

        upcoming.sort()

        embed = discord.Embed(title="🎂﹒ Upcoming Birthdays", color=0xf9a8d4)
        if not upcoming:
            embed.description = "No birthdays set yet!"
        else:
            rows = []
            for days, name, day, month in upcoming[:10]:
                rows.append(f"**{name}** — {day:02d}/{month:02d} {'🎉 Today!' if days == 0 else f'({days}d)'}")
            embed.description = "\n".join(rows)
        await ctx.send(embed=embed)

    @tasks.loop(hours=24)
    async def birthday_check(self):
        now = datetime.datetime.now()
        for gid, members in self.birthdays.items():
            guild = self.bot.get_guild(int(gid))
            if not guild:
                continue
            ch = discord.utils.find(
                lambda c: any(k in c.name.lower() for k in ["general", "chat", "welcome"]),
                guild.text_channels
            )
            if not ch:
                continue
            for uid, bd in members.items():
                if bd["day"] == now.day and bd["month"] == now.month:
                    member = guild.get_member(int(uid))
                    if member:
                        embed = discord.Embed(
                            title="🎂﹒ Happy Birthday!!",
                            description=f"✿ Everyone wish **{member.mention}** a happy birthday! 🎉🎂♡\n\nHope today is amazing and you get everything you want!",
                            color=0xf9a8d4
                        )
                        embed.set_thumbnail(url=member.display_avatar.url)
                        try:
                            await ch.send(embed=embed)
                        except Exception:
                            pass

    @birthday_check.before_loop
    async def before_birthday_check(self):
        await self.bot.wait_until_ready()

    # ─── COUNTING ──────────────────────────────────────────────────────────────

    @commands.command(name="setcounting")
    @commands.has_permissions(administrator=True)
    async def set_counting(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gid = str(ctx.guild.id)
        if gid not in self.counting:
            self.counting[gid] = {}
        self.counting[gid]["channel"] = str(channel.id)
        self.counting[gid]["count"] = 0
        self.counting[gid]["last_user"] = None
        save_json(self.counting, COUNTING_FILE)
        embed = discord.Embed(
            description=f"◎ Counting channel set to {channel.mention}! Start counting from **1**!",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        gid = str(message.guild.id)
        cd = self.counting.get(gid)
        if not cd or str(message.channel.id) != cd.get("channel"):
            return

        current = cd.get("count", 0)
        last_user = cd.get("last_user")

        try:
            num = int(message.content.strip())
        except ValueError:
            try:
                await message.delete()
            except Exception:
                pass
            return

        if str(message.author.id) == last_user:
            try:
                await message.delete()
            except Exception:
                pass
            await message.channel.send(
                embed=discord.Embed(description=f"✗ {message.author.mention} You can't count twice in a row! Count resets to 0.", color=0xef4444),
                delete_after=5
            )
            cd["count"] = 0
            cd["last_user"] = None
            save_json(self.counting, COUNTING_FILE)
            return

        if num == current + 1:
            cd["count"] = num
            cd["last_user"] = str(message.author.id)
            save_json(self.counting, COUNTING_FILE)
            if num % 100 == 0:
                await message.channel.send(
                    embed=discord.Embed(description=f"✿ We reached **{num}**! Amazing! Keep going! 🎉", color=0xfbbf24)
                )
            await message.add_reaction("✅")
        else:
            try:
                await message.delete()
            except Exception:
                pass
            await message.channel.send(
                embed=discord.Embed(description=f"✗ {message.author.mention} Wrong number! Expected **{current + 1}**. Count resets to 0 💀", color=0xef4444),
                delete_after=5
            )
            cd["count"] = 0
            cd["last_user"] = None
            save_json(self.counting, COUNTING_FILE)

    @commands.command(name="counting")
    async def counting_stats(self, ctx):
        gid = str(ctx.guild.id)
        cd = self.counting.get(gid)
        if not cd:
            return await ctx.send(embed=discord.Embed(description="✗ No counting channel set! Use `-setcounting`.", color=0xff6b9d))

        ch_id = cd.get("channel")
        ch = ctx.guild.get_channel(int(ch_id)) if ch_id else None
        embed = discord.Embed(title="◎﹒ Counting Stats", color=0xb5a8d5)
        embed.add_field(name="Channel", value=ch.mention if ch else "Not set", inline=True)
        embed.add_field(name="Current Count", value=f"**{cd.get('count', 0)}**", inline=True)
        last = cd.get("last_user")
        if last:
            m = ctx.guild.get_member(int(last))
            embed.add_field(name="Last Counted By", value=m.mention if m else f"<@{last}>", inline=True)
        await ctx.send(embed=embed)

    # ─── REACTION ROLES ────────────────────────────────────────────────────────

    @commands.command(name="reactionrole", aliases=["rr"])
    @commands.has_permissions(administrator=True)
    async def reaction_role(self, ctx, message_id: int, emoji: str, *, role: discord.Role):
        rr_file = "data/reactionroles.json"
        rr_data = load_json(rr_file)
        gid = str(ctx.guild.id)
        if gid not in rr_data:
            rr_data[gid] = {}
        key = f"{message_id}:{emoji}"
        rr_data[gid][key] = str(role.id)
        save_json(rr_data, rr_file)

        embed = discord.Embed(
            description=f"✿ Reaction role set! React with {emoji} on message `{message_id}` to get **{role.name}**!",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member and payload.member.bot:
            return
        rr_file = "data/reactionroles.json"
        rr_data = load_json(rr_file)
        gid = str(payload.guild_id)
        if gid not in rr_data:
            return
        key = f"{payload.message_id}:{str(payload.emoji)}"
        role_id = rr_data[gid].get(key)
        if not role_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = guild.get_role(int(role_id))
        if role and payload.member:
            try:
                await payload.member.add_roles(role)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        rr_file = "data/reactionroles.json"
        rr_data = load_json(rr_file)
        gid = str(payload.guild_id)
        if gid not in rr_data:
            return
        key = f"{payload.message_id}:{str(payload.emoji)}"
        role_id = rr_data[gid].get(key)
        if not role_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = guild.get_role(int(role_id))
        member = guild.get_member(payload.user_id)
        if role and member:
            try:
                await member.remove_roles(role)
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(Events(bot))
