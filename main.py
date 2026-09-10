import os
import logging
import pyodbc
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

DB_PATH = os.path.abspath("database.accdb")

def get_db_connection():
    # Uses MDBTools driver installed via Docker
    conn_str = f"Driver={{MDBTools}};DBQ={DB_PATH};"
    return pyodbc.connect(conn_str)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot connected to MS Access DB!")

async def fetch_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Replace 'YourTable' and 'ColumnName' with your database fields
        cursor.execute("SELECT TOP 5 ColumnName FROM YourTable")
        rows = cursor.fetchall()
        conn.close()

        if rows:
            text = "\n".join([f"- {row[0]}" for row in rows])
            await update.message.reply_text(f"Data from DB:\n{text}")
        else:
            await update.message.reply_text("No records found.")
    except Exception as e:
        logging.error(f"Database error: {e}")
        await update.message.reply_text(f"Database error: {e}")

def main():
    token =("8994211914:AAHaX3KByPR-cnOxVA72RUEGSNVGXYzr244")
    app = Application.builder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("data", fetch_data))
    
    app.run_polling()

if __name__ == "__main__":
    main()
