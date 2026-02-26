import os
import zipfile
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- جلب البيانات الحساسة من إعدادات السيرفر (Environment Variables) ---
# ستقوم بإضافة هذه القيم في موقع Render لاحقاً لضمان الأمان
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("compressor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- نظام الفلاسك للبقاء حياً على Render ---
web_server = Flask(__name__)

@web_server.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    # Render يرسل رقم البورت عبر متغير بيئة اسمه PORT
    # إذا لم يجده (مثل التجربة المحلية) سيستخدم 8080
    port = int(os.environ.get("PORT", 8080))
    web_server.run(host='0.0.0.0', port=port)


# --- دالة الضغط الذكية ---
def compress_logic(input_path, output_path, mode):
    # استخدام LZMA للضغط الأقصى (مثل 7zip) لإبهار صديقك بالنتائج
    method = zipfile.ZIP_LZMA if mode == "ultra" else zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(output_path, 'w', compression=method) as zipf:
        zipf.write(input_path, arcname=os.path.basename(input_path))

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def on_receive(client, message):
    # إنشاء أزرار تفاعلية
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ ضغط سريع (ZIP)", callback_data=f"fast|{message.id}")],
        [InlineKeyboardButton("💎 ضغط فائق (LZMA)", callback_data=f"ultra|{message.id}")]
    ])
    await message.reply_text("📥 استلمت الملف! اختر قوة الضغط لنهزم التحدي:", reply_markup=kb)

@app.on_callback_query()
async def process_step(client, callback_query):
    mode, msg_id = callback_query.data.split("|")
    chat_id = callback_query.message.chat.id
    
    await callback_query.message.edit_text("⏳ جاري التحميل والضغط... قد يستغرق الأمر دقائق للملفات الكبيرة.")

    # تحميل الملف من سيرفرات تلجرام
    target_msg = await client.get_messages(chat_id, int(msg_id))
    file_path = await client.download_media(target_msg)
    zip_path = f"{file_path}.zip"

    # تشغيل عملية الضغط في الخلفية لعدم تعطيل البوت
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, compress_logic, file_path, zip_path, mode)

    # إرسال النتيجة النهائية
    await client.send_document(
        chat_id, 
        document=zip_path, 
        caption=f"✅ تم الضغط بنجاح!\n⚙️ الوضع المختار: {mode.upper()}"
    )

    # تنظيف السيرفر فوراً لتوفير المساحة
    if os.path.exists(file_path): os.remove(file_path)
    if os.path.exists(zip_path): os.remove(zip_path)

if __name__ == "__main__":
    # تشغيل موقع ويب صغير في الخلفية
    Thread(target=run_flask).start()
    # تشغيل البوت الأساسي
    print("Bot is starting...")
    app.run()
