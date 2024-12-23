import asyncio
from instagrapi import Client
import requests
import random
import time
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ---------------------------
# Configuration
# ---------------------------

# Telegram Configuration
TELEGRAM_TOKEN = '7385049957:AAFeoxlOwM7URcMfCnl2AlcXJX-Rs4DZZUw'
ADMIN_CHAT_ID = '-1002284784547'

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

# Logging Setup
logging.basicConfig(
    filename='bot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# ---------------------------
# Utility Functions
# ---------------------------

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send a notification to the admin."""
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
        logging.info(f"Notification sent: {message}")
    except Exception as e:
        logging.error(f"Failed to send notification: {e}")


# ---------------------------
# Instagram Functions
# ---------------------------

async def instagram_login(username: str, password: str, context: ContextTypes.DEFAULT_TYPE):
    """Log in to Instagram dynamically."""
    global IS_LOGGED_IN
    try:
        cl.login(username, password)
        IS_LOGGED_IN = True
        logging.info("Logged in to Instagram successfully.")
        await notify_admin(context, "✅ Successfully logged in to Instagram!")
        return True
    except Exception as e:
        IS_LOGGED_IN = False
        logging.error(f"Failed to log in to Instagram: {e}")
        await notify_admin(context, f"❌ Failed to log in: {e}")
        return False


def get_latest_reels(username, amount=5):
    """Fetch the latest reels from a user."""
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


async def post_reel(video_path, caption, context: ContextTypes.DEFAULT_TYPE):
    """Post a reel to Instagram."""
    try:
        cl.clip_upload(
            path=video_path,
            caption=caption,
        )
        logging.info("Reel posted successfully.")
        await notify_admin(context, "✅ Reel posted successfully on Instagram!")
    except Exception as e:
        logging.error(f"Failed to post reel: {e}")
        await notify_admin(context, f"❌ Failed to post reel: {e}")


async def process_reels(context: ContextTypes.DEFAULT_TYPE):
    """Fetch, download, and post shuffled reels."""
    if not IS_LOGGED_IN:
        await notify_admin(context, "❌ Please log in to Instagram using /login.")
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
            await post_reel(video_path, CAPTION_TEMPLATE, context)
            uploaded_count += 1
            await asyncio.sleep(random.randint(1800, 3600))  # 30–60 min delay

    await notify_admin(context, f"✅ Uploaded {uploaded_count} reels today!")


# ---------------------------
# Telegram Commands
# ---------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Instagram Bot Commands:**\n"
        "/start - Show help\n"
        "/login <username> <password> - Log in to Instagram\n"
        "/run - Run the bot manually"
    )


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /login <username> <password>")
        return

    username, password = context.args
    success = await instagram_login(username, password, context)
    if success:
        await update.message.reply_text("✅ Logged in successfully!")
    else:
        await update.message.reply_text("❌ Failed to log in.")


async def run_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not IS_LOGGED_IN:
        await update.message.reply_text("❌ Please log in using /login first.")
        return

    await update.message.reply_text("🚀 Running the bot manually...")
    await process_reels(context)
    await update.message.reply_text("✅ Bot run completed!")


# ---------------------------
# Main Function
# ---------------------------

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('login', login))
    app.add_handler(CommandHandler('run', run_bot))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.wait_for_stop()


if __name__ == "__main__":
    asyncio.run(main())
