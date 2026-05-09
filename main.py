from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pickle
import numpy as np
import random
from environment import RPGEnvironment

app = FastAPI(title="Munchkin AI API")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/docs", StaticFiles(directory="docs"), name="docs")

env = RPGEnvironment()
q_table = {}
state = env.reset()
step_count = 1

HERO_CLASSES = [
    {"name": "Munchkin Savaşçısı", "emoji": "🪓"},
    {"name": "Sinsi Hırsız", "emoji": "🗡️"},
    {"name": "Kibirli Büyücü", "emoji": "🧙‍♂️"},
    {"name": "Kutsal Rahip", "emoji": "📜"}
]


def get_monster_info(power):
    if power <= 2:
        return {"name": "Saksı Çiçeği", "emoji": "🪴"}
    elif power <= 5:
        return {"name": "Salya Sümük", "emoji": "🦠"}
    elif power <= 10:
        return {"name": "Uçan Kurbağa", "emoji": "🐸"}
    elif power <= 15:
        return {"name": "İnternet Trolü", "emoji": "🧌"}
    elif power <= 25:
        return {"name": "Gıcık Avukat", "emoji": "🧛‍♂️"}
    else:
        return {"name": "Plütonyum Ejderhası", "emoji": "🐉"}


# YENİ: Sınıf Avantajlarını Hesaplayan Fonksiyon
def get_class_bonus(hero_name, monster_name):
    if hero_name == "Sinsi Hırsız" and monster_name == "Uçan Kurbağa": return 3
    if hero_name == "Munchkin Savaşçısı" and monster_name == "İnternet Trolü": return 3
    if hero_name == "Kibirli Büyücü" and monster_name == "Saksı Çiçeği": return 3
    if hero_name == "Kutsal Rahip" and monster_name == "Gıcık Avukat": return 3
    return 0


def get_item_base_name(slot, power):
    if power == 0: return "Boş"
    items = {
        "head": ["Kese Kağıdı", "Teneke Kova", "Boynuzlu Kask", "Kral Tacı"],
        "body": ["Deri Yelek", "Dikenli Zırh", "Şövalye Zırhı", "Mithril Gömlek"],
        "hand_1": ["Tahta Sopa", "Paslı Kılıç", "Cırtlak Kılıç", "Alevli Kılıç"],
        "hand_2": ["Tahta Kapak", "Demir Kalkan", "Aynalı Kalkan", "Ejderha Kalkanı"],
        "feet": ["Yırtık Çorap", "Deri Çizme", "Hızlı Bot", "Uçan Pabuç"]
    }
    idx = min(power - 1, 3)
    return items[slot][idx]


def get_item_name(slot, power):
    if power == 0: return "Boş"
    return f"{get_item_base_name(slot, power)} (+{power})"


SLOT_NAMES = {
    "head": "Kafa",
    "body": "Gövde",
    "hand_1": "Sağ El",
    "hand_2": "Sol El",
    "feet": "Ayaklar"
}

current_hero = random.choice(HERO_CLASSES)

try:
    with open('models/q_table.pkl', 'rb') as f:
        q_table = pickle.load(f)
except FileNotFoundError:
    print("UYARI: Model bulunamadı.")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/reset")
async def reset_game():
    global state, step_count, current_hero
    state = env.reset()
    step_count = 1
    current_hero = random.choice(HERO_CLASSES)
    return {"message": "Oyun sıfırlandı."}


@app.get("/play-step")
async def play_step():
    global state, step_count, current_hero

    if env.player_level >= env.max_level:
        return {"status": "kazandi"}

    player_lvl, num_cards, active_power, monster_power, def_bonus = state

    # Şu anki canavarı ve sınıf bonusunu hesapla
    current_monster_info = get_monster_info(monster_power)
    class_bonus = get_class_bonus(current_hero["name"], current_monster_info["name"])

    if state in q_table:
        q_vals = q_table[state].copy()
        if num_cards == 0:
            q_vals[2] = -9999
        action = int(np.argmax(q_vals))
    else:
        valid_actions = [0, 1, 3] if num_cards == 0 else [0, 1, 2, 3]
        action = int(random.choice(valid_actions))

    action_names = {0: "⚔️ SALDIR!", 1: "🏃 KAÇ!", 2: "🎒 EKİPMAN GİY!", 3: "🛡️ SAVUNMA YAP!"}

    # Hamleyi uygularken Sınıf Bonusunu da gönderiyoruz!
    next_state, reward, done = env.step(action, class_bonus=class_bonus)

    new_player_lvl, new_num_cards, new_active_power, new_monster_power, new_def_bonus = next_state

    # Yeni turun bonuslarını ve gücünü arayüz için hazırla
    new_monster_info = get_monster_info(new_monster_power)
    new_class_bonus = get_class_bonus(current_hero["name"], new_monster_info["name"])

    total_power = new_player_lvl + new_active_power + new_def_bonus + new_class_bonus

    status = "devam"
    if done:
        status = "kazandi" if new_player_lvl >= env.max_level else "oldu"

    formatted_cards = []
    for c in env.treasure_cards:
        formatted_cards.append({
            "name": get_item_base_name(c["slot"], c["power"]),
            "power": c["power"]
        })

    response_data = {
        "step": step_count,
        "action_taken": action_names[action],
        "hero_info": current_hero,
        "monster_info": new_monster_info,
        "equipment": {SLOT_NAMES[k]: get_item_name(k, v) for k, v in env.equipment.items()},
        "player": {
            "level": new_player_lvl,
            "total_power": total_power,
            "def_bonus": new_def_bonus,
            "class_bonus": new_class_bonus,  # Yeni veriyi arayüze gönder
            "cards_list": formatted_cards,
            "active_card_power": new_active_power
        },
        "monster": {
            "power": new_monster_power
        },
        "status": status
    }

    state = next_state
    step_count += 1

    return response_data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)