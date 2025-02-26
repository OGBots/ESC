from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.database import Database
from utils.helpers import validate_amount, format_currency

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /wallet command"""
    user_data = Database.get_user(update.effective_user.id)

    if user_data.get("is_banned"):
        await update.message.reply_text("You are banned from using this bot.")
        return

    await update.message.reply_text(
        f"💰 Wallet Balance: {format_currency(user_data['balance'])}\n\n"
        f"Completed Deals: {user_data['completed_deals']}\n"
        f"Pending Deals: {user_data['pending_deals']}\n\n"
        "To add funds, please contact the admin."
    )

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /redeem command"""
    if len(context.args) != 1:
        await update.message.reply_text("Please provide the redeem code.\nUsage: /redeem OGRDM-XXXXX")
        return

    user_id = update.effective_user.id
    code = context.args[0]

    code_data = Database.get_redeem_code(code)
    if not code_data or code_data.get("used"):
        await update.message.reply_text("Invalid or already used redeem code.")
        return

    user_data = Database.get_user(user_id)
    if user_data.get("is_banned"):
        await update.message.reply_text("You are banned from using this bot.")
        return

    # Update user balance and mark code as used
    amount = code_data["amount"]
    user_data["balance"] += amount
    code_data["used"] = True
    code_data["used_by"] = user_id

    Database.save_user(user_id, user_data)
    Database.save_redeem_code(code, code_data)

    await update.message.reply_text(
        f"Successfully redeemed code!\n"
        f"Amount added: {format_currency(amount)}\n"
        f"New balance: {format_currency(user_data['balance'])}"
    )