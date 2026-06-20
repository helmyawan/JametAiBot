import discord
from discord import app_commands
from discord.ext import commands
import time
import math
from database import get_user_reputation, reset_reputation, clear_thread_history, get_stats, get_top_reputation

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="jamet_ping", description="Cek latensi JametAI")
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong asu! Latensi Discord: {latency}ms.")

    @app_commands.command(name="jamet_rep", description="Cek profil reputasi user")
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def rep(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        notes, score = await get_user_reputation(target.id)
        tier = "Suhu / Pinter" if score >= 5 else "Goblok Akut" if score <= -5 else "Biasa / Ndes"
        await interaction.response.send_message(f"**Profil {target.display_name}**\nScore: {score} ({tier})\nCatatan: {notes or 'Kosong cok'}")

    @app_commands.command(name="jamet_status", description="Cek status bot")
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def status(self, interaction: discord.Interaction):
        uptime = round(time.time() - self.start_time)
        m, s = divmod(uptime, 60)
        h, m = divmod(m, 60)
        users, threads = await get_stats()
        await interaction.response.send_message(f"**Status JametAI**\nUptime: {h}h {m}m {s}s\nUser Diingat: {users}\nTotal Thread: {threads}")

    @app_commands.command(name="jamet_topbodoh", description="Leaderboard user paling minus")
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def topbodoh(self, interaction: discord.Interaction):
        rows = await get_top_reputation(5, asc=True)
        if not rows:
            return await interaction.response.send_message("Sepi cok, ra ono sing bodoh.")
        res = "**Top 5 Goblok Akut:**\n" + "\n".join([f"<@{r[0]}>: {r[1]} point" for r in rows])
        await interaction.response.send_message(res)

    @app_commands.command(name="jamet_toppinter", description="Leaderboard user paling pinter")
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def toppinter(self, interaction: discord.Interaction):
        rows = await get_top_reputation(5, asc=False)
        if not rows:
            return await interaction.response.send_message("Sepi cok, ra ono sing pinter.")
        res = "**Top 5 Suhu:**\n" + "\n".join([f"<@{r[0]}>: {r[1]} point" for r in rows])
        await interaction.response.send_message(res)

    @app_commands.command(name="jamet_reset", description="[ADMIN] Hapus memori user")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def reset(self, interaction: discord.Interaction, member: discord.Member):
        await reset_reputation(member.id)
        await interaction.response.send_message(f"Dosa-dosane <@{member.id}> wis tak hapus cok.")

    @app_commands.command(name="jamet_clear_thread", description="[ADMIN] Hapus history LLM thread ini")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def clear_thread(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.Thread):
            return await interaction.response.send_message("Iki dudu thread asu!", ephemeral=True)
        await clear_thread_history(interaction.channel.id)
        await interaction.response.send_message("Amnesia! History thread iki wis tak bakar.")

    def cog_load(self):
        pass

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            wait_time = math.ceil(error.retry_after)
            await interaction.response.send_message(f"Kesuwen asu! Ngenteni {wait_time} detik maneh cok.", ephemeral=True)
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("Raimu sopo cok? Kowe dudu admin!", ephemeral=True)
        else:
            await interaction.response.send_message("Error bajilak! Gak iso ngeksekusi command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SlashCommands(bot))