"""
cogs/antilink.py
Supprime automatiquement les liens Discord (invitations) et/ou les URLs
dans les salons configurés. Les modérateurs sont exemptés.
"""

import discord
from discord.ext import commands
from discord import app_commands
import re, json, os

CONFIG_FILE = "data/antilink.json"

INVITE_PATTERN = re.compile(
    r"(discord\.gg|discord\.com/invite|discordapp\.com/invite)/[a-zA-Z0-9-_]+",
    re.IGNORECASE
)
URL_PATTERN = re.compile(
    r"https?://[^\s]+",
    re.IGNORECASE
)

def load():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_settings(guild_id: int) -> dict:
    data = load()
    return data.get(str(guild_id), {
        "enabled": False,
        "block_invites": True,
        "block_links": False,
        "whitelist_channels": [],
        "whitelist_roles": [],
        "warn_user": True,
        "action": "delete",      # "delete" | "warn" | "kick"
    })


class AntiLink(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        s = get_settings(message.guild.id)
        if not s["enabled"]:
            return

        # Exemptions
        if message.channel.id in s["whitelist_channels"]:
            return
        member = message.author
        if any(r.id in s["whitelist_roles"] for r in member.roles):
            return
        if member.guild_permissions.manage_messages:
            return

        content = message.content
        triggered = False
        reason = ""

        if s["block_invites"] and INVITE_PATTERN.search(content):
            triggered = True
            reason = "Invitation Discord"
        elif s["block_links"] and URL_PATTERN.search(content):
            triggered = True
            reason = "Lien externe"

        if not triggered:
            return

        # Supprimer le message
        try:
            await message.delete()
        except discord.Forbidden:
            pass

        if s["warn_user"]:
            try:
                warn_msg = await message.channel.send(
                    f"🚫 {member.mention}, les **{reason.lower()}s** ne sont pas autorisés ici.",
                    delete_after=6
                )
            except Exception:
                pass

        if s["action"] == "warn":
            pass  # Déjà notifié
        elif s["action"] == "kick":
            try:
                await member.kick(reason=f"Anti-link : {reason}")
            except Exception:
                pass
        elif s["action"] == "timeout":
            from datetime import timedelta
            until = discord.utils.utcnow() + timedelta(minutes=10)
            try:
                await member.timeout(until, reason=f"Anti-link : {reason}")
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.on_message(after)

    # ── COMMANDES ─────────────────────────────────────────────────

    @app_commands.command(name="antilink", description="🔗 Configurer l'anti-lien")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        enabled="Activer/désactiver",
        block_invites="Bloquer les invitations Discord",
        block_links="Bloquer tous les liens (http/https)",
        action="Action : delete / warn / kick / timeout",
        warn_user="Prévenir l'utilisateur",
    )
    async def antilink_cmd(
        self,
        interaction: discord.Interaction,
        enabled: bool = None,
        block_invites: bool = None,
        block_links: bool = None,
        action: str = None,
        warn_user: bool = None,
    ):
        data = load()
        gid = str(interaction.guild.id)
        s = get_settings(interaction.guild.id)

        if enabled       is not None: s["enabled"]       = enabled
        if block_invites is not None: s["block_invites"] = block_invites
        if block_links   is not None: s["block_links"]   = block_links
        if warn_user     is not None: s["warn_user"]     = warn_user
        if action        is not None and action in ("delete","warn","kick","timeout"):
            s["action"] = action

        data[gid] = s
        save(data)

        embed = discord.Embed(title="🔗 Anti-Lien — Config", color=discord.Color.blurple())
        embed.add_field(name="État",              value="✅" if s["enabled"] else "❌",        inline=True)
        embed.add_field(name="Anti-invites",      value="✅" if s["block_invites"] else "❌",   inline=True)
        embed.add_field(name="Anti-liens",        value="✅" if s["block_links"] else "❌",     inline=True)
        embed.add_field(name="Action",            value=f"`{s['action']}`",                    inline=True)
        embed.add_field(name="Avertir l'user",    value="✅" if s["warn_user"] else "❌",       inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="antilink-whitelist", description="✅ Exempter un salon ou rôle du filtre")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(salon="Salon à exempter", role="Rôle à exempter")
    async def antilink_whitelist(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel = None,
        role: discord.Role = None,
    ):
        data = load()
        gid = str(interaction.guild.id)
        s = get_settings(interaction.guild.id)

        added = []
        if salon:
            if salon.id not in s["whitelist_channels"]:
                s["whitelist_channels"].append(salon.id)
                added.append(salon.mention)
        if role:
            if role.id not in s["whitelist_roles"]:
                s["whitelist_roles"].append(role.id)
                added.append(role.mention)

        data[gid] = s
        save(data)
        await interaction.response.send_message(
            f"✅ Ajouté à la whitelist : {', '.join(added) if added else 'Aucun changement.'}",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiLink(bot))
