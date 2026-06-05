import os
import random
import numpy as np
import matplotlib.pyplot as plt
import torch

from environment import MunchkinEnvironment
from agent import DQNAgent


def train(episodes=10000, save_path="models/dqn_model.pth", verbose=True):
    env = MunchkinEnvironment()
    agent = DQNAgent(state_dim=9, action_space_size=5, epsilon=1.0)

    wins = 0
    total_rewards = []
    episode_lengths = []
    win_history = []

    # Loglama noktalarını 10.000'e göre ayarladık
    milestones = {1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000}

    os.makedirs("docs", exist_ok=True)
    # DİKKAT: Eski Q-Learning dosyalarının üzerine yazmamak için isimleri 'dqn_' ile başlattık
    with open("docs/dqn_milestone_results.txt", "w", encoding="utf-8") as f_out:
        f_out.write("Episode\tKazanma_Orani\tOrt_Odul\tEpsilon\tBellek\n")

    TARGET_UPDATE_FREQ = 10

    for ep in range(1, episodes + 1):
        state = env.reset()
        ep_rew = 0
        done = False
        steps = 0
        max_steps = 300

        while not done and steps < max_steps:
            action = agent.choose_action(state, env)
            next_state, reward, done, _ = env.step(action)

            agent.remember(state, action, reward, next_state, done)
            agent.learn()

            state = next_state
            ep_rew += reward
            steps += 1

        agent.decay_epsilon()

        if ep % TARGET_UPDATE_FREQ == 0:
            agent.update_target_network()

        # Erken durdurma (Early stopping) mekanizmasını 10.000 grafiğini tam görmek için kaldırdık.

        # Verileri kaydet
        total_rewards.append(ep_rew)
        episode_lengths.append(steps)

        if env.player_level >= env.max_level:
            wins += 1
            win_history.append(1)
        else:
            win_history.append(0)

        # Loglama
        if ep in milestones and verbose:
            recent = total_rewards[-200:]
            win_rate = wins / ep * 100
            print(f"Ep {ep:5d} | Kazanma %{win_rate:.1f} | "
                  f"Ort.Ödül: {np.mean(recent):.1f} | "
                  f"Epsilon: {agent.epsilon:.3f} | "
                  f"Bellek: {len(agent.memory):,}")

            with open("docs/dqn_milestone_results.txt", "a", encoding="utf-8") as f_out:
                f_out.write(f"{ep}\t{win_rate:.1f}\t{np.mean(recent):.1f}\t{agent.epsilon:.3f}\t{len(agent.memory)}\n")

    # Modeli Kaydet
    os.makedirs("models", exist_ok=True)
    torch.save(agent.policy_net.state_dict(), save_path)
    print(f"\n✅ DQN Eğitimi tamamlandı! Model kaydedildi: {save_path}")

    # ---------------------------------------------------------
    # GÖRSELDEKİ GİBİ 3 PANEL DASHBOARD ÇİZİMİ
    # ---------------------------------------------------------
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor('#1e1e2f')

    window = 200

    if len(total_rewards) >= window:
        avg_rewards = np.convolve(total_rewards, np.ones(window) / window, mode='valid')
        avg_wins = np.convolve(win_history, np.ones(window) / window, mode='valid') * 100
        avg_lengths = np.convolve(episode_lengths, np.ones(window) / window, mode='valid')
        x_axis = np.arange(window - 1, len(total_rewards))
    else:
        avg_rewards = total_rewards
        avg_wins = [w * 100 for w in win_history]
        avg_lengths = episode_lengths
        x_axis = np.arange(len(total_rewards))

    # Üst Panel: Toplam Ödül
    ax1 = plt.subplot(2, 1, 1)
    ax1.set_facecolor('#1e1e2f')
    ax1.plot(total_rewards, color='#3a4b86', alpha=0.6, linewidth=0.5)
    ax1.plot(x_axis, avg_rewards, color='#f0c040', linewidth=2, label=f'{window}-ep ort.')
    ax1.set_title(f'Munchkin AI (DQN) — Eğitim Sonuçları | Ajan Belleği: {len(agent.memory)} durum', color='white',
                  pad=15)
    ax1.set_ylabel('Ödül')
    ax1.grid(color='#2a2a3f', linestyle='--', linewidth=0.5)
    ax1.legend(facecolor='#1e1e2f', edgecolor='#4facfe', loc='center right')

    # Sol Alt Panel: Kazanma Oranı
    ax2 = plt.subplot(2, 2, 3)
    ax2.set_facecolor('#1e1e2f')
    ax2.plot(x_axis, avg_wins, color='#00ffc8', linewidth=2)
    ax2.set_title('Kazanma Oranı (%)', color='white')
    ax2.set_xlabel('Episode')
    ax2.set_ylabel('%')
    ax2.set_ylim(0, 105)
    ax2.grid(color='#2a2a3f', linestyle='--', linewidth=0.5)

    # Sağ Alt Panel: Episode Uzunluğu
    ax3 = plt.subplot(2, 2, 4)
    ax3.set_facecolor('#1e1e2f')
    ax3.plot(x_axis, avg_lengths, color='#ff416c', linewidth=2)
    ax3.set_title('Ort. Episode Uzunluğu', color='white')
    ax3.set_xlabel('Episode')
    ax3.set_ylabel('Adım')
    ax3.grid(color='#2a2a3f', linestyle='--', linewidth=0.5)

    plt.tight_layout(pad=3.0)
    # DİKKAT: Eski grafiği silmemek için adını dqn_training_dashboard.png yaptık
    plt.savefig("docs/dqn_training_dashboard.png", facecolor=fig.get_facecolor(), dpi=150)
    print("📊 3 Panelli DQN Eğitim grafiği docs/dqn_training_dashboard.png olarak kaydedildi!")

    # ---------------------------------------------------------
    # AKADEMİK RAPOR ÇIKTISI
    # ---------------------------------------------------------
    # DİKKAT: Eski raporu ezmemek için adını dqn_ai_final_report.txt yaptık
    with open("docs/dqn_ai_final_report.txt", "w", encoding="utf-8") as report:
        report.write("==================================================\n")
        report.write("      MUNCHKIN AI (DQN) EĞİTİM ÖZET RAPORU        \n")
        report.write("==================================================\n")
        report.write(f"Toplam Eğitim Bölümü (Episode): {episodes}\n")
        report.write(f"Toplam Başarılı Kazanma (Level 10): {wins} / {episodes}\n")
        report.write(f"Genel Başarı Yüzdesi: %{wins / episodes * 100:.2f}\n")

        if len(win_history) >= 500:
            son_500 = sum(win_history[-500:])
            report.write(f"Son 500 Oyun Başarı Yüzdesi: %{son_500 / 500 * 100:.2f}\n")

        report.write(f"Ajanın Belleğindeki Deneyim Sayısı (Replay Buffer): {len(agent.memory)}\n")
        report.write("Kullanılan Mimari: Deep Q-Network (PyTorch)\n")
        report.write("==================================================\n")
    print("📝 Akademik özet raporu docs/dqn_ai_final_report.txt olarak oluşturuldu!")

    return agent


if __name__ == "__main__":
    train(episodes=10000)