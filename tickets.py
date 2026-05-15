import discord
from discord.ext import commands
from discord import app_commands
import json, os, datetime

CONFIG_FILE = "data/config.json"
TICKETS_FILE = "data/tickets.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE) as f:
        return json.load(f)

def load_tickets():
    if not os.path.exists(TICKETS_FILE):
        return {}
    with open(TICKETS_FILE) as f:
        return json.load(f)

def save_tickets(data):
    os.makedirs("data", exist_ok=True)
    with open(TICKETS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Ouvrir un ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        tickets = load_tickets()
        uid = str(interaction.user.id)

        existing = tickets.get(str(guild.id), {}).get(uid)
        if existing:
            ch = guild.get_channel(existing)
            if ch:
                return await interaction.response.send_message(f"❌ Vous avez déjà un ticket ouvert : {ch.mention}", ephemeral=True)

        config = load_config()
        category_id = config.get(str(guild.id), {}).get("ticket_category")
        category = guild.get_channel(category_id) if category_id else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            category=category,
            topic=f"Ticket de {interaction.user}"
        )

        if str(guild.id) not in tickets:
            tickets[str(guild.id)] = {}
        tickets[str(guild.id)][uid] = channel.id
        save_tickets(tickets)

        embed = discord.Embed(
            title="🎫 Ticket ouvert",
            description=f"Bonjour {interaction.user.mention} !\nDécris ton problème, un modérateur va t'aider.",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        view = CloseTicketView()
        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ton ticket a été créé : {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        tickets = load_tickets()
        gid = str(interaction.guild.id)

        # Trouver et supprimer de la liste
        for uid, cid in list(tickets.get(gid, {}).items()):
            if cid == channel.id:
                del tickets[gid][uid]
                save_tickets(tickets)
                break

        await interaction.response.send_message("🔒 Ce ticket va être fermé dans 5 secondes...")
        import asyncio
        await asyncio.sleep(5)
        await channel.delete(reason="Ticket fermé")

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketButton())
        bot.add_view(CloseTicketView())

    # ── TICKET SETUP ─────────────────────────────────────────────
    @app_commands.command(name="ticket-setup", description="Envoyer le panel de tickets")
    @app_commands.default_permissions(administrator=True)
    async def ticket_setup(self, interaction: discord.Interaction, salon: discord.TextChannel, categorie: discord.CategoryChannel = None):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        if categorie:
            config[gid]["ticket_category"] = categorie.id

        from data_utils import save_config
        import json
        os.makedirs("data", exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)

        embed = discord.Embed(
            title="🎫 Support",
            description="Clique sur le bouton ci-dessous pour ouvrir un ticket.\nUn membre du staff vous répondra rapidement.",
            color=discord.Color.blurple()
        )
        await salon.send(embed=embed, view=TicketButton())
        await interaction.response.send_message(f"✅ Panel de tickets envoyé dans {salon.mention}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
