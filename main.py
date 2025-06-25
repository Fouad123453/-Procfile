from flask import Flask, request
import requests
import os
import random
import string

app = Flask(__name__)

# 🛠️ إعدادات
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "PASTE_YOUR_PAGE_TOKEN")

# 🧠 تخزين البيانات المؤقتة
shared_questions = {}     # code: {question, sender_id}
awaiting_code = {}        # user_id: True
awaiting_answer = {}      # user_id: code

# ✅ إرسال رسالة مع أزرار اختيارية
def send_message(recipient_id, text, quick_replies=None):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    if quick_replies:
        payload["message"]["quick_replies"] = quick_replies

    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    return requests.post(url, json=payload)

# 🔢 توليد كود فريد
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# 🚀 Webhook الأساسي
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "رمز التحقق غير صالح"

    elif request.method == "POST":
        data = request.get_json()
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                if "message" in messaging and "text" in messaging["message"]:
                    text = messaging["message"]["text"].strip()

                    # 🔑 إدخال كود؟
                    if awaiting_code.get(sender_id):
                        code = text.upper()
                        if code in shared_questions:
                            q = shared_questions[code]
                            send_message(sender_id, f"🔎 سؤال صديقك:\n{q['question']}")
                            awaiting_answer[sender_id] = code
                        else:
                            send_message(sender_id, "❌ الكود غير صالح أو منتهي.")
                        awaiting_code[sender_id] = False
                        continue

                    # ✅ هل ينتظر جواب؟
                    if sender_id in awaiting_answer:
                        code = awaiting_answer[sender_id]
                        correct_answer = "طوكيو"
                        user_answer = text.strip()

                        if user_answer.lower() == correct_answer.lower():
                            send_message(sender_id, "✅ إجابة صحيحة: طوكيو 🇯🇵", quick_replies=[
                                {"content_type": "text", "title": "ابدأ"},
                                {"content_type": "text", "title": "📤 مشاركة السؤال"},
                                {"content_type": "text", "title": "🔑 إدخال كود"}
                            ])
                            if code in shared_questions:
                                owner_id = shared_questions[code]["sender_id"]
                                send_message(owner_id, "✅ صديقك جاوب على سؤالك بشكل صحيح!")
                        else:
                            send_message(sender_id, "❌ إجابة خاطئة. حاول مرة أخرى!", quick_replies=[
                                {"content_type": "text", "title": "ابدأ"},
                                {"content_type": "text", "title": "📤 مشاركة السؤال"},
                                {"content_type": "text", "title": "🔑 إدخال كود"}
                            ])
                            if code in shared_questions:
                                owner_id = shared_questions[code]["sender_id"]
                                send_message(owner_id, f"❌ صديقك أخطأ في سؤالك.\nإجابته كانت: ({user_answer})")
                        del awaiting_answer[sender_id]
                        continue

                    # ▶️ التعامل مع الأوامر حسب نص الزر
                    if text == "ابدأ":
                        question = "ما هي عاصمة اليابان؟\n🔤 الحروف: ط،و،ك،ي،و"
                        send_message(sender_id, question, quick_replies=[
                            {"content_type": "text", "title": "💡 تلميح"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال"},
                            {"content_type": "text", "title": "🔑 إدخال كود"}
                        ])

                    elif text == "💡 تلميح":
                        send_message(sender_id, "📌 يبدأ بحرف ط وينتهي بـ و", quick_replies=[
                            {"content_type": "text", "title": "💡 تلميح"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال"},
                            {"content_type": "text", "title": "🔑 إدخال كود"}
                        ])

                    elif text == "📤 مشاركة السؤال":
                        code = generate_code()
                        shared_questions[code] = {
                            "question": "ما هي عاصمة اليابان؟",
                            "sender_id": sender_id
                        }
                        send_message(sender_id, f"🔗 انسخ وابعث الكود لصديقك:\n📌 الكود: {code}", quick_replies=[
                            {"content_type": "text", "title": "🔑 إدخال كود"},
                            {"content_type": "text", "title": "ابدأ"}
                        ])

                    elif text == "🔑 إدخال كود":
                        awaiting_code[sender_id] = True
                        send_message(sender_id, "📥 أرسل كود السؤال الذي وصلك:")

                    else:
                        send_message(sender_id, "❌ لم أفهم، حاول من جديد.", quick_replies=[
                            {"content_type": "text", "title": "ابدأ"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال"},
                            {"content_type": "text", "title": "🔑 إدخال كود"}
                        ])
        return "ok", 200

# 🌀 تشغيل الخادم
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
