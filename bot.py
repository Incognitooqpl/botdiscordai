import os
import asyncio
from threading import Thread

import discord
from discord.ext import commands
from flask import Flask
from google import genai
from google.genai import types

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

Gemini

gemini = genai.Client(api_key=GEMINI_API_KEY)

Minimalny serwer HTTP dla monitoringu Render/UptimeRobot

app = Flask(name)

@app.get("/")
def home():
return "Incognito AI is running!", 200

@app.get("/health")
def health():
return {"status": "ok", "bot": "Incognito AI"}, 200

def run_web_server():
port = int(os.environ.get("PORT", "10000"))
app.run(host="0.0.0.0", port=port, use_reloader=False)

Discord

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="+", intents=intents)

@bot.event
async def on_ready():
print(f"Zalogowano jako {bot.user}")
print("Incognito AI jest online!")

@bot.command(name="ai")
async def ai_command(ctx, *, prompt: str = ""):
if not prompt.strip():
await ctx.reply(
"Podaj pytanie! Przykład: "+ai Napisz hello world w Pythonie""
)
return

# Ograniczenie długości promptu
prompt = prompt[:4000]

async with ctx.typing():
    try:
        response = await asyncio.to_thread(
            gemini.models.generate_content,
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Jesteś pomocnym asystentem AI na Discordzie. "
                    "Odpowiadasz po polsku, chyba że użytkownik poprosi "
                    "o inny język. Pisz jasno i zwięźle."
                ),
                max_output_tokens=1500,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            await ctx.reply("Gemini nie zwróciło odpowiedzi. Spróbuj ponownie.")
            return

        # Discord pozwala na maksymalnie 2000 znaków w zwykłej wiadomości.
        footer = "\n\n✨ *Powered by Google Gemini*"
        chunks = [
            answer[i:i + 1800]
            for i in range(0, len(answer), 1800)
        ]

        for index, chunk in enumerate(chunks):
            if index == 0:
                await ctx.reply(chunk[:2000 - len(footer)] + footer)
            else:
                await ctx.send(chunk)

    except Exception as error:
        print(f"Błąd Gemini: {type(error).__name__}: {error}")
        await ctx.reply(
            "Nie udało się uzyskać odpowiedzi. Spróbuj ponownie za chwilę."
        )

async def main():
web_thread = Thread(target=run_web_server, daemon=True)
web_thread.start()

async with bot:
    await bot.start(DISCORD_TOKEN)

if name == "main":
asyncio.run(main())