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

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── ROLE ADD ─────────────────────────────────────────────────
    @app_commands.command(name="role-add", description="Ajouter un rôle à un membre")
    @app_commands.default_permissions(manage_roles=True)
    async def role_add(self, interaction: discord.Interaction, membre: discord.Member, role: discord.Role):
        await membre.add_roles(role)
        await interaction.response.send_message(f"✅ Rôle **{role.name}** ajouté à **{membre}**.")

    # ── ROLE REMOVE ──────────────────────────────────────────────
    @app_commands.command(name="role-remove", description="Retirer un rôle à un membre")
    @app_commands.default_permissions(manage_roles=True)
    async def role_remove(self, interaction: discord.Interaction, membre: discord.Member, role: discord.Role):
        await membre.remove_roles(role)
        await interaction.response.send_message(f"✅ Rôle **{role.name}** retiré de **{membre}**.")

    # ── AUTOROLE ─────────────────────────────────────────────────
    @app_commands.command(name="autorole", description="Rôle automatique donné à l'arrivée")
    @app_commands.default_permissions(administrator=True)
    async def autorole(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["autorole"] = role.id
        save_config(config)
        await interaction.response.send_message(f"✅ AutoRole configuré : **{role.name}**")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = load_config()
        gid = str(member.guild.id)
        role_id = config.get(gid, {}).get("autorole")
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role)

    # ── REACTION ROLE SETUP ──────────────────────────────────────
    @app_commands.command(name="reactionrole", description="Créer un message de rôle par réaction")
    @app_commands.describe(role="Le rôle à attribuer", emoji="L'émoji à utiliser", message="Texte du message")
    @app_commands.default_permissions(administrator=True)
    async def reactionrole(self, interaction: discord.Interaction, role: discord.Role, emoji: str, message: str = "Réagis pour obtenir un rôle !"):
        embed = discord.Embed(description=f"{emoji} → **{role.name}**\n\n{message}", color=discord.Color.blurple())
        await interaction.response.send_message("✅ Message de reaction role créé !")
        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction(emoji)

        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        if "reactionroles" not in config[gid]:
            config[gid]["reactionroles"] = {}
        config[gid]["reactionroles"][str(msg.id)] = {"emoji": emoji, "role_id": role.id}
        save_config(config)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        config = load_config()
        gid = str(payload.guild_id)
        rr = config.get(gid, {}).get("reactionroles", {})
        entry = rr.get(str(payload.message_id))
        if entry and str(payload.emoji) == entry["emoji"] and not payload.member.bot:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(entry["role_id"])
            if role:
                await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        config = load_config()
        gid = str(payload.guild_id)
        rr = config.get(gid, {}).get("reactionroles", {})
        entry = rr.get(str(payload.message_id))
        if entry and str(payload.emoji) == entry["emoji"]:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = guild.get_role(entry["role_id"])
            if role and member:
                await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(Roles(bot))
