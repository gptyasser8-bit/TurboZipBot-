import os
import zipfile
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- إعدادات البيئة ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# إنشاء التطبيق
app = Client("compressor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- نظام الفلاسك للبقاء حياً ---
web_server = Flask(__name__)

@web_server.route('/')
def home():
    return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_server.run(host='0.0.0.0', port=port)

# --- دالة الضغط ---
def compress_logic(input_path, output_path, mode):
    method = zipfile.ZIP_LZMA if mode == "ultra" else zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(output_path, 'w', compression=method) as zipf:
        zipf.write(input_path, arcname=os.path.basename(input_path))

@app.on_message(filters.document | filters.video | filters.audio)
async def on_receive(client, message):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚡ سريع", callback_data=f"fast|{message.id}"),
        InlineKeyboardButton("💎 فائق", callback_data=f"ultra|{message.id}")
    ]])
    await message.reply_text("اختر قوة الضغط:", reply_markup=kb)

@app.on_callback_query()
async def process_step(client, callback_query):
    mode, msg_id = callback_query.data.split("|")
    await callback_query.message.edit_text("⏳ جاري المعالجة...")
    
    target_msg = await client.get_messages(callback_query.message.chat.id, int(msg_id))
    file_path = await client.download_media(target_msg)
    zip_path = f"{file_path}.zip"

    # تشغيل الضغط بدون حجز الـ Loop
    await asyncio.to_thread(compress_logic, file_path, zip_path, mode)

    await client.send_document(callback_query.message.chat.id, document=zip_path)
    
    if os.path.exists(file_path): os.remove(file_path)
    if os.path.exists(zip_path): os.remove(zip_path)

# --- التشغيل الصحيح لتجنب RuntimeError ---
if __name__ == "__main__":
    # 1. تشغيل الفلاسك في خلفية منفصلة
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    # 2. تشغيل البوت باستخدام الدالة المناسبة للنسخ الحديثة
    print("Starting Bot...")
    app.run()
