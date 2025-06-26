import os
import subprocess
from flask import Flask, request
import telebot
import requests

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
OWNER_ID = 7131675269  # بدل هذا بـ ID تاعك في تيليجرام
running_process = None

@app.route('/webhook', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(content_types=['document'])
def handle_file(message):
    global running_process
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "🚫 غير مسموح.")
        return

    file_info = bot.get_file(message.document.file_id)
    file_name = message.document.file_name
    if not file_name.endswith(".py"):
        bot.reply_to(message, "📛 فقط ملفات .py مسموح بها.")
        return

    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_name, 'wb') as f:
        f.write(downloaded_file)

    try:
        if running_process:
            running_process.kill()

        running_process = subprocess.Popen(
            ['python3', file_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        bot.reply_to(message, f"✅ تم تشغيل: `{file_name}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {e}")

@bot.message_handler(commands=['stop'])
def stop_script(message):
    global running_process
    if message.from_user.id != OWNER_ID:
        return

    if running_process:
        running_process.kill()
        running_process = None
        bot.reply_to(message, "🛑 تم إيقاف السكريبت.")
    else:
        bot.reply_to(message, "❌ لا يوجد سكريبت قيد التشغيل.")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 أرسل ملف .py وسأقوم بتشغيله.")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
