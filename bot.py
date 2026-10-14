import os
import asyncio
from threading import Thread

import discord
from discord.ext import commands
from flask import Flask
from google import genai
from google.genai import types

=========================

CONFIGURATION

=========================

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

if not DISCORD_TOKEN:
raise RuntimeError("Brakuje zmiennej DISCORD_TOKEN!")

if not GEMINI_API_KEY:
raise RuntimeError("Brakuje zmiennej GEMINI_API_KEY!")

=========================

GEMINI

=========================

gemini = genai.Client(api_key=GEMINI_API_KEY)

=========================

FLASK SERVER

=========================

app = Flask(name)

@app.get("/")
def home():
return "Incognito AI is running!", 200

@app.get("/health")
def health():
return {
"status": "ok",
"bot": "Incognito AI",
}, 200

def run_web_server():
port = int(os.environ.get("PORT", "10000"))

app.run(
    host="0.0.0.0",
    port=port,
    use_reloader=False,
)

=========================

DISCORD BOT

=========================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
command_prefix="+",
intents=intents,
help_command=None,
)

@bot.event
async def on_ready():
print(f"Zalogowano jako {bot.user}!")
print("Incognito AI jest online!")
print(f"Model Gemini: {GEMINI_MODEL}")

=========================

AI COMMAND

=========================

@bot.command(name="ai")
async def ai_command(ctx, *, prompt: str = ""):
if not prompt.strip():
await ctx.reply(
"Podaj pytanie!\n"
"Przykład: "+ai Napisz hello world w Pythonie""
)
return

# Ograniczenie długości zapytania
prompt = prompt[:4000]

async with ctx.typing():
    try:
        response = await asyncio.to_thread(
            gemini.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Jesteś pomocnym asystentem AI na Discordzie. "
                    "Odpowiadasz po polsku, chyba że użytkownik "
                    "poprosi o inny język. "
                    "Formatuj kod za pomocą bloków Markdown. "
                    "Pisz jasno i zrozumiale."
                ),
                max_output_tokens=1500,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            await ctx.reply(
                "Gemini nie zwróciło tekstowej odpowiedzi. "
                "Spróbuj zadać inne pytanie."
            )
            return

        # Stopka tylko w pierwszej wiadomości
        footer = "\n\n✨ Powered by Google Gemini"

        # Dziel odpowiedź na fragmenty mieszczące się na Discordzie
        chunks = [
            answer[i:i + 1800]
            for i in range(0, len(answer), 1800)
        ]

        first_message = chunks[0][:2000 - len(footer)] + footer

        await ctx.reply(
            first_message,
            allowed_mentions=discord.AllowedMentions.none(),
        )

        for chunk in chunks[1:]:
            await ctx.send(
                chunk,
                allowed_mentions=discord.AllowedMentions.none(),
            )

    except Exception as error:
        print(
            f"Błąd Gemini: {type(error).__name__}: {error}"
        )

        await ctx.reply(
            "Wystąpił błąd podczas generowania odpowiedzi. "
            "Sprawdź logi hostingu i spróbuj ponownie.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

=========================

HELP COMMAND

=========================

@bot.command(name="help")
async def help_command(ctx):
await ctx.reply(
"Incognito AI — pomoc\n\n"
""+ai <zapytanie>" — zadaj pytanie AI\n"
""+help" — wyświetl pomoc\n\n"
"✨ Powered by Google Gemini",
allowed_mentions=discord.AllowedMentions.none(),
)

=========================

START

=========================

async def main():
# Serwer HTTP działa w osobnym wątku
web_thread = Thread(
target=run_web_server,
daemon=True,
)
web_thread.start()

# Uruchom połączenie z Discordem
async with bot:
    await bot.start(DISCORD_TOKEN)

if name == "main":
asyncio.run(main())
