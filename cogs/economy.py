import discord
from discord.ext import commands
import json
import os
import random
import time
import logging

logger = logging.getLogger(__name__)
DATA_FILE = "data/economy.json"

CURRENCY = "✿ coins"
CURRENCY_SYMBOL = "✿"

SHOP_ITEMS = {
    "vip_tag": {"name": "⟡ VIP Tag", "price": 5000, "description": "Show off your VIP status", "type": "cosmetic"},
    "custom_color": {"name": "◎ Custom Color", "price": 3000, "description": "Stand out in chat", "type": "cosmetic"},
    "luck_boost": {"name": "✦ Luck Boost", "price": 1500, "description": "Better crime/rob chances for 1hr", "type": "boost"},
    "daily_boost": {"name": "★ Daily Boost", "price": 2000, "description": "Double daily for 24hrs", "type": "boost"},
    "mystery_box": {"name": "░ Mystery Box", "price": 500, "description": "Random coins: 0–2000!", "type": "gamble"},
    "piggy_bank": {"name": "♡ Piggy Bank", "price": 1000, "description": "Protects 50% coins on rob", "type": "protect"},
}

WORK_JOBS = [
    ("delivered pizzas", 200, 500),
    ("coded all night", 300, 700),
    ("streamed for viewers", 150, 600),
    ("did someone's homework", 100, 400),
    ("sold memes online", 200, 800),
    ("walked 10 dogs", 150, 350),
    ("answered tech support", 250, 550),
    ("made aesthetic edits", 300, 650),
    ("fixed a server", 400, 900),
    ("pulled an all-nighter", 100, 1000),
]

CRIME_SCENARIOS = [
    ("stole a vending machine", 500, 1500),
    ("hacked into a discord server", 1000, 3000),
    ("scammed someone at chess", 300, 800),
    ("robbed a lemonade stand", 200, 600),
    ("faked being a celebrity", 800, 2000),
]

FAIL_CRIME = [
    "got caught red-handed 💀 fine: ",
    "slipped on a banana peel 🍌 fine: ",
    "your getaway driver was asleep 😴 fine: ",
    "forgot your mask at home 🎭 fine: ",
    "posted about it on twitter first 💀 fine: ",
]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def get_user(self, guild_id, user_id):
        gid = str(guild_id)
        uid = str(user_id)
        if gid not in self.data:
            self.data[gid] = {}
        if uid not in self.data[gid]:
            self.data[gid][uid] = {
                "coins": 0, "bank": 0,
                "daily_last": 0, "work_last": 0, "crime_last": 0, "rob_last": 0,
                "inventory": [], "total_earned": 0
            }
        return self.data[gid][uid]

    def save(self):
        save_data(self.data)

    @commands.command(name="balance", aliases=["bal", "coins", "wallet"])
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        ud = self.get_user(ctx.guild.id, member.id)
        embed = discord.Embed(title=f"ıllı﹒ {member.display_name}'s Wallet", color=0xb5a8d5)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="✿ Wallet", value=f"**{ud['coins']:,}** coins", inline=True)
        embed.add_field(name="◖ Bank", value=f"**{ud['bank']:,}** coins", inline=True)
        embed.add_field(name="★ Total", value=f"**{ud['coins'] + ud['bank']:,}** coins", inline=True)
        embed.set_footer(text="﹒✶﹒ Use -daily to claim free coins! ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily(self, ctx):
        ud = self.get_user(ctx.guild.id, ctx.author.id)
        now = time.time()
        cooldown = 86400
        elapsed = now - ud.get("daily_last", 0)

        if elapsed < cooldown:
            remaining = cooldown - elapsed
            h = int(remaining // 3600)
            m = int((remaining % 3600) // 60)
            return await ctx.send(embed=discord.Embed(
                description=f"ᶻz You already claimed! Come back in **{h}h {m}m**.",
                color=0x94a3b8
            ))

        boost = "daily_boost" in ud.get("inventory", [])
        amount = random.randint(400, 800)
        if boost:
            amount *= 2

        streak = ud.get("streak", 0)
        if elapsed < 172800:
            streak += 1
        else:
            streak = 1
        ud["streak"] = streak
        bonus = min(streak * 50, 500)
        amount += bonus

        ud["coins"] += amount
        ud["daily_last"] = now
        ud["total_earned"] = ud.get("total_earned", 0) + amount
        self.save()

        embed = discord.Embed(
            title="✿﹒ Daily Claimed!",
            description=f"You got **{amount:,}** {CURRENCY}!",
            color=0xb5a8d5
        )
        embed.add_field(name="🔥 Streak", value=f"**{streak}** days", inline=True)
        embed.add_field(name="◎ Streak Bonus", value=f"+**{bonus}** coins", inline=True)
        if boost:
            embed.add_field(name="★ Boost Active", value="Daily boosted x2!", inline=True)
        embed.set_footer(text="﹒✶﹒ Come back tomorrow! ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="work")
    async def work(self, ctx):
        ud = self.get_user(ctx.guild.id, ctx.author.id)
        now = time.time()
        cooldown = 3600
        elapsed = now - ud.get("work_last", 0)

        if elapsed < cooldown:
            remaining = cooldown - elapsed
            m = int(remaining // 60)
            s = int(remaining % 60)
            return await ctx.send(embed=discord.Embed(
                description=f"ᶻz You're still tired! Rest for **{m}m {s}s**.",
                color=0x94a3b8
            ))

        job, min_pay, max_pay = random.choice(WORK_JOBS)
        amount = random.randint(min_pay, max_pay)
        ud["coins"] += amount
        ud["work_last"] = now
        ud["total_earned"] = ud.get("total_earned", 0) + amount
        self.save()

        embed = discord.Embed(
            description=f"◎﹒ You **{job}** and earned **{amount:,}** {CURRENCY}!",
            color=0xb5a8d5
        )
        embed.set_footer(text="﹒✶﹒ Come back in 1 hour! ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="crime")
    async def crime(self, ctx):
        ud = self.get_user(ctx.guild.id, ctx.author.id)
        now = time.time()
        cooldown = 7200
        elapsed = now - ud.get("crime_last", 0)

        if elapsed < cooldown:
            remaining = cooldown - elapsed
            h = int(remaining // 3600)
            m = int((remaining % 3600) // 60)
            return await ctx.send(embed=discord.Embed(
                description=f"ᶻz Lay low for **{h}h {m}m** before doing crime again.",
                color=0x94a3b8
            ))

        success_rate = 0.55
        if "luck_boost" in ud.get("inventory", []):
            success_rate = 0.75

        ud["crime_last"] = now

        if random.random() < success_rate:
            scenario, min_earn, max_earn = random.choice(CRIME_SCENARIOS)
            amount = random.randint(min_earn, max_earn)
            ud["coins"] += amount
            ud["total_earned"] = ud.get("total_earned", 0) + amount
            self.save()
            embed = discord.Embed(
                title="◍﹒ Crime Successful!",
                description=f"You **{scenario}** and got away with **{amount:,}** {CURRENCY}! 💀",
                color=0x22c55e
            )
        else:
            fine = random.randint(100, 500)
            ud["coins"] = max(0, ud["coins"] - fine)
            self.save()
            msg = random.choice(FAIL_CRIME)
            embed = discord.Embed(
                title="◍﹒ Crime Failed!",
                description=f"You {msg}**{fine:,}** {CURRENCY}! 💀",
                color=0xef4444
            )
        embed.set_footer(text="﹒✶﹒ Crime doesn't always pay! ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="rob")
    async def rob(self, ctx, target: discord.Member):
        if target == ctx.author or target.bot:
            return await ctx.send(embed=discord.Embed(description="✗ You can't rob yourself or a bot!", color=0xff6b9d))

        ud = self.get_user(ctx.guild.id, ctx.author.id)
        td = self.get_user(ctx.guild.id, target.id)
        now = time.time()
        cooldown = 14400
        elapsed = now - ud.get("rob_last", 0)

        if elapsed < cooldown:
            remaining = cooldown - elapsed
            h = int(remaining // 3600)
            m = int((remaining % 3600) // 60)
            return await ctx.send(embed=discord.Embed(
                description=f"ᶻz Wait **{h}h {m}m** before robbing again.",
                color=0x94a3b8
            ))

        if td["coins"] < 100:
            return await ctx.send(embed=discord.Embed(
                description=f"✗ **{target.display_name}** is too broke to rob! 💀",
                color=0xff6b9d
            ))

        ud["rob_last"] = now

        success_rate = 0.45
        if "luck_boost" in ud.get("inventory", []):
            success_rate = 0.65

        if random.random() < success_rate:
            steal_pct = random.uniform(0.1, 0.4)
            if "piggy_bank" in td.get("inventory", []):
                steal_pct *= 0.5
            amount = int(td["coins"] * steal_pct)
            td["coins"] -= amount
            ud["coins"] += amount
            self.save()
            embed = discord.Embed(
                title="◍﹒ Rob Successful!",
                description=f"You robbed **{target.display_name}** and stole **{amount:,}** {CURRENCY}! 💀",
                color=0x22c55e
            )
        else:
            fine = random.randint(200, 800)
            ud["coins"] = max(0, ud["coins"] - fine)
            self.save()
            embed = discord.Embed(
                title="◍﹒ Rob Failed!",
                description=f"**{target.display_name}** caught you and you got fined **{fine:,}** {CURRENCY}! 💀",
                color=0xef4444
            )
        await ctx.send(embed=embed)

    @commands.command(name="give", aliases=["pay"])
    async def give(self, ctx, target: discord.Member, amount: int):
        if target == ctx.author or target.bot:
            return await ctx.send(embed=discord.Embed(description="✗ Invalid target!", color=0xff6b9d))
        if amount <= 0:
            return await ctx.send(embed=discord.Embed(description="✗ Amount must be positive!", color=0xff6b9d))

        ud = self.get_user(ctx.guild.id, ctx.author.id)
        td = self.get_user(ctx.guild.id, target.id)

        if ud["coins"] < amount:
            return await ctx.send(embed=discord.Embed(description="✗ You don't have enough coins!", color=0xff6b9d))

        ud["coins"] -= amount
        td["coins"] += amount
        self.save()
        embed = discord.Embed(
            description=f"✿ You gave **{amount:,}** {CURRENCY} to **{target.display_name}**! ♡",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @commands.command(name="shop")
    async def shop(self, ctx):
        embed = discord.Embed(title="◎﹒ Item Shop", description="Use `-buy <item>` to purchase!", color=0xb5a8d5)
        for item_id, item in SHOP_ITEMS.items():
            embed.add_field(
                name=f"{item['name']} — {item['price']:,} coins",
                value=f"*{item['description']}*\n`-buy {item_id}`",
                inline=True
            )
        embed.set_footer(text="﹒✶﹒ Spend wisely! ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="buy")
    async def buy(self, ctx, *, item_id: str):
        item_id = item_id.lower().replace(" ", "_")
        if item_id not in SHOP_ITEMS:
            return await ctx.send(embed=discord.Embed(description=f"✗ Item `{item_id}` not found! Use `-shop`.", color=0xff6b9d))

        item = SHOP_ITEMS[item_id]
        ud = self.get_user(ctx.guild.id, ctx.author.id)

        if ud["coins"] < item["price"]:
            return await ctx.send(embed=discord.Embed(
                description=f"✗ You need **{item['price']:,}** coins but only have **{ud['coins']:,}**!",
                color=0xff6b9d
            ))

        if item_id in ud.get("inventory", []) and item["type"] in ["cosmetic", "protect"]:
            return await ctx.send(embed=discord.Embed(description="✗ You already own this item!", color=0xff6b9d))

        ud["coins"] -= item["price"]

        if item_id == "mystery_box":
            prize = random.randint(0, 2000)
            ud["coins"] += prize
            self.save()
            return await ctx.send(embed=discord.Embed(
                title="░﹒ Mystery Box!",
                description=f"You opened it and got **{prize:,}** {CURRENCY}!",
                color=0xfbbf24
            ))

        if "inventory" not in ud:
            ud["inventory"] = []
        ud["inventory"].append(item_id)
        self.save()

        embed = discord.Embed(
            description=f"✿ You bought **{item['name']}** for **{item['price']:,}** coins!",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        ud = self.get_user(ctx.guild.id, member.id)
        inv = ud.get("inventory", [])

        embed = discord.Embed(title=f"◖﹒ {member.display_name}'s Inventory", color=0xb5a8d5)
        embed.set_thumbnail(url=member.display_avatar.url)

        if not inv:
            embed.description = "Empty inventory! Use `-shop` to buy items."
        else:
            lines = []
            for item_id in inv:
                item = SHOP_ITEMS.get(item_id, {"name": item_id})
                lines.append(f"• {item['name']}")
            embed.description = "\n".join(lines)

        await ctx.send(embed=embed)

    @commands.command(name="richest", aliases=["econlb"])
    async def richest(self, ctx):
        gd = self.data.get(str(ctx.guild.id), {})
        sorted_data = sorted(gd.items(), key=lambda x: x[1].get("coins", 0) + x[1].get("bank", 0), reverse=True)[:10]

        embed = discord.Embed(title="ıllı﹒ Richest Members", color=0xb5a8d5)
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        rows = []
        for i, (uid, udata) in enumerate(sorted_data):
            total = udata.get("coins", 0) + udata.get("bank", 0)
            if total == 0:
                continue
            m = ctx.guild.get_member(int(uid))
            name = m.display_name if m else f"User {uid}"
            rows.append(f"{medals[i]} **{name}** — **{total:,}** coins")

        embed.description = "\n".join(rows) if rows else "No economy data yet!"
        embed.set_footer(text="﹒✶﹒ Work hard, get rich! ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx, amount: str):
        ud = self.get_user(ctx.guild.id, ctx.author.id)
        amt = ud["coins"] if amount.lower() == "all" else int(amount)
        if amt <= 0 or amt > ud["coins"]:
            return await ctx.send(embed=discord.Embed(description="✗ Invalid amount!", color=0xff6b9d))
        ud["coins"] -= amt
        ud["bank"] += amt
        self.save()
        await ctx.send(embed=discord.Embed(description=f"✿ Deposited **{amt:,}** coins to your bank!", color=0xb5a8d5))

    @commands.command(name="withdraw", aliases=["with"])
    async def withdraw(self, ctx, amount: str):
        ud = self.get_user(ctx.guild.id, ctx.author.id)
        amt = ud["bank"] if amount.lower() == "all" else int(amount)
        if amt <= 0 or amt > ud["bank"]:
            return await ctx.send(embed=discord.Embed(description="✗ Invalid amount!", color=0xff6b9d))
        ud["bank"] -= amt
        ud["coins"] += amt
        self.save()
        await ctx.send(embed=discord.Embed(description=f"✿ Withdrew **{amt:,}** coins from bank!", color=0xb5a8d5))

async def setup(bot):
    await bot.add_cog(Economy(bot))
