from flask import Flask, request
import requests
import os
import random
import string

app = Flask(__name__)

# ✅ توكنات
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "PASTE_YOUR_PAGE_TOKEN")

# 🧠 قاعدة بيانات مؤقتة للأسئلة المشاركة
shared_questions = {}  # code: {question, sender_id, answered}
awaiting_code = {}     # user_id: True لما ننتظر منه كود

# 🛠 إرسال رسالة مع أزرار
def send_message(recipient_id, text, quick_replies=None):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }

    if quick_replies:
        payload["message"]["quick_replies"] = quick_replies

    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    return requests.post(url, json=payload)

# 🔠 توليد كود عشوائي
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# 🔁 Webhook الرئيسي
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

                    # 🧠 قيد إدخال كود سؤال؟
                    if awaiting_code.get(sender_id):
                        code = text.upper()
                        if code in shared_questions:
                            q = shared_questions[code]
                            send_message(sender_id, f"🔎 سؤال صديقك:\n{q['question']}")
                            send_message(q["sender_id"], "📬 صديقك جاوب على سؤالك! ✅")

                            # أعد الأزرار
                            send_message(sender_id, "👇 اختر إجراء آخر:", quick_replies=[
                                {"content_type": "text", "title": "ابدأ", "payload": "START"},
                                {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                                {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"},
                            ])
                        else:
                            send_message(sender_id, "❌ الكود غير صالح أو منتهي.")
                        awaiting_code[sender_id] = False
                        continue

                    # ▶️ البداية
                    if text.lower() in ["ابدأ", "start"]:
                        question = "ما هي عاصمة اليابان؟\n🔤 الحروف: ط،و،ك،ي،و"
                        send_message(sender_id, question, quick_replies=[
                            {"content_type": "text", "title": "💡 تلميح", "payload": "HINT"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                            {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                        ])

                    elif text == "💡 تلميح":
                        send_message(sender_id, "📌 يبدأ بحرف ط وينتهي بـ و", quick_replies=[
                            {"content_type": "text", "title": "💡 تلميح", "payload": "HINT"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                            {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                        ])

                    elif text == "📤 مشاركة السؤال":
                        code = generate_code()
                        shared_questions[code] = {
                            "question": "ما هي عاصمة اليابان؟",
                            "sender_id": sender_id,
                            "answered": False
                        }
                        send_message(sender_id, f"🔗 انسخ وابعث الكود لصديقك:\nالكود: {code}", quick_replies=[
                            {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"},
                            {"content_type": "text", "title": "ابدأ", "payload": "START"},
                        ])

                    elif text == "🔑 إدخال كود":
                        awaiting_code[sender_id] = True
                        send_message(sender_id, "📥 أرسل الآن كود السؤال الذي وصلك:")

                    elif "طوكيو" in text:
                        send_message(sender_id, "✅ إجابة صحيحة: طوكيو 🇯🇵", quick_replies=[
                            {"content_type": "text", "title": "ابدأ", "payload": "START"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                            {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                        ])

                    else:
                        send_message(sender_id, "❌ إجابة خاطئة أو أمر غير مفهوم.", quick_replies=[
                            {"content_type": "text", "title": "ابدأ", "payload": "START"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                            {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                        ])
        return "ok", 200

# 🔁 إعداد التشغيل في Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
