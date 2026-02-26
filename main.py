import os
import lzma
import zipfile
import threading
import time
import asyncio
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- 1. خادم الويب (متوافق مع بورت 7860) ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "System: Extreme Compressor Active - Developed by Y_SH@"

def run_web():
    port = int(os.environ.get("PORT", 7860))
    web_app.run(host="0.0.0.0", port=port)

# --- 2. إعدادات البوت والحقوق ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
RIGHTS = "برمجه وتطوير Y_SH@"

app = Client("extreme_bot", api_id=int(API_ID) if API_ID else 0, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_data = {}

# --- 3. دالة شريط التقدم ---
async def progress_bar(current, total, message, text):
    try:
        percent = current * 100 / total
        if int(percent) % 15 == 0 or current == total: # التحديث كل 15% لتجنب الحظر
            bar = "█" * int(percent / 10) + "░" * (10 - int(percent / 10))
            await message.edit_text(f"⚙️ {text}\n\n📊 التقدم: {percent:.1f}%\n[{bar}]\n\n🛡 {RIGHTS}")
    except: pass

# --- 4. محرك الضغط المزدوج ---
def compress_engine(input_file, output_file, mode):
    if mode == "xz":
        my_filters = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME}]
        with lzma.open(output_file, "wb", filters=my_filters) as f_out:
            with open(input_file, "rb") as f_in:
                while chunk := f_in.read(1024*1024):
                    f_out.write(chunk)
    else:
        with zipfile.ZipFile(output_file, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(input_file, arcname=os.path.basename(input_file))

# --- 5. استقبال الأوامر والملفات ---
@app.on_message(filters.command("start"))
async def start_command(client, message):
    welcome_msg = (
        "👋 أهلاً بك في بوت الضغط الفائق!\n\n"
        "📖 **طريقة الاستخدام:**\n"
        "أرسل أي ملف (فيديو، مستند، صوت) وسأقوم بعصره لك بأقصى قوة ممكنة.\n\n"
        f"🛡 {RIGHTS}"
    )
    await message.reply_text(welcome_msg)

@app.on_message(filters.document | filters.video | filters.audio)
async def handle_file(client, message):
    msg = await message.reply_text("📥 جاري بدء استلام الملف...")
    
    # تحميل الملف مع شريط تقدم
    path = await message.download(
        progress=progress_bar, 
        progress_args=(msg, "جاري التحميل من تلجرام...")
    )
    
    user_data[message.from_user.id] = path
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ ZIP (سريع/عادي)", callback_data="type_zip")],
        [InlineKeyboardButton("💎 XZ (عصر فائق/أصغر حجم)", callback_data="type_xz")]
    ])
    await msg.edit_text(
        f"📦 **الملف:** `{os.path.basename(path)}`\n\nاختر تقنية الضغط التي تريدها لهزيمة الخصوم:", 
        reply_markup=buttons
    )

# --- 6. معالجة الضغط والرفع ---
@app.on_callback_query(filters.regex("^type_"))
async def start_compression(client, callback):
    mode = callback.data.split("_")[1]
    user_id = callback.from_user.id
    input_p = user_data.get(user_id)
    
    if not input_p or not os.path.exists(input_p):
        await callback.answer("❌ الملف غير موجود، أرسله مجدداً!", show_alert=True)
        return

    output_p = f"{input_p}.{mode if mode == 'xz' else 'zip'}"
    await callback.message.edit_text(f"🚀 يتم الآن استخدام تقنية {mode.upper()}... انتظر المعجزة!")

    size_before = os.path.getsize(input_p) / (1024*1024)

    try:
        # تشغيل المحرك في خيط منفصل
        await asyncio.to_thread(compress_engine, input_p, output_p, mode)
        
        size_after = os.path.getsize(output_p) / (1024*1024)
        ratio = (1 - (size_after / size_before)) * 100

        await callback.message.edit_text("📤 تم سحق الملف بنجاح! جاري الرفع الآن...")
        
        await client.send_document(
            chat_id=callback.message.chat.id, 
            document=output_p,
            caption=(
                f"✅ **اكتمل العصر بنجاح!**\n\n"
                f"📂 **النوع:** {mode.upper()}\n"
                f"📉 **قبل:** {size_before:.2f} MB\n"
                f"📈 **بعد:** {size_after:.2f} MB\n"
                f"🔥 **نسبة السحق:** {ratio:.1f}%\n\n"
                f"🛡 {RIGHTS}"
            ),
            progress=progress_bar,
            progress_args=(callback.message, "جاري الرفع إلى تلجرام...")
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ حدث خطأ تقني: {e}")
    finally:
        if os.path.exists(input_p): os.remove(input_p)
        if os.path.exists(output_p): os.remove(output_p)
        user_data.pop(user_id, None)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    print("Bot is Starting... Developed by Y_SH@")
    app.run()
