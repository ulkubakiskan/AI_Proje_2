import pickle
import os
import matplotlib.pyplot as plt
from environment import RPGEnvironment
from agent import QLearningAgent


def train():
    env = RPGEnvironment()
    agent = QLearningAgent(env.action_space_size)
    rewards = []

    print("Yapay Zeka Eğitiliyor. Lütfen Bekleyin...")
    for episode in range(5000):
        state = env.reset()
        done = False
        total_reward = 0
        step_count = 0

        while not done and step_count < 200:
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)
            agent.learn(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            step_count += 1

        agent.decay_epsilon()
        rewards.append(total_reward)

    # Q-Tablosunu (Beyni) Kaydet
    os.makedirs('models', exist_ok=True)
    with open('models/q_table.pkl', 'wb') as f:
        pickle.dump(agent.q_table, f)

    # Grafiği Çiz ve Kaydet
    os.makedirs('docs', exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(rewards, alpha=0.6, color='blue')
    moving_avg = [sum(rewards[max(0, i - 50):i + 1]) / min(i + 1, 51) for i in range(len(rewards))]
    plt.plot(moving_avg, color='red', linewidth=2)
    plt.title("Yapay Zeka Eğitim Süreci")
    plt.xlabel("Oyun")
    plt.ylabel("Ödül Skoru")
    plt.savefig("docs/training_results.png")

    print("Eğitim Bitti! Model ve Grafikler başarıyla kaydedildi.")


if __name__ == "__main__":
    train()