# quran.py

import requests

# حفظ التقدم في السورة
user_progress = {}  # user_id: {"sura": int, "ayah": int}

def get_surah_ayahs(sura_number):
    try:
        url = f"https://api.alquran.cloud/v1/surah/{sura_number}/ar.alafasy"
        response = requests.get(url)
        data = response.json()
        if data["status"] == "OK":
            return data["data"]["ayahs"]
        else:
            return []
    except:
        return []

def get_ayahs_batch(ayahs, start, count=10):
    batch = ayahs[start:start+count]
    return "\n".join([f"{a['numberInSurah']}. {a['text']}" for a in batch])

def save_progress(user_id, sura, ayah_index):
    user_progress[user_id] = {"sura": sura, "ayah": ayah_index}

def get_saved_progress(user_id):
    return user_progress.get(user_id)

def clear_progress(user_id):
    if user_id in user_progress:
        del user_progress[user_id]
