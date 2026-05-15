"""
cogs/minigames.py
Mini-jeux Discord :
  /trivia     — Question de culture générale (30s)
  /deviner    — Deviner un nombre entre 1 et 100
  /scramble   — Reconstituer un mot mélangé
  /fasttype   — Taper un mot le plus vite possible
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio, random, time

# ── Données ───────────────────────────────────────────────────────
TRIVIA = [
    {"q": "Quelle est la capitale de l'Australie ?", "r": "canberra", "hint": "Ce n'est pas Sydney ni Melbourne."},
    {"q": "Combien de cordes a une guitare classique ?", "r": "6", "hint": "Moins de 10."},
    {"q": "Quel est l'animal le plus rapide du monde ?", "r": "guépard", "hint": "Un félin."},
    {"q": "En quelle année a eu lieu la Révolution française ?", "r": "1789", "hint": "Fin du XVIIIe siècle."},
    {"q": "Quel est le plus grand océan ?", "r": "pacifique", "hint": "Il borde l'Asie et l'Amérique."},
    {"q": "Combien de planètes compte le Système Solaire ?", "r": "8", "hint": "Pluton n'en fait plus partie."},
    {"q": "Qui a peint la Joconde ?", "r": "léonard de vinci", "hint": "Un génie de la Renaissance italienne."},
    {"q": "Quelle est la formule chimique de l'eau ?", "r": "h2o", "hint": "Deux lettres + un chiffre."},
    {"q": "Quel est le pays le plus grand du monde ?", "r": "russie", "hint": "Il s'étend sur 11 fuseaux horaires."},
    {"q": "Dans quel sport utilise-t-on un shuttlecock ?", "r": "badminton", "hint": "Se joue avec une raquette."},
    {"q": "Quelle planète est surnommée la planète rouge ?", "r": "mars", "hint": "4e planète du système solaire."},
    {"q": "Combien font 7 × 8 ?", "r": "56", "hint": "Entre 50 et 60."},
    {"q": "Quelle est la monnaie du Japon ?", "r": "yen", "hint": "Symbole ¥."},
    {"q": "Quel est le plus long fleuve du monde ?", "r": "nil", "hint": "En Afrique."},
    {"q": "Combien de secondes dans une heure ?", "r": "3600", "hint": "60 × 60."},
    {"q": "Quel animal est le symbole de l'Australie ?", "r": "kangourou", "hint": "Il a une poche."},
    {"q": "Quelle est la capitale de l'Espagne ?", "r": "madrid", "hint": "Commence par M."},
    {"q": "Combien de côtés a un hexagone ?", "r": "6", "hint": "Hexa = 6 en grec."},
    {"q": "Quel est le métal le plus conducteur ?", "r": "argent", "hint": "Symbole Ag."},
    {"q": "Qui a écrit 'Les Misérables' ?", "r": "victor hugo", "hint": "Auteur français du XIXe siècle."},
]

WORDS = [
    "discord", "serveur", "moderation", "niveau", "musique",
    "python", "discord", "ticket", "boost", "giveaway",
    "message", "commande", "salon", "membre", "reaction",
    "bienvenue", "bannir", "expulser", "avertissement", "leaderboard",
]

FAST_WORDS = [
    "programmation", "développeur", "intelligence", "ordinateur",
    "clavier", "algorithme", "interface", "protocole", "serveur",
    "javascript", "python", "terminal", "database", "réseau",
]

# Sessions actives par guild
_sessions: dict[int, str] = {}  # guild_id -> type de jeu actif


class MiniGames(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── TRIVIA ───────────────────────────────────────────────────
    @app_commands.command(name="trivia", description="🎯 Question de culture générale — 30 secondes pour répondre !")
    async def trivia(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        if _sessions.get(gid):
            return await interaction.response.send_message(
                f"❌ Un jeu est déjà en cours dans ce serveur (`{_sessions[gid]}`). Attendez qu'il se termine.",
                ephemeral=True
            )

        qa = random.choice(TRIVIA)
        _sessions[gid] = "trivia"

        embed = discord.Embed(
            title="🎯 Trivia !",
            description=f"**{qa['q']}**\n\n⏱ Tu as **30 secondes** pour répondre dans ce salon.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Tape ta réponse directement dans le chat !")
        await interaction.response.send_message(embed=embed)

        # Hint après 15s
        async def send_hint():
            await asyncio.sleep(15)
            if _sessions.get(gid) == "trivia":
                await interaction.channel.send(f"💡 Indice : *{qa['hint']}*", delete_after=15)

        asyncio.create_task(send_hint())

        def check(m: discord.Message):
            return (
                m.channel == interaction.channel
                and not m.author.bot
                and m.content.lower().strip() == qa["r"]
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            embed_win = discord.Embed(
                title="✅ Bonne réponse !",
                description=f"🎉 **{msg.author.mention}** a trouvé : **{qa['r']}** !",
                color=discord.Color.green()
            )
            await interaction.channel.send(embed=embed_win)
        except asyncio.TimeoutError:
            embed_lose = discord.Embed(
                title="⏰ Temps écoulé !",
                description=f"La réponse était : **{qa['r']}**",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=embed_lose)
        finally:
            _sessions.pop(gid, None)

    # ── DEVINER ──────────────────────────────────────────────────
    @app_commands.command(name="deviner", description="🔢 Devine le nombre entre 1 et 100 !")
    async def deviner(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        if _sessions.get(gid):
            return await interaction.response.send_message(
                f"❌ Un jeu est déjà en cours (`{_sessions[gid]}`).", ephemeral=True
            )

        number = random.randint(1, 100)
        _sessions[gid] = "deviner"
        attempts = [0]
        MAX_ATTEMPTS = 7

        embed = discord.Embed(
            title="🔢 Devine le nombre !",
            description=f"J'ai choisi un nombre entre **1 et 100**.\nTu as **{MAX_ATTEMPTS} essais** !",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

        def check(m: discord.Message):
            return (
                m.channel == interaction.channel
                and not m.author.bot
                and m.content.isdigit()
            )

        winner = None
        while attempts[0] < MAX_ATTEMPTS:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                await interaction.channel.send("⏰ Temps écoulé ! La partie est terminée.")
                _sessions.pop(gid, None)
                return

            guess = int(msg.content)
            attempts[0] += 1
            left = MAX_ATTEMPTS - attempts[0]

            if guess == number:
                winner = msg.author
                break
            elif guess < number:
                hint = "📈 **Plus grand !**"
            else:
                hint = "📉 **Plus petit !**"

            if left > 0:
                await msg.reply(f"{hint} (Il te reste **{left}** essai{'s' if left > 1 else ''}.)", delete_after=10)
            else:
                await msg.reply(f"{hint} — Plus d'essais !", delete_after=5)

        if winner:
            embed = discord.Embed(
                title="🎉 Gagné !",
                description=f"**{winner.mention}** a trouvé **{number}** en **{attempts[0]}** essai{'s' if attempts[0]>1 else ''} !",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="💀 Perdu !",
                description=f"Personne n'a trouvé. La réponse était **{number}**.",
                color=discord.Color.red()
            )
        await interaction.channel.send(embed=embed)
        _sessions.pop(gid, None)

    # ── SCRAMBLE ─────────────────────────────────────────────────
    @app_commands.command(name="scramble", description="🔤 Reconstitue le mot mélangé !")
    async def scramble(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        if _sessions.get(gid):
            return await interaction.response.send_message(
                f"❌ Un jeu est déjà en cours (`{_sessions[gid]}`).", ephemeral=True
            )

        word = random.choice(WORDS)
        scrambled = list(word)
        while "".join(scrambled) == word:
            random.shuffle(scrambled)
        scrambled_str = " ".join(scrambled).upper()
        _sessions[gid] = "scramble"

        embed = discord.Embed(
            title="🔤 Scramble !",
            description=f"**Mot mélangé :** `{scrambled_str}`\n\n⏱ 20 secondes pour trouver le mot !",
            color=discord.Color.orange()
        )
        embed.add_field(name="💡 Indice", value=f"Longueur : **{len(word)} lettres**")
        await interaction.response.send_message(embed=embed)

        def check(m: discord.Message):
            return (
                m.channel == interaction.channel
                and not m.author.bot
                and m.content.lower().strip() == word
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=20)
            embed_win = discord.Embed(
                title="✅ Bravo !",
                description=f"🎉 **{msg.author.mention}** a trouvé le mot : **{word}** !",
                color=discord.Color.green()
            )
            await interaction.channel.send(embed=embed_win)
        except asyncio.TimeoutError:
            embed_lose = discord.Embed(
                title="⏰ Temps écoulé !",
                description=f"Le mot était : **{word}**",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=embed_lose)
        finally:
            _sessions.pop(gid, None)

    # ── FASTTYPE ─────────────────────────────────────────────────
    @app_commands.command(name="fasttype", description="⌨️ Tape le mot affiché le plus vite possible !")
    async def fasttype(self, interaction: discord.Interaction):
        gid = interaction.guild.id
        if _sessions.get(gid):
            return await interaction.response.send_message(
                f"❌ Un jeu est déjà en cours (`{_sessions[gid]}`).", ephemeral=True
            )

        word = random.choice(FAST_WORDS)
        _sessions[gid] = "fasttype"

        embed = discord.Embed(
            title="⌨️ Fast Type !",
            description=f"**Tape ce mot exactement :**\n```\n{word}\n```\n⏱ Le plus rapide gagne !",
            color=discord.Color.teal()
        )
        await interaction.response.send_message(embed=embed)
        start = time.time()

        def check(m: discord.Message):
            return (
                m.channel == interaction.channel
                and not m.author.bot
                and m.content.strip() == word
            )

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=30)
            elapsed = round(time.time() - start, 2)
            embed_win = discord.Embed(
                title="⚡ Parfait !",
                description=f"**{msg.author.mention}** a tapé le mot en **{elapsed}s** !",
                color=discord.Color.green()
            )
            await interaction.channel.send(embed=embed_win)
        except asyncio.TimeoutError:
            await interaction.channel.send("⏰ Personne n'a réussi à temps !")
        finally:
            _sessions.pop(gid, None)


async def setup(bot: commands.Bot):
    await bot.add_cog(MiniGames(bot))
