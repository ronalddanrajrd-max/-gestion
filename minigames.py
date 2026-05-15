import discord
from discord.ext import commands
from discord import app_commands
import random, asyncio

class MiniGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trivia_actif = {}
        self.wordgame_actif = {}

    # ── DEVINER LE NOMBRE ────────────────────────────────────────
    @app_commands.command(name="deviner", description="Devine un nombre entre 1 et 100 !")
    async def deviner(self, interaction: discord.Interaction):
        nombre = random.randint(1, 100)
        tentatives = 7
        await interaction.response.send_message(
            f"🎮 J'ai choisi un nombre entre **1 et 100**.\nTu as **{tentatives} tentatives** ! Réponds avec un nombre."
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit()

        for i in range(tentatives):
            try:
                msg = await self.bot.wait_for("message", timeout=30.0, check=check)
                guess = int(msg.content)
                restant = tentatives - i - 1

                if guess == nombre:
                    await interaction.channel.send(f"🎉 **Bravo {interaction.user.mention} !** Tu as trouvé **{nombre}** en {i+1} tentative(s) !")
                    return
                elif guess < nombre:
                    await interaction.channel.send(f"📈 **Plus grand !** ({restant} tentative(s) restante(s))")
                else:
                    await interaction.channel.send(f"📉 **Plus petit !** ({restant} tentative(s) restante(s))")
            except asyncio.TimeoutError:
                await interaction.channel.send(f"⏰ Temps écoulé ! Le nombre était **{nombre}**.")
                return

        await interaction.channel.send(f"❌ Tu as épuisé tes tentatives ! Le nombre était **{nombre}**.")

    # ── TRIVIA ───────────────────────────────────────────────────
    @app_commands.command(name="trivia", description="Question culture générale !")
    async def trivia(self, interaction: discord.Interaction):
        questions = [
            {"q": "Quelle est la capitale de la France ?", "r": "paris", "choices": ["Paris", "Lyon", "Marseille", "Bordeaux"]},
            {"q": "Combien font 7 x 8 ?", "r": "56", "choices": ["54", "56", "58", "64"]},
            {"q": "Quel est le plus grand océan du monde ?", "r": "pacifique", "choices": ["Atlantique", "Indien", "Pacifique", "Arctique"]},
            {"q": "En quelle année a été créé Discord ?", "r": "2015", "choices": ["2013", "2014", "2015", "2016"]},
            {"q": "Quelle planète est la plus proche du soleil ?", "r": "mercure", "choices": ["Vénus", "Mercure", "Mars", "Terre"]},
            {"q": "Combien de côtés a un hexagone ?", "r": "6", "choices": ["5", "6", "7", "8"]},
            {"q": "Qui a peint la Joconde ?", "r": "leonard de vinci", "choices": ["Picasso", "Michel-Ange", "Léonard de Vinci", "Raphaël"]},
        ]

        q = random.choice(questions)
        random.shuffle(q["choices"])

        embed = discord.Embed(
            title="🧠 Trivia",
            description=q["q"],
            color=discord.Color.blue()
        )
        for i, c in enumerate(q["choices"]):
            embed.add_field(name=f"{['🅰️','🅱️','🆎','🆑'][i]}", value=c, inline=True)
        embed.set_footer(text="Tu as 15 secondes pour répondre !")

        await interaction.response.send_message(embed=embed)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await self.bot.wait_for("message", timeout=15.0, check=check)
            if msg.content.lower() in q["r"].lower() or q["r"].lower() in msg.content.lower():
                await interaction.channel.send(f"✅ **Bonne réponse {interaction.user.mention} !** C'était bien **{q['choices'][[c.lower() for c in q['choices']].index(q['r']) if q['r'] in [c.lower() for c in q['choices']] else 0]}**.")
            else:
                await interaction.channel.send(f"❌ **Mauvaise réponse !** La bonne réponse était **{q['r'].capitalize()}**.")
        except asyncio.TimeoutError:
            await interaction.channel.send(f"⏰ Temps écoulé ! La réponse était **{q['r'].capitalize()}**.")

    # ── PIERRE FEUILLE CISEAUX MULTIJOUEUR ──────────────────────
    @app_commands.command(name="duel", description="Défie un autre membre au Pierre Feuille Ciseaux !")
    async def duel(self, interaction: discord.Interaction, adversaire: discord.Member):
        if adversaire.bot or adversaire == interaction.user:
            return await interaction.response.send_message("❌ Choisis un vrai membre !", ephemeral=True)

        await interaction.response.send_message(
            f"⚔️ **{interaction.user.mention}** défie **{adversaire.mention}** au Pierre Feuille Ciseaux !\n"
            f"{adversaire.mention} réponds avec `pierre`, `feuille` ou `ciseaux` en 20 secondes !"
        )

        choix_initiateur = random.choice(["pierre", "feuille", "ciseaux"])
        await interaction.user.send(f"🎮 Ton choix dans le duel : **{choix_initiateur}** (choix aléatoire pour ce mode)")

        def check(m):
            return m.author == adversaire and m.channel == interaction.channel and m.content.lower() in ["pierre", "feuille", "ciseaux"]

        try:
            msg = await self.bot.wait_for("message", timeout=20.0, check=check)
            choix_adversaire = msg.content.lower()
            wins = {"pierre": "ciseaux", "feuille": "pierre", "ciseaux": "feuille"}
            emojis = {"pierre": "🪨", "feuille": "📄", "ciseaux": "✂️"}

            if choix_initiateur == choix_adversaire:
                result = "🟡 Égalité !"
                winner = None
            elif wins[choix_initiateur] == choix_adversaire:
                result = f"🏆 **{interaction.user.mention}** gagne !"
                winner = interaction.user
            else:
                result = f"🏆 **{adversaire.mention}** gagne !"
                winner = adversaire

            embed = discord.Embed(title="⚔️ Résultat du duel", color=discord.Color.gold())
            embed.add_field(name=str(interaction.user), value=f"{emojis[choix_initiateur]} {choix_initiateur.capitalize()}")
            embed.add_field(name=str(adversaire), value=f"{emojis[choix_adversaire]} {choix_adversaire.capitalize()}")
            embed.add_field(name="Résultat", value=result, inline=False)
            await interaction.channel.send(embed=embed)

        except asyncio.TimeoutError:
            await interaction.channel.send(f"⏰ **{adversaire.mention}** n'a pas répondu à temps. **{interaction.user.mention}** gagne par forfait !")

    # ── MOT MYSTERE ──────────────────────────────────────────────
    @app_commands.command(name="motmystere", description="Devine le mot caché lettre par lettre !")
    async def motmystere(self, interaction: discord.Interaction):
        mots = ["discord", "python", "musique", "serveur", "moderation", "giveaway", "booster", "commande"]
        mot = random.choice(mots)
        trouve = ["_"] * len(mot)
        essais = 6
        lettres_essayees = []

        def afficher():
            return " ".join(trouve) + f"\n\nEssais restants : {'❤️' * essais}{'🖤' * (6 - essais)}\nLettres essayées : {', '.join(lettres_essayees) or 'aucune'}"

        await interaction.response.send_message(f"🔤 **Mot Mystère** — {len(mot)} lettres\n\n{afficher()}")

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and len(m.content) == 1 and m.content.isalpha()

        while essais > 0 and "_" in trouve:
            try:
                msg = await self.bot.wait_for("message", timeout=30.0, check=check)
                lettre = msg.content.lower()

                if lettre in lettres_essayees:
                    await interaction.channel.send(f"⚠️ Tu as déjà essayé **{lettre}** !", delete_after=3)
                    continue

                lettres_essayees.append(lettre)

                if lettre in mot:
                    for i, c in enumerate(mot):
                        if c == lettre:
                            trouve[i] = lettre
                    await interaction.channel.send(f"✅ Bonne lettre !\n{afficher()}")
                else:
                    essais -= 1
                    await interaction.channel.send(f"❌ La lettre **{lettre}** n'est pas dans le mot.\n{afficher()}")

            except asyncio.TimeoutError:
                await interaction.channel.send(f"⏰ Temps écoulé ! Le mot était **{mot}**.")
                return

        if "_" not in trouve:
            await interaction.channel.send(f"🎉 **Bravo {interaction.user.mention} !** Tu as trouvé le mot **{mot}** !")
        else:
            await interaction.channel.send(f"💀 Perdu ! Le mot était **{mot}**.")

async def setup(bot):
    await bot.add_cog(MiniGames(bot))
