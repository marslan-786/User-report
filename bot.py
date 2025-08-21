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
os.makedirs(SESSIONS_DIR, exist_ok=True)

user_data = {}

# ---------------- Report Sender ----------------
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
                # --- اصل response دکھاؤ ---
                if hasattr(resp, "to_dict"):
                    resp_text = str(resp.to_dict())
                else:
                    resp_text = str(resp)

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"[{sess}] Report {i+1}/{count}:\n{resp_text}"
                )
            except Exception as e:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"[{sess}] ERROR: {e}"
                )
            await asyncio.sleep(5)  # delay between each report
        await client.disconnect()

# ---------------- Bot Handlers ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📣 Get User Report", callback_data="get_report")]]
    await update.message.reply_text("👋 Welcome! Select an option:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "get_report":
        user_data[uid] = {}
        await query.message.reply_text("🔎 Send the username or user URL to report:")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    if uid not in user_data:
        return

    if "username" not in user_data[uid]:
        user_data[uid]["username"] = update.message.text
        keyboard = [
            [InlineKeyboardButton("🚫 Spam", callback_data="reason_spam")],
            [InlineKeyboardButton("❓ Other", callback_data="reason_other")]
        ]
        await update.message.reply_text("⚡ Select report reason:",
                                        reply_markup=InlineKeyboardMarkup(keyboard))

    elif "reason" not in user_data[uid]:
        # shouldn’t happen since we use buttons
        pass

    elif "message" not in user_data[uid]:
        user_data[uid]["message"] = update.message.text
        await update.message.reply_text("📝 Now send number of reports to send:")

    elif "count" not in user_data[uid]:
        try:
            user_data[uid]["count"] = int(update.message.text)
        except:
            await update.message.reply_text("❌ Invalid number, try again.")
            return

        await update.message.reply_text("⏳ Reports sending in background...")

        # Background Task
        asyncio.create_task(send_reports(uid, update, context))

async def reason_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    if query.data == "reason_spam":
        user_data[uid]["reason"] = InputReportReasonSpam()
    elif query.data == "reason_other":
        user_data[uid]["reason"] = InputReportReasonOther()
    await query.message.reply_text("✍️ Now send a message (reason details):")

# ---------------- Run Bot ----------------
def main():
    application = Application.builder().token("8249045464:AAEN5I2fPTRV6mcahJ41UD3tU1iGQckhw5s").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern="get_report"))
    application.add_handler(CallbackQueryHandler(reason_handler, pattern="reason_.*"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    application.run_polling()

if __name__ == "__main__":
    main()