import os
import asyncio
import logging
from threading import Thread

import discord
from discord.ext import commands
from flask import Flask
from google import genai
from google.genai import types


# ==============================
# CONFIGURATION
# ==============================

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN environment variable.")

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY environment variable.")


# ==============================
# LOGGING
# ==============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("incognito-ai")


# ==============================
# GEMINI CLIENT
# ==============================

gemini = genai.Client(api_key=GEMINI_API_KEY)


# ==============================
# WEB SERVER
# ==============================

app = Flask(__name__)


@app.get("/")
def home():
    return "Incognito AI is running!", 200


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Incognito AI",
    }, 200


def run_web_server():
    port = int(os.environ.get("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False,
    )


# ==============================
# DISCORD BOT
# ==============================

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="+",
    intents=intents,
    help_command=None,
)


@bot.event
async def on_ready():
    logger.info("Logged in as %s", bot.user)
    logger.info("Incognito AI is online!")
    logger.info("Gemini model: %s", GEMINI_MODEL)


# ==============================
# AI COMMAND
# ==============================

@bot.command(name="ai")
@commands.cooldown(1, 5, commands.BucketType.user)
async def ai_command(ctx, *, prompt: str = ""):
    if not prompt.strip():
        await ctx.reply(
            "Podaj pytanie!\n"
            "Przykład: `+ai Napisz Hello World w Pythonie`",
            mention_author=False,
        )
        return

    prompt = prompt[:4000]

    async with ctx.typing():
        try:
            response = await asyncio.to_thread(
                gemini.models.generate_content,
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Jesteś Incognito AI, pomocnym asystentem "
                        "na Discordzie. Domyślnie odpowiadasz po polsku. "
                        "Jeżeli użytkownik poprosi o inny język, "
                        "dostosuj się. Kod programistyczny formatuj "
                        "w blokach Markdown. Odpowiadaj konkretnie."
                    ),
                    max_output_tokens=1500,
                ),
            )

            answer = (response.text or "").strip()

            if not answer:
                await ctx.reply(
                    "Gemini nie zwróciło tekstowej odpowiedzi. "
                    "Spróbuj zadać inne pytanie.",
                    mention_author=False,
                )
                return

            footer = "\n\n✨ Powered by Google Gemini"
            first_limit = 2000 - len(footer)

            first_chunk = answer[:first_limit]

            await ctx.reply(
                first_chunk + footer,
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none(),
            )

            remaining = answer[first_limit:]

            while remaining:
                chunk = remaining[:1900]
                remaining = remaining[1900:]

                await ctx.send(
                    chunk,
                    allowed_mentions=discord.AllowedMentions.none(),
                )

        except Exception:
            logger.exception("Gemini request failed")

            await ctx.reply(
                "Nie udało się uzyskać odpowiedzi AI. "
                "Spróbuj ponownie za chwilę.",
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none(),
            )


# ==============================
# HELP COMMAND
# ==============================

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="Incognito AI",
        description="Twój asystent AI na Discordzie.",
        color=discord.Color.purple(),
    )

    embed.add_field(
        name="+ai <zapytanie>",
        value="Zadaj pytanie sztucznej inteligencji.",
        inline=False,
    )

    embed.add_field(
        name="+help",
        value="Wyświetl listę komend.",
        inline=False,
    )

    embed.set_footer(text="Powered by Google Gemini")

    await ctx.reply(
        embed=embed,
        mention_author=False,
        allowed_mentions=discord.AllowedMentions.none(),
    )


# ==============================
# ERROR HANDLER
# ==============================

@ai_command.error
async def ai_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(
            f"Zwolnij trochę! Spróbuj ponownie za "
            f"{error.retry_after:.1f} s.",
            mention_author=False,
        )
    else:
        logger.error(
            "Discord command error: %s",
            error,
            exc_info=(type(error), error, error.__traceback__),
        )


# ==============================
# START
# ==============================

async def main():
    web_thread = Thread(
        target=run_web_server,
        daemon=True,
    )
    web_thread.start()

    logger.info("Starting Incognito AI...")

    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
