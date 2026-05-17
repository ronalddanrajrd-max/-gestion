import discord
from discord.ext import commands
from discord import app_commands
import datetime, platform

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── USERINFO ─────────────────────────────────────────────────
    @app_commands.command(name="userinfo", description="Infos détaillées sur un membre")
    async def userinfo(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        roles = [r.mention for r in membre.roles if r != interaction.guild.default_role]
        embed = discord.Embed(
            title=f"👤 {membre}",
            color=membre.color if membre.color != discord.Color.default() else discord.Color.blurple()
        )
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="ID", value=membre.id)
        embed.add_field(name="Surnom", value=membre.nick or "Aucun")
        embed.add_field(name="Compte créé", value=f"<t:{int(membre.created_at.timestamp())}:R>")
        embed.add_field(name="A rejoint", value=f"<t:{int(membre.joined_at.timestamp())}:R>")
        embed.add_field(name=f"Rôles ({len(roles)})", value=" ".join(roles) if roles else "Aucun", inline=False)
        embed.add_field(name="Bot ?", value="✅" if membre.bot else "❌")
        embed.add_field(name="Booster ?", value="✅" if membre.premium_since else "❌")
        await interaction.response.send_message(embed=embed)

    # ── SERVERINFO ───────────────────────────────────────────────
    @app_commands.command(name="serverinfo", description="Infos sur le serveur")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        bots = sum(1 for m in guild.members if m.bot)
        humans = guild.member_count - bots
        embed = discord.Embed(
            title=f"🏠 {guild.name}",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Propriétaire", value=guild.owner)
        embed.add_field(name="Membres", value=f"👤 {humans} humains | 🤖 {bots} bots")
        embed.add_field(name="Salons", value=f"💬 {len(guild.text_channels)} texte | 🔊 {len(guild.voice_channels)} vocal")
        embed.add_field(name="Rôles", value=len(guild.roles))
        embed.add_field(name="Emojis", value=len(guild.emojis))
        embed.add_field(name="Boosts", value=f"⚡ {guild.premium_subscription_count} (Niveau {guild.premium_tier})")
        embed.add_field(name="Créé le", value=f"<t:{int(guild.created_at.timestamp())}:D>")
        await interaction.response.send_message(embed=embed)

    # ── BOTINFO ──────────────────────────────────────────────────
    @app_commands.command(name="botinfo", description="Infos sur le bot")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(title=f"🤖 {self.bot.user.name}", color=discord.Color.blurple())
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="Serveurs", value=len(self.bot.guilds))
        embed.add_field(name="Utilisateurs", value=sum(g.member_count for g in self.bot.guilds))
        embed.add_field(name="Commandes", value=len(self.bot.tree.get_commands()))
        embed.add_field(name="Python", value=platform.python_version())
        embed.add_field(name="discord.py", value=discord.__version__)
        embed.add_field(name="Latence", value=f"{round(self.bot.latency * 1000)}ms")
        await interaction.response.send_message(embed=embed)

    # ── PING ─────────────────────────────────────────────────────
    @app_commands.command(name="ping", description="Latence du bot")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        color = discord.Color.green() if latency < 100 else discord.Color.orange() if latency < 300 else discord.Color.red()
        embed = discord.Embed(title="🏓 Pong !", description=f"**Latence :** {latency}ms", color=color)
        await interaction.response.send_message(embed=embed)

    # ── AVATAR ───────────────────────────────────────────────────
    @app_commands.command(name="avatar", description="Voir l'avatar d'un membre")
    async def avatar(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        embed = discord.Embed(title=f"🖼️ Avatar de {membre}", color=discord.Color.blurple())
        embed.set_image(url=membre.display_avatar.url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
