import discord
from discord.ext import commands
import asyncio
import logging

logger = logging.getLogger(__name__)

AESTHETIC = "﹒✶﹒⊹﹒"

CHANNEL_STRUCTURE = [
    # ── WELCOME & INFO ─────────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒✶﹒ welcome ﹒✶﹒",
        "channels": [
            {"type": "text", "name": "✿﹒rules", "topic": "﹒✶﹒⊹﹒ Read the rules before doing anything! ﹒⊹﹒✶﹒"},
            {"type": "text", "name": "⟡﹒announcements", "topic": "Important server announcements!"},
            {"type": "text", "name": "◎﹒roles", "topic": "React or use commands to get your roles!"},
            {"type": "text", "name": "⿴﹒info", "topic": "Server info and FAQ"},
        ]
    },
    # ── GENERAL ────────────────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒⟡﹒ general ﹒⟡﹒",
        "channels": [
            {"type": "text", "name": "✿﹒general", "topic": "﹒✶﹒⊹﹒ Talk about anything! ﹒⊹﹒✶﹒"},
            {"type": "text", "name": "♡﹒introductions", "topic": "Introduce yourself to the server!"},
            {"type": "text", "name": "◖﹒media", "topic": "Share pics, videos, memes!"},
            {"type": "text", "name": "⊹﹒memes", "topic": "Meme central 💀"},
            {"type": "text", "name": "ᶻz﹒vent", "topic": "Vent anonymously, be kind ♡"},
            {"type": "text", "name": "⿴﹒suggestions", "topic": "Suggest stuff for the server!"},
            {"type": "text", "name": "◌﹒bot-commands", "topic": "Use bot commands here!"},
        ]
    },
    # ── PERSONAL VCS ───────────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒◖﹒ t5 vcs ﹒◖﹒",
        "channels": [
            {"type": "voice", "name": "✶﹒normal vc 1", "user_limit": 5},
            {"type": "voice", "name": "✶﹒normal vc 2", "user_limit": 5},
            {"type": "voice", "name": "✶﹒normal vc 3", "user_limit": 5},
            {"type": "voice", "name": "✶﹒normal vc 4", "user_limit": 5},
            {"type": "voice", "name": "✶﹒normal vc 5", "user_limit": 5},
        ]
    },
    # ── CREATE YOUR OWN VC ─────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒⿴﹒ create ur vc ﹒⿴﹒",
        "jtc": True,
        "jtc_type": "normal",
        "channels": [
            {"type": "voice", "name": "➜﹒join to create", "jtc": True, "jtc_type": "normal", "user_limit": 1},
        ]
    },
    # ── PRIVATE VCS ────────────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒✦﹒ private vcs ﹒✦﹒",
        "channels": [
            {"type": "voice", "name": "✦﹒join to create private", "jtc": True, "jtc_type": "private", "user_limit": 1},
        ]
    },
    # ── SPECIAL VCS ────────────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒◖﹒ special vcs ﹒◖﹒",
        "channels": [
            {"type": "voice", "name": "◖﹒shivam vc", "user_limit": 0},
            {"type": "voice", "name": "⊹﹒ice tea vc", "user_limit": 0},
        ]
    },
    # ── DUO VCS ────────────────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒♡﹒ duo vcs ﹒♡﹒",
        "channels": [
            {"type": "voice", "name": "♡﹒join to create duo", "jtc": True, "jtc_type": "duo", "user_limit": 1},
            {"type": "voice", "name": "♡﹒duo vc 1", "user_limit": 2},
            {"type": "voice", "name": "♡﹒duo vc 2", "user_limit": 2},
        ]
    },
    # ── GAMING VCS ─────────────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒◍﹒ gaming vcs ﹒◍﹒",
        "channels": [
            {"type": "voice", "name": "◍﹒join to create game", "jtc": True, "jtc_type": "gaming", "user_limit": 1},
            {"type": "voice", "name": "░﹒among us", "user_limit": 10},
            {"type": "voice", "name": "▨﹒free fire", "user_limit": 4},
            {"type": "voice", "name": "▧﹒bgmi", "user_limit": 4},
            {"type": "voice", "name": "▦﹒ludo king", "user_limit": 4},
            {"type": "voice", "name": "▥﹒cod mobile", "user_limit": 5},
            {"type": "voice", "name": "◎﹒valorant", "user_limit": 5},
            {"type": "voice", "name": "⟡﹒minecraft", "user_limit": 0},
            {"type": "voice", "name": "✿﹒roblox", "user_limit": 0},
        ]
    },
    # ── MUSIC ──────────────────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒ıllı﹒ music ﹒ıllı﹒",
        "channels": [
            {"type": "voice", "name": "ıllı﹒music vc", "user_limit": 0},
            {"type": "text", "name": "ıllı﹒music-commands", "topic": "Music bot commands here!"},
        ]
    },
    # ── STAFF ──────────────────────────────────────────────────────────
    {
        "type": "category",
        "name": "﹒★﹒ staff ﹒★﹒",
        "staff_only": True,
        "channels": [
            {"type": "text", "name": "★﹒staff-chat", "topic": "Staff only chat"},
            {"type": "text", "name": "◎﹒mod-logs", "topic": "Moderation logs"},
            {"type": "voice", "name": "★﹒staff vc", "user_limit": 0},
        ]
    },
]


class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def setup_server(self, ctx):
        msg = await ctx.send("⟡ Starting full server setup... this may take a minute!")

        from cogs.vc_manager import VCManager
        vc_cog = self.bot.get_cog("VCManager")

        created_cats = 0
        created_channels = 0
        skipped = 0

        mod_role = discord.utils.get(ctx.guild.roles, name="◎ moderator")
        staff_roles = ["⟡ owner", "✸ co-owner", "★ head mod", "◎ moderator", "⿴ helper"]

        for item in CHANNEL_STRUCTURE:
            if item["type"] != "category":
                continue

            existing_cat = discord.utils.get(ctx.guild.categories, name=item["name"])
            if existing_cat:
                category = existing_cat
                skipped += 1
            else:
                overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True)}

                if item.get("staff_only"):
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    }
                    for role_name in staff_roles:
                        role = discord.utils.get(ctx.guild.roles, name=role_name)
                        if role:
                            overwrites[role] = discord.PermissionOverwrite(read_messages=True)

                category = await ctx.guild.create_category(item["name"], overwrites=overwrites)
                created_cats += 1
                await asyncio.sleep(0.5)

            for ch_cfg in item.get("channels", []):
                existing_ch = discord.utils.get(category.channels, name=ch_cfg["name"])
                if existing_ch:
                    skipped += 1

                    if ch_cfg.get("jtc") and vc_cog:
                        vc_cog.add_jtc(existing_ch.id, category.id, ch_cfg.get("jtc_type", "normal"))
                    continue

                try:
                    if ch_cfg["type"] == "text":
                        ch = await ctx.guild.create_text_channel(
                            ch_cfg["name"],
                            category=category,
                            topic=ch_cfg.get("topic", "")
                        )
                    elif ch_cfg["type"] == "voice":
                        ch = await ctx.guild.create_voice_channel(
                            ch_cfg["name"],
                            category=category,
                            user_limit=ch_cfg.get("user_limit", 0)
                        )
                        if ch_cfg.get("jtc") and vc_cog:
                            vc_cog.add_jtc(ch.id, category.id, ch_cfg.get("jtc_type", "normal"))

                    created_channels += 1
                    await asyncio.sleep(0.4)
                except Exception as e:
                    logger.error(f"Error creating channel {ch_cfg['name']}: {e}")

        embed = discord.Embed(
            title="✿﹒⟡﹒ Setup Complete! ﹒⟡﹒✿",
            description=(
                f"✅ Categories created: **{created_cats}**\n"
                f"✅ Channels created: **{created_channels}**\n"
                f"⏭️ Skipped (already exist): **{skipped}**\n\n"
                f"Now run `!setuproles` to create all roles!"
            ),
            color=0xb5a8d5
        )
        embed.set_footer(text="﹒✶﹒⊹﹒ Your server is ready! ﹒⊹﹒✶﹒")
        await msg.edit(content=None, embed=embed)

    @commands.command(name="setupvcs")
    @commands.has_permissions(administrator=True)
    async def setup_vcs(self, ctx):
        msg = await ctx.send("⟡ Setting up join-to-create channels...")
        from cogs.vc_manager import VCManager
        vc_cog = self.bot.get_cog("VCManager")
        if not vc_cog:
            return await msg.edit(content="✗ VC Manager not loaded!")

        count = 0
        for item in CHANNEL_STRUCTURE:
            if item["type"] != "category":
                continue
            category = discord.utils.get(ctx.guild.categories, name=item["name"])
            if not category:
                continue
            for ch_cfg in item.get("channels", []):
                if ch_cfg.get("jtc"):
                    ch = discord.utils.get(category.channels, name=ch_cfg["name"])
                    if ch:
                        vc_cog.add_jtc(ch.id, category.id, ch_cfg.get("jtc_type", "normal"))
                        count += 1

        embed = discord.Embed(
            description=f"✿ Registered **{count}** join-to-create channels!",
            color=0xb5a8d5
        )
        await msg.edit(content=None, embed=embed)

    @commands.command(name="starweek")
    @commands.has_permissions(manage_roles=True)
    async def star_of_week(self, ctx, member: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name="⟡ star of the week")
        if not role:
            return await ctx.send("✗ Star of the Week role not found! Run `!setuproles` first.")

        for m in ctx.guild.members:
            if role in m.roles and m != member:
                await m.remove_roles(role)

        await member.add_roles(role)
        embed = discord.Embed(
            title="⟡﹒ Star of the Week!",
            description=f"✶ Congratulations to **{member.mention}** for being the **Star of the Week**! ✶\n\n"
                        f"They are the most amazing member this week! ♡",
            color=0xfbbf24
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="﹒✶﹒ Keep being awesome! ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo")
    async def server_info(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(
            title=f"✿﹒ {guild.name}",
            color=0xb5a8d5
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="◎ Members", value=f"**{guild.member_count}**", inline=True)
        embed.add_field(name="⿴ Channels", value=f"**{len(guild.channels)}**", inline=True)
        embed.add_field(name="◖ Roles", value=f"**{len(guild.roles)}**", inline=True)
        embed.add_field(name="⟡ Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="✶ Created", value=guild.created_at.strftime("%b %d, %Y"), inline=True)
        embed.add_field(name="ıllı Boosts", value=f"**{guild.premium_subscription_count}**", inline=True)
        embed.set_footer(text="﹒✶﹒⊹﹒ " + guild.name + " ﹒⊹﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="memberinfo")
    async def member_info(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"◎﹒ {member.display_name}",
            color=member.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="◖ Username", value=str(member), inline=True)
        embed.add_field(name="⟡ ID", value=str(member.id), inline=True)
        embed.add_field(name="✿ Joined", value=member.joined_at.strftime("%b %d, %Y") if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="◎ Account Created", value=member.created_at.strftime("%b %d, %Y"), inline=True)
        top_role = member.top_role.name if member.top_role.name != "@everyone" else "None"
        embed.add_field(name="★ Top Role", value=top_role, inline=True)
        embed.add_field(name="⊹ Roles", value=f"**{len(member.roles) - 1}** roles", inline=True)
        embed.set_footer(text="﹒✶﹒⊹﹒ Member Info ﹒⊹﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = 10):
        if amount < 1 or amount > 100:
            return await ctx.send("✗ Amount must be between 1 and 100.")
        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"✿ Deleted **{len(deleted) - 1}** messages!")
        await asyncio.sleep(3)
        try:
            await msg.delete()
        except Exception:
            pass

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason given"):
        await member.kick(reason=reason)
        embed = discord.Embed(description=f"✿ Kicked **{member}** | Reason: {reason}", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason given"):
        await member.ban(reason=reason)
        embed = discord.Embed(description=f"✿ Banned **{member}** | Reason: {reason}", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, username: str):
        banned = [entry async for entry in ctx.guild.bans()]
        for entry in banned:
            if str(entry.user) == username:
                await ctx.guild.unban(entry.user)
                embed = discord.Embed(description=f"✿ Unbanned **{entry.user}**!", color=0xb5a8d5)
                return await ctx.send(embed=embed)
        await ctx.send(f"✗ Could not find banned user `{username}`")

    @commands.command(name="mute")
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = "No reason given"):
        muted_role = discord.utils.get(ctx.guild.roles, name="muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)
        await member.add_roles(muted_role, reason=reason)
        embed = discord.Embed(description=f"🔇 Muted **{member}** | Reason: {reason}", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @commands.command(name="unmute")
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member):
        muted_role = discord.utils.get(ctx.guild.roles, name="muted")
        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role)
            embed = discord.Embed(description=f"🔊 Unmuted **{member}**!", color=0xb5a8d5)
            await ctx.send(embed=embed)
        else:
            await ctx.send("✗ That member is not muted.")

async def setup(bot):
    await bot.add_cog(Setup(bot))
