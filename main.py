import os
import logging
import pyodbc
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

def get_db_connection():
    conn_str = f"Driver={{MDBTools}};DBQ={DB_PATH};"
    return pyodbc.connect(conn_str)

# Main Menu Keyboard
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Tables", callback_data="menu_tables")],
        [InlineKeyboardButton("🔍 Queries / Views", callback_data="menu_queries")],
        [InlineKeyboardButton("📤 Export DB File", callback_data="menu_export")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! Choose an option or upload a new .accdb file:",
        reply_markup=main_menu_keyboard(),
    )

# Handle Upload of new .accdb file
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if doc.file_name.endswith(".accdb") or doc.file_name.endswith(".mdb"):
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(DB_PATH)
        await update.message.reply_text(
            f"✅ Database '{doc.file_name}' uploaded successfully!",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text("⚠️ Please upload a valid .accdb or .mdb file.")

# Handle Button Clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_tables":
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Fetch table names from metadata
            tables = [row.table_name for row in cursor.tables(tableType="TABLE")]
            conn.close()

            if tables:
                text = "📁 **Tables in Database:**\n\n" + "\n".join([f"• {t}" for t in tables])
            else:
                text = "No user tables found."
            await query.edit_message_text(text=text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(text=f"Error reading tables: {e}", reply_markup=main_menu_keyboard())

    elif query.data == "menu_queries":
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Fetch queries/views from metadata
            views = [row.table_name for row in cursor.tables(tableType="VIEW")]
            conn.close()

            if views:
                text = "🔍 **Queries/Views in Database:**\n\n" + "\n".join([f"• {v}" for v in views])
            else:
                text = "No saved queries/views found."
            await query.edit_message_text(text=text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(text=f"Error reading queries: {e}", reply_markup=main_menu_keyboard())

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
    token = ("8994211914:AAHaX3KByPR-cnOxVA72RUEGSNVGXYzr244")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
