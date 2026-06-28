import mysql.connector

db = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="rahul",
    password="Rahul@123",
    database="telegram_bot"
)

cursor = db.cursor()

def save_pdf(chat_id, message_id, file_name, raw_text):
    sql = """
    INSERT INTO pdf_data (
        telegram_chat_id,
        telegram_message_id,
        file_name,
        raw_text
    )
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(sql, (
        chat_id,
        message_id,
        file_name,
        raw_text
    ))

    db.commit()

    return cursor.lastrowid