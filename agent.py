import numpy as np
import random


class QLearningAgent:
    """
    Geliştirilmiş Q-Learning Agent
    - 5 aksiyon (PDF mekanikleri: Yardım Çağır eklendi)
    - Daha akıllı keşif politikası
    - Durum özellik çıkarımı
    """
    def __init__(self, action_space_size=5, learning_rate=0.1, discount_factor=0.95,
                 epsilon=1.0, epsilon_decay=0.9975, min_epsilon=0.01):
        self.action_space_size = action_space_size
        self.q_table           = {}
        self.lr                = learning_rate
        self.gamma             = discount_factor
        self.epsilon           = epsilon
        self.epsilon_decay     = epsilon_decay
        self.min_epsilon       = min_epsilon

    def _get_q(self, state):
        if state not in self.q_table:
            self.q_table[state] = np.zeros(self.action_space_size)
        return self.q_table[state]

    def extract_features(self, raw_state):
        """Ham state'den sıkıştırılmış özellik vektörü çıkar"""
        # GÜNCELLEME: Gelen ham durumun (raw_state) boyutuna göre esnek parçalama yapıyoruz
        if len(raw_state) == 9:
            player_lvl, num_cards, active_power, monster_power, def_bonus, class_idx, race_idx, potential_upg, power_diff = raw_state
        else:
            # Eğer eski 8 elemanlı state gelirse hata vermemesi için koruma adımı
            player_lvl, num_cards, active_power, monster_power, def_bonus, class_idx, potential_upg, power_diff = raw_state
            race_idx = 0  # varsayılan değer

        return (
            max(-6, min(6, power_diff)),   # güç farkı
            min(num_cards, 4),             # el kartı sayısı (max 4)
            min(potential_upg, 5),         # en iyi yükseltme kazancı
            def_bonus > 0,                 # savunma aktif mi
            player_lvl >= 8,               # kritik seviye mi (10'a yakın)
        )

    def choose_action(self, state, env=None):
        feats     = self.extract_features(state)
        num_cards = state[1]

        if random.random() < self.epsilon:
            # Akıllı keşif — kartı olmayan giymeyi deneme
            choices = [0, 1, 3, 4]
            if num_cards > 0 and env and env.has_upgrade_card():
                choices = [0, 2, 3, 4]
            return random.choice(choices)

        q_vals = self._get_q(feats).copy()
        if num_cards == 0:
            q_vals[2] = -9999  # kart yoksa giyme
        return int(np.argmax(q_vals))

    def learn(self, state, action, reward, next_state, done):
        f      = self.extract_features(state)
        f_next = self.extract_features(next_state)
        q      = self._get_q(f)
        q_next = self._get_q(f_next)
        max_next = 0 if done else np.max(q_next)
        q[action] = q[action] + self.lr * (reward + self.gamma * max_next - q[action])
        self.q_table[f] = q

    def decay_epsilon(self):
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)