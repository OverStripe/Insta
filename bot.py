import asyncio
import random
import requests
import logging
import time
from datetime import datetime
from instagrapi import Client
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ---------------------------
# CONFIGURATION
# ---------------------------

# Telegram Configuration
TELEGRAM_TOKEN = '7385049957:AAGhwdyRJiyPVc8RwTKdqJ3n8T8cFcw8O2c'

# Instagram Configuration
cl = Client()
IS_LOGGED_IN = False

# Target Instagram Accounts
TARGET_ACCOUNTS = [
    'pfk.edits',
    'withshyamm'
]

# Default Caption Template
CAPTION_TEMPLATE = """
#🎬 Elevate Your Content Game!

Explore our latest reel showcasing creativity and precision. 🌟  
Stay tuned for more updates, and don't forget to **like, share, and comment**! ❤️

➡️ Follow for daily inspiration!  
#Trending #Reels #CreativeContent
"""

# Logging Configuration
logging.basicConfig(
    filename='bot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# ---------------------------
# UTILITY FUNCTIONS
# ---------------------------

async def notify_user(update: Update, message: str):
    """Send a notification to the user who triggered the command."""
    try:
        await update.message.reply_text(message)
        logging.info(f"Notification sent to user: {message}")
    except Exception as e:
        logging.error(f"Failed to send notification: {e}")


# ---------------------------
# INSTAGRAM FUNCTIONS
# ---------------------------

async def instagram_login(username: str, password: str, update: Update):
    """Log in to Instagram dynamically."""
    global IS_LOGGED_IN
    try:
        cl.login(username, password)
        IS_LOGGED_IN = True
        logging.info("Successfully logged into Instagram.")
        await notify_user(update, "✅ Successfully logged in to Instagram!")
        return True
    except Exception as e:
        IS_LOGGED_IN = False
        logging.error(f"Failed to log in to Instagram: {e}")
        await notify_user(update, f"❌ Failed to log in: {e}")
        return False


def get_latest_reels(username, amount=5):
    """Fetch the latest reels from an Instagram user."""
    try:
        user_id = cl.user_id_from_username(username)
        reels = cl.user_clips(user_id, amount=amount)
        random.shuffle(reels)
        logging.info(f"Fetched {len(reels)} reels from {username}.")
        return reels
    except Exception as e:
        logging.error(f"Failed to fetch reels from {username}: {e}")
    return []


def download_reel(video_url, filename="reel.mp4"):
    """Download a reel video."""
    try:
        response = requests.get(video_url)
        with open(filename, "wb") as f:
            f.write(response.content)
        logging.info("Reel downloaded successfully.")
        return filename
    except Exception as e:
        logging.error(f"Failed to download reel: {e}")
    return None


async def post_reel(video_path, caption, update: Update):
    """Post a reel to Instagram."""
    try:
        cl.clip_upload(
            path=video_path,
            caption=caption,
        )
        logging.info("Reel posted successfully.")
        await notify_user(update, "✅ Reel posted successfully on Instagram!")
    except Exception as e:
        logging.error(f"Failed to post reel: {e}")
        await notify_user(update, f"❌ Failed to post reel: {e}")


async def process_reels(update: Update):
    """Fetch, download, and post shuffled reels."""
    if not IS_LOGGED_IN:
        await notify_user(update, "❌ Please log in to Instagram using /login.")
        return

    selected_reels = []
    for account in TARGET_ACCOUNTS:
        reels = get_latest_reels(account, amount=5)
        selected_reels.extend(reels)

    random.shuffle(selected_reels)
    daily_reel_count = random.randint(7, 10)
    uploaded_count = 0

    for reel in selected_reels[:daily_reel_count]:
        video_url = reel.video_url
        video_path = download_reel(video_url)
        if video_path:
            await post_reel(video_path, CAPTION_TEMPLATE, update)
            uploaded_count += 1
            await asyncio.sleep(random.randint(1800, 3600))  # 30–60 min delay

    await notify_user(update, f"✅ Uploaded {uploaded_count} reels today!")


# ---------------------------
# TELEGRAM COMMANDS
# ---------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Instagram Bot Commands:**\n"
        "/start - Show help\n"
        "/login <username> <password> - Log in to Instagram\n"
        "/update_caption - Update the caption template\n"
        "/add_account <username> - Add a target Instagram account\n"
        "/list_accounts - List all target accounts\n"
        "/remove_account <username> - Remove a target account\n"
        "/run - Run the bot manually"
    )


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await notify_user(update, "❌ Usage: /login <username> <password>")
        return

    username, password = context.args
    success = await instagram_login(username, password, update)
    if success:
        await notify_user(update, "✅ Logged in successfully!")
    else:
        await notify_user(update, "❌ Failed to log in.")


async def run_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not IS_LOGGED_IN:
        await notify_user(update, "❌ Please log in using /login first.")
        return

    await notify_user(update, "🚀 Running the bot manually...")
    await process_reels(update)
    await notify_user(update, "✅ Bot run completed!")


# ---------------------------
# MAIN FUNCTION
# ---------------------------

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
  
