"""
cogs/boost.py
Notification en direct quand un membre booste le serveur.
Commande /setboost pour configurer le salon + message personnalisé.
"""

import discord
from discord.ext import commands
from discord import app_commands
import json, os, datetime

CONFIG_FILE = "data/config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


class Boost(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Détecte un nouveau boost en comparant les rôles premium."""
        guild = after.guild

        # Le membre vient de booster si son premium_since est apparu
        if before.premium_since is None and after.premium_since is not None:
            config = load_config()
            gid = str(guild.id)
            boost_channel_id = config.get(gid, {}).get("boost_channel")
            if not boost_channel_id:
                return

            channel = guild.get_channel(boost_channel_id)
            if not channel:
                return

            # Niveau actuel du serveur
            level = guild.premium_tier
            total = guild.premium_subscription_count or 0

            # Message personnalisé
            custom_msg = config.get(gid, {}).get("boost_message", "")

            embed = discord.Embed(
                title="💎 Nouveau Boost !",
                description=(
                    f"✨ **{after.mention}** vient de **booster le serveur** !\n"
                    f"Merci infiniment pour ton soutien 💜\n\n"
                    + (f"📝 {custom_msg}\n\n" if custom_msg else "")
                    + f"🏆 **Niveau Boost :** {level} | **Total boosts :** {total}"
                ),
                color=discord.Color.from_rgb(255, 105, 180),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text=guild.name, icon_url=guild.icon.url if guild.icon else None)

            # Bannière du serveur si disponible
            if guild.banner:
                embed.set_image(url=guild.banner.url)

            await channel.send(content=after.mention, embed=embed)

    @commands.Cog.listener()
    async def on_member_update_unboost(self, before: discord.Member, after: discord.Member):
        """Optionnel : détecter la fin d'un boost."""
        pass  # Peut être étendu plus tard

    # ── SETBOOST ─────────────────────────────────────────────────
    @app_commands.command(name="setboost", description="💎 Configurer les notifications de boost")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        salon="Salon où envoyer les notifications de boost",
        message="Message personnalisé (optionnel, ex: 'Tu as droit à un rôle spécial !')"
    )
    async def setboost(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        message: str = ""
    ):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["boost_channel"] = salon.id
        if message:
            config[gid]["boost_message"] = message
        save_config(config)

        embed = discord.Embed(
            title="💎 Notifications de Boost configurées",
            description=f"Les boosts seront annoncés dans {salon.mention}.",
            color=discord.Color.from_rgb(255, 105, 180)
        )
        if message:
            embed.add_field(name="Message personnalisé", value=message)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── TEST BOOST ────────────────────────────────────────────────
    @app_commands.command(name="testboost", description="🧪 Tester la notification de boost")
    @app_commands.default_permissions(administrator=True)
    async def testboost(self, interaction: discord.Interaction):
        config = load_config()
        gid = str(interaction.guild.id)
        boost_channel_id = config.get(gid, {}).get("boost_channel")
        if not boost_channel_id:
            return await interaction.response.send_message(
                "❌ Aucun salon de boost configuré. Utilise `/setboost` d'abord.", ephemeral=True
            )
        channel = interaction.guild.get_channel(boost_channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)

        guild = interaction.guild
        level = guild.premium_tier
        total = guild.premium_subscription_count or 0
        custom_msg = config.get(gid, {}).get("boost_message", "")
        after = interaction.user

        embed = discord.Embed(
            title="💎 Nouveau Boost ! (TEST)",
            description=(
                f"✨ **{after.mention}** vient de **booster le serveur** !\n"
                f"Merci infiniment pour ton soutien 💜\n\n"
                + (f"📝 {custom_msg}\n\n" if custom_msg else "")
                + f"🏆 **Niveau Boost :** {level} | **Total boosts :** {total}"
            ),
            color=discord.Color.from_rgb(255, 105, 180),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=after.display_avatar.url)
        embed.set_footer(text=f"{guild.name} — Ceci est un test")
        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Test envoyé dans {channel.mention}", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Boost(bot))
