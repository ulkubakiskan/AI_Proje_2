from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import numpy as np
import random
import os
import torch

from environment import MunchkinEnvironment
from agent import DQNAgent

app = FastAPI(title="Munchkin AI")
app.mount("/static", StaticFiles(directory="static"), name="static")
try:
    app.mount("/docs", StaticFiles(directory="docs"), name="docs")
except Exception:
    pass

env = MunchkinEnvironment()
agent = DQNAgent(state_dim=9, action_space_size=5)

# PyTorch Model Yükleme
MODEL_PATH = "models/dqn_model.pth"
if os.path.exists(MODEL_PATH):
    try:
        # Ajanın device ayarına göre CPU veya GPU'ya yükle
        agent.policy_net.load_state_dict(torch.load(MODEL_PATH, map_location=agent.device, weights_only=True))
        agent.policy_net.eval()  # Ağı değerlendirme moduna al
        agent.epsilon = agent.min_epsilon  # Eğitilmiş model olduğu için rastgeleliği (keşfi) minimuma indir
        print("DQN Modeli başarıyla yüklendi!")
    except Exception as e:
        print(f"Model yüklenirken hata oluştu: {e}")
else:
    print("Model bulunamadı, sıfırdan başlıyor.")

state = env.reset()
step_count = 0

# İstatistikler
stats = {"games": 0, "wins": 0, "total_steps": 0}

ACTION_NAMES = {
    0: "⚔️ SALDIRI!",
    1: "🏃 KAÇ!",
    2: "🎒 EKİPMAN GİY!",
    3: "🛡️ SAVUNMA!",
    4: "🤝 YARDIM ÇAĞIR!",
}


def get_agent_action():
    """DQN ile ajan aksiyonu seç"""
    action = agent.choose_action(state, env)

    # index.html 'q-table' stringini beklediği için uyumluluk adına bu ismi dönüyoruz.
    # Frontend'de css bozulmaması için yapıldı, ancak arkada çalışan sistem artık bir Sinir Ağı.
    mode = "q-table"

    return action, mode


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/reset")
async def reset_game():
    global state, step_count
    state = env.reset()
    step_count = 0
    return {"message": "Yeni oyun başladı!", "status": env.get_status_dict()}


@app.get("/play-step")
async def play_step():
    global state, step_count

    if env.player_level >= env.max_level:
        return {"status": "kazandi", "game_status": env.get_status_dict()}

    action, mode = get_agent_action()

    prev_level = env.player_level
    next_state, reward, done, event = env.step(action)

    level_up = env.player_level > prev_level

    # Online Öğrenme (DQN Deneyim Belleği ve Öğrenme Adımı)
    agent.remember(state, action, reward, next_state, done)
    agent.learn()
    agent.decay_epsilon()

    step_count += 1
    stats["total_steps"] += 1

    # ÖNEMLİ DÜZELTME: Oyun sıfırlanmadan ÖNCE durumu kaydediyoruz!
    current_game_status = env.get_status_dict()

    # Eğer ajan öldüyse, ekranda canavarla karşılaştığı anki seviyesi görünsün
    if done and env.player_level < env.max_level:
        current_game_status["player_level"] = prev_level

    final_status = "devam"
    if done:
        stats["games"] += 1
        if env.player_level >= env.max_level:
            stats["wins"] += 1
            final_status = "kazandi"
        else:
            final_status = "oldu"

        # Durum arayüze kaydedildikten SONRA yeni oyun başlat
        state = env.reset()
    else:
        state = next_state

    win_rate = f"{stats['wins'] / stats['games'] * 100:.1f}%" if stats["games"] > 0 else "—"

    return {
        "step": step_count,
        "action": ACTION_NAMES[action],
        "action_id": action,
        "agent_mode": mode,
        "reward": reward,
        "event": event,
        "level_up": level_up,
        "status": final_status,
        "stats": {**stats, "win_rate": win_rate, "epsilon": round(agent.epsilon, 3), "q_states": len(agent.memory)},
        "game_status": current_game_status,  # Artık sıfırlanmış değil, o anki durumu gönderiyor
    }


@app.get("/stats")
async def get_stats():
    return {**stats, "q_states": len(agent.memory), "epsilon": agent.epsilon}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)