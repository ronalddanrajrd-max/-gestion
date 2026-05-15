import discord
from discord.ext import commands
from discord import app_commands
import random, aiohttp

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── 8BALL ────────────────────────────────────────────────────
    @app_commands.command(name="8ball", description="Pose une question à la boule magique")
    @app_commands.describe(question="Ta question")
    async def ball(self, interaction: discord.Interaction, question: str):
        reponses = [
            "✅ Oui, absolument !", "✅ C'est certain.", "✅ Sans aucun doute.",
            "✅ Oui, définitivement.", "✅ Tu peux compter dessus.",
            "🤔 Difficile à dire.", "🤔 Repose la question.", "🤔 Concentre-toi et recommence.",
            "❌ Non.", "❌ Je ne le pense pas.", "❌ Certainement pas.", "❌ Mes sources disent non."
        ]
        embed = discord.Embed(
            title="🎱 8Ball",
            description=f"**Question :** {question}\n**Réponse :** {random.choice(reponses)}",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

    # ── COINFLIP ─────────────────────────────────────────────────
    @app_commands.command(name="coinflip", description="Pile ou face ?")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["🪙 **Pile !**", "🪙 **Face !**"])
        await interaction.response.send_message(result)

    # ── DICE ─────────────────────────────────────────────────────
    @app_commands.command(name="dice", description="Lancer un dé")
    @app_commands.describe(faces="Nombre de faces (défaut: 6)")
    async def dice(self, interaction: discord.Interaction, faces: int = 6):
        result = random.randint(1, faces)
        await interaction.response.send_message(f"🎲 Tu as obtenu : **{result}** (d{faces})")

    # ── CHOOSE ───────────────────────────────────────────────────
    @app_commands.command(name="choose", description="Choisir entre plusieurs options")
    @app_commands.describe(options="Options séparées par des virgules")
    async def choose(self, interaction: discord.Interaction, options: str):
        choices = [o.strip() for o in options.split(",")]
        choice = random.choice(choices)
        await interaction.response.send_message(f"🤔 Je choisis : **{choice}** !")

    # ── JOKE ─────────────────────────────────────────────────────
    @app_commands.command(name="joke", description="Une blague aléatoire")
    async def joke(self, interaction: discord.Interaction):
        jokes = [
            ("Pourquoi les plongeurs plongent-ils toujours en arrière ?", "Parce que sinon ils tomberaient dans le bateau !"),
            ("Qu'est-ce qu'un crocodile qui surveille la cour de récré ?", "Un sac à dents !"),
            ("Pourquoi les canards ont-ils des plumes ?", "Pour couvrir leur derrière de canard !"),
            ("Qu'est-ce qu'un chat tombé dans un pot de peinture ?", "Un chat peint !"),
        ]
        setup, punchline = random.choice(jokes)
        embed = discord.Embed(title="😄 Blague", color=discord.Color.yellow())
        embed.add_field(name="Question", value=setup, inline=False)
        embed.add_field(name="Réponse", value=f"||{punchline}||", inline=False)
        await interaction.response.send_message(embed=embed)

    # ── RPS ──────────────────────────────────────────────────────
    @app_commands.command(name="rps", description="Pierre, feuille, ciseaux !")
    @app_commands.choices(choix=[
        app_commands.Choice(name="Pierre 🪨", value="pierre"),
        app_commands.Choice(name="Feuille 📄", value="feuille"),
        app_commands.Choice(name="Ciseaux ✂️", value="ciseaux"),
    ])
    async def rps(self, interaction: discord.Interaction, choix: app_commands.Choice[str]):
        bot_choice = random.choice(["pierre", "feuille", "ciseaux"])
        emojis = {"pierre": "🪨", "feuille": "📄", "ciseaux": "✂️"}
        wins = {"pierre": "ciseaux", "feuille": "pierre", "ciseaux": "feuille"}

        if choix.value == bot_choice:
            result = "🟡 Égalité !"
        elif wins[choix.value] == bot_choice:
            result = "✅ Tu as gagné !"
        else:
            result = "❌ Tu as perdu !"

        embed = discord.Embed(title="🎮 Pierre, Feuille, Ciseaux", color=discord.Color.blurple())
        embed.add_field(name="Toi", value=f"{emojis[choix.value]} {choix.value.capitalize()}")
        embed.add_field(name="Bot", value=f"{emojis[bot_choice]} {bot_choice.capitalize()}")
        embed.add_field(name="Résultat", value=result, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
