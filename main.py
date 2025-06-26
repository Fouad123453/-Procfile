from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "PASTE_YOUR_TOKEN")
FB_API_URL = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

wilayas = {
    "أدرار": "Adrar", "الشلف": "Chlef", "الأغواط": "Laghouat", "أم البواقي": "Oum El Bouaghi",
    "باتنة": "Batna", "بجاية": "Bejaia", "بسكرة": "Biskra", "بشار": "Bechar", "البليدة": "Blida",
    "البويرة": "Bouira", "تمنراست": "Tamanrasset", "تبسة": "Tebessa", "تلمسان": "Tlemcen",
    "تيارت": "Tiaret", "تيزي وزو": "Tizi Ouzou", "الجزائر": "Algiers", "الجلفة": "Djelfa",
    "جيجل": "Jijel", "سطيف": "Setif", "سعيدة": "Saida", "سكيكدة": "Skikda", "سيدي بلعباس": "Sidi Bel Abbes",
    "عنابة": "Annaba", "قالمة": "Guelma", "قسنطينة": "Constantine", "المدية": "Medea",
    "مستغانم": "Mostaganem", "المسيلة": "M'sila", "معسكر": "Mascara", "ورقلة": "Ouargla",
    "وهران": "Oran", "البيض": "El Bayadh", "إليزي": "Illizi", "برج بوعريريج": "Bordj Bou Arreridj",
    "بومرداس": "Boumerdes", "الطارف": "El Tarf", "تندوف": "Tindouf", "تيسمسيلت": "Tissemsilt",
    "الوادي": "El Oued", "خنشلة": "Khenchela", "سوق أهراس": "Souk Ahras", "تيبازة": "Tipaza",
    "ميلة": "Mila", "عين الدفلى": "Ain Defla", "النعامة": "Naama", "عين تموشنت": "Ain Temouchent",
    "غرداية": "Ghardaia", "غليزان": "Relizane", "تميمون": "Timimoun", "برج باجي مختار": "Bordj Badji Mokhtar",
    "أولاد جلال": "Ouled Djellal", "بني عباس": "Beni Abbes", "عين صالح": "Ain Salah",
    "عين قزام": "Ain Guezzam", "تقرت": "Touggourt", "جانت": "Djanet", "المغير": "El Meghaier",
    "المنيعة": "El Meniaa"
}

morning_azkar = """☀️ أذكار الصباح:

1. 🌅 أصبحنا وأصبح الملك لله...
2. 🕊 اللهم بك أصبحنا وبك أمسينا...
3. ☁️ رضيت بالله ربًا...
4. ✨ اللهم إني أسألك خير هذا اليوم...
5. ❤️ اللهم ما أصبح بي من نعمة...
"""

evening_azkar = """🌙 أذكار المساء:

1. 🌇 أمسينا وأمسى الملك لله...
2. 🌌 اللهم بك أمسينا وبك أصبحنا...
3. ☁️ رضيت بالله ربًا...
4. ✨ اللهم إني أسألك خير هذه الليلة...
5. ❤️ اللهم ما أمسى بي من نعمة...
"""

def send_message(recipient_id, message_data):
    payload = {
        "recipient": {"id": recipient_id},
        "message": message_data
    }
    requests.post(FB_API_URL, json=payload)

def quick_replies(text):
    return {
        "text": text,
        "quick_replies": [
            {"content_type": "text", "title": "إدخال الولاية", "payload": "enter_wilaya"},
            {"content_type": "text", "title": "أذكار الصباح", "payload": "morning_azkar"},
            {"content_type": "text", "title": "أذكار المساء", "payload": "evening_azkar"}
        ]
    }

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if token == VERIFY_TOKEN:
            return challenge
        return "Invalid verification token"

    if request.method == "POST":
        data = request.get_json()
        for entry in data.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]

                if "message" in messaging and "text" in messaging["message"]:
                    text = messaging["message"]["text"].strip()

                    if text == "إدخال الولاية":
                        send_message(sender_id, {"text": "✍️ من فضلك اكتب اسم ولايتك بالعربية:"})

                    elif text in wilayas:
                        city = wilayas[text]
                        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Algeria&method=3"
                        response = requests.get(url)
                        if response.status_code == 200:
                            data_api = response.json()
                            timings = data_api["data"]["timings"]
                            today = data_api["data"]["date"]["gregorian"]["date"]
                            msg = f"🕌 مواقيت الصلاة في {text} ليوم {today}:\n"
                            msg += f"🌙 الفجر: {timings['Fajr']}\n"
                            msg += f"🌞 الظهر: {timings['Dhuhr']}\n"
                            msg += f"🍃 العصر: {timings['Asr']}\n"
                            msg += f"🌇 المغرب: {timings['Maghrib']}\n"
                            msg += f"🌙 العشاء: {timings['Isha']}"
                            send_message(sender_id, {"text": msg})

                        else:
                            send_message(sender_id, {"text": "❌ حدث خطأ أثناء جلب مواقيت الصلاة."})

                    elif text == "أذكار الصباح":
                        send_message(sender_id, {"text": morning_azkar})

                    elif text == "أذكار المساء":
                        send_message(sender_id, {"text": evening_azkar})

                    else:
                        send_message(sender_id, quick_replies("مرحبًا! اختر أحد الخيارات التالية:"))

        return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
