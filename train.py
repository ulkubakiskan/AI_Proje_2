"""
Geliştirilmiş Munchkin Eğitim Scripti
PDF kuralları ile zenginleştirilmiş environment üzerinde Q-learning eğitimi
"""
import pickle, os, random
import numpy as np
import matplotlib.pyplot as plt

from environment import MunchkinEnvironment
from agent import QLearningAgent

def train(episodes=5000, save_path="models/q_table.pkl", verbose=True):
    env   = MunchkinEnvironment()
    agent = QLearningAgent(action_space_size=5, epsilon=1.0)

    wins, total_rewards = 0, []
    milestones = {1000, 2000, 3000, 4000, 5000}

    # 1. ADIM: Klasörü oluşturup dosyanın başlık satırını döngü başlamadan önce (1 kez) yazıyoruz
    os.makedirs("docs", exist_ok=True)
    with open("docs/milestone_results.txt", "w", encoding="utf-8") as f_out:
        f_out.write("Episode\tKazanma_Orani\tOrt_Odul\tEpsilon\tQ_Durumlari\n")

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
        # train.py içindeki döngünün sonuna (agent.decay_epsilon() sonrasına) eklenebilir:
        if ep > 500:
            recent_wins = total_rewards[-100:]
            # Eğer son 100 turun 90'ında ajan seviye 10'a ulaşıp büyük ödül aldıysa
            if len([r for r in recent_wins if r > 300]) >= 90:
                print(f"Target accuracy reached at episode {ep}! Stopping training early...")
                break
        total_rewards.append(ep_rew)
        if env.player_level >= env.max_level:
            wins += 1

        # 2. ADIM: Her 1000. turda değerleri hem ekrana basıyoruz hem de txt dosyasına ekliyoruz
        if ep in milestones and verbose:
            recent   = total_rewards[-200:]
            win_rate = wins / ep * 100
            print(f"Ep {ep:5d} | Kazanma %{win_rate:.1f} | "
                  f"Ort.Ödül: {np.mean(recent):.1f} | "
                  f"Epsilon: {agent.epsilon:.3f} | "
                  f"Q-Durumlar: {len(agent.q_table):,}")

            # Girinti kontrolü: 'if ep in milestones' bloğunun tam içerisinde hizalıdır
            with open("docs/milestone_results.txt", "a", encoding="utf-8") as f_out:
                f_out.write(f"{ep}\t{win_rate:.1f}\t{np.mean(recent):.1f}\t{agent.epsilon:.3f}\t{len(agent.q_table)}\n")

    # Döngü bitti, modeli kaydediyoruz
    os.makedirs("models", exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(agent.q_table, f)
    print(f"\n✅ Eğitim tamamlandı! Model kaydedildi: {save_path}")
    print(f"   Toplam kazanma: {wins}/{episodes} (%{wins/episodes*100:.1f})")
    print(f"   Q-tablo boyutu: {len(agent.q_table):,} durum")

    # 3. ADIM: Performans Grafiğini Çizdirme ve Kaydetme
    plt.figure(figsize=(10, 5))
    plt.plot(total_rewards, label="Bölüm Ödülü", color="purple", alpha=0.3)

    moving_avg = np.convolve(total_rewards, np.ones(100)/100, mode='valid')
    plt.plot(moving_avg, label="100 Bölüm Ortalaması", color="blue")
    plt.xlabel("Bölüm (Episode)")
    plt.ylabel("Toplam Ödül")
    plt.title("Munchkin AI Eğitim Performansı")
    plt.legend()
    plt.savefig("docs/training_performance_graph.png")
    print("📊 Eğitim grafiği docs/ klasörüne kaydedildi!")

    # 4. ADIM: Word Raporu İçin Genel Özet Çıktısı Oluşturma
    with open("docs/ai_final_report.txt", "w", encoding="utf-8") as report:
        report.write("==================================================\n")
        report.write("        MUNCHKIN AI EĞİTİM ÖZET RAPORU            \n")
        report.write("==================================================\n")
        report.write(f"Toplam Eğitim Bölümü (Episode): {episodes}\n")
        report.write(f"Toplam Başarılı Kazanma (Level 10): {wins} / {episodes}\n")
        report.write(f"Genel Başarı Yüzdesi: %{wins/episodes*100:.2f}\n")
        report.write(f"Yapay Zekanın Keşfettiği Durum Sayısı: {len(agent.q_table)}\n")
        report.write("==================================================\n")
    print("📝 Akademik özet raporu docs/ai_final_report.txt olarak kaydedildi!")

    return agent

if __name__ == "__main__":
    train(episodes=5000)