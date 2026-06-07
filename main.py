import os
import tempfile
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# OCR and PDF libraries
import pytesseract
from PIL import Image
import pdfplumber
from pypdf import PdfReader
import subprocess

BOT_TOKEN = "8702129419:AAFjPbH15xNtB1pt_jzn6fsTwcvcgW6U4Sc"


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF — tries pdfplumber first, falls back to OCR."""
    text = ""

    # Step 1: Try direct text extraction
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        pass

    if text.strip():
        return text.strip()

    # Step 2: No text layer found — PDF is scanned. Use OCR via pdftoppm + tesseract.
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, "page")
            subprocess.run(
                ["pdftoppm", "-jpeg", "-r", "150", file_path, prefix],
                check=True, capture_output=True
            )
            image_files = sorted(
                f for f in os.listdir(tmpdir) if f.endswith(".jpg")
            )
            for img_name in image_files:
                img_path = os.path.join(tmpdir, img_name)
                img = Image.open(img_path)
                page_text = pytesseract.image_to_string(img)
                text += page_text + "\n"
    except Exception as e:
        return f"[OCR failed: {e}]"

    return text.strip() or "[No text could be extracted]"


def extract_text_from_txt(file_path: str) -> str:
    """Read plain text files — tries UTF-8, falls back to latin-1."""
    for enc in ("utf-8", "latin-1"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read().strip()
        except UnicodeDecodeError:
            continue
    return "[Could not decode file]"


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    mime = doc.mime_type or ""
    name = doc.file_name or ""

    # Accept PDFs and plain-text files
    is_pdf = mime == "application/pdf" or name.lower().endswith(".pdf")
    is_txt = mime.startswith("text/") or name.lower().endswith((".txt", ".csv", ".log", ".md"))

    if not (is_pdf or is_txt):
        await update.message.reply_text(
            "Please send a PDF or text file (.txt, .csv, .md, etc.)."
        )
        return

    await update.message.reply_text("⏳ Processing your file, please wait...")

    try:
        tg_file = await context.bot.get_file(doc.file_id)

        with tempfile.NamedTemporaryFile(
            suffix=".pdf" if is_pdf else ".txt", delete=False
        ) as tmp:
            tmp_path = tmp.name

        await tg_file.download_to_drive(tmp_path)

        # Extract text
        if is_pdf:
            extracted = extract_text_from_pdf(tmp_path)
        else:
            extracted = extract_text_from_txt(tmp_path)

        os.unlink(tmp_path)

        # Telegram messages max out at 4096 chars — split if needed
        MAX_LEN = 4000
        if not extracted:
            await update.message.reply_text("[No text found in file]")
            return

        chunks = [extracted[i:i + MAX_LEN] for i in range(0, len(extracted), MAX_LEN)]
        for i, chunk in enumerate(chunks):
            header = f"📄 *Extracted text* (part {i+1}/{len(chunks)}):\n\n" if len(chunks) > 1 else "📄 *Extracted text:*\n\n"
            await update.message.reply_text(
                header + chunk, parse_mode="Markdown"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Error processing file: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    print(f"Received: {user_message}")
    await update.message.reply_text(f"You said: {user_message}")


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot started...")
app.run_polling()