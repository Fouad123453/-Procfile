from flask import Flask, request
import requests
import os
from templates import main_menu, back_button
from wilayas import wilayas
from azkar import morning_azkar, evening_azkar
from quran import get_surah_verses, save_progress, get_saved_ayah, delete_saved_ayah

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "PASTE_YOUR_TOKEN")

URL = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

def send_message(recipient_id, message):
    payload = {
        "recipient": {"id": recipient_id},
        "message": message
    }
    requests.post(URL, json=payload)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Invalid verification token", 403

    elif request.method == "POST":
        data = request.get_json()
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]

                if "message" in messaging and "text" in messaging["message"]:
                    text = messaging["message"]["text"].strip()

                    if text == "إدخال الولاية":
                        send_message(sender_id, {"text": "✍️ من فضلك أدخل اسم ولايتك بالعربية:"})

                    elif text in wilayas:
                        send_message(sender_id, {"text": f"🕌 سيتم جلب مواقيت الصلاة لولاية {text} قريبًا."})

                    elif text == "☀️ أذكار الصباح":
                        send_message(sender_id, {"text": morning_azkar})

                    elif text == "🌙 أذكار المساء":
                        send_message(sender_id, {"text": evening_azkar})

                    elif text == "📖 قراءة القرآن الكريم":
                        send_message(sender_id, {"text": "📥 أدخل اسم السورة بالعربية لبدء القراءة:"})

                    elif text.startswith("سورة"):
                        surah = text.replace("سورة", "").strip()
                        verses = get_surah_verses(surah)
                        save_progress(sender_id, surah, 10)
                        send_message(sender_id, {"text": verses})

                    elif text == "✅ أكمل":
                        surah, idx = get_saved_ayah(sender_id)
                        verses = get_surah_verses(surah, start=idx)
                        save_progress(sender_id, surah, idx + 10)
                        send_message(sender_id, {"text": verses})

                    elif text == "🗑 حذف الحفظ":
                        delete_saved_ayah(sender_id)
                        send_message(sender_id, {"text": "✅ تم حذف التقدم المحفوظ."})

                    else:
                        # إرسال القائمة الرئيسية
                        send_message(sender_id, main_menu())

        return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
