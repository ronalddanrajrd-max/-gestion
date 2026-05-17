import discord
from discord.ext import commands
from discord import app_commands
import asyncio

OWNER_ID = 1467602579482480821
OWNER_ID2 = 1504570877360996442

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id in (OWNER_ID, OWNER_ID2)

    # ── NUKE SALON ───────────────────────────────────────────────
    @app_commands.command(name="nuke", description="Supprimer et recréer un salon [OWNER ONLY]")
    @app_commands.describe(salon="Salon à nuke")
    async def nuke(self, interaction: discord.Interaction, salon: discord.TextChannel = None):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌ Commande réservée au owner.", ephemeral=True)

        channel = salon or interaction.channel
        position = channel.position
        category = channel.category
        name = channel.name
        overwrites = channel.overwrites

        await interaction.response.send_message("💣 Nuke en cours...", ephemeral=True)
        await channel.delete(reason="Nuke par owner")

        new_channel = await interaction.guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites,
            position=position
        )

        embed = discord.Embed(
            title="💣 NUKE",
            description="Ce salon a été nuké par le owner.",
            color=discord.Color.red()
        )
        await new_channel.send(embed=embed)

    # ── LOCKDOWN OWNER ───────────────────────────────────────────
    @app_commands.command(name="owner-lockdown", description="Verrouiller tout le serveur [OWNER ONLY]")
    async def owner_lockdown(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌ Commande réservée au owner.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        locked = 0
        for channel in interaction.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(interaction.guild.default_role)
                overwrite.send_messages = False
                await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
                locked += 1
                await asyncio.sleep(0.3)
            except Exception:
                pass
        await interaction.followup.send(f"🔒 **{locked} salons** verrouillés !", ephemeral=True)

    # ── UNLOCK OWNER ─────────────────────────────────────────────
    @app_commands.command(name="owner-unlock", description="Déverrouiller tout le serveur [OWNER ONLY]")
    async def owner_unlock(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌ Commande réservée au owner.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        for channel in interaction.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(interaction.guild.default_role)
                overwrite.send_messages = None
                await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
                await asyncio.sleep(0.3)
            except Exception:
                pass
        await interaction.followup.send("🔓 Serveur déverrouillé !", ephemeral=True)

    # ── MASS BAN ─────────────────────────────────────────────────
    @app_commands.command(name="massban", description="Bannir plusieurs membres d'un coup [OWNER ONLY]")
    @app_commands.describe(ids="IDs séparés par des espaces")
    async def massban(self, interaction: discord.Interaction, ids: str):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌ Commande réservée au owner.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        banned = 0
        for uid in ids.split():
            try:
                user = await self.bot.fetch_user(int(uid))
                await interaction.guild.ban(user, reason="Mass ban par owner")
                banned += 1
                await asyncio.sleep(0.5)
            except Exception:
                pass
        await interaction.followup.send(f"🔨 **{banned} membres** bannis !", ephemeral=True)

    # ── OWNER INFO ───────────────────────────────────────────────
    @app_commands.command(name="owner-info", description="Infos owner [OWNER ONLY]")
    async def owner_info(self, interaction: discord.Interaction):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("❌ Commande réservée au owner.", ephemeral=True)

        embed = discord.Embed(
            title="👑 Commandes Owner",
            description=(
                "Commandes accessibles **uniquement par toi** :\n\n"
                "`/nuke` — Supprimer et recréer un salon\n"
                "`/owner-lockdown` — Verrouiller tout le serveur\n"
                "`/owner-unlock` — Déverrouiller tout le serveur\n"
                "`/massban` — Bannir plusieurs membres d'un coup\n"
                "`/owner-info` — Cette liste\n\n"
                "Ces commandes ne peuvent être utilisées par **personne d'autre**, même les admins."
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Owner(bot))
