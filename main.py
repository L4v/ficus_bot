import os
import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import sys
import requests
import json
import psycopg2 as pg 
from psycopg2 import Error

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
QUOTES_FILENAME = "quotes.txt"
WORDS_FILENAME = "serbian-latin.txt"
HELP_FILENAME = "help.txt"

HANGMAN_NO_GUESSES = 0
HANGMAN_NEW= True
HANGMAN_WORDS = ["liman", "ciklopentanoperhidrofenantren", "kasicica", "cao"]
HANGMAN_GUESSED_LETTERS = []
HANGMAN_CORRECT_WORD = ""
HANGMAN_PROGRESS = ""
HANGMAN_PICS = ['''
  +---+
  |   |
      |
      |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
      |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
  |   |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
 /|\  |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
 /|\  |
 /    |
      |
=========''', '''
  +---+
  |   |
  O   |
 /|\  |
 / \  |
      |
=========''']

bot = commands.Bot(command_prefix="!")

def init_db():
    connection = None
    query = '''CREATE TABLE IF NOT EXISTS highscore
    (USERNAME VARCHAR(255) PRIMARY KEY,
    SCORE INT );'''
    try:
        connection = pg.connect(os.getenv("DATABASE_URL"))
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()
        print("Created table")
    except (Exception, Error) as err:
        print("Error with postgresql: ", err)
    finally:
        if(connection):
            cursor.close()
            connection.close()

def add_or_update_score(user_score):
    user, score = user_score
    score = str(score)
    connection = None
    try:
        connection = pg.connect(os.getenv("DATABASE_URL"))
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM highscore")
        scores = cursor.fetchall()
        for s in scores:
            if s[0] == user and s[1] > int(score):
                cursor.execute(f"UPDATE highscore SET score = {score} WHERE USERNAME = '{user}'")
                connection.commit()
                break
        else:
            cursor.execute(f"INSERT INTO highscore (USERNAME, SCORE) VALUES('{user}' , {score} )")
            connection.commit()
    except (Exception, Error) as err:
        print("Postgres error while updating/adding score: ", err)
    finally:
        if(connection):
            cursor.close()
            connection.close()

def get_score():
    result = []
    connection = None
    try:
        connection = pg.connect(os.getenv("DATABASE_URL"))
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM highscore")
        result = cursor.fetchall()
    except (Exception, Error) as err:
        print("Postgres error while getting scores: ", err)
    finally:
        if(connection):
            cursor.close()
            connection.close()
    return result

@bot.event
async def on_ready():
    init_db()
    global HANGMAN_WORDS
    print(f'{bot.user.name} has connected to Discord!')
    sys.stdout.flush()
    with open(WORDS_FILENAME) as f:
        HANGMAN_WORDS = [line.rstrip() for line in f]


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
    elif arg1 == "scoreboard":
        response = "```"
        for score in get_score():
            response += score[0] + "\t" + str(score[1]) + "\n"
        response += "```"
        await ctx.send(response)
    #elif arg1 == "test":
    #    add_or_update_score(["Test", 4])
    elif arg1 == "join" and arg2 is not None:
        await ficus_join(ctx, arg2)
    elif arg1 == "branches":
        await ficus_branches(ctx, arg2)
    elif arg1 == "hm":
        await ficus_hangman(ctx, arg2)
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
    git = git if git != "" else "PSW-2020-ORG1/MedbayTech"
    get_response = requests.get(f"https://api.github.com/repos/{git}/branches")
    get_response_json = get_response.json()
    response = "```\nShowing branches for: https://github.com/" + git + "\n" + "\n".join([b["name"] for b in get_response_json]) + "\n```"
    await ctx.send(response)

async def ficus_hangman(ctx, guess):
    global HANGMAN_NEW
    global HANGMAN_CORRECT_WORD
    global HANGMAN_WORDS
    global HANGMAN_GUESSED_LETTERS
    global HANGMAN_PROGRESS
    global HANGMAN_PICS
    global HANGMAN_NO_GUESSES
    if not guess:
        if not HANGMAN_NEW:
            response = "```\n"
            response += hangman_progress()
            response += "\n```"
            await ctx.send(response)
            return
        else:
            hangman_reset()
            await ctx.send("```\nStarting new game...\n```")
            return
    guess = guess.lower()
    if HANGMAN_NEW:
        hangman_reset()

    HANGMAN_PROGRESS = ""
    if guess not in HANGMAN_CORRECT_WORD and guess not in HANGMAN_GUESSED_LETTERS:
        HANGMAN_NO_GUESSES += 1

    for c in HANGMAN_CORRECT_WORD:
        if guess == c or c in HANGMAN_GUESSED_LETTERS:
            HANGMAN_PROGRESS += c
        else:
            HANGMAN_PROGRESS += "_ "
    HANGMAN_GUESSED_LETTERS.append(guess)

    response = "```\n"
    if guess == HANGMAN_CORRECT_WORD or HANGMAN_PROGRESS == HANGMAN_CORRECT_WORD:
        response += "Finally!\n"
        response += "The word was: " + HANGMAN_CORRECT_WORD + "\n"
        response += "```"
        HANGMAN_NEW = True
        winner = ctx.author.name
        scores = get_score()
        for score in scores:
            if score[0] == winner:
                add_or_update_score([score[0], score[1] + 1])
                break
        else:
            add_or_update_score([winner, 1])
    else:
        response += hangman_progress()
        if HANGMAN_NO_GUESSES == 6:
            response += "\nGame over!\n"
            response += "The word was: " + HANGMAN_CORRECT_WORD + "\n"
            HANGMAN_NEW = True
            HANGMAN_NO_GUESSES = 0;
        response += "\n```"
    await ctx.send(response)

def hangman_reset():
    global HANGMAN_NEW
    global HANGMAN_CORRECT_WORD
    global HANGMAN_WORDS
    global HANGMAN_GUESSED_LETTERS
    global HANGMAN_PROGRESS
    global HANGMAN_PICS
    global HANGMAN_NO_GUESSES
    HANGMAN_NEW = False
    HANGMAN_CORRECT_WORD = random.choice(HANGMAN_WORDS)
    HANGMAN_GUESSED_LETTERS = []
    HANGMAN_NO_GUESSES = 0;

def hangman_progress():
    global HANGMAN_GUESSED_LETTERS
    global HANGMAN_PROGRESS
    global HANGMAN_PICS
    global HANGMAN_NO_GUESSES
    response = "Guesses: [" + " ".join(set(HANGMAN_GUESSED_LETTERS)) + "]\n"
    response += "Progress: " + HANGMAN_PROGRESS + "\n"
    response += "Number of guesses: " + str(HANGMAN_NO_GUESSES) + "/6\n"
    response += HANGMAN_PICS[HANGMAN_NO_GUESSES]
    return response

bot.run(TOKEN)
