import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        node = wavelink.Node(
    uri='http://lavalink.clxud.eu:2333',
    password='youshallnotpass'
        )
        await wavelink.Pool.connect(nodes=[node], client=self.bot)

    @app_commands.command(name="play", description="Jouer une musique")
    @app_commands.describe(recherche="Titre ou URL")
    async def play(self, interaction: discord.Interaction, recherche: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ Rejoins un salon vocal d'abord !", ephemeral=True)

        await interaction.response.defer()

        vc: wavelink.Player = interaction.guild.voice_client

        if not vc:
            vc = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        elif vc.channel != interaction.user.voice.channel:
            await vc.move_to(interaction.user.voice.channel)

        vc.autoplay = wavelink.AutoPlayMode.partial

        tracks = await wavelink.Playable.search(recherche)
        if not tracks:
            return await interaction.followup.send("❌ Aucune musique trouvée !")

        track = tracks[0]
        await vc.queue.put_wait(track)

        if not vc.playing:
            await vc.play(vc.queue.get())

        embed = discord.Embed(
            title="🎵 Ajouté à la file",
            description=f"**{track.title}** — {track.author}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="skip", description="Passer la musique en cours")
    async def skip(self, interaction: discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or not vc.playing:
            return await interaction.response.send_message("❌ Rien en cours.", ephemeral=True)
        await vc.skip()
        await interaction.response.send_message("⏭️ Musique passée !")

    @app_commands.command(name="stop", description="Arrêter la musique et déconnecter")
    async def stop(self, interaction: discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("❌ Pas connecté à un vocal.", ephemeral=True)
        await vc.disconnect()
        await interaction.response.send_message("⏹️ Musique arrêtée et bot déconnecté.")

    @app_commands.command(name="pause", description="Mettre en pause")
    async def pause(self, interaction: discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or not vc.playing:
            return await interaction.response.send_message("❌ Rien en cours.", ephemeral=True)
        await vc.pause(not vc.paused)
        état = "⏸️ En pause." if vc.paused else "▶️ Reprise !"
        await interaction.response.send_message(état)

    @app_commands.command(name="resume", description="Reprendre la musique")
    async def resume(self, interaction: discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or not vc.paused:
            return await interaction.response.send_message("❌ Pas en pause.", ephemeral=True)
        await vc.pause(False)
        await interaction.response.send_message("▶️ Musique reprise !")

    @app_commands.command(name="queue", description="Voir la file d'attente")
    async def queue(self, interaction: discord.Interaction):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc or vc.queue.is_empty:
            return await interaction.response.send_message("📋 La file est vide.")
        desc = "\n".join([f"**{i+1}.** {t.title}" for i, t in enumerate(vc.queue)])
        embed = discord.Embed(title="📋 File d'attente", description=desc, color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Changer le volume (0-100)")
    async def volume(self, interaction: discord.Interaction, niveau: int):
        vc: wavelink.Player = interaction.guild.voice_client
        if not vc:
            return await interaction.response.send_message("❌ Rien en cours.", ephemeral=True)
        if not 0 <= niveau <= 100:
            return await interaction.response.send_message("❌ Entre 0 et 100.", ephemeral=True)
        await vc.set_volume(niveau)
        await interaction.response.send_message(f"🔊 Volume : **{niveau}%**")

async def setup(bot):
    await bot.add_cog(Music(bot))
