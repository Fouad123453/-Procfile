from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ⛓️ توكنات
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")  # حطها في إعدادات Render
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "PASTE_YOUR_PAGE_TOKEN")

# 📤 دالة إرسال رسالة مع أزرار
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

# 📬 Webhook
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "رمز تحقق غير صالح"

    elif request.method == "POST":
        data = request.get_json()
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                if "message" in messaging and "text" in messaging["message"]:
                    text = messaging["message"]["text"].strip()

                    if text.lower() in ["ابدأ", "start"]:
                        question = "ما هي عاصمة اليابان؟\n🔤 الحروف: ط،و،ك،ي،و"
                        quick_replies = [
                            {"content_type": "text", "title": "💡 تلميح", "payload": "HINT"},
                            {"content_type": "text", "title": "❌ حذف حرف", "payload": "REMOVE"},
                            {"content_type": "text", "title": "🔁 تخمين جديد", "payload": "RETRY"}
                        ]
                        send_message(sender_id, question, quick_replies)

                    elif text == "💡 تلميح":
                        send_message(sender_id, "📌 التلميح: تبدأ بحرف ط وتنتهي بحرف و.")
                    elif text == "❌ حذف حرف":
                        send_message(sender_id, "❌ حذفنا حرف غير صحيح: 'ف'")
                    elif text == "🔁 تخمين جديد":
                        send_message(sender_id, "🔁 أعد المحاولة. فكر جيدًا.")
                    elif "طوكيو" in text:
                        send_message(sender_id, "✅ صحيح! 🎉 طوكيو هي العاصمة.")
                    else:
                        send_message(sender_id, "❌ خطأ. جرب من جديد أو استخدم زر التلميح.")

        return "ok", 200

# 🚀 إعداد التشغيل في Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
