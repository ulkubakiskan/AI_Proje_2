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
    {"name": "Munchkin Savaşçısı", "emoji": "🪓", "class_idx": 0},
    {"name": "Sinsi Hırsız", "emoji": "🗡️", "class_idx": 1},
    {"name": "Kibirli Büyücü", "emoji": "🧙‍♂️", "class_idx": 2},
    {"name": "Kutsal Rahip", "emoji": "📜", "class_idx": 3},
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


def get_class_bonus(hero_name, monster_name):
    bonuses = {
        ("Sinsi Hırsız", "Uçan Kurbağa"): 3,
        ("Munchkin Savaşçısı", "İnternet Trolü"): 3,
        ("Kibirli Büyücü", "Saksı Çiçeği"): 3,
        ("Kutsal Rahip", "Gıcık Avukat"): 3,
    }
    return bonuses.get((hero_name, monster_name), 0)


# YENİ: Eşyalar efsanevi seviyeye (max 6) göre güncellendi
def get_item_base_name(slot, power):
    if power == 0: return "Boş"
    items = {
        "head": ["Kese Kağıdı", "Teneke Kova", "Boynuzlu Kask", "Kral Tacı", "Mithril Miğfer", "Görünmezlik Bandanası"],
        "body": ["Deri Yelek", "Dikenli Zırh", "Şövalye Zırhı", "Mithril Gömlek", "Ejderha Pulu Zırh",
                 "Gölge Pelerini"],
        "hand_1": ["Tahta Sopa", "Paslı Kılıç", "Cırtlak Kılıç", "Alevli Kılıç", "Lazer Kılıcı", "Sonsuzluk Kılıcı"],
        "hand_2": ["Tahta Kapak", "Demir Kalkan", "Aynalı Kalkan", "Ejderha Kalkanı", "Kuvvet Alanı", "Zaman Kalkanı"],
        "feet": ["Yırtık Çorap", "Deri Çizme", "Hızlı Bot", "Uçan Pabuç", "Işınlanma Çizmesi", "Kuantum Terlikleri"],
    }
    return items[slot][min(power - 1, 5)]


def get_item_name(slot, power):
    if power == 0: return "Boş"
    return f"{get_item_base_name(slot, power)} (+{power})"


# YENİ: Eşya Dezavantaj (Ceza) Sistemi
def get_equipment_penalty(equipment, monster_name):
    penalty = 0
    if monster_name == "Uçan Kurbağa" and equipment["body"] > 0:
        penalty += 1
    elif monster_name == "Salya Sümük" and equipment["hand_1"] > 0:
        penalty += 1
    elif monster_name == "Gıcık Avukat" and equipment["hand_2"] > 0:
        penalty += 1
    return penalty


# GÜNCELLENEN: Durum uzayı daraltması (Ceza dahil)
def extract_features(current_state, class_bonus, item_penalty):
    player_lvl, num_cards, active_power, monster_power, def_bonus, hero_class_idx, potential_upgrade = current_state
    total_power = player_lvl + active_power + def_bonus + class_bonus - item_penalty
    power_diff = total_power - monster_power
    power_diff = max(-5, min(5, power_diff))

    return (
        power_diff,
        num_cards > 0,
        potential_upgrade,
        def_bonus > 0
    )


SLOT_NAMES = {"head": "Kafa", "body": "Gövde", "hand_1": "Sağ El", "hand_2": "Sol El", "feet": "Ayaklar"}
current_hero = random.choice(HERO_CLASSES)

try:
    with open('models/q_table.pkl', 'rb') as f:
        q_table = pickle.load(f)
    print(f"Model yüklendi: {len(q_table):,} durum")
except FileNotFoundError:
    print("UYARI: Model bulunamadı. train.py çalıştırın.")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/reset")
async def reset_game():
    global state, step_count, current_hero
    current_hero = random.choice(HERO_CLASSES)
    state = env.reset(hero_class=current_hero["class_idx"])
    step_count = 1
    return {"message": "Oyun sıfırlandı."}


@app.get("/play-step")
async def play_step():
    global state, step_count, current_hero

    if env.player_level >= env.max_level:
        return {"status": "kazandi"}

    player_lvl, num_cards, active_power, monster_power, def_bonus, hero_class_idx, potential_upgrade = state

    current_monster_info = get_monster_info(monster_power)
    class_bonus = get_class_bonus(current_hero["name"], current_monster_info["name"])

    # Ceza hesaplama
    item_penalty = get_equipment_penalty(env.equipment, current_monster_info["name"])

    # YENİ Q-STATE
    q_state = extract_features(state, class_bonus, item_penalty)

    if q_state in q_table:
        q_vals = q_table[q_state].copy()
        if num_cards == 0:
            q_vals[2] = -9999
        action = int(np.argmax(q_vals))
        agent_mode = "q-table"
    else:
        # Sezgisel yedek (Ceza dahil edildi)
        total_power = player_lvl + active_power + def_bonus + class_bonus - item_penalty
        has_upgrade = env.has_upgrade_card()
        if has_upgrade and active_power < 10:
            action = 2
        elif total_power >= monster_power:
            action = 0
        elif total_power < monster_power - 3:
            action = 3
        else:
            action = random.choice([0, 1, 3])
        agent_mode = "sezgisel"

    action_names = {0: "⚔️ SALDIRI!", 1: "🏃 KAÇ!", 2: "🎒 EKİPMAN GİY!", 3: "🛡️ SAVUNMA!"}

    # Adımı at
    next_state, reward, done = env.step(action, class_bonus=class_bonus, item_penalty=item_penalty)
    new_player_lvl, new_num_cards, new_active_power, new_monster_power, new_def_bonus, _, new_upgrade = next_state

    new_monster_info = get_monster_info(new_monster_power)
    new_class_bonus = get_class_bonus(current_hero["name"], new_monster_info["name"])
    new_item_penalty = get_equipment_penalty(env.equipment, new_monster_info["name"])

    total_power = new_player_lvl + new_active_power + new_def_bonus + new_class_bonus - new_item_penalty

    status = "devam"
    if done:
        status = "kazandi" if new_player_lvl >= env.max_level else "oldu"

    # Çantadaki kartları hazırla
    formatted_cards = []
    for c in env.treasure_cards:
        gain = c["power"] - env.equipment[c["slot"]]
        formatted_cards.append({
            "name": get_item_base_name(c["slot"], c["power"]),
            "power": c["power"],
            "slot": SLOT_NAMES[c["slot"]],
            "is_upgrade": gain > 0,
            "gain": gain,
        })

    best_idx = env.get_best_card_index()

    response_data = {
        "step": step_count,
        "action_taken": action_names[action],
        "agent_mode": agent_mode,
        "reward": reward,
        "hero_info": current_hero,
        "monster_info": new_monster_info,
        "equipment": {SLOT_NAMES[k]: get_item_name(k, v) for k, v in env.equipment.items()},
        "player": {
            "level": new_player_lvl,
            "total_power": total_power,
            "def_bonus": new_def_bonus,
            "class_bonus": new_class_bonus,
            "item_penalty": new_item_penalty,  # API'ye eklendi
            "cards_list": formatted_cards,
            "active_card_power": new_active_power,
            "best_card_idx": best_idx,
            "potential_upgrade": new_upgrade,
        },
        "monster": {"power": new_monster_power},
        "status": status,
    }

    state = next_state
    step_count += 1
    return response_data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)