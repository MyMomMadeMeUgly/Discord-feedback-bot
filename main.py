import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta, UTC
import threading
import time

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=['!', '?'], intents=intents)

GUILD_ID = 1397866568314261555  # ← CHANGE TO YOUR SERVER ID
FEEDBACK_CHANNEL_ID = int(os.getenv("FEEDBACK_CHANNEL_ID"))
cooldowns = {}

def on_cooldown(user_id):
    now = datetime.now(UTC)
    if user_id in cooldowns:
        if now - cooldowns[user_id] < timedelta(seconds=60):
            return False
    cooldowns[user_id] = now
    return True

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print('Slash commands synced!')
    except:
        pass
    print('COMMANDS: !ping, !feedback <text>, ?timeout @user <minutes>')

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! `{round(bot.latency * 1000)}ms`")

@bot.command()
async def feedback(ctx, *, text: str = None):
    if not text:
        await ctx.send("Usage: `!feedback <message>`")
        return
    if not on_cooldown(ctx.author.id):
        await ctx.send("Wait 1 minute!")
        return
    channel = bot.get_channel(FEEDBACK_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="Feedback", description=text, color=0x00ff00, timestamp=datetime.now(UTC))
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        await channel.send(embed=embed)
        await ctx.send("Sent!")
    else:
        await ctx.send("Error!")

@bot.command()
@commands.has_permissions(administrator=True)
async def timeout(ctx, member: discord.Member = None, minutes: int = None):
    if not member or not minutes:
        await ctx.send("Usage: `?timeout @user <minutes>`")
        return
    if not on_cooldown(ctx.author.id):
        await ctx.send("Wait 1 minute!")
        return
    await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes))
    await ctx.send(f"{member.mention} timed out for {minutes}m")

# Flask (optional but keeps Railway happy)
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!"
threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), use_reloader=False), daemon=True).start()
time.sleep(1)

print("Starting bot...")
bot.run(os.getenv("DISCORD_TOKEN"))
