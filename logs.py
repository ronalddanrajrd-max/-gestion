import discord
from discord.ext import commands
from discord import app_commands
import datetime, json, os

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

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_log_channel(self, guild):
        config = load_config()
        channel_id = config.get(str(guild.id), {}).get("log_channel")
        return guild.get_channel(channel_id) if channel_id else None

    # ── SET LOGS ─────────────────────────────────────────────────
    @app_commands.command(name="setlogs", description="Définir le salon de logs")
    @app_commands.default_permissions(administrator=True)
    async def setlogs(self, interaction: discord.Interaction, salon: discord.TextChannel):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["log_channel"] = salon.id
        save_config(config)
        await interaction.response.send_message(f"✅ Salon de logs : {salon.mention}")

    # ── MESSAGE DELETE ────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        channel = await self.get_log_channel(message.guild)
        if channel:
            embed = discord.Embed(
                title="🗑️ Message supprimé",
                description=f"**Auteur :** {message.author.mention}\n**Salon :** {message.channel.mention}\n**Contenu :** {message.content or '*vide*'}",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            await channel.send(embed=embed)

    # ── MESSAGE EDIT ──────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild or before.content == after.content:
            return
        channel = await self.get_log_channel(before.guild)
        if channel:
            embed = discord.Embed(
                title="✏️ Message modifié",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Auteur", value=before.author.mention)
            embed.add_field(name="Salon", value=before.channel.mention)
            embed.add_field(name="Avant", value=before.content[:1024] or "*vide*", inline=False)
            embed.add_field(name="Après", value=after.content[:1024] or "*vide*", inline=False)
            await channel.send(embed=embed)

    # ── MEMBER JOIN ───────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = await self.get_log_channel(member.guild)
        if channel:
            embed = discord.Embed(
                title="✅ Nouveau membre",
                description=f"{member.mention} a rejoint le serveur.\n**Compte créé :** <t:{int(member.created_at.timestamp())}:R>",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await channel.send(embed=embed)

    # ── MEMBER LEAVE ──────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = await self.get_log_channel(member.guild)
        if channel:
            embed = discord.Embed(
                title="👋 Membre parti",
                description=f"**{member}** a quitté le serveur.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.utcnow()
            )
            await channel.send(embed=embed)

    # ── MEMBER BAN ────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        channel = await self.get_log_channel(guild)
        if channel:
            embed = discord.Embed(
                title="🔨 Membre banni",
                description=f"**{user}** (ID: {user.id}) a été banni.",
                color=discord.Color.dark_red(),
                timestamp=datetime.datetime.utcnow()
            )
            await channel.send(embed=embed)

    # ── MEMBER UNBAN ──────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        channel = await self.get_log_channel(guild)
        if channel:
            embed = discord.Embed(
                title="✅ Membre débanni",
                description=f"**{user}** (ID: {user.id}) a été débanni.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            await channel.send(embed=embed)

    # ── ROLE CHANGE ───────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles:
            return
        channel = await self.get_log_channel(before.guild)
        if channel:
            added = [r for r in after.roles if r not in before.roles]
            removed = [r for r in before.roles if r not in after.roles]
            embed = discord.Embed(
                title="🎭 Rôles modifiés",
                color=discord.Color.blurple(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Membre", value=before.mention)
            if added:
                embed.add_field(name="Rôle(s) ajouté(s)", value=" ".join(r.mention for r in added), inline=False)
            if removed:
                embed.add_field(name="Rôle(s) retiré(s)", value=" ".join(r.mention for r in removed), inline=False)
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
