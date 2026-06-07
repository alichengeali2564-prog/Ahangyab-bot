import os
import re
import hmac
import hashlib
import base64
import time
import requests
import yt_dlp
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8868394177:AAHdFVVPG4-nbLhkpPMNfHsjzUQdqnsS81E"
ACR_HOST = "eu-api-v2.acrcloud.com"
ACR_ACCESS_KEY = "18029f6a2d960df0b36ffb4ea7053d4e"
ACR_SECRET_KEY = "wbM7kNRYPkNm0JZKU54NnL4whulYbCayzIHBaCjW"

def recognize_audio(file_path):
    url = f"https://{ACR_HOST}/v1/identify"
    timestamp = str(int(time.time()))
    string_to_sign = f"POST\n/v1/identify\n{ACR_ACCESS_KEY}\naudio\n1\n{timestamp}"
    signature = base64.b64encode(
        hmac.new(ACR_SECRET_KEY.encode('utf-8'), string_to_sign.encode('utf-8'), digestmod=hashlib.sha1).digest()
    ).decode('utf-8')
    with open(file_path, 'rb') as f:
        audio_data = f.read()
    files = {'sample': ('audio.mp3', audio_data, 'audio/mpeg')}
    data = {'access_key': ACR_ACCESS_KEY, 'sample_bytes': len(audio_data), 'timestamp': timestamp, 'signature': signature, 'data_type': 'audio', 'signature_version': '1'}
    response = requests.post(url, files=files, data=data, timeout=30)
    return response.json()

def download_audio_from_url(url, output_path):
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': output_path, 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}], 'quiet': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋 به ربات آهنگ‌یاب خوش اومدی! 🎵\n\n"
        "من می‌تونم آهنگ داخل ویدیوهات رو پیدا کنم!\n\n"
        "📌 کافیه لینک ویدیو رو برام بفرستی:\n"
        "• اینستاگرام 📸\n"
        "• یوتیوب ▶️\n"
        "• TikTok 🎵\n\n"
        "بفرست تا آهنگشو پیدا کنم! 🔍"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not re.match(r'https?://\S+', text):
        await update.message.reply_text("لطفاً یه لینک معتبر بفرست! 🙏")
        return
    msg = await update.message.reply_text("⏳ دارم پردازش می‌کنم...")
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'audio')
            download_audio_from_url(text, output_path)
            files = os.listdir(tmpdir)
            mp3_file = os.path.join(tmpdir, files[0]) if files else None
            if not mp3_file:
                raise Exception("فایل پیدا نشد")
            await msg.edit_text("🔍 دارم آهنگ رو شناسایی می‌کنم...")
            result = recognize_audio(mp3_file)
            if result.get('status', {}).get('code') == 0:
                music = result['metadata']['music'][0]
                title = music.get('title', 'نامشخص')
                artist = music['artists'][0]['name'] if music.get('artists') else 'نامشخص'
                album = music.get('album', {}).get('name', '')
                text_out = f"🎵 آهنگ پیدا شد!\n\n🎤 خواننده: {artist}\n🎼 عنوان: {title}"
                if album:
                    text_out += f"\n💿 آلبوم: {album}"
                ext = music.get('external_metadata', {})
                if 'spotify' in ext:
                    sid = ext['spotify'].get('track', {}).get('id', '')
                    if sid:
                        text_out += f"\n🎧 Spotify: https://open.spotify.com/track/{sid}"
                if 'youtube' in ext:
                    vid = ext['youtube'].get('vid', '')
                    if vid:
                        text_out += f"\n▶️ YouTube: https://youtube.com/watch?v={vid}"
                await msg.edit_text(text_out)
            else:
                await msg.edit_text("❌ آهنگ شناسایی نشد.")
    except Exception as e:
        await msg.edit_text(f"❌ خطا: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات شروع کرد!")
    app.run_polling()

if __name__ == '__main__':
    main()
