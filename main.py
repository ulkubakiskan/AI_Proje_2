from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pickle, numpy as np, random
from environment import MunchkinEnvironment
from agent import QLearningAgent

app = FastAPI(title="Munchkin AI")
app.mount("/static", StaticFiles(directory="static"), name="static")
try:
    app.mount("/docs", StaticFiles(directory="docs"), name="docs")
except:
    pass

env   = MunchkinEnvironment()
agent = QLearningAgent(action_space_size=5)

# Q-table yükleme (eski tablo varsa yükle, yoksa yenisini başlat)
try:
    with open("models/q_table.pkl", "rb") as f:
        loaded = pickle.load(f)
    # Eski tablo uyumluluk kontrolü
    if isinstance(loaded, dict):
        agent.q_table = loaded
        print(f"Model yüklendi: {len(agent.q_table):,} durum")
    else:
        print("Eski model formatı, yeni model başlatıldı.")
except FileNotFoundError:
    print("Model bulunamadı, sıfırdan başlıyor.")

state      = env.reset()
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
    """Agent aksiyonu seç (Q-table veya sezgisel)"""
    feats = agent.extract_features(state)
    if feats in agent.q_table:
        q_vals = agent.q_table[feats].copy()
        if state[1] == 0:
            q_vals[2] = -9999
        action = int(np.argmax(q_vals))
        mode   = "q-table"
    else:
        # Sezgisel yedek (PDF mantığına uygun)
        power_diff = state[7]  # player - monster güç farkı
        if env.has_upgrade_card() and env.active_power < 12:
            action = 2
        elif power_diff > 0:
            action = 0
        elif power_diff < -3:
            action = 3  # önce savunma
        elif power_diff < -5:
            action = 1  # kaç
        else:
            action = random.choice([3, 4])
        mode = "sezgisel"
    return action, mode


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/reset")
async def reset_game():
    global state, step_count
    state      = env.reset()
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

    # Online öğrenme
    agent.learn(state, action, reward, next_state, done)
    agent.decay_epsilon()

    step_count        += 1
    stats["total_steps"] += 1

    final_status = "devam"
    if done:
        stats["games"] += 1
        if env.player_level >= env.max_level:
            stats["wins"]   += 1
            final_status     = "kazandi"
        else:
            final_status = "oldu"
        # Yeni oyun başlat
        state = env.reset()
    else:
        state = next_state

    win_rate = f"{stats['wins']/stats['games']*100:.1f}%" if stats["games"] > 0 else "—"

    return {
        "step":         step_count,
        "action":       ACTION_NAMES[action],
        "action_id":    action,
        "agent_mode":   mode,
        "reward":       reward,
        "event":        event,
        "level_up":     level_up,
        "status":       final_status,
        "stats":        {**stats, "win_rate": win_rate, "epsilon": round(agent.epsilon, 3)},
        "game_status":  env.get_status_dict(),
    }


@app.get("/stats")
async def get_stats():
    return {**stats, "q_table_size": len(agent.q_table), "epsilon": agent.epsilon}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
