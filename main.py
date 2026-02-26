import os
import lzma
import zipfile
import threading
import asyncio
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- 1. خادم الويب (بورت 7860) ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Extreme Compressor Online - By @Y_SH95"

def run_web():
    port = int(os.environ.get("PORT", 7860))
    web_app.run(host="0.0.0.0", port=port)

# --- 2. إعدادات البوت والحقوق ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
RIGHTS = "برمجه وتطوير @Y_SH95"

app = Client("extreme_bot", api_id=int(API_ID) if API_ID else 0, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}

# --- 3. دالة شريط التقدم ---
async def progress_bar(current, total, message, text):
    try:
        percent = current * 100 / total
        if int(percent) % 15 == 0 or current == total:
            bar = "█" * int(percent / 10) + "░" * (10 - int(percent / 10))
            await message.edit_text(f"⚙️ {text}\n\n📊 التقدم: {percent:.1f}%\n[{bar}]\n\n🛡 {RIGHTS}")
    except: pass

# --- 4. محرك الضغط الذكي (نظام القطع Chunks) ---
def compress_engine(input_file, output_file, mode, level=None):
    if mode == "xz":
        # استخدام preset 6 لضمان أقصى ضغط مستقر دون تعليق السيرفر
        my_filters = [{"id": lzma.FILTER_LZMA2, "preset": 6}]
        with lzma.open(output_file, "wb", filters=my_filters) as f_out:
            with open(input_file, "rb") as f_in:
                # معالجة الملف قطعة قطعة (Chunking) لمنع الانهيار
                while True:
                    chunk = f_in.read(1024 * 1024) # 1MB بكل مرة
                    if not chunk: break
                    f_out.write(chunk)
    else:
        # ضغط ZIP بالمستوى المطلوب
        with zipfile.ZipFile(output_file, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=level) as zipf:
            zipf.write(input_file, arcname=os.path.basename(input_file))

# --- 5. الأوامر والترحيب ---
@app.on_message(filters.command("start"))
async def start_command(client, message):
    welcome_msg = (
        "👋 أهلاً بك في بوت الضغط الفائق!\n\n"
        "📖 **طريقة الاستخدام:**\n"
        "أرسل أي ملف (فيديو، مستند، صوت) وسأقوم بضغطه لك بأقصى قوة ممكنة.\n\n"
        f"🛡 {RIGHTS}"
    )
    await message.reply_text(welcome_msg)

# --- 6. استقبال الملفات ---
@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):
    msg = await message.reply_text("📥 جاري بدء استلام الملف...")
    path = await message.download(progress=progress_bar, progress_args=(msg, "جاري التحميل من تلجرام..."))
    
    user_data[message.from_user.id] = path
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ ضغط بصيغة ZIP", callback_data="ask_zip")],
        [InlineKeyboardButton("💎 عصر فائق بصيغة XZ", callback_data="type_xz")]
    ])
    await msg.edit_text(f"✅ تم تحميل: `{os.path.basename(path)}`\n\nاختر طريقة الضغط:", reply_markup=kb)

# --- 7. معالجة الضغط ---
@app.on_callback_query()
async def on_callback(client, callback):
    data = callback.data
    user_id = callback.from_user.id
    input_p = user_data.get(user_id)

    if not input_p or not os.path.exists(input_p):
        await callback.answer("❌ الملف غير موجود!", show_alert=True)
        return

    if data == "ask_zip":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 سريع (Lvl 1)", callback_data="zip_1")],
            [InlineKeyboardButton("⚖️ متوازن (Lvl 6)", callback_data="zip_6")],
            [InlineKeyboardButton("🔥 أقصى ضغط (Lvl 9)", callback_data="zip_9")]
        ])
        await callback.message.edit_text("اختر مستوى قوة ZIP:", reply_markup=kb)
        return

    mode = "xz" if data == "type_xz" else "zip"
    level = int(data.split("_")[1]) if mode == "zip" else 6
    output_p = f"{input_p}.{mode}"
    
    await callback.message.edit_text(f"🚀 جاري العصر بتقنية {mode.upper()}...\n(يرجى الانتظار، جاري العمل بأقصى قوة)")
    
    size_before = os.path.getsize(input_p) / (1024*1024)

    try:
        # تنفيذ الضغط في خيط مستقل
        await asyncio.to_thread(compress_engine, input_p, output_p, mode, level)
        
        size_after = os.path.getsize(output_p) / (1024*1024)
        ratio = (1 - (size_after / size_before)) * 100

        await callback.message.edit_text("📤 اكتمل العصر! جاري الرفع...")
        
        await client.send_document(
            chat_id=callback.message.chat.id, 
            document=output_p,
            caption=(
                f"✅ **تم الضغط بنجاح!**\n\n"
                f"📂 **النوع:** {mode.upper()}\n"
                f"📉 **قبل:** {size_before:.2f} MB\n"
                f"📈 **بعد:** {size_after:.2f} MB\n"
                f"🔥 **نسبة السحق:** {ratio:.1f}%\n\n"
                f"🛡 {RIGHTS}"
            ),
            progress=progress_bar,
            progress_args=(callback.message, "جاري الرفع...")
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ حدث خطأ: {e}")
    finally:
        if os.path.exists(input_p): os.remove(input_p)
        if os.path.exists(output_p): os.remove(output_p)
        user_data.pop(user_id, None)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app.run()
