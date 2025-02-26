from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = (
        "<b>🤖 Available Commands</b>\n\n"
        "<b>General Commands:</b>\n"
        "• /start - Start the bot and check channel membership\n"
        "• /help - Show this help message\n"
        "• /wallet - Check your wallet balance\n"
        "• /redeem - Redeem a code (Usage: /redeem CODE)\n\n"
        "<b>Escrow Commands:</b>\n"
        "• /escrow - Create new escrow deal\n"
        "• /find_deal - Find a deal by ID (Usage: /find_deal DEAL_ID)\n\n"
        "For support, contact: @satsnova"
    )

    await update.message.reply_text(help_text, parse_mode='HTML')

async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /og command - Show admin commands (admin only)"""
    from config import ADMIN_IDS

    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ This command is only for administrators.")
        return

    admin_help = (
        "<b>👑 Admin Control Panel</b>\n\n"
        "<b>👥 User Management:</b>\n"
        "• /admin_stats - View user statistics\n"
        "• /admin_ban username - Ban a user\n"
        "• /admin_unban username - Unban a user\n\n"
        "<b>💰 Balance Management:</b>\n"
        "• /admin_add_balance username amount - Add funds\n"
        "• /admin_remove_balance username amount - Remove funds\n\n"
        "<b>🎁 Redeem Codes:</b>\n"
        "• /admin_generateredeem amount - Create code\n\n"
        "<b>📢 Communication:</b>\n"
        "• /admin_broadcast message - Message all users\n\n"
        "<b>📺 Channel Management:</b>\n"
        "• /adminaddchannel channelid name - Add channel\n"
        "• /adminremovechannel channelid - Remove channel"
    )

    await update.message.reply_text(admin_help, parse_mode='HTML')