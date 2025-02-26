import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from config import BOT_TOKEN
from handlers.start import start, check_join_callback
from handlers.escrow import (
    start_escrow, product_name, product_description, product_price, 
    buyer_username, find_deal, handle_deal_response, handle_product_delivery,
    process_product_delivery, handle_confirmation,
    approve_deal_command, decline_deal_command, confirm_deal_command, report_deal_command,
    PRODUCT_NAME, PRODUCT_DESCRIPTION, PRODUCT_PRICE, BUYER_USERNAME
)
from handlers.wallet import wallet, redeem
from handlers.admin import (
    admin_stats, admin_ban, admin_unban,
    admin_add_balance, admin_remove_balance,
    admin_generateredeem, admin_broadcast,
    admin_add_channel, admin_remove_channel
)
from handlers.help import help_command, admin_commands

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))

    # Help handlers
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("og", admin_commands))

    # Escrow conversation handler
    escrow_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("escrow", start_escrow)],
        states={
            PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_name)],
            PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_description)],
            PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_price)],
            BUYER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_username)],
        },
        fallbacks=[],
    )
    application.add_handler(escrow_conv_handler)

    # Deal handlers
    application.add_handler(CommandHandler("find_deal", find_deal))
    application.add_handler(CommandHandler("approve_deal", approve_deal_command))
    application.add_handler(CommandHandler("decline_deal", decline_deal_command))
    application.add_handler(CommandHandler("confirm_deal", confirm_deal_command))
    application.add_handler(CommandHandler("report_deal", report_deal_command))
    application.add_handler(CallbackQueryHandler(handle_deal_response, pattern="^(approve|decline)_"))
    application.add_handler(CallbackQueryHandler(handle_product_delivery, pattern="^send_product_"))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, process_product_delivery))
    application.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^confirm_"))
    application.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^report_"))

    # Other handlers
    application.add_handler(CommandHandler("wallet", wallet))
    application.add_handler(CommandHandler("redeem", redeem))

    # Admin handlers
    application.add_handler(CommandHandler("admin_stats", admin_stats))
    application.add_handler(CommandHandler("admin_ban", admin_ban))
    application.add_handler(CommandHandler("admin_unban", admin_unban))
    application.add_handler(CommandHandler("admin_add_balance", admin_add_balance))
    application.add_handler(CommandHandler("admin_remove_balance", admin_remove_balance))
    application.add_handler(CommandHandler("admin_generateredeem", admin_generateredeem))
    application.add_handler(CommandHandler("admin_broadcast", admin_broadcast))
    application.add_handler(CommandHandler("adminaddchannel", admin_add_channel))
    application.add_handler(CommandHandler("adminremovechannel", admin_remove_channel))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()