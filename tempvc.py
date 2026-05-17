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
        select = discord.ui.Select(placeholder="Choisis un membre à expulser", options=options)
        select.callback = self.kick_member
        self.add_item(select)

    async def kick_member(self, interaction: discord.Interaction):
        uid = int(interaction.data["values"][0])
        member = interaction.guild.get_member(uid)
        if member and member.voice and member.voice.channel == self.channel:
            await member.move_to(None, reason="Expulsé du vocal temporaire")
            await interaction.response.send_message(f"👢 **{member.display_name}** expulsé !", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ce membre n'est plus dans le vocal.", ephemeral=True)

class TempVCControlView(discord.ui.View):
    """Panel de contrôle envoyé dans le chat du vocal"""
    def __init__(self):
        super().__init__(timeout=None)

    def get_owner_channel(self, interaction):
        """Récupérer le vocal du membre qui clique"""
        tempvc = load_tempvc()
        gid = str(interaction.guild.id)
        uid = str(interaction.user.id)
        channel_id = tempvc.get(gid, {}).get(uid)
        if not channel_id:
            return None
        return interaction.guild.get_channel(channel_id)

    @discord.ui.button(label="✏️ Renommer", style=discord.ButtonStyle.primary, custom_id="vc_rename_v2", row=0)
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = self.get_owner_channel(interaction)
        if not channel:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        if interaction.channel.id != channel.id:
            return await interaction.response.send_message("❌ Utilise ce bouton dans ton vocal.", ephemeral=True)
        await interaction.response.send_modal(RenameModal(channel))

    @discord.ui.button(label="👥 Limite", style=discord.ButtonStyle.secondary, custom_id="vc_limit_v2", row=0)
    async def limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = self.get_owner_channel(interaction)
        if not channel:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        if interaction.channel.id != channel.id:
            return await interaction.response.send_message("❌ Utilise ce bouton dans ton vocal.", ephemeral=True)
        await interaction.response.send_modal(LimitModal(channel))

    @discord.ui.button(label="🔒 Verrouiller", style=discord.ButtonStyle.danger, custom_id="vc_lock_v2", row=0)
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = self.get_owner_channel(interaction)
        if not channel:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        if interaction.channel.id != channel.id:
            return await interaction.response.send_message("❌ Utilise ce bouton dans ton vocal.", ephemeral=True)
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.connect = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔒 Vocal verrouillé !", ephemeral=True)

    @discord.ui.button(label="🔓 Déverrouiller", style=discord.ButtonStyle.success, custom_id="vc_unlock_v2", row=0)
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = self.get_owner_channel(interaction)
        if not channel:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        if interaction.channel.id != channel.id:
            return await interaction.response.send_message("❌ Utilise ce bouton dans ton vocal.", ephemeral=True)
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.connect = True
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 Vocal déverrouillé !", ephemeral=True)

    @discord.ui.button(label="👢 Expulser", style=discord.ButtonStyle.danger, custom_id="vc_kick_v2", row=1)
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = self.get_owner_channel(interaction)
        if not channel:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        if interaction.channel.id != channel.id:
            return await interaction.response.send_message("❌ Utilise ce bouton dans ton vocal.", ephemeral=True)
        members = [m for m in channel.members if m.id != interaction.user.id]
        if not members:
            return await interaction.response.send_message("❌ Personne à expulser.", ephemeral=True)
        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in members]
        view = KickSelectView(channel, options)
        await interaction.response.send_message("👢 Qui veux-tu expulser ?", view=view, ephemeral=True)

    @discord.ui.button(label="🔇 Mute tous", style=discord.ButtonStyle.secondary, custom_id="vc_muteall_v2", row=1)
    async def muteall(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = self.get_owner_channel(interaction)
        if not channel:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        if interaction.channel.id != channel.id:
            return await interaction.response.send_message("❌ Utilise ce bouton dans ton vocal.", ephemeral=True)
        for member in channel.members:
            if member.id != interaction.user.id:
                try:
                    await member.edit(mute=True)
                except Exception:
                    pass
        await interaction.response.send_message("🔇 Tous les membres ont été mutés !", ephemeral=True)

    @discord.ui.button(label="🔊 Unmute tous", style=discord.ButtonStyle.success, custom_id="vc_unmuteall_v2", row=1)
    async def unmuteall(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = self.get_owner_channel(interaction)
        if not channel:
            return await interaction.response.send_message("❌ Tu n'as pas de vocal actif.", ephemeral=True)
        if interaction.channel.id != channel.id:
            return await interaction.response.send_message("❌ Utilise ce bouton dans ton vocal.", ephemeral=True)
        for member in channel.members:
            try:
                await member.edit(mute=False)
            except Exception:
                pass
        await interaction.response.send_message("🔊 Tous les membres sont unmutés !", ephemeral=True)

class TempVC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TempVCControlView())

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
            try:
                channel = await member.guild.create_voice_channel(
                    name=f"🎮 {member.display_name}",
                    category=category,
                    user_limit=0
                )
                # Donner les permissions au créateur
                await channel.set_permissions(
                    member,
                    connect=True,
                    manage_channels=True,
                    move_members=True,
                    mute_members=True
                )
                # Déplacer le membre dans son vocal
                await member.move_to(channel)
            except Exception as e:
                print(f"Erreur création vocal temp: {e}")
                return

            # Sauvegarder
            tempvc = load_tempvc()
            if gid not in tempvc:
                tempvc[gid] = {}
            tempvc[gid][str(member.id)] = channel.id
            save_tempvc(tempvc)

            # Envoyer le panel dans le CHAT DU VOCAL
            try:
                embed = discord.Embed(
                    title="🎛️ Panel de contrôle",
                    description=(
                        f"👋 Bienvenue {member.mention} dans ton vocal !\n\n"
                        f"**Utilise les boutons ci-dessous pour gérer ton salon :**\n\n"
                        f"✏️ **Renommer** — Changer le nom\n"
                        f"👥 **Limite** — Limiter le nombre de membres\n"
                        f"🔒 **Verrouiller** — Empêcher les nouveaux d'entrer\n"
                        f"🔓 **Déverrouiller** — Rouvrir le salon\n"
                        f"👢 **Expulser** — Mettre quelqu'un dehors\n"
                        f"🔇 **Mute tous** — Muter tout le monde\n"
                        f"🔊 **Unmute tous** — Unmuter tout le monde"
                    ),
                    color=discord.Color.blurple()
                )
                embed.set_footer(text=f"Salon créé par {member.display_name}")
                await channel.send(embed=embed, view=TempVCControlView())
            except Exception as e:
                print(f"Erreur envoi panel: {e}")

        # Quitter → supprimer si vide
        if before.channel and before.channel.id != create_channel_id:
            tempvc = load_tempvc()
            gid_str = str(member.guild.id)
            for owner_id, ch_id in list(tempvc.get(gid_str, {}).items()):
                if before.channel.id == ch_id and len(before.channel.members) == 0:
                    try:
                        await before.channel.delete(reason="Vocal temporaire vide")
                    except Exception:
                        pass
                    del tempvc[gid_str][owner_id]
                    save_tempvc(tempvc)
                    break

    # ── SETUP ────────────────────────────────────────────────────
    @app_commands.command(name="tempvc-setup", description="Configurer le système de vocaux temporaires")
    @app_commands.describe(
        salon_creation="Salon vocal à rejoindre pour créer un vc",
        categorie="Catégorie où créer les vocaux (optionnel)"
    )
    async def tempvc_setup(self, interaction: discord.Interaction, salon_creation: discord.VoiceChannel, categorie: discord.CategoryChannel = None):
        if not interaction.user.guild_permissions.administrator and not is_owner(interaction.user.id):
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["tempvc_create"] = salon_creation.id
        if categorie:
            config[gid]["tempvc_category"] = categorie.id
        save_config(config)
        embed = discord.Embed(
            title="✅ Vocaux temporaires configurés !",
            description=(
                f"🔊 **Salon création :** {salon_creation.mention}\n\n"
                f"Les membres rejoignent ce salon pour créer leur propre vocal.\n"
                f"Le panel de contrôle apparaît directement dans le chat du vocal !"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # ── COMMANDES ADMIN ──────────────────────────────────────────
    @app_commands.command(name="vc-delete", description="Supprimer le vocal d'un membre [ADMIN]")
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
            await channel.delete(reason=f"Supprimé par {interaction.user}")
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
            old_limit = channel.user_limit
            await channel.edit(user_limit=0)
            await interaction.response.send_message(f"✅ Rejoins {channel.mention} maintenant !", ephemeral=True)
            await asyncio.sleep(15)
            await channel.edit(user_limit=old_limit)

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
            count = len(channel.members) if channel else 0
            desc += f"👤 **{name}** → {ch} ({count} membres)\n"
        embed = discord.Embed(title=f"🔊 Vocaux actifs ({len(vcs)})", description=desc, color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TempVC(bot))

