import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
from collections import deque

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'cookiefile': 'cookies.txt',
}

queues = {}

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = deque()
    return queues[guild_id]

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_next(self, channel, guild):
        queue = get_queue(guild.id)
        vc = guild.voice_client
        if not vc or not queue:
            return
        url, title = queue.popleft()
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        vc.play(
            discord.PCMVolumeTransformer(source, volume=0.5),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(channel, guild), self.bot.loop
            )
        )
        embed = discord.Embed(
            title="🎵 En cours de lecture",
            description=f"**{title}**",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)

    @app_commands.command(name="play", description="Jouer une musique depuis YouTube")
    @app_commands.describe(recherche="Titre ou URL YouTube")
    async def play(self, interaction: discord.Interaction, recherche: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ Rejoins un salon vocal d'abord !", ephemeral=True)

        await interaction.response.defer()

        vc = interaction.guild.voice_client
        voice_channel = interaction.user.voice.channel

        try:
            if vc is None:
                vc = await voice_channel.connect()
            elif vc.channel != voice_channel:
                await vc.move_to(voice_channel)
        except Exception as e:
            return await interaction.followup.send(f"❌ Impossible de rejoindre le vocal : {e}")

        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                if not recherche.startswith("http"):
                    recherche = f"ytsearch:{recherche}"
                info = ydl.extract_info(recherche, download=False)
                if "entries" in info:
                    info = info["entries"][0]
                url = info["url"]
                title = info.get("title", "Titre inconnu")
        except Exception as e:
            return await interaction.followup.send(f"❌ Impossible de trouver la musique : {e}")

        queue = get_queue(interaction.guild.id)

        if vc.is_playing() or vc.is_paused():
            queue.append((url, title))
            await interaction.followup.send(f"📋 Ajouté à la file : **{title}**")
        else:
            queue.append((url, title))
            await self.play_next(interaction.channel, interaction.guild)
            await interaction.followup.send(f"✅ Lecture lancée !")

    @app_commands.command(name="skip", description="Passer la musique en cours")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message("⏭️ Musique passée !")
        else:
            await interaction.response.send_message("❌ Rien en cours.", ephemeral=True)

    @app_commands.command(name="queue", description="Voir la file d'attente")
    async def queue(self, interaction: discord.Interaction):
        q = get_queue(interaction.guild.id)
        if not q:
            return await interaction.response.send_message("📋 La file est vide.")
        desc = "\n".join([f"**{i+1}.** {title}" for i, (_, title) in enumerate(q)])
        embed = discord.Embed(title="📋 File d'attente", description=desc, color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stop", description="Arrêter la musique et déconnecter")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            queues[interaction.guild.id] = deque()
            await vc.disconnect()
            await interaction.response.send_message("⏹️ Musique arrêtée et bot déconnecté.")
        else:
            await interaction.response.send_message("❌ Pas connecté à un vocal.", ephemeral=True)

    @app_commands.command(name="pause", description="Mettre en pause")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ En pause.")
        else:
            await interaction.response.send_message("❌ Rien en cours.", ephemeral=True)

    @app_commands.command(name="resume", description="Reprendre la musique")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Musique reprise !")
        else:
            await interaction.response.send_message("❌ Pas en pause.", ephemeral=True)

    @app_commands.command(name="volume", description="Changer le volume (0-100)")
    async def volume(self, interaction: discord.Interaction, niveau: int):
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            return await interaction.response.send_message("❌ Rien en cours.", ephemeral=True)
        if not 0 <= niveau <= 100:
            return await interaction.response.send_message("❌ Entre 0 et 100.", ephemeral=True)
        vc.source.volume = niveau / 100
        await interaction.response.send_message(f"🔊 Volume : **{niveau}%**")

async def setup(bot):
    await bot.add_cog(Music(bot))
