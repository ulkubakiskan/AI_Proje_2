import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque


class QNetwork(nn.Module):
    """3 Katmanlı Basit Bir İleri Beslemeli Sinir Ağı"""

    def __init__(self, input_dim, output_dim):
        super(QNetwork, self).__init__()
        # 9 elemanlı durumu alıp 64 nöronlu gizli katmanlara aktarıyoruz
        self.fc1 = nn.Linear(input_dim, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, output_dim)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)


class DQNAgent:
    """
    Derin Q-Öğrenme Ajanı (DQN)
    - PyTorch tabanlı Sinir Ağı
    - Experience Replay (Deneyim Belleği)
    """

    def __init__(self, state_dim=9, action_space_size=5, learning_rate=0.001,
                 discount_factor=0.95, epsilon=1.0, epsilon_decay=0.9975, min_epsilon=0.01):

        self.state_dim = state_dim
        self.action_space_size = action_space_size
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon

        # CPU veya GPU kullanımı
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Policy Net (Karar Ağı) ve Target Net (Hedef Ağ)
        self.policy_net = QNetwork(state_dim, action_space_size).to(self.device)
        self.target_net = QNetwork(state_dim, action_space_size).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # Hedef ağ sadece değerlendirme içindir

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)

        # Loss Fonksiyonu (Mean Squared Error)
        self.loss_fn = nn.MSELoss()

        # Deneyim Belleği
        self.memory = deque(maxlen=10000)
        self.batch_size = 64

    def remember(self, state, action, reward, next_state, done):
        """Deneyimleri belleğe kaydet"""
        self.memory.append((state, action, reward, next_state, done))

    def choose_action(self, state, env=None):
        num_cards = state[1]

        # Keşif (Exploration)
        if random.random() < self.epsilon:
            choices = [0, 1, 3, 4]
            if num_cards > 0 and env and env.has_upgrade_card():
                choices = [0, 2, 3, 4]
            return random.choice(choices)

        # Sömürü (Exploitation) - Sinir ağı karar veriyor
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_vals = self.policy_net(state_tensor).cpu().numpy()[0]

            # Eğer kart yoksa giyme aksiyonunu (-9999) cezalandır
            if num_cards == 0:
                q_vals[2] = -9999
            return int(np.argmax(q_vals))

    def learn(self):
        """Bellekten rastgele batch (küme) çekerek sinir ağını eğit"""
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        # Tensörlere çevirme
        states = torch.FloatTensor(np.array(states)).to(self.device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(self.device)

        # Mevcut durum için Policy Ağının Q değerleri
        curr_Q = self.policy_net(states).gather(1, actions)

        # Sonraki durum için Target Ağının maksimum Q değerleri
        with torch.no_grad():
            max_next_Q = self.target_net(next_states).max(1)[0].unsqueeze(1)
            target_Q = rewards + (self.gamma * max_next_Q * (1 - dones))

        # Ağı güncelle
        loss = self.loss_fn(curr_Q, target_Q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def update_target_network(self):
        """Hedef ağı, belirli aralıklarla policy ağı ile senkronize et"""
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)