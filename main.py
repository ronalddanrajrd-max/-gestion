import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

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
    print(f"📡 Connecté à {len(bot.guilds)} serveur(s)\n")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN manquant dans le fichier .env")
    else:
        bot.run(token)
