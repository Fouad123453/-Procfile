from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "PASTE_YOUR_PAGE_TOKEN")

# دالة لإرسال رسالة مع quick replies
def send_message(recipient_id, text, quick_replies=None):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    if quick_replies:
        payload["message"]["quick_replies"] = quick_replies

    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    response = requests.post(url, json=payload)
    return response.json()

# الواجهة الرئيسية - quick replies
def main_menu():
    return [
        {"content_type": "text", "title": "📍 إدخال الولاية", "payload": "ENTER_WILAYA"},
        {"content_type": "text", "title": "☀️ أذكار الصباح", "payload": "MORNING_AZKAR"},
        {"content_type": "text", "title": "🌙 أذكار المساء", "payload": "EVENING_AZKAR"},
        {"content_type": "text", "title": "📖 قراءة القرآن", "payload": "READ_QURAN"},
        {"content_type": "text", "title": "📌 حفظ الآية", "payload": "SAVE_AYA"},
        {"content_type": "text", "title": "🔙 الرجوع للآية المحفوظة", "payload": "RETURN_AYA"}
    ]

# المتغيرات لتخزين بيانات مؤقتة (مثال)
user_saved_ayah = {}

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # التحقق من التوكن
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Invalid verification token"

    elif request.method == 'POST':
        data = request.get_json()
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                
                if "message" in messaging and "text" in messaging["message"]:
                    text = messaging["message"]["text"].strip()
                    payload = messaging["message"].get("quick_reply", {}).get("payload")

                    # لو استعمل quick reply
                    if payload:
                        if payload == "ENTER_WILAYA":
                            send_message(sender_id, "✍️ من فضلك اكتب اسم ولايتك:")
                        elif payload == "MORNING_AZKAR":
                            azkar = "☀️ أذكار الصباح:\n1. أصبحنا وأصبح الملك لله..."
                            send_message(sender_id, azkar, quick_replies=main_menu())
                        elif payload == "EVENING_AZKAR":
                            azkar = "🌙 أذكار المساء:\n1. أمسينا وأمسى الملك لله..."
                            send_message(sender_id, azkar, quick_replies=main_menu())
                        elif payload == "READ_QURAN":
                            send_message(sender_id, "📖 أرسل رقم السورة والآية لقراءتها، مثلاً: 2:255")
                        elif payload == "SAVE_AYA":
                            send_message(sender_id, "📌 أرسل الآية التي تريد حفظها:")
                        elif payload == "RETURN_AYA":
                            saved = user_saved_ayah.get(sender_id, "لا توجد آيات محفوظة حتى الآن.")
                            send_message(sender_id, f"📋 الآيات المحفوظة:\n{saved}", quick_replies=main_menu())
                        else:
                            send_message(sender_id, "❌ خيار غير معروف.", quick_replies=main_menu())

                    else:
                        # استقبال الردود النصية حسب حالة المستخدم
                        # مثلاً: هنا تخزن الآيات المحفوظة مؤقتًا
                        if text.startswith("حفظ:"):
                            ayah = text[4:].strip()
                            user_saved_ayah[sender_id] = ayah
                            send_message(sender_id, "✅ تم حفظ الآية.", quick_replies=main_menu())
                        else:
                            send_message(sender_id, "مرحبا! اختر من القائمة:", quick_replies=main_menu())
        return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
