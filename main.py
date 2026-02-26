import os, lzma, zipfile, threading, time, asyncio
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- نظام البقاء حياً ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Active!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- إعدادات البوت ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("ultimate_bot", api_id=int(API_ID) if API_ID else 0, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}

# --- محرك الضغط الذكي ---
def compress_engine(input_file, output_file, mode):
    if mode == "xz":
        # ضغط XZ (عصر فائق)
        my_filters = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
        with lzma.open(output_file, "wb", filters=my_filters) as f_out:
            with open(input_file, "rb") as f_in:
                while chunk := f_in.read(1024*1024): f_out.write(chunk)
    else:
        # ضغط ZIP (سريع ومشهور)
        with zipfile.ZipFile(output_file, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(input_file, arcname=os.path.basename(input_file))

@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):
    msg = await message.reply_text("📥 جاري التحميل...")
    path = await message.download()
    user_data[message.from_user.id] = path
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ ZIP (سريع)", callback_data="z_zip")],
        [InlineKeyboardButton("💎 XZ (أصغر حجم ممكن)", callback_data="z_xz")]
    ])
    await msg.edit_text(f"📦 الملف: {os.path.basename(path)}\nاختر نوع الضغط:", reply_markup=kb)

@app.on_callback_query(filters.regex("^z_"))
async def start(client, callback):
    mode = callback.data.split("_")[1]
    input_p = user_data.get(callback.from_user.id)
    output_p = f"{input_p}.{mode if mode == 'xz' else 'zip'}"
    
    await callback.message.edit_text(f"🚀 جاري الضغط بصيغة {mode.upper()}...")
    
    # حساب الحجم قبل الضغط
    size_before = os.path.getsize(input_p) / (1024*1024)
    
    await asyncio.to_thread(compress_engine, input_p, output_p, mode)
    
    # حساب الحجم بعد الضغط
    size_after = os.path.getsize(output_p) / (1024*1024)
    
    await callback.message.edit_text("📤 اكتمل الضغط! جاري الرفع...")
    await client.send_document(
        chat_id=callback.message.chat.id, 
        document=output_p,
        caption=f"✅ تم الضغط بنجاح!\n\n📉 قبل: {size_before:.2f} MB\n📈 بعد: {size_after:.2f} MB"
    )
    
    # تنظيف
    if os.path.exists(input_p): os.remove(input_p)
    if os.path.exists(output_p): os.remove(output_p)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app.run()
