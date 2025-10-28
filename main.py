# main.py
import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import datetime, timedelta
import threading
import time
import asyncio

# ---------- CONFIG ----------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=['!', '?'], intents=intents)  # PREFIX: ! and ?

# CHANGE THIS TO YOUR SERVER ID (for slash commands)
GUILD_ID = 1397866568314261555  # ← YOUR SERVER ID HERE
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
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print('Slash commands synced to your server!')
    except:
        print('Slash sync failed — prefix commands still work!')
    print('PREFIX COMMANDS: !feedback, ?timeout')

# ---------- PREFIX: !feedback ----------
@bot.command(name="feedback")
async def prefix_feedback(ctx, *, text: str):
    if not on_cooldown(ctx.author.id):
        await ctx.send("Please wait 1 minute!")
        return

    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if not channel:
        await ctx.send("Error: Staff channel not found!")
        return

    embed = discord.Embed(title="New Feedback", description=text, color=0x00ff00)
    embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
    embed.add_field(name="User ID", value=ctx.author.id, inline=True)
    await channel.send(embed=embed)
    await ctx.send("Feedback sent! Thank you!")

# ---------- PREFIX: ?timeout ----------
@bot.command(name="timeout")
@commands.has_permissions(administrator=True)
async def prefix_timeout(ctx, member: discord.Member, minutes: int):
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
        await ctx.send("I don't have permission!")

# ---------- SLASH COMMANDS (Optional - Keep for Future) ----------
@bot.tree.command(name="feedback", description="Send feedback to staff")
@app_commands.describe(text="Your message")
async def slash_feedback(interaction: discord.Interaction, text: str):
    if not on_cooldown(interaction.user.id):
        await interaction.response.send_message("Please wait 1 minute!", ephemeral=True)
        return

    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("Error!", ephemeral=True)
        return

    embed = discord.Embed(title="New Feedback", description=text, color=0x00ff00)
    embed.set_author(name=interaction.user, icon_url=interaction.user.display_avatar.url)
    await channel.send(embed=embed)
    await interaction.response.send_message("Feedback sent!", ephemeral=True)

@bot.tree.command(name="timeout", description="Timeout a member")
@app_commands.describe(user="User", minutes="Minutes")
@app_commands.default_permissions(administrator=True)
async def slash_timeout(interaction: discord.Interaction, user: discord.Member, minutes: int):
    if not on_cooldown(interaction.user.id):
        await interaction.response.send_message("Please wait 1 minute!", ephemeral=True)
        return

    await user.timeout(discord.utils.utcnow() + timedelta(minutes=minutes))
    await interaction.response.send_message(f"{user.mention} timed out for {minutes}m")

# ---------- FLASK SERVER ----------
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is running! Use !feedback or ?timeout"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
time.sleep(1)

print("Starting bot...")
bot.run(os.getenv("DISCORD_TOKEN"))
