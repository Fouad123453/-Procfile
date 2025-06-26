from flask import Flask, request
import requests
import os
import subprocess

app = Flask(__name__)

# متغيرات البيئة
BOT_TOKEN = os.environ.get("BOT_TOKEN")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")

# رابط API تاع تليجرام
URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# حفظ العملية لتوقيفها لاحقاً
current_process = None

@app.route("/")
def home():
    return "✅ Bot is running on Render"

@app.route("/webhook", methods=["POST"])
def webhook():
    global current_process
    data = request.get_json()

    if "message" in data:
        msg = data["message"]
        chat_id = msg["chat"]["id"]

        # تشغيل ملف .py
        if "document" in msg:
            file_id = msg["document"]["file_id"]
            file_name = msg["document"]["file_name"]

            if file_name.endswith(".py"):
                # جلب رابط التنزيل
                file_info = requests.get(f"{URL}getFile?file_id={file_id}").json()
                file_path = file_info["result"]["file_path"]
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

                # تحميل الملف
                r = requests.get(file_url)
                with open("user_script.py", "wb") as f:
                    f.write(r.content)

                # تشغيل الكود
                try:
                    if current_process:
                        current_process.kill()
                    current_process = subprocess.Popen(["python3", "user_script.py"])
                    send_message(chat_id, "✅ تم تشغيل الكود بنجاح.")
                except Exception as e:
                    send_message(chat_id, f"❌ خطأ في التشغيل: {e}")
            else:
                send_message(chat_id, "❌ أرسل ملف بلاحقة `.py` فقط.")
        
        # أوامر إضافية
        elif "text" in msg:
            text = msg["text"].strip().lower()
            if text == "/stop":
                if current_process:
                    current_process.kill()
                    current_process = None
                    send_message(chat_id, "🛑 تم إيقاف الكود.")
                else:
                    send_message(chat_id, "⚠️ لا يوجد كود قيد التشغيل.")
            elif text == "/start":
                send_message(chat_id, "👋 أرسل ملف Python (.py) ليتم تشغيله على الاستضافة.")
            else:
                send_message(chat_id, "❓ أمر غير مفهوم.")

    return "ok", 200

# إرسال رسالة
def send_message(chat_id, text):
    requests.post(f"{URL}sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

# تشغيل السيرفر
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
