import os
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.account import ReportPeerRequest
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonFake,
    InputReportReasonViolence,
    InputReportReasonPornography,
    InputReportReasonChildAbuse,
    InputReportReasonCopyright,
    InputReportReasonOther
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# BOT CONFIG
BOT_TOKEN = "8249045464:AAEN5I2fPTRV6mcahJ41UD3tU1iGQckhw5s"
SESSIONS_DIR = "sessions"   # folder where .session files are stored
API_ID = 94575
API_HASH = "a3406de8d171bb422bb6ddf3bbd800e2"

# In-memory user flow data
user_data = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🚨 Get User Report", callback_data="get_report")]]
    await update.message.reply_text("Welcome! Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

# Callback handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_report":
        user_data[query.from_user.id] = {}
        await query.message.reply_text("Send the @username or profile link of the user to report:")

# Username capture
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if uid in user_data and "username" not in user_data[uid]:
        user_data[uid]["username"] = update.message.text.strip()

        keyboard = [
            [InlineKeyboardButton("Spam", callback_data="reason_spam")],
            [InlineKeyboardButton("Fake", callback_data="reason_fake")],
            [InlineKeyboardButton("Violence", callback_data="reason_violence")],
            [InlineKeyboardButton("Pornography", callback_data="reason_porn")],
            [InlineKeyboardButton("Child Abuse", callback_data="reason_child")],
            [InlineKeyboardButton("Copyright", callback_data="reason_copyright")],
            [InlineKeyboardButton("Other", callback_data="reason_other")]
        ]
        await update.message.reply_text("Choose the report reason:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif uid in user_data and "reason" in user_data[uid] and "message" not in user_data[uid]:
        # format: "Message | Count"
        parts = update.message.text.strip().split("|")
        if len(parts) < 2:
            await update.message.reply_text("⚠️ Please send in this format:\n\nReportMessage | NumberOfReports")
            return
        user_data[uid]["message"] = parts[0].strip()
        try:
            user_data[uid]["count"] = int(parts[1].strip())
        except:
            await update.message.reply_text("⚠️ Please enter a valid number after |")
            return

        await update.message.reply_text("✅ Report started in background... you will receive live responses here.")

        # background task
        asyncio.create_task(send_reports(uid, update, context))

# Reason selection
async def reason_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    reason_map = {
        "reason_spam": InputReportReasonSpam(),
        "reason_fake": InputReportReasonFake(),
        "reason_violence": InputReportReasonViolence(),
        "reason_porn": InputReportReasonPornography(),
        "reason_child": InputReportReasonChildAbuse(),
        "reason_copyright": InputReportReasonCopyright(),
        "reason_other": InputReportReasonOther()
    }
    user_data[uid]["reason"] = reason_map[query.data]

    if query.data == "reason_other":
        await query.message.reply_text("Please type your custom reason:")
    else:
        await query.message.reply_text("Now send the report message followed by count.\n\nFormat:\n`Report Message | NumberOfReports`")

# Actual reporting in background
async def send_reports(uid, update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = user_data[uid]
    target = data["username"]
    reason = data["reason"]
    msg = data["message"]
    count = data["count"]

    sessions = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".session")]

    for sess in sessions:
        client = TelegramClient(os.path.join(SESSIONS_DIR, sess), API_ID, API_HASH)
        await client.start()
        for i in range(count):
            try:
                resp = await client(ReportPeerRequest(peer=target, reason=reason, message=msg))
                # اصل response LIVE بھیجیں
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"[{sess}] Report {i+1}/{count}:\n{resp.to_dict()}"
                )
            except Exception as e:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"[{sess}] ERROR: {e}"
                )
            await asyncio.sleep(5)  # delay between each report
        await client.disconnect()

    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ All reports finished.")

# Main bot runner
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button, pattern="get_report"))
    app.add_handler(CallbackQueryHandler(reason_handler, pattern="reason_.*"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()

if __name__ == "__main__":
    main()