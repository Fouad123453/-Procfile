from flask import Flask, request
import requests
import os
import random
import string

app = Flask(__name__)

# إعدادات
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "PASTE_YOUR_PAGE_TOKEN")

# تخزين مؤقت للبيانات
shared_questions = {}     # code: {question, sender_id}
awaiting_code = {}        # user_id: True (عند طلب إدخال كود)
awaiting_answer = {}      # user_id: code (بعد إدخال الكود، ننتظر الجواب)

# إرسال رسالة مع أزرار اختيارية (quick replies)
def send_message(recipient_id, text, quick_replies=None):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    if quick_replies:
        payload["message"]["quick_replies"] = quick_replies

    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    response = requests.post(url, json=payload)
    return response

# توليد كود فريد
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Webhook الأساسي
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # للتحقق من التوكين عند الإعداد
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "رمز التحقق غير صالح"

    elif request.method == "POST":
        data = request.get_json()
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]

                # التعامل مع أزرار postback
                if "postback" in messaging:
                    payload = messaging["postback"]["payload"]

                    if payload == "START":
                        question = "ما هي عاصمة اليابان؟\n🔤 الحروف: ط،و،ك،ي،و"
                        send_message(sender_id, question, quick_replies=[
                            {"content_type": "text", "title": "💡 تلميح", "payload": "HINT"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                            {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                        ])

                    elif payload == "HINT":
                        send_message(sender_id, "📌 يبدأ بحرف ط وينتهي بـ و", quick_replies=[
                            {"content_type": "text", "title": "💡 تلميح", "payload": "HINT"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                            {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                        ])

                    elif payload == "SHARE":
                        code = generate_code()
                        shared_questions[code] = {
                            "question": "ما هي عاصمة اليابان؟",
                            "sender_id": sender_id
                        }
                        send_message(sender_id, f"🔗 انسخ وابعث الكود لصديقك:\n📌 الكود: {code}", quick_replies=[
                            {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"},
                            {"content_type": "text", "title": "ابدأ", "payload": "START"}
                        ])

                    elif payload == "CODE":
                        awaiting_code[sender_id] = True
                        send_message(sender_id, "📥 أرسل كود السؤال الذي وصلك:")

                    else:
                        send_message(sender_id, "❌ لم أفهم، حاول من جديد.", quick_replies=[
                            {"content_type": "text", "title": "ابدأ", "payload": "START"},
                            {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                            {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                        ])

                # التعامل مع الرسائل النصية العادية
                elif "message" in messaging and "text" in messaging["message"]:
                    text = messaging["message"]["text"].strip()

                    # هل المستخدم ينتظر إدخال كود؟
                    if awaiting_code.get(sender_id):
                        code = text.upper()
                        if code in shared_questions:
                            q = shared_questions[code]
                            send_message(sender_id, f"🔎 سؤال صديقك:\n{q['question']}")
                            awaiting_answer[sender_id] = code  # ننتظر الجواب
                        else:
                            send_message(sender_id, "❌ الكود غير صالح أو منتهي.")
                        awaiting_code[sender_id] = False
                        continue

                    # هل المستخدم ينتظر جواب؟
                    if sender_id in awaiting_answer:
                        code = awaiting_answer[sender_id]
                        correct_answer = "طوكيو"
                        user_answer = text.strip()

                        if user_answer.lower() == correct_answer.lower():
                            send_message(sender_id, "✅ إجابة صحيحة: طوكيو 🇯🇵", quick_replies=[
                                {"content_type": "text", "title": "ابدأ", "payload": "START"},
                                {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                                {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                            ])
                            if code in shared_questions:
                                owner_id = shared_questions[code]["sender_id"]
                                send_message(owner_id, "✅ صديقك جاوب على سؤالك بشكل صحيح!")
                        else:
                            send_message(sender_id, "❌ إجابة خاطئة. حاول مرة أخرى!", quick_replies=[
                                {"content_type": "text", "title": "ابدأ", "payload": "START"},
                                {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                                {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                            ])
                            if code in shared_questions:
                                owner_id = shared_questions[code]["sender_id"]
                                send_message(owner_id, f"❌ صديقك أخطأ في سؤالك.\nإجابته كانت: ({user_answer})")

                        del awaiting_answer[sender_id]
                        continue

                    # لو الرسالة نصية عادية ومش مذكورة أعلاه
                    send_message(sender_id, "❌ لم أفهم، حاول من جديد.", quick_replies=[
                        {"content_type": "text", "title": "ابدأ", "payload": "START"},
                        {"content_type": "text", "title": "📤 مشاركة السؤال", "payload": "SHARE"},
                        {"content_type": "text", "title": "🔑 إدخال كود", "payload": "CODE"}
                    ])
        return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
