import discord
from discord.ext import commands
import json
import os
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)
DATA_FILE = "data/selfroles.json"

# ── Auto setup pages ──────────────────────────────────────────────────────────
AUTO_PAGES = [
    {
        "name": "✦ Interests",
        "description": "✿ Pick your interests below!\n⊹ Click a button to get or remove a role.",
        "roles": [
            {"name": "Gaming",  "search": "gaming",      "color": 0x5865F2, "fallback": "🎮"},
            {"name": "Music",   "search": "headphones",  "color": 0xEB459E, "fallback": "🎵"},
            {"name": "Art",     "search": "palette",     "color": 0xFEE75C, "fallback": "🎨"},
            {"name": "Anime",   "search": "anime",       "color": 0xFF6B9D, "fallback": "✨"},
            {"name": "Movies",  "search": "popcorn",     "color": 0xED4245, "fallback": "🎬"},
            {"name": "Coding",  "search": "programmer",  "color": 0x57F287, "fallback": "💻"},
            {"name": "Sports",  "search": "trophy",      "color": 0xF0B232, "fallback": "🏆"},
            {"name": "Cooking", "search": "chef",        "color": 0xFF9F43, "fallback": "🍳"},
        ]
    },
    {
        "name": "♡ Status & Age",
        "description": "⟡ Choose your relationship status and age group!\n⊹ Click a button to get or remove a role.",
        "roles": [
            {"name": "Single",  "search": "heartbreak",  "color": 0xFF6B6B, "fallback": "💔"},
            {"name": "Taken",   "search": "love",        "color": 0xFF9FF3, "fallback": "💕"},
            {"name": "18+",     "search": "crown",       "color": 0x9B59B6, "fallback": "👑"},
            {"name": "18-",     "search": "star",        "color": 0x3498DB, "fallback": "⭐"},
        ]
    }
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

class SelfRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = load_data()
        self.active_setups = set()

    # ── Interaction handler ───────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")

        # Page navigation
        if custom_id.startswith("selfrole_nav:"):
            parts = custom_id.split(":")
            direction = parts[1]
            current_page = int(parts[2])
            gid = str(interaction.guild.id)
            pages = self.data.get(gid, {}).get("pages", [])
            if not pages:
                return

            new_page = current_page - 1 if direction == "prev" else current_page + 1
            new_page = max(0, min(len(pages) - 1, new_page))

            embed = self.build_page_embed(pages, new_page)
            view = self.build_page_view(pages, interaction.guild, new_page)
            await interaction.response.edit_message(embed=embed, view=view)
            return

        # Role toggle
        if custom_id.startswith("selfrole:"):
            role_id = int(custom_id.split(":")[1])
            role = interaction.guild.get_role(role_id)
            if not role:
                return await interaction.response.send_message(
                    embed=discord.Embed(description="✿ That role no longer exists!", color=0xb5a8d5),
                    ephemeral=True
                )
            member = interaction.user
            if role in member.roles:
                await member.remove_roles(role)
                await interaction.response.send_message(
                    embed=discord.Embed(description=f"ᶻz Removed **{role.name}** from you!", color=0xb5a8d5),
                    ephemeral=True
                )
            else:
                await member.add_roles(role)
                await interaction.response.send_message(
                    embed=discord.Embed(description=f"✿ Gave you **{role.name}**!", color=0xb5a8d5),
                    ephemeral=True
                )

    # ── View & Embed builders ─────────────────────────────────────────────────

    def build_page_view(self, pages, guild, current_page):
        view = discord.ui.View(timeout=None)
        page_roles = pages[current_page].get("roles", [])
        total_pages = len(pages)

        for i, entry in enumerate(page_roles):
            role = guild.get_role(int(entry["role_id"]))
            if not role:
                continue
            emoji_str = entry.get("emoji")
            label = entry.get("label") or role.name
            try:
                emoji = discord.PartialEmoji.from_str(emoji_str) if emoji_str else None
            except Exception:
                emoji = emoji_str
            row = i // 5
            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                custom_id=f"selfrole:{entry['role_id']}",
                style=discord.ButtonStyle.secondary,
                row=row
            )
            view.add_item(button)

        if total_pages > 1:
            prev_btn = discord.ui.Button(
                label="◀ Prev",
                custom_id=f"selfrole_nav:prev:{current_page}",
                style=discord.ButtonStyle.primary,
                disabled=(current_page == 0),
                row=4
            )
            page_indicator = discord.ui.Button(
                label=f"Page {current_page + 1} / {total_pages}",
                custom_id="selfrole_nav:page",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                row=4
            )
            next_btn = discord.ui.Button(
                label="Next ▶",
                custom_id=f"selfrole_nav:next:{current_page}",
                style=discord.ButtonStyle.primary,
                disabled=(current_page == total_pages - 1),
                row=4
            )
            view.add_item(prev_btn)
            view.add_item(page_indicator)
            view.add_item(next_btn)

        return view

    def build_page_embed(self, pages, current_page):
        page = pages[current_page]
        total_pages = len(pages)
        page_name = page.get("name", f"Page {current_page + 1}")
        description = page.get("description", "✿ Click a button to get or remove a role!")

        embed = discord.Embed(
            title=f"⟡﹒ Self Roles  ﹒  {page_name}",
            description=description,
            color=0xb5a8d5
        )
        roles_display = []
        for r in page.get("roles", []):
            emoji = r.get("emoji", "✿")
            label = r.get("label", "Role")
            roles_display.append(f"{emoji} **{label}**")

        if roles_display:
            embed.add_field(name="Available Roles", value="\n".join(roles_display), inline=False)

        embed.set_footer(text=f"﹒✶﹒⊹﹒ Page {current_page + 1} of {total_pages}  ﹒  Toggle roles with buttons below ﹒⊹﹒✶﹒")
        return embed

    def build_simple_view(self, roles_data, guild):
        view = discord.ui.View(timeout=None)
        for i, entry in enumerate(roles_data):
            role = guild.get_role(int(entry["role_id"]))
            if not role:
                continue
            emoji_str = entry.get("emoji")
            label = entry.get("label") or role.name
            try:
                emoji = discord.PartialEmoji.from_str(emoji_str) if emoji_str else None
            except Exception:
                emoji = emoji_str
            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                custom_id=f"selfrole:{entry['role_id']}",
                style=discord.ButtonStyle.secondary,
                row=i // 5
            )
            view.add_item(button)
        return view

    # ── Emoji.gg helpers ──────────────────────────────────────────────────────

    async def fetch_emoji_gg(self, query):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://emoji.gg/api/") as resp:
                    if resp.status != 200:
                        return None
                    all_emojis = await resp.json(content_type=None)
                    results = [e for e in all_emojis if query.lower() in e.get("title", "").lower()]
                    return results[0] if results else None
        except Exception as e:
            logger.error(f"emoji.gg fetch error: {e}")
            return None

    async def download_image(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.read()
        except Exception as e:
            logger.error(f"Image download error: {e}")
        return None

    # ── Main group ────────────────────────────────────────────────────────────

    @commands.group(name="selfrole", aliases=["sr"], invoke_without_command=True)
    async def selfrole(self, ctx):
        embed = discord.Embed(
            title="⟡﹒ Self Roles",
            color=0xb5a8d5,
            description=(
                "**⭐ Auto Setup** *(Admin)*\n"
                "`-selfrole auto [#channel]` — fully automatic\n\n"
                "**Manual** *(Admin)*\n"
                "`-selfrole setup` — guided wizard\n"
                "`-selfrole add <emoji> <@role> [label]`\n"
                "`-selfrole remove <@role>`\n"
                "`-selfrole panel [#channel]`\n"
                "`-selfrole list`\n"
                "`-selfrole clear`\n\n"
                "**Emoji**\n"
                "`-selfrole emoji <search>` — search emoji.gg"
            )
        )
        embed.set_footer(text="﹒✶﹒⊹﹒ Self Roles System ﹒⊹﹒✶﹒")
        await ctx.send(embed=embed)

    # ── Auto setup ────────────────────────────────────────────────────────────

    @selfrole.command(name="auto")
    @commands.has_permissions(administrator=True, manage_roles=True, manage_emojis=True)
    async def selfrole_auto(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gid = str(ctx.guild.id)

        status = await ctx.send(embed=discord.Embed(
            title="⟡﹒ Auto Self Roles Setup",
            description="⟡ Starting... fetching emojis from emoji.gg",
            color=0xb5a8d5
        ))

        saved_pages = []
        log_lines = []

        for page_config in AUTO_PAGES:
            page_entry = {
                "name": page_config["name"],
                "description": page_config["description"],
                "roles": []
            }

            for preset in page_config["roles"]:
                name = preset["name"]

                await status.edit(embed=discord.Embed(
                    title="⟡﹒ Auto Self Roles Setup",
                    description=f"⟡ Processing **{name}**...\n\n" + "\n".join(log_lines[-6:]),
                    color=0xb5a8d5
                ))

                # Fetch emoji from emoji.gg
                emoji_data = await self.fetch_emoji_gg(preset["search"])
                custom_emoji = None

                if emoji_data:
                    image_bytes = await self.download_image(emoji_data.get("image", ""))
                    if image_bytes:
                        emoji_name = f"sr{name.lower().replace('+', 'plus').replace('-', 'minus')}"
                        existing = discord.utils.get(ctx.guild.emojis, name=emoji_name)
                        if existing:
                            custom_emoji = existing
                        else:
                            try:
                                custom_emoji = await ctx.guild.create_custom_emoji(
                                    name=emoji_name,
                                    image=image_bytes,
                                    reason="Auto self-roles setup"
                                )
                            except discord.HTTPException as e:
                                logger.warning(f"Emoji upload failed for {name}: {e}")

                emoji_str = str(custom_emoji) if custom_emoji else preset["fallback"]

                # Create role
                role = discord.utils.get(ctx.guild.roles, name=name)
                if not role:
                    try:
                        role = await ctx.guild.create_role(
                            name=name,
                            color=discord.Color(preset["color"]),
                            reason="Auto self-roles setup"
                        )
                        log_lines.append(f"✿ Created **{name}** {emoji_str}")
                    except discord.HTTPException as e:
                        log_lines.append(f"✗ Failed **{name}**: {e}")
                        continue
                else:
                    log_lines.append(f"⟡ Found **{name}** {emoji_str}")

                page_entry["roles"].append({
                    "role_id": str(role.id),
                    "emoji": emoji_str,
                    "label": name
                })

                await asyncio.sleep(0.6)

            if page_entry["roles"]:
                saved_pages.append(page_entry)

        if not saved_pages:
            return await status.edit(embed=discord.Embed(
                description="✗ Setup failed! Make sure the bot has **Manage Roles** and **Manage Emojis** permissions.",
                color=0xff6b6b
            ))

        # Save
        if gid not in self.data:
            self.data[gid] = {}
        self.data[gid]["pages"] = saved_pages
        save_data(self.data)

        # Send panel at page 0
        embed = self.build_page_embed(saved_pages, 0)
        view = self.build_page_view(saved_pages, ctx.guild, 0)
        msg = await channel.send(embed=embed, view=view)

        self.data[gid]["panel_message_id"] = str(msg.id)
        self.data[gid]["panel_channel_id"] = str(channel.id)
        save_data(self.data)

        total_roles = sum(len(p["roles"]) for p in saved_pages)
        await status.edit(embed=discord.Embed(
            title="✿ Auto Setup Complete!",
            description=(
                f"**{total_roles} roles** across **{len(saved_pages)} pages** set up!\n\n"
                + "\n".join(log_lines)
                + f"\n\n⟡ Panel sent to {channel.mention}!"
            ),
            color=0x57F287
        ))

    # ── Guided wizard ─────────────────────────────────────────────────────────

    async def ask(self, ctx, embed, timeout=60):
        await ctx.send(embed=embed)
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=timeout)
            return msg.content.strip()
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(description="⏱ Setup timed out!", color=0xff6b6b))
            return None

    @selfrole.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def selfrole_setup(self, ctx):
        gid = str(ctx.guild.id)
        if ctx.author.id in self.active_setups:
            return await ctx.send(embed=discord.Embed(description="✿ You already have a setup running!", color=0xb5a8d5))

        self.active_setups.add(ctx.author.id)
        try:
            answer = await self.ask(ctx, discord.Embed(
                title="⟡﹒ Self Roles Setup  【1 / 6】",
                description="**Which channel for the panel?**\nMention it (e.g. `#roles`)",
                color=0xb5a8d5
            ).set_footer(text="Type 'cancel' anytime to stop"))
            if not answer or answer.lower() == "cancel":
                return await ctx.send(embed=discord.Embed(description="✿ Cancelled.", color=0xb5a8d5))
            try:
                cid = int(answer.strip("<#>"))
                panel_channel = ctx.guild.get_channel(cid)
            except Exception:
                panel_channel = None
            if not panel_channel:
                return await ctx.send(embed=discord.Embed(description="✿ Channel not found! Run setup again.", color=0xff6b6b))

            answer2 = await self.ask(ctx, discord.Embed(
                title="⟡﹒ Self Roles Setup  【2 / 6】",
                description="**Panel title?** (or `skip`)",
                color=0xb5a8d5
            ))
            if not answer2 or answer2.lower() == "cancel":
                return await ctx.send(embed=discord.Embed(description="✿ Cancelled.", color=0xb5a8d5))
            panel_title = "⟡﹒ Self Roles" if answer2.lower() == "skip" else answer2

            answer3 = await self.ask(ctx, discord.Embed(
                title="⟡﹒ Self Roles Setup  【3 / 6】",
                description="**Panel description?** (or `skip`)",
                color=0xb5a8d5
            ))
            if not answer3 or answer3.lower() == "cancel":
                return await ctx.send(embed=discord.Embed(description="✿ Cancelled.", color=0xb5a8d5))
            panel_desc = "✿ Click a button to get or remove a role!" if answer3.lower() == "skip" else answer3

            answer4 = await self.ask(ctx, discord.Embed(
                title="⟡﹒ Self Roles Setup  【4 / 6】",
                description="**How many roles to add?** (1–20)",
                color=0xb5a8d5
            ))
            if not answer4 or answer4.lower() == "cancel":
                return await ctx.send(embed=discord.Embed(description="✿ Cancelled.", color=0xb5a8d5))
            try:
                num_roles = max(1, min(20, int(answer4)))
            except ValueError:
                return await ctx.send(embed=discord.Embed(description="✿ Invalid number!", color=0xff6b6b))

            await self.ask(ctx, discord.Embed(
                title="⟡﹒ Self Roles Setup  【5 / 6】",
                description=(
                    "**Emoji tip!**\n\n"
                    "✿ Unicode: paste directly `🎮` `🎨`\n"
                    "⟡ Custom emoji: `<:name:id>`\n"
                    "◎ From emoji.gg: `-selfrole emoji <search>`\n\n"
                    "Type `ok` to continue!"
                ),
                color=0xb5a8d5
            ))

            roles_added = []
            for i in range(num_roles):
                answer6 = await self.ask(ctx, discord.Embed(
                    title=f"⟡﹒ Self Roles Setup  【6 / 6】  Role {i+1}/{num_roles}",
                    description="Format: `<emoji> <@role> [label]`\nExample: `🎮 @Gamers Gaming`",
                    color=0xb5a8d5
                ), timeout=90)
                if not answer6 or answer6.lower() == "cancel":
                    break
                parts = answer6.split()
                if len(parts) < 2:
                    await ctx.send(embed=discord.Embed(description="✿ Invalid format! Skipping.", color=0xff6b6b))
                    continue
                emoji_part = parts[0]
                try:
                    role_id = int(parts[1].strip("<@&>"))
                    role = ctx.guild.get_role(role_id)
                except Exception:
                    role = None
                if not role:
                    await ctx.send(embed=discord.Embed(description="✿ Role not found! Skipping.", color=0xff6b6b))
                    continue
                label = " ".join(parts[2:]) if len(parts) > 2 else role.name
                roles_added.append({"role_id": str(role.id), "emoji": emoji_part, "label": label})
                await ctx.send(embed=discord.Embed(description=f"{emoji_part} Added **{label}** ✿", color=0xb5a8d5))

            if not roles_added:
                return await ctx.send(embed=discord.Embed(description="✿ No roles added!", color=0xff6b6b))

            if gid not in self.data:
                self.data[gid] = {}

            page = {"name": panel_title, "description": panel_desc, "roles": roles_added}
            pages = self.data[gid].get("pages", [])
            pages.append(page)
            self.data[gid]["pages"] = pages
            save_data(self.data)

            embed = self.build_page_embed(pages, len(pages) - 1)
            view = self.build_page_view(pages, ctx.guild, len(pages) - 1)
            msg = await panel_channel.send(embed=embed, view=view)
            self.data[gid]["panel_message_id"] = str(msg.id)
            self.data[gid]["panel_channel_id"] = str(panel_channel.id)
            save_data(self.data)

            await ctx.send(embed=discord.Embed(
                title="✿ Done!",
                description=f"Panel sent to {panel_channel.mention} with **{len(roles_added)}** roles!",
                color=0xb5a8d5
            ))
        finally:
            self.active_setups.discard(ctx.author.id)

    # ── Emoji search ──────────────────────────────────────────────────────────

    @selfrole.command(name="emoji")
    async def selfrole_emoji(self, ctx, *, query: str):
        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://emoji.gg/api/") as resp:
                        if resp.status != 200:
                            return await ctx.send(embed=discord.Embed(description="✿ Can't reach emoji.gg!", color=0xff6b6b))
                        all_emojis = await resp.json(content_type=None)
                        results = [e for e in all_emojis if query.lower() in e.get("title", "").lower()][:5]
            except Exception:
                return await ctx.send(embed=discord.Embed(description="✿ emoji.gg is unavailable right now.", color=0xff6b6b))

        if not results:
            return await ctx.send(embed=discord.Embed(description=f"✿ No results for `{query}`!", color=0xb5a8d5))

        embed = discord.Embed(title=f"⟡﹒ emoji.gg — '{query}'", color=0xb5a8d5,
                              description="Add to your server, then use as `<:name:id>`\n")
        for e in results:
            embed.add_field(
                name=f"✿ {e.get('title', 'Unknown')}",
                value=f"[emoji.gg](https://emoji.gg/emoji/{e.get('slug', '')})  ﹒  [Download]({e.get('image', '')})",
                inline=True
            )
        embed.set_footer(text="Server Settings → Emoji → Upload Emoji")
        await ctx.send(embed=embed)

    # ── Manual commands ───────────────────────────────────────────────────────

    @selfrole.command(name="add")
    @commands.has_permissions(administrator=True)
    async def selfrole_add(self, ctx, emoji: str, role: discord.Role, *, label: str = None):
        gid = str(ctx.guild.id)
        if gid not in self.data:
            self.data[gid] = {}
        if "pages" not in self.data[gid]:
            self.data[gid]["pages"] = [{"name": "⟡﹒ Self Roles", "description": "✿ Click to get or remove a role!", "roles": []}]
        for r in self.data[gid]["pages"][0]["roles"]:
            if r["role_id"] == str(role.id):
                return await ctx.send(embed=discord.Embed(description="✿ Already in the list!", color=0xb5a8d5))
        self.data[gid]["pages"][0]["roles"].append({"role_id": str(role.id), "emoji": emoji, "label": label or role.name})
        save_data(self.data)
        await ctx.send(embed=discord.Embed(
            description=f"{emoji} Added **{label or role.name}** → {role.mention}\nRun `-selfrole panel` to update.",
            color=0xb5a8d5
        ))

    @selfrole.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def selfrole_remove(self, ctx, role: discord.Role):
        gid = str(ctx.guild.id)
        if gid not in self.data or "pages" not in self.data[gid]:
            return await ctx.send(embed=discord.Embed(description="No self roles set up!", color=0xb5a8d5))
        removed = False
        for page in self.data[gid]["pages"]:
            before = len(page["roles"])
            page["roles"] = [r for r in page["roles"] if r["role_id"] != str(role.id)]
            if len(page["roles"]) < before:
                removed = True
        if not removed:
            return await ctx.send(embed=discord.Embed(description="✿ Role not found in any page!", color=0xb5a8d5))
        save_data(self.data)
        await ctx.send(embed=discord.Embed(description=f"✿ Removed **{role.name}**! Run `-selfrole panel` to update.", color=0xb5a8d5))

    @selfrole.command(name="list")
    async def selfrole_list(self, ctx):
        gid = str(ctx.guild.id)
        pages = self.data.get(gid, {}).get("pages", [])
        if not pages:
            return await ctx.send(embed=discord.Embed(description="No self roles set up!", color=0xb5a8d5))
        embed = discord.Embed(title="⟡﹒ Self Roles List", color=0xb5a8d5)
        for i, page in enumerate(pages):
            lines = []
            for r in page["roles"]:
                role = ctx.guild.get_role(int(r["role_id"]))
                mention = role.mention if role else "*(deleted)*"
                lines.append(f"{r['emoji']} **{r['label']}** → {mention}")
            embed.add_field(
                name=f"Page {i+1} — {page['name']}",
                value="\n".join(lines) if lines else "Empty",
                inline=False
            )
        await ctx.send(embed=embed)

    @selfrole.command(name="panel")
    @commands.has_permissions(administrator=True)
    async def selfrole_panel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        gid = str(ctx.guild.id)
        pages = self.data.get(gid, {}).get("pages", [])
        if not pages:
            return await ctx.send(embed=discord.Embed(description="✿ No roles yet! Use `-selfrole auto` or `-selfrole add`.", color=0xb5a8d5))
        embed = self.build_page_embed(pages, 0)
        view = self.build_page_view(pages, ctx.guild, 0)
        msg = await channel.send(embed=embed, view=view)
        self.data[gid]["panel_message_id"] = str(msg.id)
        self.data[gid]["panel_channel_id"] = str(channel.id)
        save_data(self.data)
        if channel.id != ctx.channel.id:
            await ctx.send(embed=discord.Embed(description=f"✿ Panel sent to {channel.mention}!", color=0xb5a8d5))

    @selfrole.command(name="clear")
    @commands.has_permissions(administrator=True)
    async def selfrole_clear(self, ctx):
        gid = str(ctx.guild.id)
        self.data[gid] = {}
        save_data(self.data)
        await ctx.send(embed=discord.Embed(description="✿ Cleared all self roles!", color=0xb5a8d5))

async def setup(bot):
    await bot.add_cog(SelfRoles(bot))
