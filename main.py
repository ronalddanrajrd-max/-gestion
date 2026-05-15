import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

OWNER_ID = 1467602579482480821

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
bot.owner_id = OWNER_ID

# Chargement des cogs
async def load_cogs():
    cogs = [
        "moderation",
        "roles",
        "welcome",
        "tickets",
        "giveaway",
        "fun",
        "stats",
        "logs",
        "music",
        "config",
        "antiraid",
        "antilink",
        "boost",
        "levels",
        "minigames",
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog chargé : {cog}")
        except Exception as e:
            print(f"❌ Erreur chargement {cog} : {e}")

@bot.event
async def on_ready():
    await load_cogs()
    await bot.tree.sync()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} serveurs | /help"
        )
    )
    print(f"\n🤖 Bot connecté : {bot.user} (ID: {bot.user.id})")
    print(f"👑 Owner ID : {OWNER_ID}")
    print(f"📡 Connecté à {len(bot.guilds)} serveur(s)\n")

# Gestion globale des erreurs + bypass owner
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        if interaction.user.id == OWNER_ID:
            return  # Owner bypass silencieux
        await interaction.response.send_message("❌ Tu n'as pas les permissions nécessaires.", ephemeral=True)
    elif isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(f"⏳ Attends encore {error.retry_after:.1f}s.", ephemeral=True)
    else:
        try:
            await interaction.response.send_message(f"❌ Erreur : {error}", ephemeral=True)
        except Exception:
            pass

# Override des permissions pour le owner
class OwnerBypassTree(discord.app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == OWNER_ID:
            return True
        return await super().interaction_check(interaction)

bot.tree.__class__ = OwnerBypassTree

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN manquant dans le fichier .env")
    else:
        bot.run(token)
