import os
import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import sys
import requests
import json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
QUOTES_FILENAME = "quotes.txt"
HELP_FILENAME = "help.txt"

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    sys.stdout.flush()


@bot.command(name="ficus")
async def ficus_says(ctx, arg1="", arg2=""):

    ficus_quotes = []
    with open(QUOTES_FILENAME) as f:
        ficus_quotes = [line.rstrip() for line in f]

    if arg1 == "come":
        await ficus_come(ctx)
    elif arg1 == "shoo":
        await ficus_shoo(ctx)
    elif arg1 == "kokain":
        response = "Gde mi je kasicica..."
        await ctx.send(response)
    elif arg1 == "help":
        response = ""
        with open(HELP_FILENAME) as f:
            response = f.read()
        await ctx.send(response)
    elif arg1 == "newest":
        response = ficus_quotes[-1]
        await ctx.send(response)
    elif arg1 == "join" and arg2 is not None:
        await ficus_join(ctx, arg2)
    elif arg1 == "branches":
        await ficus_branches(ctx, arg2)
    else:
        response = random.choice(ficus_quotes)
        await ctx.send(response)

#@bot.command(pass_context=True, name="ficus_here_boy")
async def ficus_come(ctx):
    await ficus_disconnect(ctx)
    user = ctx.author
    channel = user.voice.channel
    await channel.connect()
    await ficus_ciao(ctx)
    await ctx.send("Eo mene opet, eo mene opet ja")

async def ficus_join(ctx, channel_name):
    channel = next((c for c in ctx.guild.voice_channels if c.name == channel_name), None)
    if channel is not None:
        await ficus_disconnect(ctx)
        await channel.connect()
        await ficus_ciao(ctx)

#@bot.command(name="ficus_shoo")
async def ficus_shoo(ctx):
    await ficus_disconnect(ctx)
    await ctx.send("Bye " + ctx.author.name)

async def ficus_disconnect(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()

async def ficus_ciao(ctx):
    guild = ctx.guild
    voice_client = ctx.voice_client
    if voice_client is not None:
        audio_source = discord.FFmpegPCMAudio("cao.mp3")
    if not voice_client.is_playing():
        voice_client.play(audio_source, after=None)

async def ficus_branches(ctx, git):
    git = git if git is not None else "PSW-2020-ORG1/MedbayTech"
    get_response = requests.get(f"https://api.github.com/repos/{git}/branches")
    get_response_json = get_response.json()
    response = "```\nShowing branches for: https://github.com/" + git + "\n" + "\n".join([b["name"] for b in response_json]) + "\n```"
    await ctx.send(response)

bot.run(TOKEN)
