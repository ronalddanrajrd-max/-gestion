import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import timedelta
import json
import os

WARNS_FILE = "data/warns.json"

def load_warns():
    if not os.path.exists(WARNS_FILE):
        return {}
    with open(WARNS_FILE, "r") as f:
        return json.load(f)

def save_warns(data):
    os.makedirs("data", exist_ok=True)
    with open(WARNS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def embed(self, title, description, color=discord.Color.red()):
        e = discord.Embed(title=title, description=description, color=color)
        return e

    # ── BAN ──────────────────────────────────────────────────────
    @app_commands.command(name="ban", description="Bannir un membre")
    @app_commands.describe(membre="Membre à bannir", raison="Raison du ban")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Vous ne pouvez pas bannir ce membre.", ephemeral=True)
        await membre.ban(reason=raison)
        await interaction.response.send_message(embed=self.embed("🔨 Ban", f"**{membre}** a été banni.\n**Raison :** {raison}"))

    # ── KICK ─────────────────────────────────────────────────────
    @app_commands.command(name="kick", description="Expulser un membre")
    @app_commands.describe(membre="Membre à expulser", raison="Raison du kick")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ Vous ne pouvez pas expulser ce membre.", ephemeral=True)
        await membre.kick(reason=raison)
        await interaction.response.send_message(embed=self.embed("👢 Kick", f"**{membre}** a été expulsé.\n**Raison :** {raison}"))

    # ── MUTE (timeout) ───────────────────────────────────────────
    @app_commands.command(name="mute", description="Rendre silencieux un membre")
    @app_commands.describe(membre="Membre", duree="Durée en minutes", raison="Raison")
    @app_commands.default_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, membre: discord.Member, duree: int = 10, raison: str = "Aucune raison"):
        until = discord.utils.utcnow() + timedelta(minutes=duree)
        await membre.timeout(until, reason=raison)
        await interaction.response.send_message(embed=self.embed("🔇 Mute", f"**{membre}** a été rendu silencieux pendant **{duree} min**.\n**Raison :** {raison}", discord.Color.orange()))

    # ── UNMUTE ───────────────────────────────────────────────────
    @app_commands.command(name="unmute", description="Enlever le mute d'un membre")
    @app_commands.default_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, membre: discord.Member):
        await membre.timeout(None)
        await interaction.response.send_message(embed=self.embed("🔊 Unmute", f"**{membre}** peut de nouveau parler.", discord.Color.green()))

    # ── WARN ─────────────────────────────────────────────────────
    @app_commands.command(name="warn", description="Avertir un membre")
    @app_commands.describe(membre="Membre", raison="Raison")
    @app_commands.default_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        warns = load_warns()
        uid = str(membre.id)
        if uid not in warns:
            warns[uid] = []
        warns[uid].append({"raison": raison, "par": str(interaction.user)})
        save_warns(warns)
        count = len(warns[uid])
        await interaction.response.send_message(embed=self.embed("⚠️ Avertissement", f"**{membre}** a reçu un avertissement.\n**Raison :** {raison}\n**Total warns :** {count}", discord.Color.yellow()))

    # ── WARNS ────────────────────────────────────────────────────
    @app_commands.command(name="warns", description="Voir les avertissements d'un membre")
    @app_commands.default_permissions(manage_messages=True)
    async def warns(self, interaction: discord.Interaction, membre: discord.Member):
        warns = load_warns()
        uid = str(membre.id)
        liste = warns.get(uid, [])
        if not liste:
            return await interaction.response.send_message(f"✅ **{membre}** n'a aucun avertissement.", ephemeral=True)
        desc = "\n".join([f"**{i+1}.** {w['raison']} *(par {w['par']})*" for i, w in enumerate(liste)])
        await interaction.response.send_message(embed=self.embed(f"⚠️ Warns de {membre}", desc, discord.Color.yellow()))

    # ── CLEARWARN ────────────────────────────────────────────────
    @app_commands.command(name="clearwarn", description="Effacer les avertissements d'un membre")
    @app_commands.default_permissions(administrator=True)
    async def clearwarn(self, interaction: discord.Interaction, membre: discord.Member):
        warns = load_warns()
        warns[str(membre.id)] = []
        save_warns(warns)
        await interaction.response.send_message(embed=self.embed("🧹 Warns effacés", f"Les avertissements de **{membre}** ont été supprimés.", discord.Color.green()))

    # ── PURGE ────────────────────────────────────────────────────
    @app_commands.command(name="purge", description="Supprimer des messages en masse")
    @app_commands.describe(nombre="Nombre de messages à supprimer (max 100)")
    @app_commands.default_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, nombre: int):
        if nombre < 1 or nombre > 100:
            return await interaction.response.send_message("❌ Entre 1 et 100 messages.", ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=nombre)
        await interaction.followup.send(f"🗑️ **{len(deleted)}** messages supprimés.", ephemeral=True)

    # ── LOCK ─────────────────────────────────────────────────────
    @app_commands.command(name="lock", description="Verrouiller un salon")
    @app_commands.default_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(embed=self.embed("🔒 Salon verrouillé", f"{interaction.channel.mention} est maintenant verrouillé.", discord.Color.red()))

    # ── UNLOCK ───────────────────────────────────────────────────
    @app_commands.command(name="unlock", description="Déverrouiller un salon")
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message(embed=self.embed("🔓 Salon déverrouillé", f"{interaction.channel.mention} est maintenant ouvert.", discord.Color.green()))

    # ── SLOWMODE ─────────────────────────────────────────────────
    @app_commands.command(name="slowmode", description="Activer le mode lent")
    @app_commands.describe(secondes="Délai en secondes (0 = désactiver)")
    @app_commands.default_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, secondes: int):
        await interaction.channel.edit(slowmode_delay=secondes)
        msg = f"Mode lent activé : **{secondes}s**" if secondes > 0 else "Mode lent désactivé."
        await interaction.response.send_message(embed=self.embed("🐢 Slowmode", msg, discord.Color.blue()))

    # ── UNBAN ────────────────────────────────────────────────────
    @app_commands.command(name="unban", description="Débannir un utilisateur par ID")
    @app_commands.describe(user_id="ID de l'utilisateur banni")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(embed=self.embed("✅ Unban", f"**{user}** a été débanni.", discord.Color.green()))
        except Exception:
            await interaction.response.send_message("❌ Utilisateur introuvable ou non banni.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
