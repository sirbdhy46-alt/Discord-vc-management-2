import discord
from discord.ext import commands
import json
import os
import asyncio
import random
import logging
import time
import re

logger = logging.getLogger(__name__)
DATA_FILE = "data/giveaways.json"

def parse_time(time_str: str) -> int:
    """Parse time string like 10s, 5m, 2h, 1d into seconds."""
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    match = re.match(r"^(\d+)([smhd])$", time_str.lower())
    if not match:
        raise ValueError("Invalid time format. Use 10s, 5m, 2h, 1d, etc.")
    val, unit = int(match.group(1)), match.group(2)
    return val * units[unit]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"active": {}, "last": {}}

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.bot.loop.create_task(self.resume_giveaways())

    async def resume_giveaways(self):
        await self.bot.wait_until_ready()
        for msg_id, gdata in list(self.data["active"].items()):
            remaining = gdata["end_time"] - time.time()
            if remaining <= 0:
                await self.end_giveaway(int(msg_id), gdata)
            else:
                self.bot.loop.create_task(self.wait_and_end(int(msg_id), gdata, remaining))

    async def wait_and_end(self, msg_id, gdata, delay):
        await asyncio.sleep(delay)
        await self.end_giveaway(msg_id, gdata)

    async def end_giveaway(self, msg_id, gdata):
        try:
            guild = self.bot.get_guild(int(gdata["guild_id"]))
            if not guild:
                return
            channel = guild.get_channel(int(gdata["channel_id"]))
            if not channel:
                return
            msg = await channel.fetch_message(msg_id)

            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            if reaction:
                users = [u async for u in reaction.users() if not u.bot]
            else:
                users = []

            winners_count = gdata.get("winners", 1)
            if not users:
                await channel.send(embed=discord.Embed(
                    description="✗ No one entered the giveaway! No winner this time.",
                    color=0xef4444
                ), reference=msg)
            else:
                winners = random.sample(users, min(winners_count, len(users)))
                winner_mentions = ", ".join(w.mention for w in winners)
                embed = discord.Embed(
                    title="🎉﹒ Giveaway Ended!",
                    description=f"**Prize:** {gdata['prize']}\n**Winner(s):** {winner_mentions}",
                    color=0xfbbf24
                )
                embed.set_footer(text=f"﹒✶﹒ Congratulations! ﹒✶﹒")
                await channel.send(embed=embed, reference=msg)
                self.data["last"][str(gdata["guild_id"])] = {
                    "channel_id": str(gdata["channel_id"]),
                    "msg_id": str(msg_id),
                    "prize": gdata["prize"],
                    "winners": [str(w.id) for w in winners],
                }

            edit_embed = discord.Embed(
                title="🎉 GIVEAWAY ENDED",
                description=f"**Prize:** {gdata['prize']}",
                color=0x94a3b8
            )
            edit_embed.set_footer(text="Giveaway has ended.")
            await msg.edit(embed=edit_embed)

            del self.data["active"][str(msg_id)]
            save_data(self.data)
        except Exception as e:
            logger.error(f"Error ending giveaway: {e}")

    @commands.command(name="giveaway", aliases=["gw", "gcreate"])
    @commands.has_permissions(manage_guild=True)
    async def giveaway(self, ctx, time_str: str, winners: str = "1", *, prize: str):
        try:
            duration = parse_time(time_str)
        except ValueError as e:
            return await ctx.send(embed=discord.Embed(description=f"✗ {e}", color=0xff6b9d))

        try:
            num_winners = int(winners.replace("w", ""))
        except Exception:
            prize = f"{winners} {prize}"
            num_winners = 1

        end_time = time.time() + duration

        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        secs = int(duration % 60)
        time_display = f"{hours}h {minutes}m {secs}s" if hours else f"{minutes}m {secs}s"

        embed = discord.Embed(
            title="🎉 GIVEAWAY!",
            description=(
                f"**Prize:** {prize}\n"
                f"**Winners:** {num_winners}\n"
                f"**Ends:** <t:{int(end_time)}:R>\n\n"
                f"React with 🎉 to enter!"
            ),
            color=0xfbbf24
        )
        embed.set_footer(text=f"Hosted by {ctx.author.display_name} ﹒ {num_winners} winner(s)")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎉")

        gdata = {
            "guild_id": str(ctx.guild.id),
            "channel_id": str(ctx.channel.id),
            "prize": prize,
            "winners": num_winners,
            "end_time": end_time,
            "host_id": str(ctx.author.id),
        }
        self.data["active"][str(msg.id)] = gdata
        save_data(self.data)

        await ctx.message.delete()
        self.bot.loop.create_task(self.wait_and_end(msg.id, gdata, duration))

    @commands.command(name="reroll")
    @commands.has_permissions(manage_guild=True)
    async def reroll(self, ctx):
        gid = str(ctx.guild.id)
        last = self.data["last"].get(gid)
        if not last:
            return await ctx.send(embed=discord.Embed(description="✗ No recent giveaway to reroll!", color=0xff6b9d))

        channel = ctx.guild.get_channel(int(last["channel_id"]))
        if not channel:
            return await ctx.send(embed=discord.Embed(description="✗ Original channel not found!", color=0xff6b9d))

        try:
            msg = await channel.fetch_message(int(last["msg_id"]))
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            if reaction:
                users = [u async for u in reaction.users() if not u.bot]
            else:
                users = []

            if not users:
                return await ctx.send(embed=discord.Embed(description="✗ No entries found!", color=0xff6b9d))

            winner = random.choice(users)
            embed = discord.Embed(
                description=f"🎉 New winner for **{last['prize']}**: {winner.mention}! Congrats!",
                color=0xfbbf24
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(description=f"✗ Error: {e}", color=0xff6b9d))

    @commands.command(name="gend")
    @commands.has_permissions(manage_guild=True)
    async def gend(self, ctx, msg_id: int):
        gdata = self.data["active"].get(str(msg_id))
        if not gdata:
            return await ctx.send(embed=discord.Embed(description="✗ Giveaway not found!", color=0xff6b9d))
        await self.end_giveaway(msg_id, gdata)
        await ctx.send(embed=discord.Embed(description="✿ Giveaway ended!", color=0xb5a8d5))

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
