import discord
from discord.ext import commands
from discord import app_commands
import json, os, asyncio

CONFIG_FILE = "data/config.json"
TEMPVC_FILE = "data/tempvc.json"
OWNER_ID = 1467602579482480821
OWNER_ID2 = 1504570877360996442

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_tempvc():
    if not os.path.exists(TEMPVC_FILE):
        return {}
    with open(TEMPVC_FILE) as f:
        return json.load(f)

def save_tempvc(data):
    os.makedirs("data", exist_ok=True)
    with open(TEMPVC_FILE, "w") as f:
        json.dump(data, f, indent=2)

def is_owner(user_id):
    return user_id in (OWNER_ID, OWNER_ID2)

class TempVCControlView(discord.ui.View):
    """Panel de contrôle du vocal temporaire"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✏️ Renommer", style=discord.ButtonStyle.primary, custom_id="vc_rename")
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        uid = str(interaction.user.id)
        channel_id = tempvc.get(gid, {}).get(uid)
        if not channel_id:
            return await interaction.response.send_message("❌ Tu n'as pas de salon vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)
        await interaction.response.send_modal(RenameModal(channel))

    @discord.ui.button(label="🔒 Verrouiller", style=discord.ButtonStyle.danger, custom_id="vc_lock")
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        uid = str(interaction.user.id)
        channel_id = tempvc.get(gid, {}).get(uid)
        if not channel_id:
            return await interaction.response.send_message("❌ Tu n'as pas de salon vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.connect = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔒 Salon verrouillé !", ephemeral=True)

    @discord.ui.button(label="🔓 Déverrouiller", style=discord.ButtonStyle.success, custom_id="vc_unlock")
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        uid = str(interaction.user.id)
        channel_id = tempvc.get(gid, {}).get(uid)
        if not channel_id:
            return await interaction.response.send_message("❌ Tu n'as pas de salon vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.connect = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 Salon déverrouillé !", ephemeral=True)

    @discord.ui.button(label="👥 Limite", style=discord.ButtonStyle.secondary, custom_id="vc_limit")
    async def limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        uid = str(interaction.user.id)
        channel_id = tempvc.get(gid, {}).get(uid)
        if not channel_id:
            return await interaction.response.send_message("❌ Tu n'as pas de salon vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)
        await interaction.response.send_modal(LimitModal(channel))

    @discord.ui.button(label="👢 Expulser", style=discord.ButtonStyle.danger, custom_id="vc_kick")
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        uid = str(interaction.user.id)
        channel_id = tempvc.get(gid, {}).get(uid)
        if not channel_id:
            return await interaction.response.send_message("❌ Tu n'as pas de salon vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            return await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)
        # Lister les membres dans le vocal
        members = channel.members
        if not members:
            return await interaction.response.send_message("❌ Personne dans ton vocal.", ephemeral=True)
        options = [
            discord.SelectOption(label=m.display_name, value=str(m.id))
            for m in members if m.id != interaction.user.id
        ]
        if not options:
            return await interaction.response.send_message("❌ Personne à expulser.", ephemeral=True)
        view = KickSelectView(channel, options)
        await interaction.response.send_message("👢 Qui veux-tu expulser ?", view=view, ephemeral=True)

class RenameModal(discord.ui.Modal, title="✏️ Renommer le salon"):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    nom = discord.ui.TextInput(
        label="Nouveau nom",
        placeholder="Ex: Gaming avec les boys",
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.channel.edit(name=self.nom.value)
        await interaction.response.send_message(f"✅ Salon renommé : **{self.nom.value}**", ephemeral=True)

class LimitModal(discord.ui.Modal, title="👥 Limite de membres"):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    limite = discord.ui.TextInput(
        label="Limite (0 = illimitée)",
        placeholder="Ex: 5",
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.limite.value)
            await self.channel.edit(user_limit=limit)
            msg = f"✅ Limite : **{limit}** membres" if limit > 0 else "✅ Limite supprimée"
            await interaction.response.send_message(msg, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Entre un nombre valide.", ephemeral=True)

class KickSelectView(discord.ui.View):
    def __init__(self, channel, options):
        super().__init__(timeout=30)
        self.channel = channel
        select = discord.ui.Select(placeholder="Choisis un membre", options=options)
        select.callback = self.kick_member
        self.add_item(select)

    async def kick_member(self, interaction: discord.Interaction):
        uid = int(interaction.data["values"][0])
        member = interaction.guild.get_member(uid)
        if member and member.voice and member.voice.channel == self.channel:
            await member.move_to(None, reason="Expulsé du vocal temporaire")
            await interaction.response.send_message(f"👢 **{member.display_name}** expulsé !", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Membre introuvable dans le vocal.", ephemeral=True)

class TempVC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TempVCControlView())

    # ── DÉTECTION JOIN ───────────────────────────────────────────
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        config = load_config()
        gid = str(member.guild.id)
        create_channel_id = config.get(gid, {}).get("tempvc_create")
        category_id = config.get(gid, {}).get("tempvc_category")

        # Rejoindre le salon "Créer un vocal"
        if after.channel and after.channel.id == create_channel_id:
            category = member.guild.get_channel(category_id) if category_id else after.channel.category

            # Créer le vocal temporaire
            channel = await member.guild.create_voice_channel(
                name=f"🎮 {member.display_name}",
                category=category,
                user_limit=0
            )

            # Donner les permissions au créateur
            await channel.set_permissions(member, connect=True, manage_channels=True, move_members=True)

            # Déplacer le membre
            try:
                await member.move_to(channel)
            except Exception:
                await channel.delete()
                return

            # Sauvegarder
            tempvc = load_tempvc()
            if gid not in tempvc:
                tempvc[gid] = {}
            tempvc[gid][str(member.id)] = channel.id
            save_tempvc(tempvc)

            # Envoyer le panel de contrôle en DM
            try:
                embed = discord.Embed(
                    title="🎛️ Contrôle de ton vocal",
                    description=(
                        f"Ton salon **{channel.name}** a été créé !\n\n"
                        "Utilise les boutons pour le gérer :"
                    ),
                    color=discord.Color.blurple()
                )
                # Envoyer dans le salon de contrôle configuré
                control_ch_id = config.get(gid, {}).get("tempvc_control")
                control_ch = member.guild.get_channel(control_ch_id) if control_ch_id else None
                if control_ch:
                    await control_ch.send(
                        content=member.mention,
                        embed=embed,
                        view=TempVCControlView(),
                        delete_after=300
                    )
            except Exception:
                pass

        # Quitter le vocal temporaire → supprimer si vide
        if before.channel:
            tempvc = load_tempvc()
            gid = str(member.guild.id)
            uid = str(member.id)
            channel_id = tempvc.get(gid, {}).get(uid)

            if before.channel.id == channel_id:
                if len(before.channel.members) == 0:
                    try:
                        await before.channel.delete(reason="Vocal temporaire vide")
                    except Exception:
                        pass
                    if uid in tempvc.get(gid, {}):
                        del tempvc[gid][uid]
                        save_tempvc(tempvc)

            # Aussi supprimer si un vocal temp est vide (même sans owner)
            for owner_id, ch_id in list(tempvc.get(gid, {}).items()):
                if before.channel.id == ch_id and len(before.channel.members) == 0:
                    try:
                        await before.channel.delete(reason="Vocal temporaire vide")
                    except Exception:
                        pass
                    del tempvc[gid][owner_id]
                    save_tempvc(tempvc)
                    break

    # ── SETUP ────────────────────────────────────────────────────
    @app_commands.command(name="tempvc-setup", description="Configurer le système de vocaux temporaires")
    @app_commands.describe(
        salon_creation="Salon vocal où rejoindre pour créer un vc",
        salon_controle="Salon texte pour les panneaux de contrôle",
        categorie="Catégorie où créer les vocaux"
    )
    async def tempvc_setup(
        self,
        interaction: discord.Interaction,
        salon_creation: discord.VoiceChannel,
        salon_controle: discord.TextChannel,
        categorie: discord.CategoryChannel = None
    ):
        if not interaction.user.guild_permissions.administrator and not is_owner(interaction.user.id):
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)

        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["tempvc_create"] = salon_creation.id
        config[gid]["tempvc_control"] = salon_controle.id
        if categorie:
            config[gid]["tempvc_category"] = categorie.id
        save_config(config)

        embed = discord.Embed(
            title="✅ Vocaux temporaires configurés !",
            description=(
                f"🔊 **Salon création :** {salon_creation.mention}\n"
                f"🎛️ **Salon contrôle :** {salon_controle.mention}\n\n"
                "Les membres rejoignent le salon création pour obtenir leur propre vocal !"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # ── COMMANDES ADMIN ──────────────────────────────────────────
    @app_commands.command(name="vc-delete", description="Supprimer un vocal temporaire [ADMIN]")
    async def vc_delete(self, interaction: discord.Interaction, membre: discord.Member):
        if not interaction.user.guild_permissions.administrator and not is_owner(interaction.user.id):
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        channel_id = tempvc.get(gid, {}).get(str(membre.id))
        if not channel_id:
            return await interaction.response.send_message(f"❌ {membre.mention} n'a pas de vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            await channel.delete(reason=f"Supprimé par admin {interaction.user}")
        del tempvc[gid][str(membre.id)]
        save_tempvc(tempvc)
        await interaction.response.send_message(f"✅ Vocal de **{membre.display_name}** supprimé.")

    @app_commands.command(name="vc-join", description="Rejoindre un vocal même s'il est full [ADMIN]")
    async def vc_join(self, interaction: discord.Interaction, membre: discord.Member):
        if not interaction.user.guild_permissions.administrator and not is_owner(interaction.user.id):
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        channel_id = tempvc.get(gid, {}).get(str(membre.id))
        if not channel_id:
            return await interaction.response.send_message(f"❌ {membre.mention} n'a pas de vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            # Retirer temporairement la limite
            old_limit = channel.user_limit
            await channel.edit(user_limit=0)
            await interaction.response.send_message(f"✅ Tu peux rejoindre {channel.mention} !", ephemeral=True)
            await asyncio.sleep(10)
            await channel.edit(user_limit=old_limit)
        else:
            await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)

    @app_commands.command(name="vc-rename", description="Renommer le vocal d'un membre [ADMIN]")
    async def vc_rename(self, interaction: discord.Interaction, membre: discord.Member, nom: str):
        if not interaction.user.guild_permissions.administrator and not is_owner(interaction.user.id):
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        channel_id = tempvc.get(gid, {}).get(str(membre.id))
        if not channel_id:
            return await interaction.response.send_message(f"❌ {membre.mention} n'a pas de vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            await channel.edit(name=nom)
            await interaction.response.send_message(f"✅ Vocal renommé : **{nom}**")
        else:
            await interaction.response.send_message("❌ Salon introuvable.", ephemeral=True)

    @app_commands.command(name="vc-list", description="Voir tous les vocaux temporaires actifs")
    async def vc_list(self, interaction: discord.Interaction):
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        vcs = tempvc.get(gid, {})
        if not vcs:
            return await interaction.response.send_message("📭 Aucun vocal temporaire actif.", ephemeral=True)
        desc = ""
        for uid, ch_id in vcs.items():
            member = interaction.guild.get_member(int(uid))
            channel = interaction.guild.get_channel(ch_id)
            name = member.display_name if member else f"ID:{uid}"
            ch = channel.mention if channel else "Supprimé"
            members_count = len(channel.members) if channel else 0
            desc += f"👤 **{name}** → {ch} ({members_count} membres)\n"
        embed = discord.Embed(
            title=f"🔊 Vocaux temporaires ({len(vcs)})",
            description=desc,
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

    # ── COMMANDES MEMBRE ─────────────────────────────────────────
    @app_commands.command(name="vc-lock", description="Verrouiller ton vocal")
    async def vc_lock(self, interaction: discord.Interaction):
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        channel_id = tempvc.get(gid, {}).get(str(interaction.user.id))
        if not channel_id:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.connect = False
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message("🔒 Vocal verrouillé !", ephemeral=True)

    @app_commands.command(name="vc-unlock", description="Déverrouiller ton vocal")
    async def vc_unlock(self, interaction: discord.Interaction):
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        channel_id = tempvc.get(gid, {}).get(str(interaction.user.id))
        if not channel_id:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            overwrite = channel.overwrites_for(interaction.guild.default_role)
            overwrite.connect = True
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message("🔓 Vocal déverrouillé !", ephemeral=True)

    @app_commands.command(name="vc-limit", description="Changer la limite de ton vocal")
    async def vc_limit(self, interaction: discord.Interaction, limite: int):
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        channel_id = tempvc.get(gid, {}).get(str(interaction.user.id))
        if not channel_id:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            await channel.edit(user_limit=limite)
            msg = f"✅ Limite : **{limite}** membres" if limite > 0 else "✅ Limite supprimée"
            await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TempVC(bot))
