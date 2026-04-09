import discord
from discord.ext import commands
import random
import json
import os
import logging
import asyncio

logger = logging.getLogger(__name__)
DATA_FILE = "data/fun.json"

EIGHT_BALL = [
    "✿ It is certain!", "⟡ Absolutely yes!", "◎ Most likely!", "✦ Without a doubt!",
    "★ Yes!", "◖ Signs point to yes!", "ᵔᴗᵔ Outlook is good!",
    "░ Reply hazy, try again...", "ᶻz Ask again later...", "◌ Cannot predict now...",
    "✗ Don't count on it.", "◍ My sources say no.", "⟡ Very doubtful.", "✸ No!",
    "💀 Absolutely not!", "☓ Not a chance!", "◐ The stars say no...",
]

ROASTS = [
    "ur wifi password is probably your pet's name 💀",
    "you still use Internet Explorer, don't you 😭",
    "your search history is a crime scene 💀",
    "even autocorrect gave up on you",
    "your personality is a loading screen that never finishes",
    "you put the 'ugh' in 'ugh wake me up'",
    "your vibe is 'laptop with 2% battery and no charger'",
    "you're the human version of a notification you can't turn off",
    "if laziness was a sport, you'd finally get a medal",
    "your sense of direction is worse than Google Maps offline",
    "you dress like the default skin in every game",
    "you're like a Monday — nobody wants you but you show up anyway 💀",
    "you have the energy of a drained phone at 6am",
]

COMPLIMENTS = [
    "you're literally the highlight of this server ✿",
    "the world is a better place because you exist ♡",
    "your vibe is immaculate, don't let anyone tell you otherwise ⟡",
    "you're the kind of person that makes people smile just by being there",
    "honestly? you're way cooler than you think ★",
    "you give off main character energy and it's gorgeous ◎",
    "you're built different and that's a compliment ✦",
    "your laugh probably sounds amazing and I stand by that",
    "if kindness was a currency you'd be the richest person here ✿",
    "you're genuinely one of the good ones ♡",
    "you make chaos look cute and that's a talent ⟡",
    "the server is literally so much better with you in it ◎",
]

TRUTHS = [
    "What's the most embarrassing thing you've done online?",
    "Have you ever been ghosted? Did you deserve it?",
    "What's your most cursed opinion?",
    "What app do you spend the most time on and regret it?",
    "Have you ever fake-laughed at something you didn't understand?",
    "What's the worst lie you've told to get out of something?",
    "What's something you pretend not to like but actually love?",
    "Have you ever talked behind someone's back and felt bad?",
    "What's the most embarrassing thing in your camera roll?",
    "Have you ever cried at a movie you told people was bad?",
    "What's a weird habit you have that nobody knows about?",
    "Who in this server do you relate to the most?",
    "What's your most chaotic 3am decision?",
]

DARES = [
    "Send a 'I miss you' text to the last person you texted",
    "Change your nickname to something cursed for 1 hour",
    "React to the last 5 messages with the most unhinged emoji",
    "Send a voice message saying 'pineapple belongs on pizza' in your most confident voice",
    "Write a 3 sentence love poem about your favorite food",
    "Type with your eyes closed for the next 3 messages",
    "Admit your most unhinged opinion in this server",
    "Send a gif that perfectly describes your personality",
    "Change your status to something embarrassing for 30 minutes",
    "DM someone 'I've been watching you' and screenshot the reaction",
    "Do a British accent in a voice message (if in vc, do it live)",
    "Describe your type in the most chaotic way possible",
]

WYR = [
    "Have unlimited WiFi forever OR unlimited food forever?",
    "Know when you'll die OR how you'll die?",
    "Only be able to whisper OR only be able to shout?",
    "Live in your favorite game's world OR your favorite show's world?",
    "Lose all your photos OR all your contacts?",
    "Be famous but hated OR unknown but loved?",
    "Never use social media again OR never watch videos again?",
    "Be able to fly but only 1 meter off the ground OR teleport but only in your city?",
    "Have a pause button for life OR a rewind button (5 seconds)?",
    "Know every language OR be able to play every instrument?",
]

NHIE = [
    "never have I ever fallen asleep in a call",
    "never have I ever pretended to be offline",
    "never have I ever liked my own post from a different account",
    "never have I ever cyber-stalked an ex",
    "never have I ever sent a text to the wrong person and panicked",
    "never have I ever said 'on my way' while still in bed",
    "never have I ever googled myself",
    "never have I ever read someone's messages and not replied for days",
    "never have I ever had a dream about someone in this server",
    "never have I ever lied about my age online",
]

CONFESSION_FILE = "data/confessions.json"

def load_confessions():
    if os.path.exists(CONFESSION_FILE):
        with open(CONFESSION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_confessions(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFESSION_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.confessions = load_confessions()
        self.confession_channels = {}

    @commands.command(name="8ball", aliases=["eightball"])
    async def eight_ball(self, ctx, *, question: str):
        answer = random.choice(EIGHT_BALL)
        embed = discord.Embed(color=0xb5a8d5)
        embed.add_field(name="◎﹒ Question", value=question, inline=False)
        embed.add_field(name="⟡﹒ Answer", value=f"**{answer}**", inline=False)
        embed.set_footer(text="﹒✶﹒ The magic 8ball has spoken ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="ship")
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member = None):
        user2 = user2 or ctx.author
        score = random.randint(0, 100)
        bar_filled = int(score / 10)
        bar = "❤️" * bar_filled + "🖤" * (10 - bar_filled)
        if score >= 80:
            verdict = "soulmates!! 💞 literally made for each other"
        elif score >= 60:
            verdict = "strong vibes!! there's something there 💕"
        elif score >= 40:
            verdict = "possible... with some effort ♡"
        elif score >= 20:
            verdict = "it's complicated 😬"
        else:
            verdict = "this ship is sinking 💀"

        ship_name = user1.display_name[:len(user1.display_name)//2] + user2.display_name[len(user2.display_name)//2:]

        embed = discord.Embed(
            title=f"♡﹒ Ship: {ship_name}",
            color=0xff6b9d
        )
        embed.add_field(name="Couple", value=f"{user1.mention} ♡ {user2.mention}", inline=False)
        embed.add_field(name="Score", value=f"**{score}%** {bar}", inline=False)
        embed.add_field(name="Verdict", value=verdict, inline=False)
        embed.set_footer(text="﹒✶﹒ Love is mysterious ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="roast")
    async def roast(self, ctx, target: discord.Member = None):
        target = target or ctx.author
        roast = random.choice(ROASTS)
        embed = discord.Embed(
            description=f"◍﹒ {target.mention} — {roast}",
            color=0xef4444
        )
        embed.set_footer(text="﹒✶﹒ it's all love tho ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="compliment")
    async def compliment(self, ctx, target: discord.Member = None):
        target = target or ctx.author
        comp = random.choice(COMPLIMENTS)
        embed = discord.Embed(
            description=f"✿﹒ {target.mention} — {comp}",
            color=0xf9a8d4
        )
        embed.set_footer(text="﹒✶﹒ spread love ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="hug")
    async def hug(self, ctx, target: discord.Member):
        embed = discord.Embed(
            description=f"♡﹒ {ctx.author.mention} hugged {target.mention}! so wholesome 🥺",
            color=0xf9a8d4
        )
        await ctx.send(embed=embed)

    @commands.command(name="slap")
    async def slap(self, ctx, target: discord.Member):
        embed = discord.Embed(
            description=f"◍﹒ {ctx.author.mention} slapped {target.mention} 💀",
            color=0xef4444
        )
        await ctx.send(embed=embed)

    @commands.command(name="truth")
    async def truth(self, ctx):
        question = random.choice(TRUTHS)
        embed = discord.Embed(title="◎﹒ Truth Question", description=f"*{question}*", color=0xb5a8d5)
        embed.set_footer(text="﹒✶﹒ be honest... ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="dare")
    async def dare(self, ctx):
        d = random.choice(DARES)
        embed = discord.Embed(title="◖﹒ Dare!", description=f"*{d}*", color=0xff6b9d)
        embed.set_footer(text="﹒✶﹒ no backing out ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="wouldyourather", aliases=["wyr"])
    async def would_you_rather(self, ctx):
        question = random.choice(WYR)
        options = question.split(" OR ")
        embed = discord.Embed(title="⟡﹒ Would You Rather...", color=0xb5a8d5)
        embed.add_field(name="Option A 🅰️", value=options[0], inline=True)
        embed.add_field(name="Option B 🅱️", value=options[1] if len(options) > 1 else "...", inline=True)
        embed.set_footer(text="﹒✶﹒ react with 🅰️ or 🅱️ ﹒✶﹒")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🅰️")
        await msg.add_reaction("🅱️")

    @commands.command(name="neverhaveiever", aliases=["nhie"])
    async def nhie(self, ctx):
        statement = random.choice(NHIE)
        embed = discord.Embed(
            title="✸﹒ Never Have I Ever...",
            description=f"**{statement}**\n\n✅ = Have  |  ❌ = Never",
            color=0xb5a8d5
        )
        embed.set_footer(text="﹒✶﹒ react honestly ﹒✶﹒")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

    @commands.command(name="rps")
    async def rps(self, ctx, choice: str):
        choice = choice.lower()
        mapping = {"r": "rock", "p": "paper", "s": "scissors", "rock": "rock", "paper": "paper", "scissors": "scissors"}
        if choice not in mapping:
            return await ctx.send(embed=discord.Embed(description="✗ Use r/p/s or rock/paper/scissors!", color=0xff6b9d))
        choice = mapping[choice]
        bot_choice = random.choice(["rock", "paper", "scissors"])
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

        if choice == bot_choice:
            result, color = "**Tie!** 🤝", 0x94a3b8
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result, color = "**You Win!** ✿", 0x22c55e
        else:
            result, color = "**Bot Wins!** 💀", 0xef4444

        embed = discord.Embed(title="◎﹒ Rock Paper Scissors", color=color)
        embed.add_field(name="You", value=f"{emojis[choice]} {choice.title()}", inline=True)
        embed.add_field(name="Bot", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
        embed.add_field(name="Result", value=result, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="coinflip", aliases=["flip"])
    async def coinflip(self, ctx):
        result = random.choice(["Heads", "Tails"])
        emoji = "🪙" if result == "Heads" else "🌑"
        embed = discord.Embed(
            description=f"◖﹒ The coin landed on **{result}**! {emoji}",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @commands.command(name="roll")
    async def roll(self, ctx, sides: int = 6):
        if sides < 2 or sides > 1000:
            return await ctx.send(embed=discord.Embed(description="✗ Sides must be 2–1000!", color=0xff6b9d))
        result = random.randint(1, sides)
        embed = discord.Embed(
            description=f"◍﹒ Rolling a d{sides}... you got **{result}**!",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @commands.command(name="confess")
    async def confess(self, ctx, *, text: str):
        try:
            await ctx.message.delete()
        except Exception:
            pass

        gid = str(ctx.guild.id)
        conf_data = load_confessions()
        if gid not in conf_data:
            conf_data[gid] = {"channel": None, "count": 0}

        conf_data[gid]["count"] = conf_data[gid].get("count", 0) + 1
        count = conf_data[gid]["count"]
        save_confessions(conf_data)

        channel_id = conf_data[gid].get("channel")
        channel = None
        if channel_id:
            channel = ctx.guild.get_channel(int(channel_id))
        if not channel:
            channel = discord.utils.find(
                lambda c: "confess" in c.name.lower(),
                ctx.guild.text_channels
            )
        if not channel:
            channel = ctx.channel

        embed = discord.Embed(
            title=f"◌﹒ Anonymous Confession #{count}",
            description=f"*{text}*",
            color=0xb5a8d5
        )
        embed.set_footer(text="﹒✶﹒ all confessions are anonymous ﹒✶﹒")
        msg = await channel.send(embed=embed)
        await msg.add_reaction("♥️")
        await msg.add_reaction("💀")

    @commands.command(name="setconfess")
    @commands.has_permissions(administrator=True)
    async def set_confess(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        conf_data = load_confessions()
        gid = str(ctx.guild.id)
        if gid not in conf_data:
            conf_data[gid] = {"channel": None, "count": 0}
        conf_data[gid]["channel"] = str(channel.id)
        save_confessions(conf_data)
        await ctx.send(embed=discord.Embed(description=f"✿ Confession channel set to {channel.mention}!", color=0xb5a8d5))

    @commands.command(name="choose")
    async def choose(self, ctx, *, options: str):
        choices = [o.strip() for o in options.split(",")]
        if len(choices) < 2:
            return await ctx.send(embed=discord.Embed(description="✗ Give at least 2 options separated by commas!", color=0xff6b9d))
        result = random.choice(choices)
        embed = discord.Embed(
            description=f"⟡﹒ I choose: **{result}**!",
            color=0xb5a8d5
        )
        embed.set_footer(text=f"Options: {', '.join(choices)}")
        await ctx.send(embed=embed)

    @commands.command(name="rate")
    async def rate(self, ctx, *, thing: str):
        score = random.randint(0, 100)
        bar = "█" * (score // 10) + "░" * (10 - score // 10)
        embed = discord.Embed(
            title="◎﹒ Rating",
            description=f"I rate **{thing}**:\n**{score}/100** `[{bar}]`",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @commands.command(name="fact")
    async def fact(self, ctx):
        facts = [
            "Honey never expires. 3000-year-old honey has been found in Egyptian tombs.",
            "A group of flamingos is called a 'flamboyance'.",
            "Cows have best friends and get stressed when separated.",
            "The average person walks about 100,000 miles in their lifetime.",
            "Octopuses have three hearts and blue blood.",
            "Bananas are technically berries but strawberries aren't.",
            "A day on Venus is longer than a year on Venus.",
            "The moon is slowly drifting away from Earth at 3.8cm per year.",
            "Cleopatra lived closer in time to the Moon landing than to the construction of the Pyramids.",
            "The shortest war in history lasted 38 minutes.",
        ]
        embed = discord.Embed(
            title="✦﹒ Random Fact",
            description=random.choice(facts),
            color=0xb5a8d5
        )
        embed.set_footer(text="﹒✶﹒ knowledge is power ﹒✶﹒")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
