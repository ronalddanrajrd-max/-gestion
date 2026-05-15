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

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── SET WELCOME ──────────────────────────────────────────────
    @app_commands.command(name="setwelcome", description="Configurer le salon de bienvenue")
    @app_commands.default_permissions(administrator=True)
    async def setwelcome(self, interaction: discord.Interaction, salon: discord.TextChannel, message: str = "Bienvenue {member} sur **{server}** ! 🎉"):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["welcome_channel"] = salon.id
        config[gid]["welcome_message"] = message
        save_config(config)
        await interaction.response.send_message(f"✅ Salon de bienvenue : {salon.mention}\n**Message :** {message}")

    # ── SET LEAVE ────────────────────────────────────────────────
    @app_commands.command(name="setleave", description="Configurer le salon de départ")
    @app_commands.default_permissions(administrator=True)
    async def setleave(self, interaction: discord.Interaction, salon: discord.TextChannel, message: str = "**{member}** vient de quitter le serveur. 👋"):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["leave_channel"] = salon.id
        config[gid]["leave_message"] = message
        save_config(config)
        await interaction.response.send_message(f"✅ Salon de départ : {salon.mention}")

    # ── ON JOIN ──────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = load_config()
        gid = str(member.guild.id)
        channel_id = config.get(gid, {}).get("welcome_channel")
        msg_template = config.get(gid, {}).get("welcome_message", "Bienvenue {member} sur **{server}** !")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                msg = msg_template.replace("{member}", member.mention).replace("{server}", member.guild.name)
                embed = discord.Embed(description=msg, color=discord.Color.green())
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Membre #{member.guild.member_count}")
                await channel.send(embed=embed)

    # ── ON LEAVE ─────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        config = load_config()
        gid = str(member.guild.id)
        channel_id = config.get(gid, {}).get("leave_channel")
        msg_template = config.get(gid, {}).get("leave_message", "**{member}** vient de quitter le serveur.")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                msg = msg_template.replace("{member}", str(member)).replace("{server}", member.guild.name)
                embed = discord.Embed(description=msg, color=discord.Color.red())
                await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
