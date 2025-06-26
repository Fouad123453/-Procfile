from flask import Flask, request import requests import os import datetime

app = Flask(name)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "123456") PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")

wilayas = { "أدرار": "Adrar", "الشلف": "Chlef", "الأغواط": "Laghouat", "أم البواقي": "Oum El Bouaghi", "باتنة": "Batna", "بجاية": "Bejaia", "بسكرة": "Biskra", "بشار": "Bechar", "البليدة": "Blida", "البويرة": "Bouira", "تمنراست": "Tamanrasset", "تبسة": "Tebessa", "تلمسان": "Tlemcen", "تيارت": "Tiaret", "تيزي وزو": "Tizi Ouzou", "الجزائر": "Algiers", "الجلفة": "Djelfa", "جيجل": "Jijel", "سطيف": "Setif", "سعيدة": "Saida", "سكيكدة": "Skikda", "سيدي بلعباس": "Sidi Bel Abbes", "عنابة": "Annaba", "قالمة": "Guelma", "قسنطينة": "Constantine", "المدية": "Medea", "مستغانم": "Mostaganem", "المسيلة": "M'sila", "معسكر": "Mascara", "ورقلة": "Ouargla", "وهران": "Oran", "البيض": "El Bayadh", "إليزي": "Illizi", "برج بوعريريج": "Bordj Bou Arreridj", "بومرداس": "Boumerdes", "الطارف": "El Tarf", "تندوف": "Tindouf", "تيسمسيلت": "Tissemsilt", "الوادي": "El Oued", "خنشلة": "Khenchela", "سوق أهراس": "Souk Ahras", "تيبازة": "Tipaza", "ميلة": "Mila", "عين الدفلى": "Ain Defla", "النعامة": "Naama", "عين تموشنت": "Ain Temouchent", "غرداية": "Ghardaia", "غليزان": "Relizane", "تميمون": "Timimoun", "برج باجي مختار": "Bordj Badji Mokhtar", "أولاد جلال": "Ouled Djellal", "بني عباس": "Beni Abbes", "عين صالح": "Ain Salah", "عين قزام": "Ain Guezzam", "تقرت": "Touggourt", "جانت": "Djanet", "المغير": "El Meghaier", "المنيعة": "El Meniaa" }

user_quran_state = {}  # user_id: {"sura": ..., "ayah": ...} saved_ayah = {}       # user_id: (sura, ayah)

def send_message(recipient_id, text, quick_replies=None): payload = { "recipient": {"id": recipient_id}, "message": {"text": text} } if quick_replies: payload["message"]["quick_replies"] = quick_replies url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}" requests.post(url, json=payload)

@app.route("/webhook", methods=["GET", "POST"]) def webhook(): if request.method == "GET": if request.args.get("hub.verify_token") == VERIFY_TOKEN: return request.args.get("hub.challenge") return "رمز التحقق غير صالح"

if request.method == "POST":
    data = request.get_json()
    for entry in data.get("entry", []):
        for messaging in entry.get("messaging", []):
            sender_id = messaging["sender"]["id"]
            if "message" in messaging and "text" in messaging["message"]:
                text = messaging["message"]["text"].strip()

                if sender_id in user_quran_state:
                    if text == "📖 أكمل":
                        sura = user_quran_state[sender_id]["sura"]
                        ayah = user_quran_state[sender_id]["ayah"] + 40
                        send_quran(sender_id, sura, ayah)
                        continue
                    elif text == "💾 حفظ الآية":
                        saved_ayah[sender_id] = (
                            user_quran_state[sender_id]["sura"],
                            user_quran_state[sender_id]["ayah"]
                        )
                        send_message(sender_id, "✅ تم حفظ الآية.")
                        continue
                    elif text == "📌 الرجوع إلى المحفوظ":
                        if sender_id in saved_ayah:
                            s, a = saved_ayah[sender_id]
                            send_quran(sender_id, s, a)
                        else:
                            send_message(sender_id, "❌ لا يوجد آية محفوظة.")
                        continue
                    else:
                        sura = text
                        send_quran(sender_id, sura, 1)
                        continue

                if text == "📍 إدخال الولاية":
                    send_message(sender_id, "✍️ من فضلك اكتب اسم ولايتك بالعربية:")
                    user_quran_state[sender_id] = {"awaiting_wilaya": True}

                elif sender_id in user_quran_state and user_quran_state[sender_id].get("awaiting_wilaya"):
                    wilaya = text
                    user_quran_state.pop(sender_id)
                    if wilaya in wilayas:
                        city = wilayas[wilaya]
                        url = f"https://api.aladhan.com/v1/timingsByCity?city={city}&country=Algeria&method=3"
                        res = requests.get(url).json()
                        t = res["data"]["timings"]
                        msg = f"🕌 مواقيت الصلاة في {wilaya}:

الفجر: {t['Fajr']} الظهر: {t['Dhuhr']} العصر: {t['Asr']} المغرب: {t['Maghrib']} العشاء: {t['Isha']} الشروق: {t['Sunrise']}" send_message(sender_id, msg) else: send_message(sender_id, "❌ الولاية غير معروفة.")

elif text == "☀️ أذكار الصباح":
                    send_message(sender_id, "☀️ أذكار الصباح:\n1. أصبحنا وأصبح الملك لله...\n2. اللهم بك أصبحنا...\n3. رضيت بالله ربًا...")

                elif text == "🌙 أذكار المساء":
                    send_message(sender_id, "🌙 أذكار المساء:\n1. أمسينا وأمسى الملك لله...\n2. اللهم بك أمسينا...\n3. رضيت بالله ربًا...")

                elif text == "📖 قراءة القرآن الكريم":
                    send_message(sender_id, "✍️ أدخل اسم السورة التي تريد قراءتها:")
                    user_quran_state[sender_id] = {"awaiting_sura": True}

                else:
                    send_message(sender_id, "اختر أحد الخيارات:", quick_replies=[
                        {"content_type": "text", "title": "📍 إدخال الولاية", "payload": "wilaya"},
                        {"content_type": "text", "title": "☀️ أذكار الصباح", "payload": "morning"},
                        {"content_type": "text", "title": "🌙 أذكار المساء", "payload": "evening"},
                        {"content_type": "text", "title": "📖 قراءة القرآن الكريم", "payload": "quran"},
                        {"content_type": "text", "title": "📌 الرجوع إلى المحفوظ", "payload": "restore"}
                    ])
    return "ok", 200

def send_quran(user_id, sura_name, start_ayah): url = f"https://api.quran.com:443/v4/chapters" chapters = requests.get(url).json()["chapters"] match = [c for c in chapters if c["name_arabic"] == sura_name] if not match: send_message(user_id, "❌ لم أجد هذه السورة.") return

sura_id = match[0]["id"]
ayah_url = f"https://api.quran.com:443/v4/quran/verses/uthmani?chapter_number={sura_id}"
verses = requests.get(ayah_url).json()["verses"]
chunk = verses[start_ayah - 1:start_ayah - 1 + 40]

if not chunk:
    send_message(user_id, "✅ انتهت السورة.")
    return

msg = f"📖 *{sura_name}* - من الآية {start_ayah}:

\n" for v in chunk: msg += f"﴿{v['verse_number']}﴾ {v['text_uthmani']} "

send_message(user_id, msg, quick_replies=[
    {"content_type": "text", "title": "📖 أكمل", "payload": "continue"},
    {"content_type": "text", "title": "💾 حفظ الآية", "payload": "save"},
    {"content_type": "text", "title": "📌 الرجوع إلى المحفوظ", "payload": "restore"},
])

user_quran_state[user_id] = {"sura": sura_name, "ayah": start_ayah + 40}

if name == "main": port = int(os.environ.get("PORT", 5000)) app.run(host="0.0.0.0", port=port)

