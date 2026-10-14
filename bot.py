import os
import asyncio
from threading import Thread

import discord
from discord.ext import commands
from flask import Flask
from google import genai

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

gemini = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

@app.get("/")
def home():
    return "Incognito AI is running!", 200

@app.get("/health")
def health():
    return {"status": "ok"}, 200

def run_web_server():
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="+", intents=intents)

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}!")

@bot.command(name="ai")
async def ai_command(ctx, *, prompt: str = ""):
    if not prompt.strip():
        await ctx.reply("Użycie: `+ai <zapytanie>`")
        return

    async with ctx.typing():
        try:
            response = await asyncio.to_thread(
                gemini.models.generate_content,
                model=GEMINI_MODEL,
                contents=prompt[:4000],
            )

            answer = (response.text or "").strip()

            if not answer:
                await ctx.reply("Gemini nie zwróciło odpowiedzi.")
                return

            answer += "\n\n✨ Powered by Google Gemini"

            for i in range(0, len(answer), 1900):
                part = answer[i:i + 1900]
                if i == 0:
                    await ctx.reply(part)
                else:
                    await ctx.send(part)

        except Exception as error:
            print(f"Błąd API: {type(error).__name__}: {error}")
            await ctx.reply("Wystąpił błąd API. Sprawdź logi Render.")

@bot.command(name="help")
async def help_command(ctx):
    await ctx.reply("Komendy:\n`+ai <zapytanie>` — zapytaj AI\n`+help` — pomoc")

async def main():
    Thread(target=run_web_server, daemon=True).start()

    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
