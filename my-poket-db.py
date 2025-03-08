import os
import logging
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from datetime import datetime

# Configura il logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.WARN)

# Configura il database PostgreSQL
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

TOKEN = os.getenv("TOKEN")
AUTHORIZED_USER_ID = os.getenv("MY_USERID")   # Sostituisci con il tuo ID Telegram

async def start(update: Update, context: CallbackContext) -> None:
    """Messaggio di benvenuto."""
    if update.message.chat_id == AUTHORIZED_USER_ID:
        await update.message.reply_text("Ciao! Invia un messaggio nel formato:\nSPESA;DARE/AVERE;CATEGORIA;DATA;NOTE")

async def log_to_db(update: Update, context: CallbackContext) -> None:
    """Legge il messaggio e lo salva nel database."""
    if update.message.chat_id == AUTHORIZED_USER_ID:
        try:
            msg = update.message.text
            parts = msg.split(";")

            if len(parts) < 4:
                await update.message.reply_text("Formato errato! Usa: SPESA;DARE/AVERE;CATEGORIA;DATA;NOTE")
                return
            
            spesa = float(parts[0])
            dare_avere = parts[1].strip().upper()
            categoria = parts[2].strip()
            data_operazione = datetime.strptime(parts[3].strip(), "%d-%m-%Y").date()
            note = parts[4].strip() if len(parts) > 4 else ""

            if dare_avere not in ["D", "A"]:
                await update.message.reply_text("Errore: il campo DARE/AVERE deve essere 'D' o 'A'.")
                return

            # Connessione al database
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Inserimento dati
            cur.execute(
                "INSERT INTO transazioni (spesa, dare_avere, categoria, data_operazione, note) VALUES (%s, %s, %s, %s, %s)",
                (spesa, dare_avere, categoria, data_operazione, note)
            )
            
            conn.commit()
            cur.close()
            conn.close()

            await update.message.reply_text("Messaggio salvato nel database!")

        except Exception as e:
            logging.error(f"Errore: {e}")
            await update.message.reply_text("Errore nel salvataggio dei dati.")

async def totale(update: Update, context: CallbackContext) -> None:
    """Calcola la somma totale delle spese per il mese corrente."""
    if update.message.chat_id == AUTHORIZED_USER_ID:
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Calcola la somma delle spese (solo per DARE) del mese corrente
            cur.execute(
                """
                SELECT COALESCE(SUM(spesa), 0) 
                FROM transazioni 
                WHERE dare_avere = 'D' 
                AND DATE_TRUNC('month', data_operazione) = DATE_TRUNC('month', CURRENT_DATE);
                """
            )
            totale_spese = cur.fetchone()[0]
            cur.close()
            conn.close()

            await update.message.reply_text(f"Totale spese di questo mese: {totale_spese:.2f}€")

        except Exception as e:
            logging.error(f"Errore nel comando /totale: {e}")
            await update.message.reply_text("Errore nel calcolo del totale delle spese.")

def main():
    """Avvia il bot."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("totale", totale))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, log_to_db))

    app.run_polling(30)

if __name__ == "__main__":
    main()
