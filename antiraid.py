import discord
from discord.ext import commands
from discord import app_commands
import json, os, asyncio
from collections import defaultdict
from datetime import datetime, timedelta

CONFIG_FILE = "data/config.json"
OWNER_ID = 1467602579482480821

join_tracker = defaultdict(list)
message_tracker = defaultdict(list)
channel_delete_tracker = defaultdict(list)
channel_create_tracker = defaultdict(list)
role_tracker = defaultdict(list)
webhook_tracker = defaultdict(list)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def punish(guild, member, reason):
    """Bannir ou kick le raider"""
    try:
        await member.ban(reason=f"🛡️ Anti-Raid : {reason}", delete_message_days=1)
        return True
    except Exception:
        try:
            await member.kick(reason=f"🛡️ Anti-Raid : {reason}")
            return True
        except Exception:
            return False

async def log_raid(guild, description):
    """Envoyer un log dans le salon configuré"""
    config = load_config()
    gid = str(guild.id)
    log_ch_id = config.get(gid, {}).get("log_channel")
    if log_ch_id:
        ch = guild.get_channel(log_ch_id)
        if ch:
            embed = discord.Embed(
                title="🚨 ACTION ANTI-RAID",
                description=description,
                color=discord.Color.dark_red(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Système Anti-Raid")
            try:
                await ch.send(embed=embed)
            except Exception:
                pass

async def lockdown_server(guild):
    """Verrouiller tous les salons du serveur"""
    locked = 0
    for channel in guild.text_channels:
        try:
            overwrite = channel.overwrites_for(guild.default_role)
            if overwrite.send_messages != False:
                overwrite.send_messages = False
                await channel.set_permissions(guild.default_role, overwrite=overwrite)
                locked += 1
                await asyncio.sleep(0.5)  # éviter le rate limit
        except Exception:
            pass
    return locked

async def unlock_server(guild):
    """Déverrouiller tous les salons"""
    for channel in guild.text_channels:
        try:
            overwrite = channel.overwrites_for(guild.default_role)
            overwrite.send_messages = None
            await channel.set_permissions(guild.default_role, overwrite=overwrite)
            await asyncio.sleep(0.3)
        except Exception:
            pass

class AntiRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lockdown_active = {}

    def is_protected(self, guild, member):
        """Vérifier si le membre est protégé (owner, admins, bot lui-même)"""
        if member.id == OWNER_ID:
            return True
        if member.id == guild.owner_id:
            return True
        if member.bot and member.id == guild.me.id:
            return True
        if member.guild_permissions.administrator:
            return True
        return False

    # ── MASS JOIN ────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        config = load_config()
        gid = str(member.guild.id)
        if not config.get(gid, {}).get("antiraid", False):
            return
        if self.is_protected(member.guild, member):
            return

        now = datetime.utcnow()
        join_tracker[gid].append(now)
        join_tracker[gid] = [t for t in join_tracker[gid] if (now - t).seconds < 10]
        threshold = config.get(gid, {}).get("antiraid_threshold", 5)

        if len(join_tracker[gid]) >= threshold:
            # Lockdown immédiat
            if not self.lockdown_active.get(gid):
                self.lockdown_active[gid] = True
                locked = await lockdown_server(member.guild)
                await log_raid(
                    member.guild,
                    f"⚠️ **MASS JOIN DÉTECTÉ**\n"
                    f"**{len(join_tracker[gid])} membres** ont rejoint en moins de 10 secondes !\n"
                    f"🔒 **{locked} salons verrouillés automatiquement**\n"
                    f"Utilisez `/antiraid-unlock` pour déverrouiller."
                )

            # Kick/ban le membre
            await punish(member.guild, member, "Mass join détecté")

    # ── MASS CHANNEL DELETE/CREATE ────────────────────────────────
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        config = load_config()
        gid = str(channel.guild.id)
        if not config.get(gid, {}).get("antiraid", False):
            return

        now = datetime.utcnow()

        # Trouver qui a supprimé via les logs d'audit
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if (datetime.utcnow() - entry.created_at.replace(tzinfo=None)).seconds < 5:
                    perpetrator = entry.user
                    if self.is_protected(channel.guild, perpetrator):
                        return

                    uid = str(perpetrator.id)
                    channel_delete_tracker[uid].append(now)
                    channel_delete_tracker[uid] = [t for t in channel_delete_tracker[uid] if (now - t).seconds < 10]

                    if len(channel_delete_tracker[uid]) >= 3:
                        await punish(channel.guild, perpetrator, "Suppression massive de salons")
                        await log_raid(
                            channel.guild,
                            f"🗑️ **SUPPRESSION DE SALONS DÉTECTÉE**\n"
                            f"**{perpetrator}** a supprimé **{len(channel_delete_tracker[uid])} salons** en 10 secondes !\n"
                            f"✅ Banni automatiquement."
                        )
                        channel_delete_tracker[uid] = []
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        config = load_config()
        gid = str(channel.guild.id)
        if not config.get(gid, {}).get("antiraid", False):
            return

        now = datetime.utcnow()
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if (datetime.utcnow() - entry.created_at.replace(tzinfo=None)).seconds < 5:
                    perpetrator = entry.user
                    if self.is_protected(channel.guild, perpetrator):
                        return

                    uid = str(perpetrator.id)
                    channel_create_tracker[uid].append(now)
                    channel_create_tracker[uid] = [t for t in channel_create_tracker[uid] if (now - t).seconds < 10]

                    if len(channel_create_tracker[uid]) >= 3:
                        await punish(channel.guild, perpetrator, "Création massive de salons")
                        await log_raid(
                            channel.guild,
                            f"➕ **CRÉATION DE SALONS DÉTECTÉE**\n"
                            f"**{perpetrator}** a créé **{len(channel_create_tracker[uid])} salons** en 10 secondes !\n"
                            f"✅ Banni automatiquement."
                        )
                        channel_create_tracker[uid] = []
                        # Supprimer les salons créés
                        try:
                            await channel.delete(reason="Anti-raid: création massive")
                        except Exception:
                            pass
        except Exception:
            pass

    # ── MASS ROLE ────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        config = load_config()
        gid = str(after.guild.id)
        if not config.get(gid, {}).get("antiraid", False):
            return
        if before.roles == after.roles:
            return

        now = datetime.utcnow()
        try:
            async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                if (datetime.utcnow() - entry.created_at.replace(tzinfo=None)).seconds < 5:
                    perpetrator = entry.user
                    if self.is_protected(after.guild, perpetrator):
                        return

                    uid = str(perpetrator.id)
                    role_tracker[uid].append(now)
                    role_tracker[uid] = [t for t in role_tracker[uid] if (now - t).seconds < 10]

                    if len(role_tracker[uid]) >= 5:
                        await punish(after.guild, perpetrator, "Mass role update")
                        await log_raid(
                            after.guild,
                            f"🎭 **MASS ROLE DÉTECTÉ**\n"
                            f"**{perpetrator}** a modifié les rôles de **{len(role_tracker[uid])} membres** en 10 secondes !\n"
                            f"✅ Banni automatiquement."
                        )
                        role_tracker[uid] = []
        except Exception:
            pass

    # ── ANTI SPAM MESSAGE ────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        config = load_config()
        gid = str(message.guild.id)

        if not config.get(gid, {}).get("antispam", False):
            return
        if self.is_protected(message.guild, message.author):
            return

        now = datetime.utcnow()
        uid = message.author.id
        message_tracker[uid].append(now)
        message_tracker[uid] = [t for t in message_tracker[uid] if (now - t).seconds < 5]

        if len(message_tracker[uid]) >= 6:
            try:
                await message.delete()
                until = discord.utils.utcnow() + timedelta(minutes=10)
                await message.author.timeout(until, reason="Anti-spam")
                await message.channel.send(
                    f"⚠️ {message.author.mention} mute **10 min** pour spam !",
                    delete_after=5
                )
                message_tracker[uid] = []
            except Exception:
                pass

        elif len(message_tracker[uid]) >= 4:
            try:
                await message.delete()
            except Exception:
                pass

    # ── WEBHOOK PROTECTION ───────────────────────────────────────
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        config = load_config()
        gid = str(channel.guild.id)
        if not config.get(gid, {}).get("antiraid", False):
            return
        try:
            async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.webhook_create):
                if (datetime.utcnow() - entry.created_at.replace(tzinfo=None)).seconds < 5:
                    perpetrator = entry.user
                    if self.is_protected(channel.guild, perpetrator):
                        return
                    uid = str(perpetrator.id)
                    webhook_tracker[uid].append(datetime.utcnow())
                    webhook_tracker[uid] = [t for t in webhook_tracker[uid] if (datetime.utcnow() - t).seconds < 30]
                    if len(webhook_tracker[uid]) >= 2:
                        await punish(channel.guild, perpetrator, "Création massive de webhooks")
                        await log_raid(
                            channel.guild,
                            f"🔗 **WEBHOOK RAID DÉTECTÉ**\n"
                            f"**{perpetrator}** a créé plusieurs webhooks suspects !\n"
                            f"✅ Banni automatiquement."
                        )
        except Exception:
            pass

    # ── COMMANDES ────────────────────────────────────────────────
    @app_commands.command(name="antiraid", description="Activer/désactiver la protection anti-raid")
    @app_commands.choices(actif=[
        app_commands.Choice(name="✅ Activer", value="on"),
        app_commands.Choice(name="❌ Désactiver", value="off"),
    ])
    async def antiraid_cmd(self, interaction: discord.Interaction, actif: app_commands.Choice[str]):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["antiraid"] = actif.value == "on"
        save_config(config)
        status = "✅ Activé" if actif.value == "on" else "❌ Désactivé"
        embed = discord.Embed(
            title="🛡️ Anti-Raid",
            description=(
                f"Statut : **{status}**\n\n"
                f"Protection active contre :\n"
                f"• Mass join\n"
                f"• Suppression/création de salons\n"
                f"• Mass role update\n"
                f"• Spam de messages\n"
                f"• Webhooks suspects"
            ),
            color=discord.Color.green() if actif.value == "on" else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="antispam", description="Activer/désactiver l'anti-spam")
    @app_commands.choices(actif=[
        app_commands.Choice(name="✅ Activer", value="on"),
        app_commands.Choice(name="❌ Désactiver", value="off"),
    ])
    async def antispam_cmd(self, interaction: discord.Interaction, actif: app_commands.Choice[str]):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["antispam"] = actif.value == "on"
        save_config(config)
        status = "✅ Activé" if actif.value == "on" else "❌ Désactivé"
        await interaction.response.send_message(f"🛡️ Anti-Spam : **{status}**")

    @app_commands.command(name="antiraid-lockdown", description="Verrouiller manuellement tous les salons")
    async def lockdown(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        await interaction.response.defer()
        gid = str(interaction.guild.id)
        self.lockdown_active[gid] = True
        locked = await lockdown_server(interaction.guild)
        await interaction.followup.send(
            embed=discord.Embed(
                title="🔒 LOCKDOWN ACTIVÉ",
                description=f"**{locked} salons** verrouillés !\nUtilise `/antiraid-unlock` pour déverrouiller.",
                color=discord.Color.red()
            )
        )

    @app_commands.command(name="antiraid-unlock", description="Déverrouiller tous les salons")
    async def unlock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        await interaction.response.defer()
        gid = str(interaction.guild.id)
        self.lockdown_active[gid] = False
        await unlock_server(interaction.guild)
        await interaction.followup.send(
            embed=discord.Embed(
                title="🔓 LOCKDOWN LEVÉ",
                description="Tous les salons sont déverrouillés !",
                color=discord.Color.green()
            )
        )

    @app_commands.command(name="antiraid-seuil", description="Nombre de joins en 10s pour déclencher le lockdown")
    async def seuil(self, interaction: discord.Interaction, seuil: int):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["antiraid_threshold"] = seuil
        save_config(config)
        await interaction.response.send_message(f"✅ Seuil : **{seuil} joins en 10 secondes**")

    @app_commands.command(name="antiraid-status", description="Voir le statut de la protection")
    async def status(self, interaction: discord.Interaction):
        config = load_config()
        gid = str(interaction.guild.id)
        cfg = config.get(gid, {})
        embed = discord.Embed(title="🛡️ Statut Anti-Raid", color=discord.Color.blurple())
        embed.add_field(name="Anti-Raid", value="✅ Actif" if cfg.get("antiraid") else "❌ Inactif")
        embed.add_field(name="Anti-Spam", value="✅ Actif" if cfg.get("antispam") else "❌ Inactif")
        embed.add_field(name="Seuil joins", value=f"{cfg.get('antiraid_threshold', 5)} joins/10s")
        embed.add_field(name="Lockdown", value="🔒 Actif" if self.lockdown_active.get(gid) else "🔓 Inactif")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AntiRaid(bot))


    # ── WHITELIST BOT ────────────────────────────────────────────
    @app_commands.command(name="antiraid-whitelist", description="Ajouter un bot à la whitelist")
    async def whitelist(self, interaction: discord.Interaction, bot_id: str):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        if "whitelist_bots" not in config[gid]:
            config[gid]["whitelist_bots"] = []
        if int(bot_id) not in config[gid]["whitelist_bots"]:
            config[gid]["whitelist_bots"].append(int(bot_id))
        save_config(config)
        await interaction.response.send_message(f"✅ Bot `{bot_id}` ajouté à la whitelist.")

    @commands.Cog.listener()
    async def on_member_join_bot_check(self, member: discord.Member):
        """Vérifier les bots qui rejoignent"""
        if not member.bot:
            return
        config = load_config()
        gid = str(member.guild.id)
        if not config.get(gid, {}).get("antiraid", False):
            return
        whitelist = config.get(gid, {}).get("whitelist_bots", [])
        if member.id not in whitelist and member.id != member.guild.me.id:
            try:
                await member.kick(reason="🛡️ Bot non autorisé — pas dans la whitelist")
                await log_raid(
                    member.guild,
                    f"🤖 **BOT NON AUTORISÉ EXPULSÉ**\n"
                    f"**{member}** (ID: {member.id}) a été expulsé.\n"
                    f"Utilise `/antiraid-whitelist {member.id}` pour l'autoriser."
                )
            except Exception:
                pass
                          
