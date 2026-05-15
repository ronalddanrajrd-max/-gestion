import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

OWNER_ID = 1467602579482480821

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
bot.owner_id = OWNER_ID

# Override check_permissions pour le owner
original_interaction_check = discord.app_commands.CommandTree.interaction_check

async def custom_interaction_check(self, interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID:
        return True
    return await original_interaction_check(self, interaction)

discord.app_commands.CommandTree.interaction_check = custom_interaction_check

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
    print(f"👑 Owner : {OWNER_ID}")
    print(f"📡 Connecté à {len(bot.guilds)} serveur(s)\n")

# Owner bypass pour toutes les commandes avec permissions
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if interaction.user.id == OWNER_ID:
        # Le owner peut tout faire, on réessaie sans vérif
        try:
            await interaction.response.send_message("⚠️ Erreur contournée (owner mode).", ephemeral=True)
        except Exception:
            pass
        return
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Tu n'as pas les permissions.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Erreur : {error}", ephemeral=True)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN manquant dans le fichier .env")
    else:
        bot.run(token)
