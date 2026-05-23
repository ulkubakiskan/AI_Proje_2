import pickle
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from environment import RPGEnvironment
from agent import QLearningAgent

HERO_CLASSES = ["Munchkin Savaşçısı", "Sinsi Hırsız", "Kibirli Büyücü", "Kutsal Rahip"]
MONSTER_THRESHOLDS = [2, 5, 10, 15, 25]
MONSTER_NAMES = ["Saksı Çiçeği", "Salya Sümük", "Uçan Kurbağa", "İnternet Trolü", "Gıcık Avukat", "Plütonyum Ejderhası"]
CLASS_BONUSES = {
    ("Sinsi Hırsız", "Uçan Kurbağa"): 3,
    ("Munchkin Savaşçısı", "İnternet Trolü"): 3,
    ("Kibirli Büyücü", "Saksı Çiçeği"): 3,
    ("Kutsal Rahip", "Gıcık Avukat"): 3,
}


def get_monster_name(power):
    for i, threshold in enumerate(MONSTER_THRESHOLDS):
        if power <= threshold:
            return MONSTER_NAMES[i]
    return MONSTER_NAMES[-1]


def get_class_bonus(hero_class_idx, monster_power):
    hero_name = str(HERO_CLASSES[hero_class_idx])  # PyCharm'ı rahatlatmak için str() ile sardık
    monster_name = str(get_monster_name(monster_power))
    return CLASS_BONUSES.get((hero_name, monster_name), 0)


def get_equipment_penalty(equipment, monster_name):
    penalty = 0
    if monster_name == "Uçan Kurbağa" and equipment["body"] > 0:
        penalty += 1  # Kurbağa gömleğe sızar
    elif monster_name == "Salya Sümük" and equipment["hand_1"] > 0:
        penalty += 1  # Salya sümük silahı eritir
    elif monster_name == "Gıcık Avukat" and equipment["hand_2"] > 0:
        penalty += 1  # Avukat kalkanlara itiraz eder
    return penalty


def extract_features(state, class_bonus, item_penalty):
    player_lvl, num_cards, active_power, monster_power, def_bonus, hero_class_idx, potential_upgrade = state

    # Net gücü hesaplarken sınıf bonusunu ekleyip, dezavantajı (item_penalty) çıkarıyoruz
    total_power = player_lvl + active_power + def_bonus + class_bonus - item_penalty
    power_diff = total_power - monster_power
    power_diff = max(-5, min(5, power_diff))

    return (
        power_diff,
        num_cards > 0,
        potential_upgrade,
        def_bonus > 0
    )


def train():
    env = RPGEnvironment()
    agent = QLearningAgent(env.action_space_size)
    EPISODES = 10000
    rewards, win_flags, episode_lengths = [], [], []

    print("Yapay Zeka Eğitiliyor. Lütfen Bekleyin...")
    for episode in range(EPISODES):
        state = env.reset()
        done = False
        total_reward = 0
        step_count = 0

        while not done and step_count < 300:
            num_cards = state[1]
            has_upgrade = env.has_upgrade_card()

            # --- MEVCUT DURUM İÇİN ÖZELLİKLERİ ÇIKAR ---
            monster_name = get_monster_name(env.monster_power)
            class_bonus = get_class_bonus(env.hero_class, env.monster_power)
            item_penalty = get_equipment_penalty(env.equipment, monster_name)

            q_state = extract_features(state, class_bonus, item_penalty)

            # Aksiyon Seçimi
            action = agent.choose_action(q_state, num_cards=num_cards, has_upgrade=has_upgrade)

            # Aksiyonu Uygula
            next_state, reward, done = env.step(action, class_bonus=class_bonus, item_penalty=item_penalty)

            # --- YENİ DURUM İÇİN ÖZELLİKLERİ ÇIKAR ---
            next_monster_name = get_monster_name(env.monster_power)
            next_class_bonus = get_class_bonus(env.hero_class, env.monster_power)
            next_item_penalty = get_equipment_penalty(env.equipment, next_monster_name)

            next_q_state = extract_features(next_state, next_class_bonus, next_item_penalty)

            # Ajanı Eğit
            agent.learn(q_state, action, reward, next_q_state, done)

            state = next_state
            total_reward += reward
            step_count += 1

        agent.decay_epsilon()
        rewards.append(total_reward)
        win_flags.append(1 if env.player_level >= env.max_level else 0)
        episode_lengths.append(step_count)

        if (episode + 1) % 1000 == 0:
            recent_wins = sum(win_flags[-200:]) / 200 * 100
            print(
                f"  Episode {episode + 1}/{EPISODES} | Epsilon: {agent.epsilon:.3f} | Son 200 Kazanma: %{recent_wins:.1f}")

    os.makedirs('models', exist_ok=True)
    with open('models/q_table.pkl', 'wb') as f:
        pickle.dump(agent.q_table, f)

    # Eğitim Grafikleri
    os.makedirs('docs', exist_ok=True)
    window = 200
    moving_avg = [sum(rewards[max(0, i - window):i + 1]) / min(i + 1, window + 1) for i in range(len(rewards))]
    win_rate = [sum(win_flags[max(0, i - window):i + 1]) / min(i + 1, window + 1) * 100 for i in range(len(win_flags))]
    avg_length = [sum(episode_lengths[max(0, i - window):i + 1]) / min(i + 1, window + 1) for i in
                  range(len(episode_lengths))]

    fig = plt.figure(figsize=(14, 8))
    fig.patch.set_facecolor('#1a1a2e')
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.3)

    def style_ax(ax, title, xlabel, ylabel, color):
        ax.set_facecolor('#16213e')
        ax.set_title(title, color='white', fontsize=12)
        ax.set_xlabel(xlabel, color='#a9a9b3')
        ax.set_ylabel(ylabel, color='#a9a9b3')
        ax.tick_params(colors='#a9a9b3')
        for spine in ax.spines.values(): spine.set_color(color)

    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(rewards, alpha=0.2, color='#4facfe', linewidth=0.5)
    ax1.plot(moving_avg, color='#f6d365', linewidth=2.5, label=f'{window}-ep ort.')
    ax1.legend(facecolor='#0f3460', labelcolor='white')
    style_ax(ax1, "Toplam Odul Skoru", "Episode", "Odul", "#4facfe")

    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(win_rate, color='#00ffcc', linewidth=2)
    ax2.fill_between(range(len(win_rate)), win_rate, alpha=0.15, color='#00ffcc')
    ax2.set_ylim(0, 105)
    style_ax(ax2, "Kazanma Orani (%)", "Episode", "%", "#00ffcc")

    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(avg_length, color='#e94560', linewidth=2)
    style_ax(ax3, "Ort. Episode Uzunlugu", "Episode", "Adim", "#e94560")

    final_win_rate = sum(win_flags[-500:]) / 500 * 100
    fig.suptitle(
        f"Munchkin AI — Egitim Sonuclari  |  Q-Table: {len(agent.q_table):,} durum  |  Son 500 Kazanma: %{final_win_rate:.1f}",
        color='white', fontsize=11, y=0.99
    )
    plt.savefig("docs/training_results.png", bbox_inches='tight', facecolor='#1a1a2e', dpi=120)
    plt.close()

    print(f"\nEgitim Tamamlandi!")
    print(f"  Q-Table: {len(agent.q_table):,} durum")
    print(f"  Son 500 kazanma: %{final_win_rate:.1f}")


if __name__ == "__main__":
    train()