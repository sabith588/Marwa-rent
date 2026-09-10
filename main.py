import os
import sqlite3
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

ACCDB_PATH = os.path.abspath("database.accdb")
SQLITE_PATH = os.path.abspath("database.sqlite")

def convert_accdb_to_sqlite():
    """Converts uploaded .accdb file into a native SQLite database."""
    if not os.path.exists(ACCDB_PATH):
        return False
    
    if os.path.exists(SQLITE_PATH):
        os.remove(SQLITE_PATH)

    try:
        # Get table list using mdb-tables
        tables_out = subprocess.check_output(["mdb-tables", "-1", ACCDB_PATH]).decode("utf-8")
        tables = [t.strip() for t in tables_out.splitlines() if t.strip()]

        conn = sqlite3.connect(SQLITE_PATH)
        for table in tables:
            # Dump table schema and data into SQLite
            schema_cmd = f"mdb-schema '{ACCDB_PATH}' sqlite | grep -A 100 'CREATE TABLE `{table}`'"
            csv_cmd = f"mdb-export -D '%Y-%m-%d %H:%M:%S' '{ACCDB_PATH}' '{table}'"
            
            # Export data using mdb-export
            csv_data = subprocess.check_output(["mdb-export", ACCDB_PATH, table]).decode("utf-8")
            
            # Convert schema & insert into SQLite
            cursor = conn.cursor()
            headers = csv_data.splitlines()[0].split(",")
            cols = ", ".join([f"'{h.strip('\"')}' TEXT" for h in headers])
            cursor.execute(f"CREATE TABLE IF NOT EXISTS '{table}' ({cols})")
            
            for line in csv_data.splitlines()[1:]:
                vals = line.split(",")
                if len(vals) == len(headers):
                    placeholders = ", ".join(["?"] * len(vals))
                    cursor.execute(f"INSERT INTO '{table}' VALUES ({placeholders})", [v.strip('"') for v in vals])
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Conversion error: {e}")
        return False

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 View Tables", callback_data="menu_tables")],
        [InlineKeyboardButton("📤 Export File", callback_data="menu_export")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Bot is Active!**\n\nUpload your `.accdb` file to get started.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if doc.file_name.endswith(".accdb") or doc.file_name.endswith(".mdb"):
        await update.message.reply_text("⏳ Uploading and processing database...")
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(ACCDB_PATH)
        
        # Convert file
        success = convert_accdb_to_sqlite()
        if success:
            await update.message.reply_text(
                f"✅ Database `{doc.file_name}` uploaded and indexed successfully!",
                reply_markup=main_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ File uploaded, but table conversion encountered issues.")
    else:
        await update.message.reply_text("⚠️ Please upload a valid `.accdb` file.")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu_tables":
        if not os.path.exists(SQLITE_PATH):
            await query.edit_message_text("⚠️ No database converted yet. Please upload an `.accdb` file first!", reply_markup=main_menu_keyboard())
            return

        try:
            conn = sqlite3.connect(SQLITE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            if tables:
                text = "📁 **Tables in Database:**\n\n" + "\n".join([f"• `{t}`" for t in tables])
            else:
                text = "No tables found."

            await query.edit_message_text(text=text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(text=f"Error reading tables: {e}", reply_markup=main_menu_keyboard())

    elif query.data == "menu_export":
        target = ACCDB_PATH if os.path.exists(ACCDB_PATH) else SQLITE_PATH
        if os.path.exists(target):
            await query.message.reply_document(
                document=open(target, "rb"),
                filename=os.path.basename(target),
                caption="📤 Here is your database file."
            )
        else:
            await query.edit_message_text(text="No file found to export.", reply_markup=main_menu_keyboard())

def main():
    token = ("8994211914:AAHaX3KByPR-cnOxVA72RUEGSNVGXYzr244)
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Bot starting polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
