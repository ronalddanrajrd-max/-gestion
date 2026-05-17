import discord
from discord.ext import commands
from discord import app_commands
import asyncio, json, os
from collections import defaultdict
from datetime import datetime, timedelta

CONFIG_FILE = "data/config.json"
join_tracker = defaultdict(list)  # guild_id -> [timestamps]

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_tracker = defaultdict(list)  # user_id -> [timestamps]
        self.mention_tracker = defaultdict(list)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = load_config()
        gid = str(member.guild.id)
        if not config.get(gid, {}).get("antiraid", False):
            return

        now = datetime.utcnow()
        join_tracker[gid].append(now)
        # Garde seulement les 10 dernières secondes
        join_tracker[gid] = [t for t in join_tracker[gid] if (now - t).seconds < 10]

        threshold = config.get(gid, {}).get("antiraid_threshold", 5)
        if len(join_tracker[gid]) >= threshold:
            # Mode lockdown : kick tous les nouveaux
            log_ch_id = config.get(gid, {}).get("log_channel")
            log_ch = member.guild.get_channel(log_ch_id) if log_ch_id else None
            try:
                await member.kick(reason="🛡️ Anti-Raid : trop de joins simultanés")
            except Exception:
                pass
            if log_ch:
                embed = discord.Embed(
                    title="🚨 RAID DÉTECTÉ",
                    description=f"**{len(join_tracker[gid])} membres** ont rejoint en moins de 10 secondes !\n**{member}** a été expulsé automatiquement.",
                    color=discord.Color.dark_red()
                )
                await log_ch.send("@everyone", embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        config = load_config()
        gid = str(message.guild.id)

        # Anti-spam
        if config.get(gid, {}).get("antispam", False):
            now = datetime.utcnow()
            uid = message.author.id
            self.message_tracker[uid].append(now)
            self.message_tracker[uid] = [t for t in self.message_tracker[uid] if (now - t).seconds < 5]
            if len(self.message_tracker[uid]) >= 5:
                await message.delete()
                until = discord.utils.utcnow() + timedelta(minutes=5)
                await message.author.timeout(until, reason="Anti-spam automatique")
                await message.channel.send(f"⚠️ {message.author.mention} a été mute 5 min pour spam.", delete_after=5)
                return

        # Anti-mention spam
        if config.get(gid, {}).get("antimentionspam", False):
            if len(message.mentions) >= 5:
                await message.delete()
                until = discord.utils.utcnow() + timedelta(minutes=10)
                await message.author.timeout(until, reason="Mention spam")
                await message.channel.send(f"⚠️ {message.author.mention} mute 10 min pour mention spam.", delete_after=5)

    # ── ANTIRAID ON/OFF ──────────────────────────────────────────
    @app_commands.command(name="antiraid", description="Activer/désactiver la protection anti-raid")
    @app_commands.describe(actif="Activer ou désactiver")
    @app_commands.choices(actif=[
        app_commands.Choice(name="Activer", value="on"),
        app_commands.Choice(name="Désactiver", value="off"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def antiraid(self, interaction: discord.Interaction, actif: app_commands.Choice[str]):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["antiraid"] = actif.value == "on"
        save_config(config)
        status = "✅ Activé" if actif.value == "on" else "❌ Désactivé"
        await interaction.response.send_message(f"🛡️ Anti-Raid : **{status}**")

    # ── ANTISPAM ON/OFF ──────────────────────────────────────────
    @app_commands.command(name="antispam", description="Activer/désactiver l'anti-spam")
    @app_commands.choices(actif=[
        app_commands.Choice(name="Activer", value="on"),
        app_commands.Choice(name="Désactiver", value="off"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def antispam(self, interaction: discord.Interaction, actif: app_commands.Choice[str]):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["antispam"] = actif.value == "on"
        save_config(config)
        status = "✅ Activé" if actif.value == "on" else "❌ Désactivé"
        await interaction.response.send_message(f"🛡️ Anti-Spam : **{status}**")

    # ── ANTIRAID THRESHOLD ───────────────────────────────────────
    @app_commands.command(name="antiraid-seuil", description="Nombre de joins en 10s pour déclencher l'anti-raid")
    @app_commands.default_permissions(administrator=True)
    async def antiraid_seuil(self, interaction: discord.Interaction, seuil: int):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["antiraid_threshold"] = seuil
        save_config(config)
        await interaction.response.send_message(f"✅ Seuil anti-raid : **{seuil} joins en 10 secondes**")

async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
                
