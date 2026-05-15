import discord
from discord.ext import commands
from discord import app_commands
import re, json, os
from datetime import timedelta

CONFIG_FILE = "data/config.json"
LINK_REGEX = re.compile(r"(https?://|discord\.gg/|www\.)\S+", re.IGNORECASE)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

class AntiLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        # Ignorer les admins
        if message.author.guild_permissions.administrator:
            return

        config = load_config()
        gid = str(message.guild.id)
        if not config.get(gid, {}).get("antilink", False):
            return

        # Vérifier si le salon est exempté
        exempted = config.get(gid, {}).get("antilink_exempt", [])
        if message.channel.id in exempted:
            return

        # Vérifier si le rôle est exempté
        exempted_roles = config.get(gid, {}).get("antilink_exempt_roles", [])
        if any(r.id in exempted_roles for r in message.author.roles):
            return

        if LINK_REGEX.search(message.content):
            await message.delete()
            warn_msg = await message.channel.send(
                f"🔗 {message.author.mention} les liens ne sont pas autorisés ici !",
                delete_after=5
            )

    # ── ANTILINK ON/OFF ──────────────────────────────────────────
    @app_commands.command(name="antilink", description="Activer/désactiver l'anti-lien")
    @app_commands.choices(actif=[
        app_commands.Choice(name="Activer", value="on"),
        app_commands.Choice(name="Désactiver", value="off"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def antilink(self, interaction: discord.Interaction, actif: app_commands.Choice[str]):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["antilink"] = actif.value == "on"
        save_config(config)
        status = "✅ Activé" if actif.value == "on" else "❌ Désactivé"
        await interaction.response.send_message(f"🔗 Anti-Link : **{status}**")

    # ── EXEMPTER UN SALON ────────────────────────────────────────
    @app_commands.command(name="antilink-exempt", description="Exempter un salon de l'anti-lien")
    @app_commands.default_permissions(administrator=True)
    async def antilink_exempt(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        if "antilink_exempt" not in config[gid]:
            config[gid]["antilink_exempt"] = []
        if salon.id not in config[gid]["antilink_exempt"]:
            config[gid]["antilink_exempt"].append(salon.id)
        save_config(config)
        await interaction.response.send_message(f"✅ {salon.mention} est exempté de l'anti-lien.")

    # ── EXEMPTER UN ROLE ─────────────────────────────────────────
    @app_commands.command(name="antilink-role", description="Exempter un rôle de l'anti-lien")
    @app_commands.default_permissions(administrator=True)
    async def antilink_role(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        if "antilink_exempt_roles" not in config[gid]:
            config[gid]["antilink_exempt_roles"] = []
        if role.id not in config[gid]["antilink_exempt_roles"]:
            config[gid]["antilink_exempt_roles"].append(role.id)
        save_config(config)
        await interaction.response.send_message(f"✅ Le rôle **{role.name}** est exempté de l'anti-lien.")

async def setup(bot):
    await bot.add_cog(AntiLink(bot))
