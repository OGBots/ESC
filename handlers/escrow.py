from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from utils.database import Database
from utils.helpers import generate_unique_id, calculate_fee, format_currency
from config import ESCROW_ID_PREFIX, DEFAULT_FEE_PERCENTAGE

# States for conversation handler
PRODUCT_NAME, PRODUCT_DESCRIPTION, PRODUCT_PRICE, BUYER_USERNAME = range(4)

async def start_escrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start escrow creation process"""
    user_data = Database.get_user(update.effective_user.id)

    if user_data.get("is_banned"):
        await update.message.reply_text("You are banned from using this bot.")
        return ConversationHandler.END

    await update.message.reply_text("Let's create a new escrow deal!\n\nFirst, enter the product name:")
    return PRODUCT_NAME

async def product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product name input"""
    context.user_data['product_name'] = update.message.text
    await update.message.reply_text("Great! Now enter the product description:")
    return PRODUCT_DESCRIPTION

async def product_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product description input"""
    context.user_data['product_description'] = update.message.text
    await update.message.reply_text("Enter the product price (in INR):")
    return PRODUCT_PRICE

async def product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product price input"""
    if not update.message.text.isdigit():
        await update.message.reply_text("Please enter a valid number for the price.")
        return PRODUCT_PRICE

    price = float(update.message.text)
    context.user_data['price'] = price
    await update.message.reply_text("Enter the buyer's username (without @):")
    return BUYER_USERNAME

async def buyer_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buyer username input and create escrow"""
    buyer_username = update.message.text.strip('@')
    seller_id = update.effective_user.id

    escrow_id = generate_unique_id(ESCROW_ID_PREFIX)
    fee = calculate_fee(context.user_data['price'], DEFAULT_FEE_PERCENTAGE)

    deal_data = {
        "id": escrow_id,
        "seller_id": seller_id,
        "buyer_username": buyer_username,
        "product_name": context.user_data['product_name'],
        "product_description": context.user_data['product_description'],
        "price": context.user_data['price'],
        "fee": fee,
        "status": "pending",
        "product_delivered": False
    }

    Database.save_deal(escrow_id, deal_data)

    await update.message.reply_text(
        f"Escrow deal created successfully!\n\n"
        f"Deal ID: {escrow_id}\n"
        f"Please share this ID with the buyer.\n\n"
        f"Product: {deal_data['product_name']}\n"
        f"Price: {format_currency(deal_data['price'])}\n"
        f"Fee: {format_currency(fee)}"
    )

    return ConversationHandler.END

async def find_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /find_deal command"""
    if len(context.args) != 1:
        await update.message.reply_text(
            "Please provide the deal ID.\n"
            "Usage: /find_deal OGESC-XXXXX\n\n"
            "Available actions after finding a deal:\n"
            "/approve_deal DEAL_ID - Approve the deal\n"
            "/decline_deal DEAL_ID - Decline the deal\n"
            "/confirm_deal DEAL_ID - Confirm receipt of product\n"
            "/report_deal DEAL_ID - Report an issue with the deal"
        )
        return

    deal_id = context.args[0]
    deal_data = Database.get_deal(deal_id)

    if not deal_data:
        await update.message.reply_text("Deal not found.")
        return

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{deal_id}"),
            InlineKeyboardButton("❌ Decline", callback_data=f"decline_{deal_id}")
        ]
    ]

    await update.message.reply_text(
        f"Deal Details:\n\n"
        f"Product: {deal_data['product_name']}\n"
        f"Description: {deal_data['product_description']}\n"
        f"Price: {format_currency(deal_data['price'])}\n"
        f"Fee: {format_currency(deal_data['fee'])}\n\n"
        "You can use buttons below or commands:\n"
        f"/approve_deal {deal_id}\n"
        f"/decline_deal {deal_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def approve_deal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /approve_deal command"""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /approve_deal DEAL_ID")
        return

    deal_id = context.args[0]
    deal_data = Database.get_deal(deal_id)

    if not deal_data:
        await update.message.reply_text("Deal not found.")
        return

    # Handle approval logic
    buyer_data = Database.get_user(update.effective_user.id)
    total_amount = deal_data['price'] + deal_data['fee']

    if buyer_data['balance'] < total_amount:
        await update.message.reply_text("❌ Insufficient balance. Please add funds to your wallet.")
        return

    # Update deal status and transfer funds
    deal_data['status'] = "in_progress"
    buyer_data['balance'] -= total_amount
    Database.save_deal(deal_id, deal_data)
    Database.save_user(update.effective_user.id, buyer_data)

    await update.message.reply_text(
        "✅ Deal approved! Waiting for seller to deliver the product.\n\n"
        f"Product: {deal_data['product_name']}\n"
        f"Price: {format_currency(deal_data['price'])}\n"
        f"Fee: {format_currency(deal_data['fee'])}"
    )

    # Notify seller with inline keyboard
    keyboard = [[InlineKeyboardButton("📦 Send Product", callback_data=f"send_product_{deal_id}")]]
    await context.bot.send_message(
        deal_data['seller_id'],
        f"🎉 Buyer has approved the deal {deal_id} and funds have been secured.\n\n"
        "Please send the product (text, file, or any content) in your next message.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def decline_deal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /decline_deal command"""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /decline_deal DEAL_ID")
        return

    deal_id = context.args[0]
    deal_data = Database.get_deal(deal_id)

    if not deal_data:
        await update.message.reply_text("Deal not found.")
        return

    deal_data['status'] = "declined"
    Database.save_deal(deal_id, deal_data)

    await update.message.reply_text(
        "❌ Deal declined.\n\n"
        f"Product: {deal_data['product_name']}\n"
        f"Price: {format_currency(deal_data['price'])}"
    )

    # Notify seller
    await context.bot.send_message(
        deal_data['seller_id'],
        f"Deal {deal_id} has been declined by the buyer."
    )

async def confirm_deal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /confirm_deal command"""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /confirm_deal DEAL_ID")
        return

    deal_id = context.args[0]
    deal_data = Database.get_deal(deal_id)

    if not deal_data:
        await update.message.reply_text("Deal not found.")
        return

    # Release funds to seller
    seller_data = Database.get_user(deal_data['seller_id'])
    seller_data['balance'] += deal_data['price']  # Add price without fee
    seller_data['completed_deals'] += 1

    # Update buyer's completed deals
    buyer_data = Database.get_user(update.effective_user.id)
    buyer_data['completed_deals'] += 1
    buyer_data['pending_deals'] -= 1

    # Update deal status
    deal_data['status'] = "completed"

    # Save all updates
    Database.save_user(deal_data['seller_id'], seller_data)
    Database.save_user(update.effective_user.id, buyer_data)
    Database.save_deal(deal_id, deal_data)

    await update.message.reply_text(
        f"✅ Deal {deal_id} completed successfully!\n"
        f"Product: {deal_data['product_name']}\n"
        f"Amount: {format_currency(deal_data['price'])}"
    )

    # Notify seller
    await context.bot.send_message(
        chat_id=deal_data['seller_id'],
        text=f"🎉 Deal {deal_id} completed! The buyer has confirmed receipt.\n"
             f"Funds ({format_currency(deal_data['price'])}) have been added to your wallet."
    )

async def report_deal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report_deal command"""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /report_deal DEAL_ID")
        return

    deal_id = context.args[0]
    deal_data = Database.get_deal(deal_id)

    if not deal_data:
        await update.message.reply_text("Deal not found.")
        return

    await update.message.reply_text(
        f"Issue reported for deal {deal_id}.\n"
        "Please contact the admin for support."
    )

    # Notify seller
    await context.bot.send_message(
        chat_id=deal_data['seller_id'],
        text=f"⚠️ The buyer has reported an issue with deal {deal_id}.\n"
             "Please contact admin for support."
    )

async def handle_deal_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deal approval/decline"""
    query = update.callback_query
    await query.answer()

    action, deal_id = query.data.split('_')
    deal_data = Database.get_deal(deal_id)

    if not deal_data:
        await query.edit_message_text("Deal not found.", reply_markup=None)
        return

    if action == "approve":
        # Handle approval logic
        buyer_data = Database.get_user(update.effective_user.id)
        total_amount = deal_data['price'] + deal_data['fee']

        if buyer_data['balance'] < total_amount:
            await query.edit_message_text(
                "❌ Insufficient balance. Please add funds to your wallet.",
                reply_markup=None
            )
            return

        # Update deal status and transfer funds
        deal_data['status'] = "in_progress"
        buyer_data['balance'] -= total_amount
        Database.save_deal(deal_id, deal_data)
        Database.save_user(update.effective_user.id, buyer_data)

        # Update message without inline keyboard
        await query.edit_message_text(
            "✅ Deal approved! Waiting for seller to deliver the product.\n\n"
            f"Product: {deal_data['product_name']}\n"
            f"Price: {format_currency(deal_data['price'])}\n"
            f"Fee: {format_currency(deal_data['fee'])}",
            reply_markup=None
        )

        # Notify seller with inline keyboard
        keyboard = [[InlineKeyboardButton("📦 Send Product", callback_data=f"send_product_{deal_id}")]]
        await context.bot.send_message(
            deal_data['seller_id'],
            f"🎉 Buyer has approved the deal {deal_id} and funds have been secured.\n\n"
            "Please send the product (text, file, or any content) in your next message.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif action == "decline":
        deal_data['status'] = "declined"
        Database.save_deal(deal_id, deal_data)

        # Update message without inline keyboard
        await query.edit_message_text(
            "❌ Deal declined.\n\n"
            f"Product: {deal_data['product_name']}\n"
            f"Price: {format_currency(deal_data['price'])}",
            reply_markup=None
        )

        # Notify seller
        await context.bot.send_message(
            deal_data['seller_id'],
            f"Deal {deal_id} has been declined by the buyer."
        )

async def handle_product_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product delivery from seller"""
    query = update.callback_query
    await query.answer()

    # Fix the split to handle "send_product_DEALID" format
    _, _, deal_id = query.data.split('_')
    deal_data = Database.get_deal(deal_id)

    if not deal_data or deal_data['seller_id'] != update.effective_user.id:
        await query.edit_message_text(
            "Invalid deal or unauthorized access.",
            reply_markup=None
        )
        return

    context.user_data['awaiting_product'] = deal_id
    await query.edit_message_text(
        "Please send the product (text, file, or any content) in your next message.\n"
        "I'll forward it to the buyer once received.",
        reply_markup=None
    )

async def process_product_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the product sent by seller"""
    if 'awaiting_product' not in context.user_data:
        return

    deal_id = context.user_data['awaiting_product']
    deal_data = Database.get_deal(deal_id)

    if not deal_data:
        await update.message.reply_text("Deal not found.", reply_markup=None)
        return

    # Find buyer's user_id from username (case-insensitive)
    users = Database.load_data("data/users.json")
    buyer_id = None
    buyer_username = deal_data['buyer_username'].lower()

    for uid, data in users.items():
        if (uid != "example_format" and 
            isinstance(data, dict) and 
            data.get("username", "").lower() == buyer_username):
            buyer_id = int(uid)
            break

    if not buyer_id:
        error_msg = (
            f"Error: Cannot find buyer with username @{deal_data['buyer_username']}.\n"
            "Please make sure the username is correct and the buyer has started the bot.\n"
            "Contact admin for support if needed."
        )
        print(f"Buyer lookup failed - Deal ID: {deal_id}, Buyer Username: {deal_data['buyer_username']}")
        await update.message.reply_text(error_msg, reply_markup=None)
        return

    try:
        # Forward the message to buyer
        forwarded = await update.message.copy(buyer_id)

        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm Receipt", callback_data=f"confirm_{deal_id}"),
                InlineKeyboardButton("❌ Report Issue", callback_data=f"report_{deal_id}")
            ]
        ]

        await context.bot.send_message(
            chat_id=buyer_id,
            text=f"🎁 Product received for deal {deal_id}!\n"
                 "Please confirm if you've received the product as expected:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Clear the awaiting product state
        del context.user_data['awaiting_product']

        # Update deal status
        deal_data['product_delivered'] = True
        Database.save_deal(deal_id, deal_data)

        await update.message.reply_text(
            "✅ Product has been delivered to the buyer.\n"
            "Waiting for buyer's confirmation.",
            reply_markup=None
        )

    except Exception as e:
        error_msg = (
            "Error delivering product. This might happen if:\n"
            "1. The buyer has not started the bot\n"
            "2. The buyer has blocked the bot\n"
            "Please contact support for assistance."
        )
        print(f"Error delivering product: {str(e)}")
        await update.message.reply_text(error_msg, reply_markup=None)

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buyer's confirmation of product receipt"""
    query = update.callback_query
    await query.answer()

    action, deal_id = query.data.split('_')
    deal_data = Database.get_deal(deal_id)

    if not deal_data:
        await query.edit_message_text(
            "Deal not found.",
            reply_markup=None
        )
        return

    if action == "confirm":
        # Release funds to seller
        seller_data = Database.get_user(deal_data['seller_id'])
        seller_data['balance'] += deal_data['price']  # Add price without fee
        seller_data['completed_deals'] += 1

        # Update buyer's completed deals
        buyer_data = Database.get_user(update.effective_user.id)
        buyer_data['completed_deals'] += 1
        buyer_data['pending_deals'] -= 1

        # Update deal status
        deal_data['status'] = "completed"

        # Save all updates
        Database.save_user(deal_data['seller_id'], seller_data)
        Database.save_user(update.effective_user.id, buyer_data)
        Database.save_deal(deal_id, deal_data)

        # Update the message first to remove buttons
        await query.edit_message_text(
            f"✅ Deal {deal_id} completed successfully!\n"
            f"Product: {deal_data['product_name']}\n"
            f"Amount: {format_currency(deal_data['price'])}",
            reply_markup=None
        )

        # Then send notification to seller
        await context.bot.send_message(
            chat_id=deal_data['seller_id'],
            text=f"🎉 Deal {deal_id} completed! The buyer has confirmed receipt.\n"
                 f"Funds ({format_currency(deal_data['price'])}) have been added to your wallet."
        )

    elif action == "report":
        # Handle issue report
        await query.edit_message_text(
            f"Issue reported for deal {deal_id}.\n"
            "Please contact the admin for support.",
            reply_markup=None
        )

        # Notify seller about the issue
        await context.bot.send_message(
            chat_id=deal_data['seller_id'],
            text=f"⚠️ The buyer has reported an issue with deal {deal_id}.\n"
                 "Please contact admin for support."
        )