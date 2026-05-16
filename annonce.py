import discord
from discord.ext import commands
from discord import app_commands

OWNER_ID = 1467602579482480821

class Annonce(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── ANNONCE SIMPLE ───────────────────────────────────────────
    @app_commands.command(name="annonce", description="Faire une annonce stylée")
    @app_commands.describe(
        salon="Salon où envoyer l'annonce",
        titre="Titre de l'annonce",
        contenu="Contenu de l'annonce (utilise \\n pour les sauts de ligne)",
        couleur="Couleur (red, blue, green, gold, purple, orange)",
        image="URL d'une image à afficher",
        mention="Mentionner @everyone ou @here ?"
    )
    @app_commands.choices(
        couleur=[
            app_commands.Choice(name="🔴 Rouge", value="red"),
            app_commands.Choice(name="🔵 Bleu", value="blue"),
            app_commands.Choice(name="🟢 Vert", value="green"),
            app_commands.Choice(name="🟡 Or", value="gold"),
            app_commands.Choice(name="🟣 Violet", value="purple"),
            app_commands.Choice(name="🟠 Orange", value="orange"),
            app_commands.Choice(name="⚫ Noir", value="dark"),
        ],
        mention=[
            app_commands.Choice(name="@everyone", value="everyone"),
            app_commands.Choice(name="@here", value="here"),
            app_commands.Choice(name="Aucune", value="none"),
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    async def annonce(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        titre: str,
        contenu: str,
        couleur: app_commands.Choice[str] = None,
        image: str = None,
        mention: app_commands.Choice[str] = None
    ):
        if interaction.user.id != OWNER_ID and not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)

        # Couleur
        colors = {
            "red": discord.Color.red(),
            "blue": discord.Color.blue(),
            "green": discord.Color.green(),
            "gold": discord.Color.gold(),
            "purple": discord.Color.purple(),
            "orange": discord.Color.orange(),
            "dark": discord.Color.dark_theme(),
        }
        color = colors.get(couleur.value if couleur else "blue", discord.Color.blue())

        # Contenu avec sauts de ligne
        contenu_formate = contenu.replace("\\n", "\n")

        embed = discord.Embed(
            title=titre,
            description=contenu_formate,
            color=color
        )
        embed.set_author(
            name=f"By {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        if image:
            embed.set_thumbnail(url=image)
        embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

        # Mention
        ping = ""
        if mention and mention.value == "everyone":
            ping = "@everyone"
        elif mention and mention.value == "here":
            ping = "@here"

        await salon.send(content=ping if ping else None, embed=embed)
        await interaction.response.send_message(f"✅ Annonce envoyée dans {salon.mention} !", ephemeral=True)

    # ── REGLEMENT ────────────────────────────────────────────────
    @app_commands.command(name="reglement", description="Afficher le règlement du serveur")
    @app_commands.describe(
        salon="Salon où envoyer le règlement",
        regles="Les règles séparées par | (ex: Respecte les autres|Pas d'insultes)",
        image="URL d'une image (optionnel)"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def reglement(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        regles: str,
        image: str = None
    ):
        if interaction.user.id != OWNER_ID and not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)

        liste = regles.split("|")
        contenu = "📋 **RÈGLEMENT**\n\n"
        for i, regle in enumerate(liste, 1):
            contenu += f"**{i}** {regle.strip()}\n"

        embed = discord.Embed(
            title="📋 Règlement !",
            description=contenu,
            color=discord.Color.blurple()
        )
        embed.set_author(
            name=f"By {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        if image:
            embed.set_thumbnail(url=image)
        embed.set_footer(text=interaction.guild.name)

        await salon.send(embed=embed)
        await interaction.response.send_message(f"✅ Règlement envoyé dans {salon.mention} !", ephemeral=True)

    # ── EMBED CUSTOM ─────────────────────────────────────────────
    @app_commands.command(name="embed", description="Créer un embed 100% personnalisé")
    @app_commands.describe(
        salon="Salon cible",
        titre="Titre",
        description="Description",
        couleur_hex="Couleur en hex (ex: ff0000 pour rouge)",
        image_url="URL image principale",
        thumbnail_url="URL miniature (coin haut droite)",
        footer="Texte du footer"
    )
    @app_commands.default_permissions(manage_guild=True)
    async def embed_cmd(
        self,
        interaction: discord.Interaction,
        salon: discord.TextChannel,
        titre: str,
        description: str,
        couleur_hex: str = "5865f2",
        image_url: str = None,
        thumbnail_url: str = None,
        footer: str = None
    ):
        if interaction.user.id != OWNER_ID and not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)

        try:
            color = discord.Color(int(couleur_hex.replace("#", ""), 16))
        except Exception:
            color = discord.Color.blurple()

        desc = description.replace("\\n", "\n")
        embed = discord.Embed(title=titre, description=desc, color=color)

        if image_url:
            embed.set_image(url=image_url)
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        if footer:
            embed.set_footer(text=footer)

        await salon.send(embed=embed)
        await interaction.response.send_message("✅ Embed envoyé !", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Annonce(bot))
