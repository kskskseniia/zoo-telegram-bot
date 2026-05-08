import os
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
BOT_USERNAME = os.getenv("BOT_USERNAME")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")

if ADMIN_ID:
    ADMIN_ID = int(ADMIN_ID)

if not BOT_USERNAME:
    raise ValueError("BOT_USERNAME is not set in .env")