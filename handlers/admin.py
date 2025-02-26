from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from utils.database import Database
from utils.helpers import generate_unique_id, format_currency
from config import ADMIN_IDS, REDEEM_CODE_PREFIX, REQUIRED_CHANNELS

async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin_stats command"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Unauthorized access.")
        return

    users = Database.load_data("data/users.json")
    deals = Database.load_data("data/deals.json")

    total_users = len(users) - 1  # Excluding example_format
    total_deals = len(deals) - 1  # Excluding example_format
    completed_deals = len([d for d in deals.values() if d.get("status") == "completed"])
    pending_deals = len([d for d in deals.values() if d.get("status") == "pending"])

    await update.message.reply_text(
        f"📊 <b>Bot Statistics</b>\n\n"
        f"Total Users: {total_users}\n"
        f"Total Deals: {total_deals}\n"
        f"Completed Deals: {completed_deals}\n"
        f"Pending Deals: {pending_deals}",
        parse_mode='HTML'
    )

async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin_ban command"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Unauthorized access.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /admin_ban username")
        return

    username = context.args[0].replace("@", "")
    users = Database.load_data("data/users.json")

    # Find user by username
    user_id = None
    for uid, data in users.items():
        if data.get("username") == username:
            user_id = uid
            break

    if not user_id or user_id == "example_format":
        await update.message.reply_text(f"User @{username} not found.")
        return

    users[user_id]["is_banned"] = True
    Database.save_data("data/users.json", users)
    await update.message.reply_text(f"User @{username} has been banned.")

async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin_unban command"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Unauthorized access.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /admin_unban username")
        return

    username = context.args[0].replace("@", "")
    users = Database.load_data("data/users.json")

    # Find user by username
    user_id = None
    for uid, data in users.items():
        if data.get("username") == username:
            user_id = uid
            break

    if not user_id or user_id == "example_format":
        await update.message.reply_text(f"User @{username} not found.")
        return

    users[user_id]["is_banned"] = False
    Database.save_data("data/users.json", users)
    await update.message.reply_text(f"User @{username} has been unbanned.")

async def admin_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin_add_balance command"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Unauthorized access.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin_add_balance username amount")
        return

    username = context.args[0].replace("@", "")
    try:
        amount = float(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please provide a valid positive amount.")
        return

    users = Database.load_data("data/users.json")

    # Find user by username
    user_id = None
    for uid, data in users.items():
        if data.get("username") == username:
            user_id = uid
            break

    if not user_id or user_id == "example_format":
        await update.message.reply_text(f"User @{username} not found.")
        return

    users[user_id]["balance"] += amount
    Database.save_data("data/users.json", users)
    await update.message.reply_text(
        f"Added {format_currency(amount)} to @{username}'s balance.\n"
        f"New balance: {format_currency(users[user_id]['balance'])}"
    )

async def admin_remove_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin_remove_balance command"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Unauthorized access.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /admin_remove_balance username amount")
        return

    username = context.args[0].replace("@", "")
    try:
        amount = float(context.args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please provide a valid positive amount.")
        return

    users = Database.load_data("data/users.json")

    # Find user by username
    user_id = None
    for uid, data in users.items():
        if data.get("username") == username:
            user_id = uid
            break

    if not user_id or user_id == "example_format":
        await update.message.reply_text(f"User @{username} not found.")
        return

    if users[user_id]["balance"] < amount:
        await update.message.reply_text(f"Insufficient balance for @{username}.")
        return

    users[user_id]["balance"] -= amount
    Database.save_data("data/users.json", users)
    await update.message.reply_text(
        f"Removed {format_currency(amount)} from @{username}'s balance.\n"
        f"New balance: {format_currency(users[user_id]['balance'])}"
    )

async def admin_generateredeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin_generateredeem command"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Unauthorized access.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /admin_generateredeem amount")
        return

    try:
        amount = float(context.args[0])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please provide a valid positive amount.")
        return

    code = generate_unique_id(REDEEM_CODE_PREFIX)
    code_data = {
        "amount": amount,
        "used": False,
        "created_by": update.effective_user.id,
        "used_by": None
    }

    Database.save_redeem_code(code, code_data)
    await update.message.reply_text(
        f"<b>🎁 Redeem Code Generated</b>\n\n"
        f"Code: <code>{code}</code>\n"
        f"Amount: {format_currency(amount)}",
        parse_mode='HTML'
    )

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin_broadcast command"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Unauthorized access.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /admin_broadcast message")
        return

    message = " ".join(context.args)
    users = Database.load_data("data/users.json")
    sent_count = 0

    for user_id, user_data in users.items():
        if user_id == "example_format":
            continue
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"📢 <b>Broadcast Message</b>\n\n{message}",
                parse_mode='HTML'
            )
            sent_count += 1
        except Exception:
            continue

    await update.message.reply_text(f"Broadcast sent to {sent_count} users.")

async def admin_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adminaddchannel command"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Unauthorized access.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /adminaddchannel channelid name")
        return

    channel_id = context.args[0]
    channel_name = " ".join(context.args[1:])

    # Add channel to config
    if not channel_id.startswith("@"):
        channel_id = f"@{channel_id}"

    if channel_id not in REQUIRED_CHANNELS:
        REQUIRED_CHANNELS.append(channel_id)
        await update.message.reply_text(
            f"Channel {channel_id} ({channel_name}) added to required channels."
        )
    else:
        await update.message.reply_text("This channel is already in the list.")

async def admin_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adminremovechannel command"""
    if not await is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ Unauthorized access.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /adminremovechannel channelid")
        return

    channel_id = context.args[0]
    if not channel_id.startswith("@"):
        channel_id = f"@{channel_id}"

    if channel_id in REQUIRED_CHANNELS:
        REQUIRED_CHANNELS.remove(channel_id)
        await update.message.reply_text(f"Channel {channel_id} removed from required channels.")
    else:
        await update.message.reply_text("This channel is not in the list.")


def add_admin_handlers(dispatcher):
    dispatcher.add_handler(CommandHandler("admin_stats", admin_stats))
    dispatcher.add_handler(CommandHandler("admin_ban", admin_ban))
    dispatcher.add_handler(CommandHandler("admin_unban", admin_unban))
    dispatcher.add_handler(CommandHandler("admin_add_balance", admin_add_balance))
    dispatcher.add_handler(CommandHandler("admin_remove_balance", admin_remove_balance))
    dispatcher.add_handler(CommandHandler("admin_generateredeem", admin_generateredeem))
    dispatcher.add_handler(CommandHandler("admin_broadcast", admin_broadcast))
    dispatcher.add_handler(CommandHandler("adminaddchannel", admin_add_channel))
    dispatcher.add_handler(CommandHandler("adminremovechannel", admin_remove_channel))