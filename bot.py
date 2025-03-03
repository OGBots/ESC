import logging
import pytz
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    JobQueue,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from config import BOT_TOKEN
from handlers import (
    start, help_command, wallet, redeem,
    start_escrow, product_name, product_description, product_price, buyer_username,
    find_deal, approve_deal_command, decline_deal_command, confirm_deal_command,
    report_deal_command, admin_stats, admin_ban, admin_unban, admin_add_balance,
    admin_remove_balance, admin_generateredeem, admin_broadcast,
    admin_add_channel, admin_remove_channel, id_command, admin_commands,
    PRODUCT_NAME, PRODUCT_DESCRIPTION, PRODUCT_PRICE, BUYER_USERNAME
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Create JobQueue with timezone
    job_queue = JobQueue()
    job_queue.scheduler.timezone = pytz.timezone('Asia/Kolkata')

    # Create the Application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .job_queue(job_queue)
        .build()
    )

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("wallet", wallet))
    application.add_handler(CommandHandler("redeem", redeem))
    
    # Escrow conversation handler
    escrow_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("escrow", start_escrow)],
        states={
            PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_name)],
            PRODUCT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_description)],
            PRODUCT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_price)],
            BUYER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, buyer_username)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
    )
    application.add_handler(escrow_conv_handler)
    
    # Deal management commands
    application.add_handler(CommandHandler("find_deal", find_deal))
    application.add_handler(CommandHandler("approve_deal", approve_deal_command))
    application.add_handler(CommandHandler("decline_deal", decline_deal_command))
    application.add_handler(CommandHandler("confirm_deal", confirm_deal_command))
    application.add_handler(CommandHandler("report_deal", report_deal_command))
    application.add_handler(CommandHandler("id", id_command))

    # Admin commands
    application.add_handler(CommandHandler("admin_stats", admin_stats))
    application.add_handler(CommandHandler("admin_ban", admin_ban))
    application.add_handler(CommandHandler("admin_unban", admin_unban))
    application.add_handler(CommandHandler("admin_add_balance", admin_add_balance))
    application.add_handler(CommandHandler("admin_remove_balance", admin_remove_balance))
    application.add_handler(CommandHandler("admin_generateredeem", admin_generateredeem))
    application.add_handler(CommandHandler("admin_broadcast", admin_broadcast))
    application.add_handler(CommandHandler("adminaddchannel", admin_add_channel))
    application.add_handler(CommandHandler("adminremovechannel", admin_remove_channel))
    application.add_handler(CommandHandler("og", admin_commands))

    # Callback handlers
    from handlers.escrow import handle_deal_response, handle_product_delivery, process_product_delivery, handle_confirmation
    application.add_handler(CallbackQueryHandler(handle_deal_response, pattern=r"^approve_|^decline_"))
    application.add_handler(CallbackQueryHandler(handle_product_delivery, pattern=r"^send_product_"))
    application.add_handler(CallbackQueryHandler(handle_confirmation, pattern=r"^confirm_|^report_"))
    
    # Fixed media handler with correct filters
    application.add_handler(MessageHandler(
        (filters.TEXT & ~filters.COMMAND) |
        filters.PHOTO |
        filters.VIDEO |
        filters.Document.ALL |
        filters.AUDIO,
        process_product_delivery
    ))

    # Start the bot
    print("Bot is starting...")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        timeout=60,
        read_timeout=60,
        write_timeout=60,
        connect_timeout=60,
        pool_timeout=60
    )

if __name__ == '__main__':
    main()
