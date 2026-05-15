import discord
from discord.ext import commands
from discord import app_commands
import json, os, random
from datetime import datetime, timedelta

LEVELS_FILE = "data/levels.json"
CONFIG_FILE = "data/config.json"

def load_levels():
    if not os.path.exists(LEVELS_FILE):
        return {}
    with open(LEVELS_FILE) as f:
        return json.load(f)

def save_levels(data):
    os.makedirs("data", exist_ok=True)
    with open(LEVELS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def xp_needed(level):
    return 100 + (level * 50)

cooldowns = {}

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        uid = str(message.author.id)
        gid = str(message.guild.id)
        key = f"{gid}-{uid}"
        now = datetime.utcnow()

        if key in cooldowns and (now - cooldowns[key]).seconds < 60:
            return
        cooldowns[key] = now

        levels = load_levels()
        if gid not in levels:
            levels[gid] = {}
        if uid not in levels[gid]:
            levels[gid][uid] = {"xp": 0, "level": 0}

        xp_gain = random.randint(15, 25)
        levels[gid][uid]["xp"] += xp_gain
        user_data = levels[gid][uid]
        current_level = user_data["level"]
        needed = xp_needed(current_level)

        if user_data["xp"] >= needed:
            levels[gid][uid]["xp"] -= needed
            levels[gid][uid]["level"] += 1
            new_level = levels[gid][uid]["level"]
            save_levels(levels)

            config = load_config()
            channel_id = config.get(gid, {}).get("level_channel")
            channel = message.guild.get_channel(channel_id) if channel_id else message.channel

            embed = discord.Embed(
                title="🎉 Level Up !",
                description=f"{message.author.mention} est passé au niveau **{new_level}** !",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            await channel.send(embed=embed)

            level_roles = config.get(gid, {}).get("level_roles", {})
            role_id = level_roles.get(str(new_level))
            if role_id:
                role = message.guild.get_role(int(role_id))
                if role:
                    try:
                        await message.author.add_roles(role)
                    except Exception:
                        pass
        else:
            save_levels(levels)

    @app_commands.command(name="rank", description="Voir ton niveau et ton XP")
    async def rank(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        levels = load_levels()
        gid = str(interaction.guild.id)
        uid = str(membre.id)
        data = levels.get(gid, {}).get(uid, {"xp": 0, "level": 0})
        level = data["level"]
        xp = data["xp"]
        needed = xp_needed(level)

        guild_data = levels.get(gid, {})
        sorted_users = sorted(guild_data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
        rank = next((i+1 for i, (u, _) in enumerate(sorted_users) if u == uid), "?")

        bar_filled = int((xp / needed) * 20)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)

        embed = discord.Embed(title=f"📊 Rang de {membre.display_name}", color=discord.Color.blurple())
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="Niveau", value=f"⭐ **{level}**")
        embed.add_field(name="Classement", value=f"🏆 **#{rank}**")
        embed.add_field(name="XP", value=f"`{bar}` {xp}/{needed}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Top 10 membres les plus actifs")
    async def leaderboard(self, interaction: discord.Interaction):
        levels = load_levels()
        gid = str(interaction.guild.id)
        guild_data = levels.get(gid, {})
        sorted_users = sorted(guild_data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)[:10]

        embed = discord.Embed(title="🏆 Classement d'activité", color=discord.Color.gold())
        medals = ["🥇", "🥈", "🥉"]
        desc = ""
        for i, (uid, data) in enumerate(sorted_users):
            medal = medals[i] if i < 3 else f"**#{i+1}**"
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"Utilisateur ({uid})"
            desc += f"{medal} **{name}** — Nv. {data['level']} ({data['xp']} XP)\n"
        embed.description = desc or "Aucune donnée encore."
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setlevelchannel", description="Salon pour les annonces de level up")
    @app_commands.default_permissions(administrator=True)
    async def setlevelchannel(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["level_channel"] = salon.id
        save_config(config)
        await interaction.response.send_message(f"✅ Annonces de niveau dans {salon.mention}")

    @app_commands.command(name="levelrole", description="Rôle automatique à un niveau donné")
    @app_commands.default_permissions(administrator=True)
    async def levelrole(self, interaction: discord.Interaction, niveau: int, role: discord.Role):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        if "level_roles" not in config[gid]:
            config[gid]["level_roles"] = {}
        config[gid]["level_roles"][str(niveau)] = role.id
        save_config(config)
        await interaction.response.send_message(f"✅ Niveau **{niveau}** → Rôle **{role.name}**")

    @app_commands.command(name="resetxp", description="Réinitialiser l'XP d'un membre")
    @app_commands.default_permissions(administrator=True)
    async def resetxp(self, interaction: discord.Interaction, membre: discord.Member):
        levels = load_levels()
        gid = str(interaction.guild.id)
        if gid in levels and str(membre.id) in levels[gid]:
            levels[gid][str(membre.id)] = {"xp": 0, "level": 0}
            save_levels(levels)
        await interaction.response.send_message(f"✅ XP de **{membre}** réinitialisé.")

async def setup(bot):
    await bot.add_cog(Levels(bot))
