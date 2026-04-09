import discord
from discord.ext import commands
import json
import os
import logging

logger = logging.getLogger(__name__)
DATA_FILE = "data/invites.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Invites(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.invite_cache = {}

    def get_guild_data(self, guild_id):
        gid = str(guild_id)
        if gid not in self.data:
            self.data[gid] = {}
        return self.data[gid]

    def get_member_data(self, guild_id, user_id):
        gd = self.get_guild_data(guild_id)
        mid = str(user_id)
        if mid not in gd:
            gd[mid] = {"invites": 0, "left": 0, "fake": 0, "invited_by": None, "invited": []}
        return gd[mid]

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                invites = await guild.invites()
                self.invite_cache[guild.id] = {inv.code: inv.uses for inv in invites}
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if invite.guild.id not in self.invite_cache:
            self.invite_cache[invite.guild.id] = {}
        self.invite_cache[invite.guild.id][invite.code] = invite.uses

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        cache = self.invite_cache.get(invite.guild.id, {})
        cache.pop(invite.code, None)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        try:
            new_invites = await guild.invites()
        except Exception:
            return

        old_cache = self.invite_cache.get(guild.id, {})
        inviter = None
        used_code = None

        for inv in new_invites:
            old_uses = old_cache.get(inv.code, 0)
            if inv.uses > old_uses:
                inviter = inv.inviter
                used_code = inv.code
                break

        self.invite_cache[guild.id] = {inv.code: inv.uses for inv in new_invites}

        md = self.get_member_data(guild.id, member.id)
        if inviter:
            md["invited_by"] = str(inviter.id)
            inv_data = self.get_member_data(guild.id, inviter.id)
            inv_data["invites"] += 1
            if str(member.id) not in inv_data["invited"]:
                inv_data["invited"].append(str(member.id))
        save_data(self.data)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        md = self.get_member_data(guild.id, member.id)
        inviter_id = md.get("invited_by")
        if inviter_id:
            inv_data = self.get_member_data(guild.id, int(inviter_id))
            inv_data["left"] = inv_data.get("left", 0) + 1
            save_data(self.data)

    @commands.command(name="invites")
    async def check_invites(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        md = self.get_member_data(ctx.guild.id, member.id)
        real = md["invites"] - md.get("left", 0) - md.get("fake", 0)

        embed = discord.Embed(
            title=f"⟡﹒ {member.display_name}'s Invites",
            color=0xb5a8d5
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="✿ Total", value=f"**{md['invites']}**", inline=True)
        embed.add_field(name="◎ Real", value=f"**{real}**", inline=True)
        embed.add_field(name="ᶻz Left", value=f"**{md.get('left', 0)}**", inline=True)
        embed.add_field(name="✗ Fake", value=f"**{md.get('fake', 0)}**", inline=True)

        inviter_id = md.get("invited_by")
        if inviter_id:
            inviter = ctx.guild.get_member(int(inviter_id))
            if inviter:
                embed.add_field(name="⟡ Invited By", value=inviter.mention, inline=True)

        embed.set_footer(text="﹒✶﹒ Invite more people! ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="inviteleaderboard", aliases=["invlb", "topiventers"])
    async def invite_lb(self, ctx):
        gd = self.get_guild_data(ctx.guild.id)
        sorted_data = sorted(gd.items(), key=lambda x: x[1].get("invites", 0), reverse=True)[:10]

        embed = discord.Embed(
            title="⟡﹒ Invite Leaderboard",
            description="Top inviters of the server!",
            color=0xb5a8d5
        )
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        rows = []
        for i, (uid, udata) in enumerate(sorted_data):
            if udata.get("invites", 0) == 0:
                continue
            m = ctx.guild.get_member(int(uid))
            name = m.display_name if m else f"User {uid}"
            real = udata["invites"] - udata.get("left", 0) - udata.get("fake", 0)
            rows.append(f"{medals[i]} **{name}** — **{udata['invites']}** invites ({real} real)")

        embed.description = "\n".join(rows) if rows else "No invite data yet!"
        embed.set_footer(text="﹒✶﹒ Invite friends to climb the board! ﹒✶﹒")
        await ctx.send(embed=embed)

    @commands.command(name="inviteinfo")
    async def invite_info(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        md = self.get_member_data(ctx.guild.id, member.id)
        invited_ids = md.get("invited", [])

        embed = discord.Embed(
            title=f"⟡﹒ Invite Info — {member.display_name}",
            color=0xb5a8d5
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        inviter_id = md.get("invited_by")
        if inviter_id:
            inv = ctx.guild.get_member(int(inviter_id))
            embed.add_field(name="Joined via", value=inv.mention if inv else f"<@{inviter_id}>", inline=False)
        else:
            embed.add_field(name="Joined via", value="Unknown / Direct", inline=False)

        if invited_ids:
            mentions = [f"<@{uid}>" for uid in invited_ids[:10]]
            embed.add_field(name=f"Invited ({len(invited_ids)})", value=", ".join(mentions), inline=False)
        else:
            embed.add_field(name="Invited", value="Nobody yet", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="resetinvites")
    @commands.has_permissions(administrator=True)
    async def reset_invites(self, ctx, member: discord.Member = None):
        if member:
            md = self.get_member_data(ctx.guild.id, member.id)
            md["invites"] = 0
            md["left"] = 0
            md["fake"] = 0
            save_data(self.data)
            await ctx.send(embed=discord.Embed(description=f"✿ Reset invites for **{member.display_name}**!", color=0xb5a8d5))
        else:
            gid = str(ctx.guild.id)
            self.data[gid] = {}
            save_data(self.data)
            await ctx.send(embed=discord.Embed(description="✿ Reset **all** invite data!", color=0xb5a8d5))

async def setup(bot):
    await bot.add_cog(Invites(bot))
