from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 🔐 متغيرات API
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")  # أو عيّنه يدويًا
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "<TOKEN_TA3_PAGE>")

# 📤 دالة إرسال رسالة
def send_message(recipient_id, text, quick_replies=None):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }

    if quick_replies:
        payload["message"]["quick_replies"] = quick_replies

    response = requests.post(
        f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}",
        json=payload
    )
    return response.json()

# ✅ Webhook لربط فيسبوك
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "رمز التحقق خاطئ"

    elif request.method == "POST":
        data = request.get_json()
        if "entry" in data:
            for entry in data["entry"]:
                for messaging in entry.get("messaging", []):
                    sender_id = messaging["sender"]["id"]
                    if "message" in messaging and "text" in messaging["message"]:
                        text = messaging["message"]["text"].strip()

                        if text == "ابدأ" or text.lower() in ["start", "play"]:
                            question = "ما هي عاصمة اليابان؟\n🔤 الحروف: ط،و،ك،ي،و"
                            quick_replies = [
                                {
                                    "content_type": "text",
                                    "title": "💡 تلميح",
                                    "payload": "HINT"
                                },
                                {
                                    "content_type": "text",
                                    "title": "❌ حذف حرف",
                                    "payload": "REMOVE_LETTER"
                                },
                                {
                                    "content_type": "text",
                                    "title": "🔁 تخمين جديد",
                                    "payload": "RETRY"
                                }
                            ]
                            send_message(sender_id, question, quick_replies)

                        elif text == "💡 تلميح":
                            send_message(sender_id, "📌 التلميح: المدينة تبدأ بحرف ط وتنتهي بحرف و.")
                        elif text == "❌ حذف حرف":
                            send_message(sender_id, "❌ حذفنا حرف غير صحيح: 'ف'")
                        elif text == "🔁 تخمين جديد":
                            send_message(sender_id, "🔁 أعد المحاولة، استعمل الحروف المبعثرة.")
                        elif "طوكيو" in text:
                            send_message(sender_id, "✅ صحيح! 🎉 طوكيو هي العاصمة.")
                        else:
                            send_message(sender_id, "❌ خطأ، جرب مرة أخرى أو استعمل زر التلميح.")
        return "ok", 200

if __name__ == "__main__":
    app.run(debug=True)
