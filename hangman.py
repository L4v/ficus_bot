import os
import psycopg2 as pg 
from psycopg2 import Error
import random

WORDS_FILENAME = "serbian-latin.txt"
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

def init():
    init_db()
    init_words()
    print("Initialized hangman")

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

def init_words():
    global HANGMAN_WORDS
    with open(WORDS_FILENAME) as f:
        HANGMAN_WORDS = [line.rstrip() for line in f]


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
            if s[0] == user and s[1] < int(score):
                print("Updating")
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