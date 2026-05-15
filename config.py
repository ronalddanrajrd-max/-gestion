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

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── SETUP ────────────────────────────────────────────────────
    @app_commands.command(name="setup", description="Assistant de configuration rapide du serveur")
    @app_commands.default_permissions(administrator=True)
    async def setup_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="⚙️ Configuration rapide",
            description=(
                "Commandes de configuration disponibles :\n\n"
                "🔧 `/setwelcome` → Salon de bienvenue\n"
                "🔧 `/setleave` → Salon de départ\n"
                "🔧 `/setlogs` → Salon de logs\n"
                "🔧 `/autorole` → Rôle automatique\n"
                "🔧 `/ticket-setup` → Panel de tickets\n"
                "🔧 `/setsuggest` → Salon de suggestions\n"
            ),
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── SET SUGGEST ──────────────────────────────────────────────
    @app_commands.command(name="setsuggest", description="Définir le salon de suggestions")
    @app_commands.default_permissions(administrator=True)
    async def setsuggest(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["suggest_channel"] = salon.id
        save_config(config)
        await interaction.response.send_message(f"✅ Salon de suggestions : {salon.mention}")

    # ── HELP ─────────────────────────────────────────────────────
    @app_commands.command(name="help", description="Liste toutes les commandes disponibles")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📚 Aide — Toutes les commandes", color=discord.Color.blurple())
        categories = {
            "🛡️ Modération": ["/ban", "/kick", "/mute", "/unmute", "/warn", "/warns", "/clearwarn", "/purge", "/lock", "/unlock", "/slowmode", "/unban"],
            "🎭 Rôles": ["/role-add", "/role-remove", "/autorole", "/reactionrole"],
            "👋 Bienvenue": ["/setwelcome", "/setleave"],
            "🎫 Tickets": ["/ticket-setup"],
            "🎉 Events": ["/giveaway-start", "/giveaway-reroll", "/poll", "/suggest"],
            "📊 Stats": ["/userinfo", "/serverinfo", "/botinfo", "/ping", "/avatar"],
            "🎵 Musique": ["/play", "/skip", "/queue", "/stop", "/pause", "/resume"],
            "🎮 Fun": ["/8ball", "/coinflip", "/dice", "/choose", "/joke", "/rps"],
            "⚙️ Config": ["/setup", "/setlogs", "/setsuggest", "/help"],
        }
        for cat, cmds in categories.items():
            embed.add_field(name=cat, value=" • ".join(cmds), inline=False)
        embed.set_footer(text="Toutes les commandes utilisent les slash commands /")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Config(bot))
