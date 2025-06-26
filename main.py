from flask import Flask, request
import os, requests, json
from datetime import datetime

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "YOUR_PAGE_ACCESS_TOKEN")

wilayas = {
    "أدرار": "Adrar", "الشلف": "Chlef", "الأغواط": "Laghouat", "أم البواقي": "Oum El Bouaghi", "باتنة": "Batna",
    "بجاية": "Bejaia", "بسكرة": "Biskra", "بشار": "Bechar", "البليدة": "Blida", "البويرة": "Bouira",
    "تمنراست": "Tamanrasset", "تبسة": "Tebessa", "تلمسان": "Tlemcen", "تيارت": "Tiaret", "تيزي وزو": "Tizi Ouzou",
    "الجزائر": "Algiers", "الجلفة": "Djelfa", "جيجل": "Jijel", "سطيف": "Setif", "سعيدة": "Saida",
    "سكيكدة": "Skikda", "سيدي بلعباس": "Sidi Bel Abbes", "عنابة": "Annaba", "قالمة": "Guelma", "قسنطينة": "Constantine",
    "المدية": "Medea", "مستغانم": "Mostaganem", "المسيلة": "M'sila", "معسكر": "Mascara", "ورقلة": "Ouargla",
    "وهران": "Oran", "البيض": "El Bayadh", "إليزي": "Illizi", "برج بوعريريج": "Bordj Bou Arreridj", "بومرداس": "Boumerdes",
    "الطارف": "El Tarf", "تندوف": "Tindouf", "تيسمسيلت": "Tissemsilt", "الوادي": "El Oued", "خنشلة": "Khenchela",
    "سوق أهراس": "Souk Ahras", "تيبازة": "Tipaza", "ميلة": "Mila", "عين الدفلى": "Ain Defla", "النعامة": "Naama",
    "عين تموشنت": "Ain Temouchent", "غرداية": "Ghardaia", "غليزان": "Relizane", "تميمون": "Timimoun", "برج باجي مختار": "Bordj Badji Mokhtar",
    "أولاد جلال": "Ouled Djellal", "بني عباس": "Beni Abbes", "عين صالح": "Ain Salah", "عين قزام": "Ain Guezzam", "تقرت": "Touggourt",
    "جانت": "Djanet", "المغير": "El Meghaier", "المنيعة": "El Meniaa"
}

def send_message(recipient_id, text, buttons=None):
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    if buttons:
        payload["message"]["quick_replies"] = buttons

    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    requests.post(url, json=payload)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "رمز التحقق غير صالح", 403

    data = request.get_json()
    for entry in data.get("entry", []):
        for msg_event in entry.get("messaging", []):
            sender_id = msg_event["sender"]["id"]
            if "message" in msg_event and "text" in msg_event["message"]:
                text = msg_event["message"]["text"].strip()

                if text == "ابدأ":
                    send_message(sender_id, "اختر خيارًا:", buttons=[
                        {"content_type": "text", "title": "📍 الموقع", "payload": "الموقع"},
                        {"content_type": "text", "title": "📌 إدخال الولاية", "payload": "الولاية"},
                        {"content_type": "text", "title": "☀️ أذكار الصباح", "payload": "صباح"},
                        {"content_type": "text", "title": "🌙 أذكار المساء", "payload": "مساء"}
                    ])

                elif text in wilayas:
                    city = wilayas[text]
                    now = datetime.now().strftime("%Y-%m-%d")
                    url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Algeria&method=3"
                    response = requests.get(url)
                    if response.status_code == 200:
                        times = response.json()["data"]["timings"]
                        prayer_msg = f"""🕌 مواقيت الصلاة في {text} ليوم {now}:

🌙 الفجر: {times['Fajr']}
🌞 الظهر: {times['Dhuhr']}
🍃 العصر: {times['Asr']}
🌇 المغرب: {times['Maghrib']}
🌙 العشاء: {times['Isha']}
🌅 الشروق: {times['Sunrise']}
"""
                        send_message(sender_id, prayer_msg)
                    else:
                        send_message(sender_id, "❌ تعذر جلب المواقيت.")

                elif text == "📌 إدخال الولاية":
                    wilaya_list = "📍 أدخل اسم ولايتك بالعربية.\nمثال: الجزائر، وهران، الشلف..."
                    send_message(sender_id, wilaya_list)

                elif text == "☀️ أذكار الصباح":
                    send_message(sender_id, "☀️ أذكار الصباح:\n1. أصبحنا وأصبح الملك لله...\n2. اللهم بك أصبحنا وبك أمسينا...\n3. قُلْ هُوَ اللَّهُ أَحَدٌ *3 مرات*")

                elif text == "🌙 أذكار المساء":
                    send_message(sender_id, "🌙 أذكار المساء:\n1. أمسينا وأمسى الملك لله...\n2. اللهم بك أمسينا وبك أصبحنا...\n3. قُلْ أَعُوذُ بِرَبِّ النَّاسِ *3 مرات*")

                elif text == "📍 الموقع":
                    send_message(sender_id, "🔗 أرسل موقعك عبر الرابط:\nhttps://www.openstreetmap.org\nثم أرسل الولاية يدويًا.")
                    
                else:
                    send_message(sender_id, "❓ لم أفهم، أرسل 'ابدأ' للاطلاع على الخيارات.")

    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
