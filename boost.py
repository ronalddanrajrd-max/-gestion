import discord
from discord.ext import commands
from discord import app_commands
import json, os

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
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Détecter un nouveau boost
        if before.premium_since is None and after.premium_since is not None:
            config = load_config()
            gid = str(after.guild.id)
            channel_id = config.get(gid, {}).get("boost_channel")
            if not channel_id:
                return
            channel = after.guild.get_channel(channel_id)
            if not channel:
                return

            boost_count = after.guild.premium_subscription_count
            level = after.guild.premium_tier

            embed = discord.Embed(
                title="💖 Nouveau Boost !",
                description=(
                    f"**{after.mention}** vient de booster le serveur ! 🚀\n\n"
                    f"Merci infiniment pour ton soutien ! ❤️\n\n"
                    f"🔥 **Boosts totaux :** {boost_count}\n"
                    f"⭐ **Niveau actuel :** {level}"
                ),
                color=discord.Color.from_rgb(255, 105, 180)
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_footer(text=f"{after.guild.name} te remercie !")

            # Rôle boost automatique
            boost_role_id = config.get(gid, {}).get("boost_role")
            if boost_role_id:
                boost_role = after.guild.get_role(boost_role_id)
                if boost_role:
                    await after.add_roles(boost_role)

            await channel.send(content=after.mention, embed=embed)

        # Détecter la fin d'un boost
        elif before.premium_since is not None and after.premium_since is None:
            config = load_config()
            gid = str(after.guild.id)
            channel_id = config.get(gid, {}).get("boost_channel")
            if channel_id:
                channel = after.guild.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="💔 Boost perdu",
                        description=f"**{after.mention}** ne boost plus le serveur.",
                        color=discord.Color.gray()
                    )
                    await channel.send(embed=embed)

            # Retirer le rôle boost
            boost_role_id = config.get(gid, {}).get("boost_role")
            if boost_role_id:
                boost_role = after.guild.get_role(boost_role_id)
                if boost_role and boost_role in after.roles:
                    await after.remove_roles(boost_role)

    # ── SET BOOST CHANNEL ────────────────────────────────────────
    @app_commands.command(name="setboost", description="Définir le salon pour les notifications de boost")
    @app_commands.default_permissions(administrator=True)
    async def setboost(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["boost_channel"] = salon.id
        save_config(config)
        await interaction.response.send_message(f"💖 Notifications de boost dans {salon.mention}")

    # ── SET BOOST ROLE ───────────────────────────────────────────
    @app_commands.command(name="setboostrole", description="Rôle donné automatiquement aux boosters")
    @app_commands.default_permissions(administrator=True)
    async def setboostrole(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["boost_role"] = role.id
        save_config(config)
        await interaction.response.send_message(f"✅ Rôle booster : **{role.name}**")

    # ── BOOSTERS ─────────────────────────────────────────────────
    @app_commands.command(name="boosters", description="Liste des boosters du serveur")
    async def boosters(self, interaction: discord.Interaction):
        boosters = interaction.guild.premium_subscribers
        if not boosters:
            return await interaction.response.send_message("😢 Aucun booster pour l'instant.")
        desc = "\n".join([f"💖 {b.mention}" for b in boosters])
        embed = discord.Embed(
            title=f"💖 Boosters ({len(boosters)})",
            description=desc,
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.add_field(name="Niveau", value=f"⭐ {interaction.guild.premium_tier}")
        embed.add_field(name="Total boosts", value=f"🔥 {interaction.guild.premium_subscription_count}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Boost(bot))
