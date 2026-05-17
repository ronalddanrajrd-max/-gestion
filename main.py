import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

OWNER_ID = 1467602579482480821
OWNER_ID2 = 1504570877360996442
GUILD_ID = 1504582765394395306

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
bot.owner_id = OWNER_ID

COGS = [
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
    "annonce",
    "owner",
    "tempvc",
]

@bot.event
async def on_ready():
    print(f"🤖 Bot connecté : {bot.user}")

    # 1. Charger les cogs
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog chargé : {cog}")
        except Exception as e:
            print(f"❌ Erreur {cog} : {e}")

    # 2. Sync sur ton serveur
    try:
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ {len(synced)} commandes synced !")
    except Exception as e:
        print(f"❌ Erreur sync : {e}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} serveurs | /help"
        )
    )
    print(f"👑 Owner : {OWNER_ID}")
    print(f"🏠 Guild : {GUILD_ID}")
    print(f"📡 {len(bot.guilds)} serveur(s)")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, discord.app_commands.MissingPermissions):
        if interaction.user.id in (OWNER_ID, OWNER_ID2):
            return
        await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
    else:
        try:
            await interaction.response.send_message(f"❌ Erreur : {error}", ephemeral=True)
        except Exception:
            pass

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN manquant !")
    else:
        bot.run(token)
