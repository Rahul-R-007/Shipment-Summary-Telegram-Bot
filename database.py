import mysql.connector
from datetime import datetime

db = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="rahul",
    password="Rahul@123",
    database="telegram_bot"
)

cursor = db.cursor()

def save_pdf(chat_id, message_id, file_name, raw_text):
    current_time = datetime.now()

    sql = """
    INSERT INTO pdf_data (
        telegram_chat_id,
        telegram_message_id,
        file_name,
        raw_text,
        created_at,
        updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """

    cursor.execute(sql, (
        chat_id,
        message_id,
        file_name,
        raw_text,
        current_time,
        current_time
        ))

    db.commit()

    return cursor.lastrowid