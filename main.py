import os
import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN

# Import module handlers
from modules.ads.handlers import setup_ads_handlers
from modules.admin.handlers import setup_admin_handlers

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    from config import ADMIN_USER_ID
    if ADMIN_USER_ID:
        try:
            error_message = f"⚠️ An error occurred:\n\n<pre>{context.error}</pre>"
            await context.bot.send_message(chat_id=ADMIN_USER_ID, text=error_message, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to send error log to admin: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("Ads Bot", callback_data='module_ads')],
        # Future modules will be added here
        [InlineKeyboardButton("Scraper Module (Coming Soon)", callback_data='module_coming_soon')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✨ **ALL-IN-ONE PREMIUM BOT** ✨\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome to the ultimate command center.\n"
        "Select an advanced module below to get started:\n\n"
        "╰┈➤ **Available Modules:**"
    )
    
    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        query = update.callback_query
        try:
            # If the current message has a photo, we can't just edit the text. We must delete and send new.
            if query.message.photo or query.message.document or query.message.video:
                await query.message.delete()
                await context.bot.send_message(chat_id=query.message.chat_id, text=welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error returning to main menu: {e}")
            await context.bot.send_message(chat_id=query.message.chat_id, text=welcome_message, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help! Select a module from /start to use specific features.")

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Please set your BOT_TOKEN in config.py")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Add a handler for "Back to Main Menu" generic callback
    application.add_handler(CallbackQueryHandler(start, pattern='^main_menu$'))

    # Setup module handlers
    setup_ads_handlers(application)
    setup_admin_handlers(application)
    
    # Global error handler
    application.add_error_handler(error_handler)

    # Initialize the database and global Userbots
    from database import init_db
    from modules.ads.broadcaster import init_all_clients
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    loop.run_until_complete(init_all_clients())

    # Start dummy HTTP server for Render health checks
    if os.environ.get("PORT"):
        logger.info("Starting dummy web server for Render...")
        threading.Thread(target=run_dummy_server, daemon=True).start()

    # Run the bot until the user presses Ctrl-C
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

import asyncio

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main()
