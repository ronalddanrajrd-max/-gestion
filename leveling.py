"""
cogs/leveling.py
Système de niveaux (XP) complet :
  - XP gagné par message (cooldown 60s par user)
  - Passage de niveau automatique avec notification
  - /rank — voir son niveau
  - /leaderboard — top 10
  - /setlevelchan — définir le salon de notification
  - /levelrole — attribuer un rôle à un niveau donné
  - /givexp — (admin) donner de l'XP manuellement
  - /resetxp — (admin) remettre à zéro
"""

import discord
from discord.ext import commands
from discord import app_commands
import json, os, asyncio, time, math, random
from datetime import datetime

XP_FILE     = "data/xp.json"
CONFIG_FILE = "data/config.json"

# ── XP par message ────────────────────────────────────────────────
XP_MIN     = 15
XP_MAX     = 25
XP_COOLDOWN = 60  # secondes

def xp_for_level(level: int) -> int:
    """XP total nécessaire pour atteindre ce niveau."""
    return int(5 * (level ** 2) + 50 * level + 100)

def level_from_xp(xp: int) -> int:
    level = 0
    while xp >= xp_for_level(level):
        xp -= xp_for_level(level)
        level += 1
    return level

def xp_in_level(xp: int) -> tuple[int, int]:
    """Retourne (xp_actuel_dans_niveau, xp_total_pour_passer)."""
    level = 0
    while xp >= xp_for_level(level):
        xp -= xp_for_level(level)
        level += 1
    return xp, xp_for_level(level)

def progress_bar(current: int, total: int, length: int = 12) -> str:
    filled = int(length * current / total) if total else 0
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"

def load_xp() -> dict:
    if not os.path.exists(XP_FILE):
        return {}
    with open(XP_FILE) as f:
        return json.load(f)

def save_xp(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(XP_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_user(data: dict, guild_id: int, user_id: int) -> dict:
    gid, uid = str(guild_id), str(user_id)
    if gid not in data:
        data[gid] = {}
    if uid not in data[gid]:
        data[gid][uid] = {"xp": 0, "level": 0, "messages": 0}
    return data[gid][uid]


class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._cooldowns: dict[tuple, float] = {}

    async def notify_levelup(self, member: discord.Member, new_level: int):
        """Envoie une notification de passage de niveau."""
        config = load_config()
        gid = str(member.guild.id)
        ch_id = config.get(gid, {}).get("level_channel")

        embed = discord.Embed(
            title="🎉 Niveau supérieur !",
            description=(
                f"Félicitations {member.mention} !\n"
                f"Tu es passé au **niveau {new_level}** ! 🚀"
            ),
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=member.guild.name)

        # Vérifier rôles de niveau
        role_rewards = config.get(gid, {}).get("level_roles", {})
        reward_role_id = role_rewards.get(str(new_level))
        if reward_role_id:
            role = member.guild.get_role(reward_role_id)
            if role:
                try:
                    await member.add_roles(role, reason=f"Niveau {new_level} atteint")
                    embed.add_field(name="🎁 Récompense", value=f"Rôle {role.mention} obtenu !")
                except Exception:
                    pass

        if ch_id:
            ch = member.guild.get_channel(ch_id)
            if ch:
                await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if len(message.content) < 3:
            return

        key = (message.guild.id, message.author.id)
        now = time.time()

        # Cooldown
        if now - self._cooldowns.get(key, 0) < XP_COOLDOWN:
            return
        self._cooldowns[key] = now

        data = load_xp()
        user = get_user(data, message.guild.id, message.author.id)
        gained = random.randint(XP_MIN, XP_MAX)
        old_level = user["level"]
        user["xp"] += gained
        user["messages"] += 1

        # Recalculer le niveau
        new_level = level_from_xp(user["xp"])
        user["level"] = new_level
        save_xp(data)

        if new_level > old_level:
            asyncio.create_task(self.notify_levelup(message.author, new_level))

    # ── RANK ─────────────────────────────────────────────────────
    @app_commands.command(name="rank", description="📊 Voir ton niveau et ton XP")
    @app_commands.describe(membre="Membre à consulter (toi par défaut)")
    async def rank(self, interaction: discord.Interaction, membre: discord.Member = None):
        target = membre or interaction.user
        data = load_xp()
        user = get_user(data, interaction.guild.id, target.id)
        save_xp(data)

        total_xp = user["xp"]
        level = level_from_xp(total_xp)
        xp_current, xp_needed = xp_in_level(total_xp)
        bar = progress_bar(xp_current, xp_needed)

        # Classement
        gid = str(interaction.guild.id)
        all_users = data.get(gid, {})
        sorted_users = sorted(all_users.items(), key=lambda x: x[1]["xp"], reverse=True)
        rank_pos = next((i+1 for i, (uid, _) in enumerate(sorted_users) if uid == str(target.id)), "?")

        embed = discord.Embed(
            title=f"📊 Niveau de {target.display_name}",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 Niveau",       value=f"**{level}**",                    inline=True)
        embed.add_field(name="⭐ XP Total",      value=f"**{total_xp:,}**",               inline=True)
        embed.add_field(name="🥇 Classement",   value=f"**#{rank_pos}**",                 inline=True)
        embed.add_field(
            name=f"📈 Progression vers niv. {level+1}",
            value=f"{bar} `{xp_current}/{xp_needed}`",
            inline=False
        )
        embed.add_field(name="💬 Messages",      value=f"{user.get('messages',0):,}",      inline=True)
        embed.set_footer(text=f"{XP_MIN}–{XP_MAX} XP par message • cooldown {XP_COOLDOWN}s")
        await interaction.response.send_message(embed=embed)

    # ── LEADERBOARD ──────────────────────────────────────────────
    @app_commands.command(name="leaderboard", description="🏆 Top 10 des membres les plus actifs")
    async def leaderboard(self, interaction: discord.Interaction):
        data = load_xp()
        gid = str(interaction.guild.id)
        all_users = data.get(gid, {})
        sorted_users = sorted(all_users.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]

        medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
        embed = discord.Embed(
            title=f"🏆 Leaderboard — {interaction.guild.name}",
            color=discord.Color.gold()
        )

        lines = []
        for i, (uid, udata) in enumerate(sorted_users):
            member = interaction.guild.get_member(int(uid))
            name = member.display_name if member else f"Utilisateur {uid[:6]}"
            level = level_from_xp(udata["xp"])
            lines.append(f"{medals[i]} **{name}** — Niv. {level} • {udata['xp']:,} XP")

        embed.description = "\n".join(lines) if lines else "Aucune donnée."
        embed.set_footer(text="XP gagné par message actif")
        await interaction.response.send_message(embed=embed)

    # ── SETLEVELCHAN ─────────────────────────────────────────────
    @app_commands.command(name="setlevelchan", description="📢 Définir le salon de notification de niveau")
    @app_commands.default_permissions(administrator=True)
    async def setlevelchan(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["level_channel"] = salon.id
        save_config(config)
        await interaction.response.send_message(
            f"✅ Les montées de niveau seront annoncées dans {salon.mention}", ephemeral=True
        )

    # ── LEVELROLE ────────────────────────────────────────────────
    @app_commands.command(name="levelrole", description="🎁 Attribuer un rôle à un niveau donné")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(niveau="Niveau requis", role="Rôle à attribuer")
    async def levelrole(self, interaction: discord.Interaction, niveau: int, role: discord.Role):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        if "level_roles" not in config[gid]:
            config[gid]["level_roles"] = {}
        config[gid]["level_roles"][str(niveau)] = role.id
        save_config(config)
        await interaction.response.send_message(
            f"✅ {role.mention} sera attribué à partir du **niveau {niveau}**.", ephemeral=True
        )

    # ── GIVEXP (admin) ───────────────────────────────────────────
    @app_commands.command(name="givexp", description="⭐ (Admin) Donner de l'XP à un membre")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(membre="Membre cible", quantite="Quantité d'XP à donner")
    async def givexp(self, interaction: discord.Interaction, membre: discord.Member, quantite: int):
        data = load_xp()
        user = get_user(data, interaction.guild.id, membre.id)
        user["xp"] += quantite
        old_level = user["level"]
        user["level"] = level_from_xp(user["xp"])
        save_xp(data)

        if user["level"] > old_level:
            asyncio.create_task(self.notify_levelup(membre, user["level"]))

        await interaction.response.send_message(
            f"✅ **+{quantite} XP** donné à {membre.mention}. Total : **{user['xp']:,} XP** (Niv. {user['level']})",
            ephemeral=True
        )

    # ── RESETXP (admin) ──────────────────────────────────────────
    @app_commands.command(name="resetxp", description="🗑 (Admin) Remettre à zéro l'XP d'un membre")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(membre="Membre cible (laisser vide = tout le serveur)")
    async def resetxp(self, interaction: discord.Interaction, membre: discord.Member = None):
        data = load_xp()
        gid = str(interaction.guild.id)
        if membre:
            if gid in data and str(membre.id) in data[gid]:
                data[gid][str(membre.id)] = {"xp": 0, "level": 0, "messages": 0}
            save_xp(data)
            await interaction.response.send_message(f"✅ XP de {membre.mention} remis à zéro.", ephemeral=True)
        else:
            data[gid] = {}
            save_xp(data)
            await interaction.response.send_message("✅ XP de tout le serveur remis à zéro.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
