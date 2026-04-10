import discord
from discord.ext import commands
import json
import os
import asyncio
import logging
import random

logger = logging.getLogger(__name__)

DATA_FILE = "data/vc_data.json"
CONFIG_FILE = "data/vc_config.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"temp_vcs": {}, "jtc_channels": {}, "vc_owners": {}}

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

VC_SYMBOLS = ["✿", "⟡", "♡", "✶", "⊹", "❀", "★", "◎", "◖", "🌸"]

# ── Modals ────────────────────────────────────────────────────────────────────

class NameModal(discord.ui.Modal, title="♡ Rename the VC"):
    new_name = discord.ui.TextInput(
        label="New VC Name",
        placeholder="e.g. ✿ cozy corner",
        max_length=100
    )
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class LimitModal(discord.ui.Modal, title="⟡ Set User Limit"):
    limit = discord.ui.TextInput(
        label="How many people? (0 = unlimited)",
        placeholder="e.g. 5",
        max_length=2
    )
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class BitrateModal(discord.ui.Modal, title="🎵 Set Audio Bitrate"):
    bitrate = discord.ui.TextInput(
        label="Bitrate in kbps (8 to 96)",
        placeholder="e.g. 64",
        max_length=3
    )
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

class UserActionModal(discord.ui.Modal):
    user_input = discord.ui.TextInput(
        label="User ID or username",
        placeholder="Paste their ID or type their name",
        max_length=100
    )
    def __init__(self, action_title):
        super().__init__(title=action_title)
    async def on_submit(self, interaction: discord.Interaction):
        self.interaction = interaction
        self.stop()

# ── VC Control Panel View ─────────────────────────────────────────────────────

class VCControlView(discord.ui.View):
    def __init__(self, cog, channel_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.channel_id = channel_id

    async def vc_check(self, interaction):
        """Anyone in the VC can use buttons."""
        channel = interaction.guild.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="♡ This VC no longer exists~",
                    color=0xFFB6C1
                ), ephemeral=True
            )
            return False
        if interaction.user not in channel.members:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="♡ You need to be **in the VC** to use this!",
                    color=0xFFB6C1
                ), ephemeral=True
            )
            return False
        return channel

    async def owner_only_check(self, interaction):
        """Only the VC owner can use this."""
        channel = interaction.guild.get_channel(self.channel_id)
        if not channel:
            await interaction.response.send_message(
                embed=discord.Embed(description="♡ This VC no longer exists~", color=0xFFB6C1),
                ephemeral=True
            )
            return False
        owner_id = self.cog.get_vc_owner(self.channel_id)
        if str(interaction.user.id) != str(owner_id):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="♡ Only the **VC owner** can do this~",
                    color=0xFFB6C1
                ), ephemeral=True
            )
            return False
        return channel

    def success_embed(self, text):
        return discord.Embed(description=f"♡ {text}", color=0xFF9FF3)

    def error_embed(self, text):
        return discord.Embed(description=f"✗ {text}", color=0xFF6B6B)

    # ── Row 0 — Basic ─────────────────────────────────────────────────────────

    @discord.ui.button(emoji="✏️", label="Rename", style=discord.ButtonStyle.primary,
                       custom_id="vcctrl:name", row=0)
    async def btn_name(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        modal = NameModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        await channel.edit(name=modal.new_name.value)
        await modal.interaction.response.send_message(
            embed=self.success_embed(f"VC renamed to **{modal.new_name.value}**!"), ephemeral=True)

    @discord.ui.button(emoji="👥", label="Limit", style=discord.ButtonStyle.primary,
                       custom_id="vcctrl:limit", row=0)
    async def btn_limit(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        modal = LimitModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        try:
            lim = int(modal.limit.value)
            if not 0 <= lim <= 99: raise ValueError
            await channel.edit(user_limit=lim)
            txt = "unlimited" if lim == 0 else str(lim)
            await modal.interaction.response.send_message(
                embed=self.success_embed(f"Limit set to **{txt}**!"), ephemeral=True)
        except ValueError:
            await modal.interaction.response.send_message(
                embed=self.error_embed("Enter a number from 0 to 99!"), ephemeral=True)

    @discord.ui.button(emoji="🔒", label="Lock", style=discord.ButtonStyle.danger,
                       custom_id="vcctrl:lock", row=0)
    async def btn_lock(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        await channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message(
            embed=self.success_embed("VC **locked**~ no one can sneak in 🔒"), ephemeral=True)

    @discord.ui.button(emoji="🔓", label="Unlock", style=discord.ButtonStyle.success,
                       custom_id="vcctrl:unlock", row=0)
    async def btn_unlock(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        await channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message(
            embed=self.success_embed("VC **unlocked**~ everyone can join 🔓"), ephemeral=True)

    @discord.ui.button(emoji="👁️", label="Hide", style=discord.ButtonStyle.secondary,
                       custom_id="vcctrl:hide", row=0)
    async def btn_hide(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message(
            embed=self.success_embed("VC is now **hidden** from everyone~ 👁️"), ephemeral=True)

    # ── Row 1 — Visibility & Members ──────────────────────────────────────────

    @discord.ui.button(emoji="✨", label="Unhide", style=discord.ButtonStyle.secondary,
                       custom_id="vcctrl:show", row=1)
    async def btn_show(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        await channel.set_permissions(interaction.guild.default_role, view_channel=True)
        await interaction.response.send_message(
            embed=self.success_embed("VC is **visible** again ✨"), ephemeral=True)

    @discord.ui.button(emoji="🌸", label="Invite", style=discord.ButtonStyle.success,
                       custom_id="vcctrl:invite", row=1)
    async def btn_invite(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        modal = UserActionModal("🌸 Invite Someone")
        await interaction.response.send_modal(modal)
        await modal.wait()
        member = await self.cog.resolve_member(interaction.guild, modal.user_input.value)
        if not member:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("User not found!"), ephemeral=True)
        await channel.set_permissions(member, connect=True, view_channel=True)
        try:
            await member.send(embed=discord.Embed(
                description=f"♡ **{interaction.user.display_name}** invited you to **{channel.name}** in **{interaction.guild.name}**~",
                color=0xFF9FF3
            ))
        except Exception:
            pass
        await modal.interaction.response.send_message(
            embed=self.success_embed(f"Invited **{member.display_name}** 🌸"), ephemeral=True)

    @discord.ui.button(emoji="💌", label="Trust", style=discord.ButtonStyle.success,
                       custom_id="vcctrl:trust", row=1)
    async def btn_trust(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        modal = UserActionModal("💌 Trust a User")
        await interaction.response.send_modal(modal)
        await modal.wait()
        member = await self.cog.resolve_member(interaction.guild, modal.user_input.value)
        if not member:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("User not found!"), ephemeral=True)
        await channel.set_permissions(member, connect=True, speak=True, stream=True)
        await modal.interaction.response.send_message(
            embed=self.success_embed(f"**{member.display_name}** is now trusted 💌"), ephemeral=True)

    @discord.ui.button(emoji="💔", label="Untrust", style=discord.ButtonStyle.danger,
                       custom_id="vcctrl:untrust", row=1)
    async def btn_untrust(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        modal = UserActionModal("💔 Untrust a User")
        await interaction.response.send_modal(modal)
        await modal.wait()
        member = await self.cog.resolve_member(interaction.guild, modal.user_input.value)
        if not member:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("User not found!"), ephemeral=True)
        await channel.set_permissions(member, overwrite=None)
        await modal.interaction.response.send_message(
            embed=self.success_embed(f"**{member.display_name}** untrusted 💔"), ephemeral=True)

    @discord.ui.button(emoji="🎵", label="Bitrate", style=discord.ButtonStyle.secondary,
                       custom_id="vcctrl:bitrate", row=1)
    async def btn_bitrate(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        modal = BitrateModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        try:
            br = int(modal.bitrate.value)
            if not 8 <= br <= 96: raise ValueError
            await channel.edit(bitrate=br * 1000)
            await modal.interaction.response.send_message(
                embed=self.success_embed(f"Bitrate set to **{br}kbps** 🎵"), ephemeral=True)
        except ValueError:
            await modal.interaction.response.send_message(
                embed=self.error_embed("Enter a number from 8 to 96!"), ephemeral=True)

    # ── Row 2 — Kick / Ban ────────────────────────────────────────────────────

    @discord.ui.button(emoji="👢", label="Kick", style=discord.ButtonStyle.danger,
                       custom_id="vcctrl:kick", row=2)
    async def btn_kick(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        modal = UserActionModal("👢 Kick Someone")
        await interaction.response.send_modal(modal)
        await modal.wait()
        member = await self.cog.resolve_member(interaction.guild, modal.user_input.value)
        if not member:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("User not found!"), ephemeral=True)
        if member not in channel.members:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("That user isn't in the VC!"), ephemeral=True)
        if member.id == interaction.user.id:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("You can't kick yourself silly~"), ephemeral=True)
        await member.move_to(None)
        await modal.interaction.response.send_message(
            embed=self.success_embed(f"**{member.display_name}** was kicked~ 👢"), ephemeral=True)

    @discord.ui.button(emoji="🚫", label="Ban", style=discord.ButtonStyle.danger,
                       custom_id="vcctrl:ban", row=2)
    async def btn_ban(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        modal = UserActionModal("🚫 Ban from VC")
        await interaction.response.send_modal(modal)
        await modal.wait()
        member = await self.cog.resolve_member(interaction.guild, modal.user_input.value)
        if not member:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("User not found!"), ephemeral=True)
        await channel.set_permissions(member, connect=False)
        if member in channel.members:
            await member.move_to(None)
        await modal.interaction.response.send_message(
            embed=self.success_embed(f"**{member.display_name}** banned from the VC 🚫"), ephemeral=True)

    @discord.ui.button(emoji="✅", label="Unban", style=discord.ButtonStyle.success,
                       custom_id="vcctrl:unban", row=2)
    async def btn_unban(self, interaction, button):
        channel = await self.vc_check(interaction)
        if not channel: return
        modal = UserActionModal("✅ Unban from VC")
        await interaction.response.send_modal(modal)
        await modal.wait()
        member = await self.cog.resolve_member(interaction.guild, modal.user_input.value)
        if not member:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("User not found!"), ephemeral=True)
        await channel.set_permissions(member, connect=True)
        await modal.interaction.response.send_message(
            embed=self.success_embed(f"**{member.display_name}** can rejoin now ✅"), ephemeral=True)

    @discord.ui.button(emoji="👑", label="Claim", style=discord.ButtonStyle.primary,
                       custom_id="vcctrl:claim", row=2)
    async def btn_claim(self, interaction, button):
        channel = interaction.guild.get_channel(self.channel_id)
        if not channel:
            return await interaction.response.send_message(
                embed=self.error_embed("VC not found!"), ephemeral=True)
        owner_id = self.cog.get_vc_owner(self.channel_id)
        owner = interaction.guild.get_member(int(owner_id)) if owner_id else None
        if owner and owner in channel.members:
            return await interaction.response.send_message(
                embed=self.error_embed("The owner is still in the VC!"), ephemeral=True)
        if interaction.user not in channel.members:
            return await interaction.response.send_message(
                embed=self.error_embed("Join the VC first to claim it!"), ephemeral=True)
        self.cog.set_vc_owner(channel.id, interaction.user.id)
        await channel.set_permissions(interaction.user, connect=True, speak=True,
                                      move_members=True, mute_members=True, manage_channels=True)
        await interaction.response.send_message(
            embed=self.success_embed(f"**{interaction.user.display_name}** claimed the VC~ 👑"), ephemeral=True)

    @discord.ui.button(emoji="🔄", label="Transfer", style=discord.ButtonStyle.primary,
                       custom_id="vcctrl:transfer", row=2)
    async def btn_transfer(self, interaction, button):
        channel = await self.owner_only_check(interaction)
        if not channel: return
        modal = UserActionModal("🔄 Transfer VC Ownership")
        await interaction.response.send_modal(modal)
        await modal.wait()
        member = await self.cog.resolve_member(interaction.guild, modal.user_input.value)
        if not member:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("User not found!"), ephemeral=True)
        if member not in channel.members:
            return await modal.interaction.response.send_message(
                embed=self.error_embed("They need to be in the VC first!"), ephemeral=True)
        self.cog.set_vc_owner(channel.id, member.id)
        await channel.set_permissions(interaction.user, overwrite=None)
        await channel.set_permissions(member, connect=True, speak=True, move_members=True,
                                      mute_members=True, deafen_members=True, manage_channels=True)
        await modal.interaction.response.send_message(
            embed=self.success_embed(f"VC passed to **{member.display_name}**~ 🔄"), ephemeral=True)

    # ── Row 3 — Info ──────────────────────────────────────────────────────────

    @discord.ui.button(emoji="🌹", label="Status", style=discord.ButtonStyle.secondary,
                       custom_id="vcctrl:status", row=3)
    async def btn_status(self, interaction, button):
        channel = interaction.guild.get_channel(self.channel_id)
        if not channel:
            return await interaction.response.send_message(
                embed=self.error_embed("VC not found!"), ephemeral=True)
        owner_id = self.cog.get_vc_owner(self.channel_id)
        owner = interaction.guild.get_member(int(owner_id)) if owner_id else None
        perms = channel.permissions_for(interaction.guild.default_role)
        members_list = " ﹒ ".join(f"♡ {m.display_name}" for m in channel.members) or "Empty~"

        embed = discord.Embed(
            title=f"🌸﹒ {channel.name}",
            color=0xFF9FF3
        )
        embed.set_thumbnail(url=owner.display_avatar.url if owner else None)
        embed.add_field(name="👑 Owner", value=owner.mention if owner else "Unknown", inline=True)
        embed.add_field(name="👥 Members", value=f"{len(channel.members)} / {channel.user_limit or '∞'}", inline=True)
        embed.add_field(name="🎵 Bitrate", value=f"{channel.bitrate // 1000}kbps", inline=True)
        embed.add_field(name="🔒 Locked", value="Yes 🔒" if not perms.connect else "No 🔓", inline=True)
        embed.add_field(name="👁️ Hidden", value="Yes 👁️" if not perms.view_channel else "No ✨", inline=True)
        embed.add_field(name="♡ Inside", value=members_list, inline=False)
        embed.set_footer(text="﹒✶﹒⊹﹒ vc status ﹒⊹﹒✶﹒")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ── VCManager Cog ─────────────────────────────────────────────────────────────

class VCManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.config = load_config()

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

    def get_interface_channel(self, guild_id):
        cid = self.config.get(str(guild_id), {}).get("interface_channel")
        return self.bot.get_channel(int(cid)) if cid else None

    async def resolve_member(self, guild, value):
        value = value.strip().strip("<@!&>")
        try:
            return guild.get_member(int(value))
        except ValueError:
            return discord.utils.find(
                lambda m: m.display_name.lower() == value.lower() or m.name.lower() == value.lower(),
                guild.members
            )

    # ── Panel builder ─────────────────────────────────────────────────────────

    def build_panel_embed(self, member, channel):
        embed = discord.Embed(
            title=f"🌸﹒ {channel.name}",
            description=(
                "♡ **Your cozy little vc is ready~**\n"
                "⊹ Everyone inside can use the controls below!\n\n"
                "✏️ rename  ﹒  👥 set limit  ﹒  🔒 lock  ﹒  🔓 unlock\n"
                "👁️ hide  ﹒  ✨ unhide  ﹒  🌸 invite  ﹒  💌 trust\n"
                "💔 untrust  ﹒  👢 kick  ﹒  🚫 ban  ﹒  ✅ unban\n"
                "👑 claim  ﹒  🔄 transfer  ﹒  🌹 status"
            ),
            color=0xFF9FF3
        )
        embed.set_author(
            name=f"{member.display_name}'s vc~",
            icon_url=member.display_avatar.url
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="◎ Channel", value=channel.mention, inline=True)
        embed.add_field(name="👑 Owner", value=member.mention, inline=True)
        embed.add_field(name="👥 Limit", value=str(channel.user_limit) if channel.user_limit else "∞", inline=True)
        embed.set_footer(text="﹒♡﹒✿﹒⊹﹒ anyone in the vc can use these ﹒⊹﹒✿﹒♡﹒")
        return embed

    # ── Voice state listener ──────────────────────────────────────────────────

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
                mute_members=True, deafen_members=True, manage_channels=True
            )
        }
        if jtc_type == "private":
            overwrites[guild.default_role] = discord.PermissionOverwrite(connect=False)

        user_limits = {"normal": 0, "private": 0, "duo": 2, "gaming": 10}
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

            interface_ch = self.get_interface_channel(guild.id)
            if interface_ch:
                embed = self.build_panel_embed(member, new_vc)
                view = VCControlView(self, new_vc.id)
                await interface_ch.send(
                    content=f"{member.mention} ♡",
                    embed=embed,
                    view=view
                )

        except Exception as e:
            logger.error(f"Error creating temp VC: {e}")

    def get_member_vc(self, member):
        if member.voice and member.voice.channel:
            ch = member.voice.channel
            if self.is_temp_vc(ch.id) and self.is_vc_owner(ch.id, member.id):
                return ch
        return None

    # ── Admin setup ───────────────────────────────────────────────────────────

    @commands.command(name="setvcinterface")
    @commands.has_permissions(administrator=True)
    async def set_vc_interface(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gid = str(ctx.guild.id)
        if gid not in self.config:
            self.config[gid] = {}
        self.config[gid]["interface_channel"] = str(channel.id)
        save_config(self.config)
        embed = discord.Embed(
            description=f"♡ VC control panels will now appear in {channel.mention} whenever someone creates a VC~",
            color=0xFF9FF3
        )
        await ctx.send(embed=embed)

    # ── Text commands ─────────────────────────────────────────────────────────

    @commands.group(name="vc", invoke_without_command=True)
    async def vc_group(self, ctx):
        embed = discord.Embed(
            title="🌸﹒ VC Commands",
            description=(
                "Use the **control panel** in your interface channel!\n\n"
                "**Text fallback:**\n"
                "`-vc name <name>` • `-vc limit <num>` • `-vc lock` • `-vc unlock`\n"
                "`-vc hide` • `-vc show` • `-vc kick @user` • `-vc ban @user`\n"
                "`-vc invite @user` • `-vc transfer @user` • `-vc trust @user`\n\n"
                "**Admin:**\n"
                "`-setvcinterface #channel`"
            ),
            color=0xFF9FF3
        )
        embed.set_footer(text="﹒♡﹒✿﹒ Create a VC to get your control panel~ ﹒✿﹒♡﹒")
        await ctx.send(embed=embed)

    @vc_group.command(name="name")
    async def vc_name(self, ctx, *, name: str):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC right now~", color=0xFF9FF3))
        await channel.edit(name=name)
        await ctx.send(embed=discord.Embed(description=f"♡ Renamed to **{name}**~", color=0xFF9FF3))

    @vc_group.command(name="limit")
    async def vc_limit(self, ctx, limit: int):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        if not 0 <= limit <= 99:
            return await ctx.send(embed=discord.Embed(description="✗ Limit must be 0–99!", color=0xFF6B6B))
        await channel.edit(user_limit=limit)
        await ctx.send(embed=discord.Embed(description=f"♡ Limit set to **{limit or 'unlimited'}**~", color=0xFF9FF3))

    @vc_group.command(name="lock")
    async def vc_lock(self, ctx):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        await channel.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send(embed=discord.Embed(description="🔒 VC locked~", color=0xFF9FF3))

    @vc_group.command(name="unlock")
    async def vc_unlock(self, ctx):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        await channel.set_permissions(ctx.guild.default_role, connect=True)
        await ctx.send(embed=discord.Embed(description="🔓 VC unlocked~", color=0xFF9FF3))

    @vc_group.command(name="hide")
    async def vc_hide(self, ctx):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        await channel.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send(embed=discord.Embed(description="👁️ VC hidden~", color=0xFF9FF3))

    @vc_group.command(name="show")
    async def vc_show(self, ctx):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        await channel.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.send(embed=discord.Embed(description="✨ VC visible~", color=0xFF9FF3))

    @vc_group.command(name="kick")
    async def vc_kick(self, ctx, member: discord.Member):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        if member not in channel.members:
            return await ctx.send(embed=discord.Embed(description="✗ They're not in your VC!", color=0xFF6B6B))
        await member.move_to(None)
        await ctx.send(embed=discord.Embed(description=f"👢 Kicked **{member.display_name}**~", color=0xFF9FF3))

    @vc_group.command(name="ban")
    async def vc_ban(self, ctx, member: discord.Member):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        await channel.set_permissions(member, connect=False)
        if member in channel.members:
            await member.move_to(None)
        await ctx.send(embed=discord.Embed(description=f"🚫 Banned **{member.display_name}**~", color=0xFF9FF3))

    @vc_group.command(name="invite")
    async def vc_invite(self, ctx, member: discord.Member):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        await channel.set_permissions(member, connect=True, view_channel=True)
        try:
            await member.send(embed=discord.Embed(
                description=f"♡ **{ctx.author.display_name}** invited you to **{channel.name}** in **{ctx.guild.name}**~",
                color=0xFF9FF3
            ))
        except Exception:
            pass
        await ctx.send(embed=discord.Embed(description=f"🌸 Invited **{member.display_name}**~", color=0xFF9FF3))

    @vc_group.command(name="transfer")
    async def vc_transfer(self, ctx, member: discord.Member):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        if member not in channel.members:
            return await ctx.send(embed=discord.Embed(description="✗ They're not in your VC!", color=0xFF6B6B))
        self.set_vc_owner(channel.id, member.id)
        await channel.set_permissions(ctx.author, overwrite=None)
        await channel.set_permissions(member, connect=True, speak=True, move_members=True,
                                      mute_members=True, deafen_members=True, manage_channels=True)
        await ctx.send(embed=discord.Embed(description=f"🔄 Transferred to **{member.display_name}**~", color=0xFF9FF3))

    @vc_group.command(name="trust")
    async def vc_trust(self, ctx, member: discord.Member):
        channel = self.get_member_vc(ctx.author)
        if not channel:
            return await ctx.send(embed=discord.Embed(description="♡ You don't own a temp VC~", color=0xFF9FF3))
        await channel.set_permissions(member, connect=True, speak=True, stream=True)
        await ctx.send(embed=discord.Embed(description=f"💌 **{member.display_name}** is trusted~", color=0xFF9FF3))

async def setup(bot):
    await bot.add_cog(VCManager(bot))
