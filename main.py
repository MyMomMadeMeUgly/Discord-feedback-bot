# main.py
import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import datetime, timedelta
import threading

# ---------- BOT SETUP ----------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Replace with YOUR SERVER ID (for instant commands)
GUILD_ID = 1397866568314261555  # ← CHANGE THIS TO YOUR SERVER ID
FEEDBACK_CHANNEL_ID = int(os.getenv("FEEDBACK_CHANNEL_ID"))
cooldowns = {}

# ---------- COOLDOWN ----------
def on_cooldown(user_id):
    now = datetime.utcnow()
    if user_id in cooldowns:
        if now - cooldowns[user_id] < timedelta(seconds=60):
            return False
    cooldowns[user_id] = now
    return True

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    # INSTANT SYNC TO YOUR SERVER
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print('Commands synced INSTANTLY to your server!')
    print(f'Go to Discord and type / to see them!')

# ---------- /feedback ----------
@bot.tree.command(name="feedback", description="Send feedback to staff")
@app_commands.describe(text="Your message")
async def feedback(interaction: discord.Interaction, text: str):
    if not on_cooldown(interaction.user.id):
        await interaction.response.send_message("Wait 1 minute!", ephemeral=True)
        return

    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="New Feedback",
            description=text,
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="User ID", value=interaction.user.id, inline=True)
        await channel.send(embed=embed)
        await interaction.response.send_message("Feedback sent!", ephemeral=True)
    else:
        await interaction.response.send_message("Error: Staff channel not found!", ephemeral=True)

# ---------- /timeout ----------
@bot.tree.command(name="timeout", description="Timeout a member (Admin only)")
@app_commands.describe(user="Member to timeout", minutes="Minutes (1–40320)")
@app_commands.default_permissions(administrator=True)
async def timeout(interaction: discord.Interaction, user: discord.Member, minutes: int):
    if not on_cooldown(interaction.user.id):
        await interaction.response.send_message("Wait 1 minute!", ephemeral=True)
        return

    if minutes < 1 or minutes > 40320:
        await interaction.response.send_message("Minutes must be 1–40320.", ephemeral=True)
        return

    try:
        await user.timeout(discord.utils.utcnow() + timedelta(minutes=minutes),
                          reason=f"Timed out by {interaction.user}")
        await interaction.response.send_message(f"{user.mention} has been timed out for **{minutes}** minute(s).")
    except discord.Forbidden:
        await interaction.response.send_message("I don't have permission!", ephemeral=True)

# ---------- HTTP SERVER (KEEPS RENDER HAPPY) ----------
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running! Use /feedback and /timeout in Discord!"

def run_http_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

# Start HTTP server in background
http_thread = threading.Thread(target=run_http_server, daemon=True)
http_thread.start()

# ---------- RUN BOT ----------
bot.run(os.getenv("DISCORD_TOKEN"))
