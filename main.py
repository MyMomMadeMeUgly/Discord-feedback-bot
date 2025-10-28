# main.py
import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import datetime, timedelta
import threading
import time

# ---------- BOT SETUP ----------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

FEEDBACK_CHANNEL_ID = int(os.getenv("FEEDBACK_CHANNEL_ID"))
cooldowns = {}

def on_cooldown(user_id):
    now = datetime.utcnow()
    if user_id in cooldowns:
        if now - cooldowns[user_id] < timedelta(seconds=60):
            return False
    cooldowns[user_id] = now
    return True

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    await bot.tree.sync()
    print('Commands synced!')

@bot.tree.command(name="feedback", description="Send feedback")
@app_commands.describe(text="Your message")
async def feedback(interaction: discord.Interaction, text: str):
    if not on_cooldown(interaction.user.id):
        await interaction.response.send_message("Wait 1 minute!", ephemeral=True)
        return

    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="Feedback", description=text, color=0x00ff00)
        embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
        await channel.send(embed=embed)
        await interaction.response.send_message("Sent!", ephemeral=True)
    else:
        await interaction.response.send_message("Error!", ephemeral=True)

@bot.tree.command(name="timeout", description="Timeout user")
@app_commands.describe(user="User", minutes="Minutes")
@app_commands.default_permissions(administrator=True)
async def timeout(interaction: discord.Interaction, user: discord.Member, minutes: int):
    if not on_cooldown(interaction.user.id):
        await interaction.response.send_message("Wait 1 minute!", ephemeral=True)
        return

    if minutes < 1 or minutes > 40320:
        await interaction.response.send_message("1–40320 minutes only!", ephemeral=True)
        return

    await user.timeout(discord.utils.utcnow() + timedelta(minutes=minutes))
    await interaction.response.send_message(f"{user} timed out for {minutes}m")

# ---------- HTTP SERVER FOR RENDER (KEEPS IT ALIVE) ----------
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running! 🚀"

def run_http_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Start HTTP server in a separate thread (so bot runs too)
http_thread = threading.Thread(target=run_http_server, daemon=True)
http_thread.start()

# ---------- RUN BOT ----------
bot.run(os.getenv("DISCORD_TOKEN"))
