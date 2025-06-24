from flask import Flask, request
import json, os
import requests  # ضروري

app = Flask(__name__)

# المتغيرات البيئية
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")

# تحميل الأسئلة
with open("questions.json", "r", encoding="utf-8") as f:
    QUESTIONS = json.load(f)

# تحميل بيانات المستخدمين أو إنشاؤها
if os.path.exists("users.json"):
    with open("users.json", "r", encoding="utf-8") as f:
        USER_DATA = json.load(f)
else:
    USER_DATA = {}

def save_users():
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(USER_DATA, f, ensure_ascii=False, indent=2)

# ✅ دالة إرسال الرسالة إلى مستخدم Facebook
def send_message(user_id, text):
    url = "https://graph.facebook.com/v18.0/me/messages"
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {"id": user_id},
        "message": {"text": text}
    }

    res = requests.post(url, params=params, headers=headers, json=data)
    if res.status_code != 200:
        print("❌ فشل إرسال الرسالة:", res.text)

def get_question_by_id(qid):
    for q in QUESTIONS:
        if q["id"] == qid:
            return q
    return None

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    data = request.get_json()
    
    try:
        for entry in data["entry"]:
            for msg_event in entry["messaging"]:
                sender_id = msg_event["sender"]["id"]
                if "message" in msg_event and "text" in msg_event["message"]:
                    message = msg_event["message"]["text"].strip()
                else:
                    continue

                if message.startswith("ref:"):
                    _, qid, friend_id = message.split(":")
                    q = get_question_by_id(int(qid))
                    USER_DATA[sender_id] = USER_DATA.get(sender_id, {"points": 0, "stage": 1, "used_hints": 0})
                    USER_DATA[sender_id]["current_ref"] = {"qid": int(qid), "friend_id": friend_id}
                    send_message(sender_id, f"يمكنك مساعدة صديقك في الإجابة على السؤال التالي:\n❓ {q['question']}\n✍️ أجب الآن!")
                    save_users()
                    return "ok"

                if sender_id not in USER_DATA:
                    USER_DATA[sender_id] = {"points": 0, "stage": 1, "used_hints": 0}

                user = USER_DATA[sender_id]
                current_stage = user.get("stage", 1)
                current_question = get_question_by_id(current_stage)

                if message.lower() == "ابدأ":
                    send_message(sender_id, f"❓ المرحلة: {current_stage}\n{current_question['question']}\n✍️ أجب عن السؤال\n💡 أرسل 'الجواب' للحصول على الإجابة (خصم نقطة)\n🔁 أرسل 'مشاركة' لمشاركة السؤال")

                elif message == "الجواب":
                    user["points"] -= 1
                    user["used_hints"] += 1
                    send_message(sender_id, f"💡 الجواب هو: {current_question['answer']}\n📉 تم خصم نقطة. مجموع نقاطك: {user['points']}")

                elif message == "مشاركة":
                    ref_link = f"https://m.me/QuizBot?ref={current_question['id']}:{sender_id}"
                    send_message(sender_id, f"🧠 إذا لم تعرف الإجابة يمكنك طلب المساعدة عبر مشاركة السؤال مع أصدقائك:\n❓ {current_question['question']}\n👇 شارك الرابط:\n👉 {ref_link}")

                elif "current_ref" in user:
                    ref_info = user.pop("current_ref")
                    original_user_id = ref_info["friend_id"]
                    qid = ref_info["qid"]
                    question = get_question_by_id(qid)

                    if message.lower() == question["answer"].lower():
                        USER_DATA[sender_id]["points"] += 2
                        USER_DATA[original_user_id]["points"] += 1
                        send_message(sender_id, "🎉 تم الإجابة بنجاح وتم منحك 2 نقطة كمكافأة")
                        send_message(original_user_id, f"👏 صديقك أجاب على السؤال وساعدك!\n🎁 حصلت على 1 نقطة. مجموع نقاطك الآن: {USER_DATA[original_user_id]['points']}")
                    else:
                        send_message(sender_id, "❌ عذرًا، الإجابة المرسلة غير صحيحة. يمكنك المحاولة لاحقًا")

                elif message.lower() == current_question["answer"].lower():
                    user["stage"] += 1
                    user["points"] += 1
                    send_message(sender_id, f"✅ صحيح! حصلت على نقطة. مجموع نقاطك: {user['points']}\n❓ المرحلة التالية: {user['stage']}")

                else:
                    send_message(sender_id, "❌ عذرًا، الإجابة غير صحيحة. يمكنك المحاولة مرة أخرى أو طلب المساعدة.")

                save_users()

    except Exception as e:
        print("❌ خطأ في المعالجة:", e)

    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
