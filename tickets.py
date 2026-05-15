import discord
from discord.ext import commands
from discord import app_commands
import json, os, asyncio, datetime

CONFIG_FILE = "data/config.json"
TICKETS_FILE = "data/tickets.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def save_config(data):
    os.makedirs("data", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_tickets():
    if not os.path.exists(TICKETS_FILE):
        return {}
    with open(TICKETS_FILE) as f:
        return json.load(f)

def save_tickets(data):
    os.makedirs("data", exist_ok=True)
    with open(TICKETS_FILE, "w") as f:
        json.dump(data, f, indent=2)


class TicketModal(discord.ui.Modal, title="📩 Ouvrir un ticket"):
    sujet = discord.ui.TextInput(
        label="Sujet",
        placeholder="Ex: Problème avec un rôle, signalement…",
        max_length=100
    )
    description = discord.ui.TextInput(
        label="Description",
        style=discord.TextStyle.paragraph,
        placeholder="Décris ton problème en détail…",
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        tickets = load_tickets()
        uid = str(interaction.user.id)

        existing = tickets.get(str(guild.id), {}).get(uid)
        if existing:
            ch = guild.get_channel(existing)
            if ch:
                return await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket ouvert : {ch.mention}", ephemeral=True
                )

        config = load_config()
        category_id = config.get(str(guild.id), {}).get("ticket_category")
        category = guild.get_channel(category_id) if category_id else None

        # Trouver le rôle staff s'il existe
        staff_role_id = config.get(str(guild.id), {}).get("staff_role")
        staff_role = guild.get_role(staff_role_id) if staff_role_id else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # Numéro de ticket
        total = len(tickets.get(str(guild.id), {})) + 1
        channel = await guild.create_text_channel(
            name=f"ticket-{total:04d}-{interaction.user.name}",
            overwrites=overwrites,
            category=category,
            topic=f"Ticket #{total:04d} | {interaction.user} | {self.sujet.value}"
        )

        if str(guild.id) not in tickets:
            tickets[str(guild.id)] = {}
        tickets[str(guild.id)][uid] = channel.id
        save_tickets(tickets)

        embed = discord.Embed(
            title=f"🎫 Ticket #{total:04d}",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="👤 Créé par", value=interaction.user.mention, inline=True)
        embed.add_field(name="📌 Sujet", value=self.sujet.value, inline=True)
        embed.add_field(name="📝 Description", value=self.description.value, inline=False)
        embed.set_footer(text="Clique sur 🔒 Fermer pour clore ce ticket.")

        mention_text = f"{interaction.user.mention}"
        if staff_role:
            mention_text += f" | {staff_role.mention}"

        await channel.send(content=mention_text, embed=embed, view=CloseTicketView())
        await interaction.response.send_message(
            f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True
        )


class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Ouvrir un ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket_v2")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Vérifier si ticket déjà ouvert
        tickets = load_tickets()
        uid = str(interaction.user.id)
        existing = tickets.get(str(interaction.guild.id), {}).get(uid)
        if existing:
            ch = interaction.guild.get_channel(existing)
            if ch:
                return await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket ouvert : {ch.mention}", ephemeral=True
                )
        await interaction.response.send_modal(TicketModal())


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_v2")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Vérifier si c'est bien un ticket
        tickets = load_tickets()
        gid = str(interaction.guild.id)
        channel = interaction.channel
        owner_id = None

        for uid, cid in list(tickets.get(gid, {}).items()):
            if cid == channel.id:
                owner_id = uid
                break

        if not owner_id:
            return await interaction.response.send_message("❌ Ce n'est pas un ticket valide.", ephemeral=True)

        # Seul le propriétaire ou un modérateur peut fermer
        is_owner = str(interaction.user.id) == owner_id
        is_mod = interaction.user.guild_permissions.manage_channels

        if not is_owner and not is_mod:
            return await interaction.response.send_message("❌ Tu n'as pas la permission de fermer ce ticket.", ephemeral=True)

        await interaction.response.send_message("🔒 Fermeture du ticket dans **5 secondes**...")

        # Sauvegarder transcript
        messages = []
        async for msg in channel.history(limit=200, oldest_first=True):
            if not msg.author.bot:
                messages.append(f"[{msg.created_at.strftime('%H:%M')}] {msg.author}: {msg.content}")

        # Supprimer de la liste
        del tickets[gid][owner_id]
        save_tickets(tickets)

        # Envoyer transcript dans les logs si configuré
        config = load_config()
        logs_id = config.get(gid, {}).get("logs_channel")
        if logs_id and messages:
            logs_ch = interaction.guild.get_channel(logs_id)
            if logs_ch:
                transcript = "\n".join(messages[-50:])  # 50 derniers messages
                embed = discord.Embed(
                    title=f"📋 Transcript — {channel.name}",
                    description=f"```\n{transcript[:3900]}\n```",
                    color=discord.Color.greyple(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_footer(text=f"Fermé par {interaction.user}")
                await logs_ch.send(embed=embed)

        await asyncio.sleep(5)
        await channel.delete(reason=f"Ticket fermé par {interaction.user}")


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketButton())
        bot.add_view(CloseTicketView())

    # ── TICKET SETUP ─────────────────────────────────────────────
    @app_commands.command(name="ticket-setup", description="Envoyer le panel de tickets")
    @app_commands.default_permissions(administrator=True)
    async def ticket_setup(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        categorie: discord.CategoryChannel = None,
        role_staff: discord.Role = None
    ):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        if categorie:
            config[gid]["ticket_category"] = categorie.id
        if role_staff:
            config[gid]["staff_role"] = role_staff.id
        save_config(config)

        embed = discord.Embed(
            title="🎫 Support",
            description=(
                "Besoin d'aide ? Clique sur le bouton ci-dessous pour ouvrir un ticket.\n"
                "Un membre du staff te répondra dans les plus brefs délais. 💙"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Un seul ticket à la fois par membre.")
        await salon.send(embed=embed, view=TicketButton())
        await interaction.response.send_message(
            f"✅ Panel de tickets envoyé dans {salon.mention}", ephemeral=True
        )

    # ── TICKET CLOSE (commande admin) ────────────────────────────
    @app_commands.command(name="ticket-close", description="Forcer la fermeture d'un ticket")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_close(self, interaction: discord.Interaction):
        tickets = load_tickets()
        gid = str(interaction.guild.id)
        channel = interaction.channel

        for uid, cid in list(tickets.get(gid, {}).items()):
            if cid == channel.id:
                del tickets[gid][uid]
                save_tickets(tickets)
                await interaction.response.send_message("🔒 Ticket fermé par un administrateur.")
                await asyncio.sleep(3)
                await channel.delete(reason=f"Ticket forcé par {interaction.user}")
                return

        await interaction.response.send_message("❌ Ce salon n'est pas un ticket.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
