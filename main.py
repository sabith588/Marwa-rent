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

# --- KEYBOARD MENUS ---
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📖 Read (View Tables)", callback_data="crud_read")],
        [InlineKeyboardButton("➕ Create (Insert)", callback_data="crud_create")],
        [InlineKeyboardButton("✏️ Update", callback_data="crud_update")],
        [InlineKeyboardButton("❌ Delete", callback_data="crud_delete")],
        [InlineKeyboardButton("📤 Export Updated DB", callback_data="crud_export")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **MS Access CRUD Bot**\n\n"
        "Select an operation below or send standard SQL commands directly using:\n"
        "`/sql YOUR_SQL_QUERY`"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

# 1. READ: List all tables or inspect data
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "crud_read":
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            tables = [row.table_name for row in cursor.tables(tableType="TABLE")]
            conn.close()

            if tables:
                text = "📊 **Available Tables:**\n\n" + "\n".join([f"• `{t}`" for t in tables])
                text += "\n\nTo view rows, send:\n`/sql SELECT * FROM TableName`"
            else:
                text = "No tables found in database."
            await query.edit_message_text(text=text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
        except Exception as e:
            await query.edit_message_text(text=f"Error reading DB: {e}", reply_markup=main_menu_keyboard())

    elif query.data == "crud_create":
        text = "➕ **CREATE (Insert Row)**\n\nSend a command like:\n`/sql INSERT INTO TableName (Col1, Col2) VALUES ('Val1', 'Val2')`"
        await query.edit_message_text(text=text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

    elif query.data == "crud_update":
        text = "✏️ **UPDATE Row**\n\nSend a command like:\n`/sql UPDATE TableName SET Col1='NewVal' WHERE ID=1`"
        await query.edit_message_text(text=text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

    elif query.data == "crud_delete":
        text = "❌ **DELETE Row**\n\nSend a command like:\n`/sql DELETE FROM TableName WHERE ID=1`"
        await query.edit_message_text(text=text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

    elif query.data == "crud_export":
        if os.path.exists(DB_PATH):
            await query.message.reply_document(
                document=open(DB_PATH, "rb"),
                filename="updated_database.accdb",
                caption="📤 Here is your modified MS Access database."
            )
        else:
            await query.edit_message_text(text="Database file not found.", reply_markup=main_menu_keyboard())

# DYNAMIC SQL EXECUTION (Handles SELECT, INSERT, UPDATE, DELETE)
async def execute_sql(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sql_query = " ".join(context.args)
    
    if not sql_query:
        await update.message.reply_text("⚠️ Usage: `/sql YOUR_SQL_STATEMENT`", parse_mode="Markdown")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)

        # If SELECT query, fetch results
        if sql_query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            conn.close()

            if rows:
                result_text = "📖 **Results:**\n\n"
                for row in rows[:10]:  # Limit output to 10 rows for clean formatting
                    result_text += f"• {list(row)}\n"
                await update.message.reply_text(result_text, parse_mode="Markdown")
            else:
                await update.message.reply_text("No rows returned.")
        else:
            # For INSERT, UPDATE, DELETE
            conn.commit()
            conn.close()
            await update.message.reply_text("✅ SQL query executed successfully!")

    except Exception as e:
        logging.error(f"SQL Error: {e}")
        await update.message.reply_text(f"❌ **SQL Error:**\n`{e}`", parse_mode="Markdown")

# Handle uploading a new .accdb database file
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if doc.file_name.endswith(".accdb") or doc.file_name.endswith(".mdb"):
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(DB_PATH)
        await update.message.reply_text(f"✅ Database `{doc.file_name}` replaced successfully!", reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Please upload a valid `.accdb` or `.mdb` file.", parse_mode="Markdown")

def main():
    token = ("8798939159:AAHD8tEmh2lgXGOlTC6svAf93yM-eDdYaLM")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sql", execute_sql))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling()

if __name__ == "__main__":
    main()
