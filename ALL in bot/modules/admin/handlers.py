import logging
from telegram import Update
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters
from config import ADMIN_USER_ID
from database import get_total_users, update_user_premium_status, get_all_users

logger = logging.getLogger(__name__)

async def is_admin(user_id: int) -> bool:
    if not ADMIN_USER_ID:
        return False
    return user_id == ADMIN_USER_ID

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin dashboard stats."""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    total_users = await get_total_users()
    
    stats = (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👑 **Admin Command Center**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 **Total Registered Users:** `{total_users}`\n\n"
        "╰┈➤ **Available Commands:**\n"
        "├ `/premium add <user_id>`\n"
        "├ `/premium remove <user_id>`\n"
        "└ `/broadcast <message>`\n"
    )
    
    await update.message.reply_text(stats, parse_mode='Markdown')

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant or revoke premium status for a user."""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: `/premium <add/remove> <user_id>`", parse_mode='Markdown')
        return

    action = context.args[0].lower()
    try:
        target_id = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid User ID.")
        return

    if action == "add":
        success = await update_user_premium_status(target_id, True)
        msg = f"✅ Premium granted to {target_id}." if success else "Failed to grant premium."
    elif action == "remove":
        success = await update_user_premium_status(target_id, False)
        msg = f"❌ Premium revoked from {target_id}." if success else "Failed to revoke premium."
    else:
        msg = "Usage: `/premium <add/remove> <user_id>`"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast a message to all bot users."""
    user_id = update.effective_user.id
    if not await is_admin(user_id):
        return

    if not context.args:
        await update.message.reply_text("Usage: `/broadcast <message>`", parse_mode='Markdown')
        return

    message = update.message.text.split(' ', 1)[1]
    users = await get_all_users()
    
    success_count = 0
    for u in users:
        target_id = u.get('user_id')
        try:
            await context.bot.send_message(chat_id=target_id, text=f"📢 **Broadcast:**\n\n{message}", parse_mode='Markdown')
            success_count += 1
        except Exception as e:
            logger.warning(f"Failed to send broadcast to {target_id}: {e}")

    await update.message.reply_text(f"✅ Broadcast sent to {success_count}/{len(users)} users.")

def setup_admin_handlers(application: Application):
    """Register all admin handlers."""
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
