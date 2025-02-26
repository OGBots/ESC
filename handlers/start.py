from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from utils.database import Database
from utils.helpers import format_currency
from config import REQUIRED_CHANNELS

async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is member of required channels"""
    user_id = update.effective_user.id

    for channel in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked", "restricted"]:
                return False
        except Exception:
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user

    # Check channel membership
    if not await check_channel_membership(update, context):
        channels_buttons = [[InlineKeyboardButton(channel, url=f"https://t.me/{channel[1:]}")] 
                          for channel in REQUIRED_CHANNELS]
        channels_buttons.append([InlineKeyboardButton("✅ I've Joined", callback_data="check_join")])

        await update.message.reply_text(
            "Please join our channel(s) to use the bot:",
            reply_markup=InlineKeyboardMarkup(channels_buttons)
        )
        return

    # Initialize user in database if not exists
    user_data = Database.get_user(user.id) or {
        "id": user.id,
        "username": user.username,
        "balance": 0.0,
        "completed_deals": 0,
        "pending_deals": 0,
        "is_banned": False
    }
    Database.save_user(user.id, user_data)

    # Show welcome message
    await update.message.reply_text(
        f"Welcome to the Escrow Bot!\n\n"
        f"Your current balance: {format_currency(user_data['balance'])}\n\n"
        "Commands:\n"
        "/escrow - Create new escrow deal\n"
        "/wallet - Check wallet balance\n"
        "/redeem - Redeem a code\n"
        "/help - Show help message"
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel join verification callback"""
    query = update.callback_query
    await query.answer()

    if await check_channel_membership(update, context):
        await query.edit_message_text("Thank you for joining! You can now use the bot.\n\nUse /start to begin.",
                                    reply_markup=None)  # Remove buttons
    else:
        await query.answer("Please join all required channels first!", show_alert=True)