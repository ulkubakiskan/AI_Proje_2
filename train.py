"""
Geliştirilmiş Munchkin Eğitim Scripti
PDF kuralları ile zenginleştirilmiş environment üzerinde Q-learning eğitimi
"""
import pickle, os, random
import numpy as np
from environment import MunchkinEnvironment
from agent import QLearningAgent

def train(episodes=5000, save_path="models/q_table.pkl", verbose=True):
    env   = MunchkinEnvironment()
    agent = QLearningAgent(action_space_size=5, epsilon=1.0)

    wins, total_rewards = 0, []
    milestones = {1000, 2000, 3000, 4000, 5000}

    for ep in range(1, episodes + 1):
        state   = env.reset()
        ep_rew  = 0
        done    = False
        steps   = 0
        max_steps = 300

        while not done and steps < max_steps:
            action = agent.choose_action(state, env)
            next_state, reward, done, _ = env.step(action)
            agent.learn(state, action, reward, next_state, done)
            state   = next_state
            ep_rew += reward
            steps  += 1

        agent.decay_epsilon()
        total_rewards.append(ep_rew)
        if env.player_level >= env.max_level:
            wins += 1

        if ep in milestones and verbose:
            recent   = total_rewards[-200:]
            win_rate = wins / ep * 100
            print(f"Ep {ep:5d} | Kazanma %{win_rate:.1f} | "
                  f"Ort.Ödül: {np.mean(recent):.1f} | "
                  f"Epsilon: {agent.epsilon:.3f} | "
                  f"Q-Durumlar: {len(agent.q_table):,}")

    os.makedirs("models", exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(agent.q_table, f)
    print(f"\n✅ Eğitim tamamlandı! Model kaydedildi: {save_path}")
    print(f"   Toplam kazanma: {wins}/{episodes} (%{wins/episodes*100:.1f})")
    print(f"   Q-tablo boyutu: {len(agent.q_table):,} durum")
    return agent

if __name__ == "__main__":
    train(episodes=5000)
