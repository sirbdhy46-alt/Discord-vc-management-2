import discord
from discord.ext import commands
import logging
import json
import os

logger = logging.getLogger(__name__)

ROLES_CONFIG = [
    # ── OWNER & ADMIN ──────────────────────────────────────────────────
    {
        "name": "⟡ owner",
        "color": 0xffd700,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(administrator=True),
        "category": "staff",
        "description": "The server owner — supreme authority"
    },
    {
        "name": "✸ co-owner",
        "color": 0xf0a500,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(administrator=True),
        "category": "staff",
        "description": "Co-owner with near-full powers"
    },
    {
        "name": "★ head mod",
        "color": 0xff6b9d,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            manage_guild=True, manage_channels=True, manage_roles=True,
            manage_messages=True, kick_members=True, ban_members=True,
            move_members=True, mute_members=True, deafen_members=True,
            manage_nicknames=True, view_audit_log=True
        ),
        "category": "staff",
        "description": "Head Moderator"
    },
    {
        "name": "◎ moderator",
        "color": 0xc084fc,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            manage_messages=True, kick_members=True,
            move_members=True, mute_members=True, deafen_members=True,
            manage_nicknames=True, view_audit_log=True
        ),
        "category": "staff",
        "description": "Moderator — keeps peace in the server"
    },
    {
        "name": "⿴ helper",
        "color": 0x818cf8,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            manage_messages=True, mute_members=True
        ),
        "category": "staff",
        "description": "Community helper"
    },
    # ── SPECIAL ROLES ──────────────────────────────────────────────────
    {
        "name": "✿ girl",
        "color": 0xf9a8d4,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "special",
        "description": "Girl role — 💖"
    },
    {
        "name": "⟡ star of the week",
        "color": 0xfbbf24,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "special",
        "description": "Weekly highlight! Most active/fav member"
    },
    {
        "name": "✶ artist",
        "color": 0x34d399,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "special",
        "description": "Talented artists of the server"
    },
    {
        "name": "ıllı server booster",
        "color": 0xff73fa,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "special",
        "description": "Boosted the server — legend ♡"
    },
    {
        "name": "◖ shivam",
        "color": 0x60a5fa,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions(
            move_members=True, manage_channels=False
        ),
        "category": "special",
        "description": "Shivam's special role"
    },
    {
        "name": "⊹ ice tea",
        "color": 0x67e8f9,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "special",
        "description": "Ice Tea's special role"
    },
    # ── LEVEL ROLES ────────────────────────────────────────────────────
    {
        "name": "░ newbie",
        "color": 0x9ca3af,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 1,
        "description": "Level 1 — just arrived"
    },
    {
        "name": "◌ wanderer",
        "color": 0x6ee7b7,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 5,
        "description": "Level 5 — exploring"
    },
    {
        "name": "✦ regular",
        "color": 0x38bdf8,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 10,
        "description": "Level 10 — a regular now!"
    },
    {
        "name": "⟡ vibe member",
        "color": 0xa78bfa,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 15,
        "description": "Level 15 — vibing"
    },
    {
        "name": "✿ bloomer",
        "color": 0xf9a8d4,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 20,
        "description": "Level 20 — blossoming"
    },
    {
        "name": "◎ known face",
        "color": 0xfbbf24,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 30,
        "description": "Level 30 — well known"
    },
    {
        "name": "★ rising star",
        "color": 0xf97316,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 40,
        "description": "Level 40 — rising!"
    },
    {
        "name": "❀ legend",
        "color": 0xef4444,
        "hoist": True,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 50,
        "description": "Level 50 — absolute legend"
    },
    {
        "name": "✸ elite",
        "color": 0xec4899,
        "hoist": True,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 75,
        "description": "Level 75 — elite tier"
    },
    {
        "name": "⊹ immortal",
        "color": 0xffd700,
        "hoist": True,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "level",
        "level": 100,
        "description": "Level 100 — immortal legend"
    },
    # ── VC ROLES ───────────────────────────────────────────────────────
    {
        "name": "◖ vc member",
        "color": 0x6366f1,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions(
            connect=True, speak=True, use_voice_activation=True,
            stream=True, use_embedded_activities=True
        ),
        "category": "vc",
        "description": "Can join all normal VCs"
    },
    {
        "name": "⿸ vc moderator",
        "color": 0x8b5cf6,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions(
            connect=True, speak=True, move_members=True,
            mute_members=True, deafen_members=True
        ),
        "category": "vc",
        "description": "Can moderate voice channels"
    },
    # ── GENDER / SOCIAL ROLES ──────────────────────────────────────────
    {
        "name": "˃ᴗ˂ boy",
        "color": 0x60a5fa,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "social",
        "description": "Boy role"
    },
    {
        "name": "◜ᴗ◝ non-binary",
        "color": 0xa3e635,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "social",
        "description": "Non-binary role"
    },
    # ── GAMER ROLES ────────────────────────────────────────────────────
    {
        "name": "◍ gamer",
        "color": 0x22c55e,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "gaming",
        "description": "General gamer role"
    },
    {
        "name": "░ among us",
        "color": 0xdc2626,
        "hoist": False,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "gaming",
        "description": "Among Us ping role"
    },
    {
        "name": "▨ free fire",
        "color": 0xf97316,
        "hoist": False,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "gaming",
        "description": "Free Fire ping role"
    },
    {
        "name": "▧ bgmi",
        "color": 0xfbbf24,
        "hoist": False,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "gaming",
        "description": "BGMI ping role"
    },
    {
        "name": "▦ ludo",
        "color": 0x84cc16,
        "hoist": False,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "gaming",
        "description": "Ludo King ping role"
    },
    {
        "name": "▥ call of duty",
        "color": 0x6b7280,
        "hoist": False,
        "mentionable": True,
        "permissions": discord.Permissions.none(),
        "category": "gaming",
        "description": "Call of Duty ping role"
    },
    # ── MISC ───────────────────────────────────────────────────────────
    {
        "name": "ᶻz sleepy",
        "color": 0x94a3b8,
        "hoist": False,
        "mentionable": False,
        "permissions": discord.Permissions.none(),
        "category": "misc",
        "description": "Always sleepy 💤"
    },
    {
        "name": "⿴ server messager",
        "color": 0x0ea5e9,
        "hoist": False,
        "mentionable": True,
        "permissions": discord.Permissions(
            mention_everyone=True
        ),
        "category": "misc",
        "description": "Can ping @everyone/@here for announcements"
    },
]


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setuproles")
    @commands.has_permissions(administrator=True)
    async def setup_roles(self, ctx):
        msg = await ctx.send("⟡ Creating all roles... please wait!")
        created = 0
        skipped = 0
        failed = 0

        for role_cfg in ROLES_CONFIG:
            existing = discord.utils.get(ctx.guild.roles, name=role_cfg["name"])
            if existing:
                skipped += 1
                continue
            try:
                await ctx.guild.create_role(
                    name=role_cfg["name"],
                    color=role_cfg["color"],
                    hoist=role_cfg["hoist"],
                    mentionable=role_cfg["mentionable"],
                    permissions=role_cfg["permissions"],
                    reason="Bot role setup"
                )
                created += 1
                await discord.utils.sleep_until(discord.utils.utcnow())
            except Exception as e:
                logger.error(f"Failed to create role {role_cfg['name']}: {e}")
                failed += 1

        embed = discord.Embed(
            title="✿﹒ Roles Setup Complete!",
            description=f"✅ Created: **{created}**\n⏭️ Skipped (exist): **{skipped}**\n❌ Failed: **{failed}**",
            color=0xb5a8d5
        )
        await msg.edit(content=None, embed=embed)

    @commands.command(name="roles")
    async def roles_info(self, ctx):
        embed = discord.Embed(
            title="⟡﹒ Server Roles",
            description="All the roles in this server!",
            color=0xb5a8d5
        )

        categories = {
            "staff": ("★ Staff Roles", []),
            "special": ("✿ Special Roles", []),
            "level": ("⊹ Level Roles", []),
            "vc": ("◖ VC Roles", []),
            "gaming": ("◍ Gaming Roles", []),
            "social": ("♡ Social Roles", []),
            "misc": ("⿴ Misc Roles", []),
        }

        for role_cfg in ROLES_CONFIG:
            cat = role_cfg.get("category", "misc")
            level_str = f" (Lv.{role_cfg['level']})" if "level" in role_cfg else ""
            categories[cat][1].append(f"`{role_cfg['name']}`{level_str} — {role_cfg['description']}")

        for cat_key, (cat_name, entries) in categories.items():
            if entries:
                embed.add_field(name=cat_name, value="\n".join(entries), inline=False)

        embed.set_footer(text="﹒✶﹒⊹﹒ Use !setup to create all roles ﹒⊹﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="giverole")
    @commands.has_permissions(manage_roles=True)
    async def give_role(self, ctx, member: discord.Member, *, role_name: str):
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"✗ Role **{role_name}** not found!")
        await member.add_roles(role)
        embed = discord.Embed(description=f"✿ Gave **{role.name}** to **{member.display_name}**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @commands.command(name="removerole")
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, *, role_name: str):
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"✗ Role **{role_name}** not found!")
        await member.remove_roles(role)
        embed = discord.Embed(description=f"✿ Removed **{role.name}** from **{member.display_name}**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Roles(bot))
