import discord
from discord.ext import commands
from discord import app_commands
import asyncio, yt_dlp
from collections import deque

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
}

queues = {}

def get_queue(guild_id):
    if guild_id not in queues:
        queues[guild_id] = deque()
    return queues[guild_id]

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def play_next(self, interaction_or_ctx, guild):
        queue = get_queue(guild.id)
        vc = guild.voice_client
        if queue and vc:
            url, title = queue.popleft()
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(interaction_or_ctx, guild), self.bot.loop
            ))

    # ── PLAY ─────────────────────────────────────────────────────
    @app_commands.command(name="play", description="Jouer une musique depuis YouTube")
    @app_commands.describe(recherche="Titre ou URL YouTube")
    async def play(self, interaction: discord.Interaction, recherche: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Rejoins un salon vocal d'abord.", ephemeral=True)

        await interaction.response.defer()
        vc = interaction.guild.voice_client

        if not vc:
            vc = await interaction.user.voice.channel.connect()
        elif vc.channel != interaction.user.voice.channel:
            await vc.move_to(interaction.user.voice.channel)

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                if not recherche.startswith("http"):
                    recherche = f"ytsearch:{recherche}"
                info = ydl.extract_info(recherche, download=False)
                if "entries" in info:
                    info = info["entries"][0]
                url = info["url"]
                title = info.get("title", "Inconnue")
            except Exception:
                return await interaction.followup.send("❌ Impossible de trouver cette musique.")

        queue = get_queue(interaction.guild.id)
        if vc.is_playing():
            queue.append((url, title))
            await interaction.followup.send(f"📋 Ajouté à la file : **{title}**")
        else:
            source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
            vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next(interaction, interaction.guild), self.bot.loop
            ))
            await interaction.followup.send(f"🎵 En cours : **{title}**")

    # ── SKIP ─────────────────────────────────────────────────────
    @app_commands.command(name="skip", description="Passer la musique en cours")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await interaction.response.send_message("⏭️ Musique suivante !")
        else:
            await interaction.response.send_message("❌ Rien en cours.", ephemeral=True)

    # ── QUEUE ────────────────────────────────────────────────────
    @app_commands.command(name="queue", description="Voir la file d'attente")
    async def queue(self, interaction: discord.Interaction):
        q = get_queue(interaction.guild.id)
        if not q:
            return await interaction.response.send_message("📋 La file est vide.")
        desc = "\n".join([f"**{i+1}.** {title}" for i, (_, title) in enumerate(q)])
        embed = discord.Embed(title="📋 File d'attente", description=desc, color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed)

    # ── STOP ─────────────────────────────────────────────────────
    @app_commands.command(name="stop", description="Arrêter la musique et vider la file")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc:
            queues[interaction.guild.id] = deque()
            await vc.disconnect()
            await interaction.response.send_message("⏹️ Musique arrêtée.")
        else:
            await interaction.response.send_message("❌ Pas de connexion vocale.", ephemeral=True)

    # ── PAUSE ────────────────────────────────────────────────────
    @app_commands.command(name="pause", description="Mettre en pause")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ En pause.")
        else:
            await interaction.response.send_message("❌ Rien en cours.", ephemeral=True)

    # ── RESUME ───────────────────────────────────────────────────
    @app_commands.command(name="resume", description="Reprendre la musique")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Musique reprise !")
        else:
            await interaction.response.send_message("❌ Pas en pause.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Music(bot))
