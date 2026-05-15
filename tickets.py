import discord
from discord.ext import commands
from discord import app_commands
import json, os, datetime, asyncio

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

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fermer le ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_v2")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        tickets = load_tickets()
        gid = str(interaction.guild.id)
        for uid, cid in list(tickets.get(gid, {}).items()):
            if cid == channel.id:
                del tickets[gid][uid]
                save_tickets(tickets)
                break
        await interaction.response.send_message("🔒 Fermeture dans 5 secondes...")
        await asyncio.sleep(5)
        try:
            await channel.delete(reason="Ticket fermé")
        except Exception:
            pass

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Ouvrir un ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket_v2")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        tickets = load_tickets()
        uid = str(interaction.user.id)
        gid = str(guild.id)

        existing = tickets.get(gid, {}).get(uid)
        if existing:
            ch = guild.get_channel(existing)
            if ch:
                return await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket : {ch.mention}", ephemeral=True
                )

        config = load_config()
        category_id = config.get(gid, {}).get("ticket_category")
        category = guild.get_channel(category_id) if category_id else None
        support_role_id = config.get(gid, {}).get("ticket_support_role")
        support_role = guild.get_role(support_role_id) if support_role_id else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            channel = await guild.create_text_channel(
                name=f"ticket-{interaction.user.name}",
                overwrites=overwrites,
                category=category,
                topic=f"Ticket de {interaction.user}"
            )
        except Exception as e:
            return await interaction.response.send_message(f"❌ Erreur création ticket : {e}", ephemeral=True)

        if gid not in tickets:
            tickets[gid] = {}
        tickets[gid][uid] = channel.id
        save_tickets(tickets)

        embed = discord.Embed(
            title="🎫 Ticket ouvert",
            description=(
                f"Bonjour {interaction.user.mention} ! 👋\n\n"
                "Décris ton problème et le staff te répondra.\n"
                "Clique **🔒 Fermer** quand c'est résolu."
            ),
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Ticket de {interaction.user}")
        view = CloseTicketView()
        ping = support_role.mention if support_role else ""
        await channel.send(content=ping, embed=embed, view=view)
        await interaction.response.send_message(f"✅ Ticket créé : {channel.mention}", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketButton())
        bot.add_view(CloseTicketView())

    @app_commands.command(name="ticket-setup", description="Envoyer le panel de tickets")
    @app_commands.default_permissions(administrator=True)
    async def ticket_setup(self, interaction: discord.Interaction, salon: discord.TextChannel, categorie: discord.CategoryChannel = None):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        if categorie:
            config[gid]["ticket_category"] = categorie.id
        save_config(config)
        embed = discord.Embed(
            title="🎫 Support",
            description="Clique sur le bouton pour ouvrir un ticket privé. ✅",
            color=discord.Color.blurple()
        )
        await salon.send(embed=embed, view=TicketButton())
        await interaction.response.send_message(f"✅ Panel envoyé dans {salon.mention}", ephemeral=True)

    @app_commands.command(name="ticket-role", description="Rôle staff qui voit les tickets")
    @app_commands.default_permissions(administrator=True)
    async def ticket_role(self, interaction: discord.Interaction, role: discord.Role):
        config = load_config()
        gid = str(interaction.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid]["ticket_support_role"] = role.id
        save_config(config)
        await interaction.response.send_message(f"✅ Rôle support : **{role.name}**")

    @app_commands.command(name="ticket-add", description="Ajouter un membre au ticket")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_add(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.channel.set_permissions(membre, read_messages=True, send_messages=True)
        await interaction.response.send_message(f"✅ **{membre}** ajouté.")

    @app_commands.command(name="ticket-remove", description="Retirer un membre du ticket")
    @app_commands.default_permissions(manage_channels=True)
    async def ticket_remove(self, interaction: discord.Interaction, membre: discord.Member):
        await interaction.channel.set_permissions(membre, read_messages=False)
        await interaction.response.send_message(f"✅ **{membre}** retiré.")

async def setup(bot):
    await bot.add_cog(Tickets(bot))
