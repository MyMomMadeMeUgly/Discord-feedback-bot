# main.py
import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import datetime, timedelta, UTC
import threading
import time
import asyncio

# ---------- CONFIG ----------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=['!', '?'], intents=intents)

GUILD_ID = 1397866568314261555  # ← YOUR SERVER ID
FEEDBACK_CHANNEL_ID = int(os.getenv("FEEDBACK_CHANNEL_ID"))
cooldowns = {}

# ---------- COOLDOWN ----------
def on_cooldown(user_id):
    now = datetime.now(UTC)
    if user_id in cooldowns:
        if now - cooldowns[user_id] < timedelta(seconds=60):
            return False
    cooldowns[user_id] = now
    return True

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print('Slash commands synced!')
    except Exception as e:
        print(f'Slash sync failed: {e}')
    print('COMMANDS: !ping, !feedback <text>, ?timeout @user <minutes>')

# ---------- !ping ----------
@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"Pong! `{round(bot.latency * 1000)}ms`")

# ---------- !feedback ----------
@bot.command(name="feedback")
async def prefix_feedback(ctx, *, text: str = None):
    if text is None:
        await ctx.send("Usage: `!feedback <your message>`")
        return
    if not on_cooldown(ctx.author.id):
        await ctx.send("Please wait 1 minute!")
        return
    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if not channel:
        await ctx.send("Error: Staff channel not found!")
        return
    embed = discord.Embed(title="Feedback", description=text, color=0x00ff00, timestamp=datetime.now(UTC))
    embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
    await channel.send(embed=embed)
    await ctx.send("Feedback sent!")

# ---------- ?timeout ----------
@bot.command(name="timeout")
@commands.has_permissions(administrator=True)
async def prefix_timeout(ctx, member: discord.Member = None, minutes: int = None):
    if member is None or minutes is None:
        await ctx.send("Usage: `?timeout @user <minutes>`\nExample: `?timeout @John 5`")
        return
    if not on_cooldown(ctx.author.id):
        await ctx.send("Please wait 1 minute!")
        return
    if minutes < 1 or minutes > 40320:
        await ctx.send("Minutes must be 1–40320.")
        return
    try:
        await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes),
                            reason=f"Timed out by {ctx.author}")
        await ctx.send(f"{member.mention} timed out for **{minutes}** minute(s).")
    except discord.Forbidden:
        await ctx.send("I don't have permission! (Check my role position)")

# ---------- SLASH (Optional) ----------
@bot.tree.command(name="feedback", description="Send feedback")
@app_commands.describe(text="Your message")
async def slash_feedback(interaction: discord.Interaction, text: str):
    if not on_cooldown(interaction.user.id):
        await interaction.response.send_message("Wait 1 minute!", ephemeral=True)
        return
    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="Feedback", description=text, color=0x00ff00)
        embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
        await channel.send(embed=embed)
        await interaction.response.send_message("Sent!", ephemeral=True)

@bot.tree.command(name="timeout", description="Timeout user")
@app_commands.describe(user="User", minutes="Minutes")
@app_commands.default_permissions(administrator=True)
async def slash_timeout(interaction: discord.Interaction, user: discord.Member, minutes: int):
    if not on_cooldown(interaction.user.id):
        await interaction.response.send_message("Wait 1 minute!", ephemeral=True)
        return
    await user.timeout(discord.utils.utcnow() + timedelta(minutes=minutes))
    await interaction.response.send_message(f"{user.mention} timed out for {minutes}m")

# ---------- FLASK ----------
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive! Use !ping"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
threading.Thread(target=run_flask, daemon=True).start()
time.sleep(1)

print("Starting bot...")
bot.run(os.getenv("DISCORD_TOKEN"))
