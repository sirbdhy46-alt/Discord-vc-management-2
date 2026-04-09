import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

DATA_FILE = "data/vc_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"temp_vcs": {}, "jtc_channels": {}, "vc_owners": {}}

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

VC_SYMBOLS = ["✿", "⟡", "♡", "✶", "⊹", "❀", "★", "◎", "⿴", "◖", "░"]

class VCManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()

    def get_vc_owner(self, channel_id):
        return self.data["vc_owners"].get(str(channel_id))

    def set_vc_owner(self, channel_id, user_id):
        self.data["vc_owners"][str(channel_id)] = str(user_id)
        save_data(self.data)

    def is_vc_owner(self, channel_id, user_id):
        return self.get_vc_owner(channel_id) == str(user_id)

    def add_temp_vc(self, channel_id, owner_id, category_id):
        self.data["temp_vcs"][str(channel_id)] = {
            "owner": str(owner_id),
            "category": str(category_id)
        }
        save_data(self.data)

    def remove_temp_vc(self, channel_id):
        self.data["temp_vcs"].pop(str(channel_id), None)
        self.data["vc_owners"].pop(str(channel_id), None)
        save_data(self.data)

    def is_temp_vc(self, channel_id):
        return str(channel_id) in self.data["temp_vcs"]

    def add_jtc(self, channel_id, category_id, jtc_type="normal"):
        self.data["jtc_channels"][str(channel_id)] = {
            "category": str(category_id),
            "type": jtc_type
        }
        save_data(self.data)

    def get_jtc(self, channel_id):
        return self.data["jtc_channels"].get(str(channel_id))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild

        if after.channel:
            jtc_info = self.get_jtc(after.channel.id)
            if jtc_info:
                await self.create_temp_vc(member, after.channel, guild, jtc_info)

        if before.channel and before.channel != after.channel:
            if self.is_temp_vc(before.channel.id):
                await asyncio.sleep(1)
                channel = guild.get_channel(before.channel.id)
                if channel and len(channel.members) == 0:
                    try:
                        await channel.delete()
                        self.remove_temp_vc(before.channel.id)
                        logger.info(f"Deleted empty temp VC: {channel.name}")
                    except Exception as e:
                        logger.error(f"Error deleting temp VC: {e}")

    async def create_temp_vc(self, member, jtc_channel, guild, jtc_info):
        jtc_type = jtc_info.get("type", "normal")
        category = guild.get_channel(int(jtc_info["category"]))
        
        import random
        sym = random.choice(VC_SYMBOLS)
        
        if jtc_type == "private":
            vc_name = f"✦ {member.display_name}'s hideout"
        elif jtc_type == "gaming":
            vc_name = f"◎ {member.display_name}'s game"
        elif jtc_type == "duo":
            vc_name = f"♡ {member.display_name}'s duo"
        else:
            vc_name = f"{sym} {member.display_name}'s vc"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True, speak=True),
            member: discord.PermissionOverwrite(
                connect=True, speak=True, move_members=True,
                mute_members=True, deafen_members=True,
                manage_channels=True
            )
        }

        if jtc_type == "private":
            overwrites[guild.default_role] = discord.PermissionOverwrite(connect=False)
            overwrites[member] = discord.PermissionOverwrite(
                connect=True, speak=True, move_members=True,
                mute_members=True, deafen_members=True, manage_channels=True
            )

        user_limits = {
            "normal": 0,
            "private": 0,
            "duo": 2,
            "gaming": 10,
        }
        user_limit = user_limits.get(jtc_type, 0)

        try:
            new_vc = await guild.create_voice_channel(
                name=vc_name,
                category=category,
                user_limit=user_limit,
                overwrites=overwrites
            )
            self.add_temp_vc(new_vc.id, member.id, category.id if category else 0)
            self.set_vc_owner(new_vc.id, member.id)
            await member.move_to(new_vc)
            logger.info(f"Created temp VC: {new_vc.name} for {member}")
        except Exception as e:
            logger.error(f"Error creating temp VC: {e}")

    def get_member_vc(self, member):
        if member.voice and member.voice.channel:
            ch = member.voice.channel
            if self.is_temp_vc(ch.id) and self.is_vc_owner(ch.id, member.id):
                return ch
        return None

    @commands.group(name="vc", invoke_without_command=True)
    async def vc_group(self, ctx):
        embed = discord.Embed(
            title="⿴﹒VC Commands",
            description="Use `!vc <command>` to manage your voice channel.\n\n"
                        "`name <name>` • `limit <num>` • `lock` • `unlock`\n"
                        "`hide` • `show` • `kick @user` • `ban @user`\n"
                        "`invite @user` • `transfer @user`",
            color=0xb5a8d5
        )
        await ctx.send(embed=embed)

    @vc_group.command(name="name")
    async def vc_name(self, ctx, *, name: str):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        await channel.edit(name=name)
        embed = discord.Embed(description=f"✿ Renamed your VC to **{name}**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @vc_group.command(name="limit")
    async def vc_limit(self, ctx, limit: int):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        if limit < 0 or limit > 99:
            return await ctx.send("✗ Limit must be between 0 (unlimited) and 99.")
        await channel.edit(user_limit=limit)
        lim_str = "unlimited" if limit == 0 else str(limit)
        embed = discord.Embed(description=f"✿ Set user limit to **{lim_str}**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @vc_group.command(name="lock")
    async def vc_lock(self, ctx):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        await channel.set_permissions(ctx.guild.default_role, connect=False)
        embed = discord.Embed(description="🔒 Your VC is now **locked**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @vc_group.command(name="unlock")
    async def vc_unlock(self, ctx):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        await channel.set_permissions(ctx.guild.default_role, connect=True)
        embed = discord.Embed(description="🔓 Your VC is now **unlocked**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @vc_group.command(name="hide")
    async def vc_hide(self, ctx):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        await channel.set_permissions(ctx.guild.default_role, view_channel=False)
        embed = discord.Embed(description="👁️ Your VC is now **hidden**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @vc_group.command(name="show")
    async def vc_show(self, ctx):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        await channel.set_permissions(ctx.guild.default_role, view_channel=True)
        embed = discord.Embed(description="✅ Your VC is now **visible**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @vc_group.command(name="kick")
    async def vc_kick(self, ctx, member: discord.Member):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        if member not in channel.members:
            return await ctx.send("✗ That member is not in your VC!")
        await member.move_to(None)
        embed = discord.Embed(description=f"✿ Kicked **{member.display_name}** from your VC!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @vc_group.command(name="ban")
    async def vc_ban(self, ctx, member: discord.Member):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        await channel.set_permissions(member, connect=False)
        if member in channel.members:
            await member.move_to(None)
        embed = discord.Embed(description=f"✿ Banned **{member.display_name}** from your VC!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @vc_group.command(name="invite")
    async def vc_invite(self, ctx, member: discord.Member):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        await channel.set_permissions(member, connect=True, view_channel=True)
        try:
            await member.send(f"✿ **{ctx.author.display_name}** invited you to their private VC: **{channel.name}** in **{ctx.guild.name}**!")
        except Exception:
            pass
        embed = discord.Embed(description=f"✿ Invited **{member.display_name}** to your VC!", color=0xb5a8d5)
        await ctx.send(embed=embed)

    @vc_group.command(name="transfer")
    async def vc_transfer(self, ctx, member: discord.Member):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send("✗ You don't own a temporary VC right now!")
        if member not in channel.members:
            return await ctx.send("✗ That member is not in your VC!")
        self.set_vc_owner(channel.id, member.id)
        await channel.set_permissions(ctx.author, overwrite=None)
        await channel.set_permissions(member, connect=True, speak=True, move_members=True,
                                      mute_members=True, deafen_members=True, manage_channels=True)
        embed = discord.Embed(description=f"✿ Transferred VC ownership to **{member.display_name}**!", color=0xb5a8d5)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(VCManager(bot))
