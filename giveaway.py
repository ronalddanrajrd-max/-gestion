import discord
from discord.ext import commands
from discord import app_commands
import asyncio, random, datetime, json, os

GIVEAWAYS_FILE = "data/giveaways.json"

def load_giveaways():
    if not os.path.exists(GIVEAWAYS_FILE):
        return {}
    with open(GIVEAWAYS_FILE) as f:
        return json.load(f)

def save_giveaways(data):
    os.makedirs("data", exist_ok=True)
    with open(GIVEAWAYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ── GIVEAWAY START ───────────────────────────────────────────
    @app_commands.command(name="giveaway-start", description="Lancer un giveaway")
    @app_commands.describe(duree="Durée en minutes", gagnants="Nombre de gagnants", prix="Lot à gagner")
    @app_commands.default_permissions(manage_guild=True)
    async def giveaway_start(self, interaction: discord.Interaction, duree: int, gagnants: int, prix: str):
        end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=duree)
        embed = discord.Embed(
            title=f"🎉 GIVEAWAY — {prix}",
            description=(
                f"Réagis avec 🎉 pour participer !\n\n"
                f"⏰ **Fin :** <t:{int(end_time.timestamp())}:R>\n"
                f"🏆 **Gagnants :** {gagnants}\n"
                f"🎁 **Prix :** {prix}\n"
                f"👤 **Organisé par :** {interaction.user.mention}"
            ),
            color=discord.Color.gold(),
            timestamp=end_time
        )
        embed.set_footer(text="Se termine le")
        await interaction.response.send_message("✅ Giveaway lancé !", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("🎉")

        giveaways = load_giveaways()
        giveaways[str(msg.id)] = {
            "channel_id": interaction.channel.id,
            "gagnants": gagnants,
            "prix": prix,
            "end_time": end_time.isoformat(),
            "organisateur": str(interaction.user),
            "termine": False
        }
        save_giveaways(giveaways)

        await asyncio.sleep(duree * 60)
        await self._end_giveaway(msg.id, interaction.channel.id, gagnants, prix)

    async def _end_giveaway(self, msg_id, channel_id, nb_gagnants, prix):
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return
        try:
            msg = await channel.fetch_message(msg_id)
        except Exception:
            return

        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        if not reaction:
            await channel.send("❌ Personne n'a participé au giveaway.")
            return

        users = [u async for u in reaction.users() if not u.bot]
        if not users:
            await channel.send("❌ Aucun participant valide.")
            return

        winners = random.sample(users, min(nb_gagnants, len(users)))
        mentions = ", ".join(w.mention for w in winners)

        embed = discord.Embed(
            title="🎉 Giveaway terminé !",
            description=f"**Prix :** {prix}\n**Gagnant(s) :** {mentions}",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
        await channel.send(f"🎊 Félicitations {mentions} ! Vous avez gagné **{prix}** !")

        giveaways = load_giveaways()
        if str(msg_id) in giveaways:
            giveaways[str(msg_id)]["termine"] = True
            save_giveaways(giveaways)

    # ── GIVEAWAY REROLL ──────────────────────────────────────────
    @app_commands.command(name="giveaway-reroll", description="Retirer un nouveau gagnant")
    @app_commands.describe(message_id="ID du message du giveaway")
    @app_commands.default_permissions(manage_guild=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            users = [u async for u in reaction.users() if not u.bot]
            winner = random.choice(users)
            await interaction.response.send_message(f"🎉 Nouveau gagnant : {winner.mention} !")
        except Exception:
            await interaction.response.send_message("❌ Message introuvable.", ephemeral=True)

    # ── POLL ─────────────────────────────────────────────────────
    @app_commands.command(name="poll", description="Créer un sondage")
    @app_commands.describe(question="La question du sondage")
    async def poll(self, interaction: discord.Interaction, question: str):
        embed = discord.Embed(
            title="📊 Sondage",
            description=question,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Sondage par {interaction.user}")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

    # ── SUGGEST ──────────────────────────────────────────────────
    @app_commands.command(name="suggest", description="Envoyer une suggestion")
    @app_commands.describe(suggestion="Ta suggestion")
    async def suggest(self, interaction: discord.Interaction, suggestion: str):
        from data_utils import load_config
        import json
        config_file = "data/config.json"
        if os.path.exists(config_file):
            with open(config_file) as f:
                config = json.load(f)
        else:
            config = {}
        channel_id = config.get(str(interaction.guild.id), {}).get("suggest_channel")
        channel = interaction.guild.get_channel(channel_id) if channel_id else interaction.channel

        embed = discord.Embed(
            title="💡 Nouvelle suggestion",
            description=suggestion,
            color=discord.Color.yellow()
        )
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.response.send_message("✅ Suggestion envoyée !", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
