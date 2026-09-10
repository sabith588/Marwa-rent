import os
import subprocess
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

DB_PATH = os.path.abspath("database.accdb")

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Tables", callback_data="menu_tables")],
        [InlineKeyboardButton("📤 Export DB File", callback_data="menu_export")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Send /start or upload a new .accdb file:",
        reply_markup=main_menu_keyboard(),
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if doc.file_name.endswith(".accdb") or doc.file_name.endswith(".mdb"):
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(DB_PATH)
        await update.message.reply_text(
            f"✅ File '{doc.file_name}' uploaded successfully!",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text("⚠️ Please upload a valid .accdb or .mdb file.")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_tables":
        if not os.path.exists(DB_PATH):
            await query.edit_message_text(text="⚠️ No database file found. Upload one first!", reply_markup=main_menu_keyboard())
            return

        try:
            # Use CLI tool mdb-tables to inspect schema directly
            output = subprocess.check_output(["mdb-tables", "-1", DB_PATH]).decode("utf-8")
            tables = [t.strip() for t in output.splitlines() if t.strip()]

            if tables:
                text = "📁 **Tables in Database:**\n\n" + "\n".join([f"• `{t}`" for t in tables])
            else:
                text = "No user tables found in database."

            await query.edit_message_text(text=text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Error reading tables: {e}")
            await query.edit_message_text(text=f"Error reading tables: {e}", reply_markup=main_menu_keyboard())

    elif query.data == "menu_export":
        if os.path.exists(DB_PATH):
            await query.message.reply_document(
                document=open(DB_PATH, "rb"),
                filename="database_export.accdb",
                caption="📤 Here is your current database file."
            )
        else:
            await query.edit_message_text(text="Database file not found.", reply_markup=main_menu_keyboard())

def main():
    token = ("8798939159:AAHD8tEmh2lgXGOlTC6svAf93yM-eDdYaLM")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling()

if __name__ == "__main__":
    main()
