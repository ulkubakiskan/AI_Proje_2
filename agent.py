import numpy as np
import random


class QLearningAgent:
    def __init__(self, action_space_size, learning_rate=0.1, discount_factor=0.95,
                 epsilon=1.0, epsilon_decay=0.9975, min_epsilon=0.01):
        self.action_space_size = action_space_size
        self.q_table = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon

    def _get_q_values(self, state):
        if state not in self.q_table:
            self.q_table[state] = np.zeros(self.action_space_size)
        return self.q_table[state]

    def choose_action(self, state, num_cards=None, has_upgrade=False):
        if random.uniform(0, 1) < self.epsilon:
            # Keşif: upgrade yokken giymeyi daha az dene
            if num_cards == 0:
                return random.choice([0, 1, 3])
            if not has_upgrade:
                return random.choice([0, 1, 3])
            return random.randint(0, self.action_space_size - 1)

        q_vals = self._get_q_values(state).copy()
        # Kart yoksa giymeyi engelle
        if num_cards == 0:
            q_vals[2] = -9999
        return int(np.argmax(q_vals))

    def learn(self, state, action, reward, next_state, done):
        q_values = self._get_q_values(state)
        next_q_values = self._get_q_values(next_state)
        max_next_q = 0 if done else np.max(next_q_values)
        current_q = q_values[action]
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state][action] = new_q

    def decay_epsilon(self):
        if self.epsilon > self.min_epsilon:
            self.epsilon *= self.epsilon_decay
