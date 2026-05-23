import random


class RPGEnvironment:
    def __init__(self):
        self.max_level = 30
        # Aksiyonlar: 0=Saldır, 1=Kaç, 2=En İyi Kartı Giy, 3=Savunma
        self.action_space_size = 4
        self.equipment_slots = ["head", "body", "hand_1", "hand_2", "feet"]
        self.num_classes = 4
        self.reset()

    def _generate_card(self):
        # Eşya gücü maksimum 6'ya (Efsanevi) çıkarıldı
        return {"slot": random.choice(self.equipment_slots), "power": random.randint(1, 6)}

    def reset(self, hero_class=None):
        self.player_level = 1
        self.treasure_cards = [self._generate_card() for _ in range(3)]
        self.equipment = {"head": 0, "body": 0, "hand_1": 0, "hand_2": 0, "feet": 0}
        self.active_treasure_power = 0
        self.defense_bonus = 0
        self.monster_power = self._spawn_monster()
        self.hero_class = hero_class if hero_class is not None else random.randint(0, self.num_classes - 1)
        return self._get_state()

    def _spawn_monster(self):
        return max(1, self.player_level + random.randint(-1, 3))

    def get_best_card_index(self):
        best_idx = None
        best_gain = 0
        for i, card in enumerate(self.treasure_cards):
            gain = card["power"] - self.equipment[card["slot"]]
            if gain > best_gain:
                best_gain = gain
                best_idx = i
        return best_idx

    def has_upgrade_card(self):
        return self.get_best_card_index() is not None

    def _get_state(self):
        best_idx = self.get_best_card_index()
        potential_upgrade = 0
        if best_idx is not None:
            card = self.treasure_cards[best_idx]
            potential_upgrade = card["power"] - self.equipment[card["slot"]]

        # Potansiyel kazanç sınırı yeni eşya seviyelerine göre 6'ya çekildi
        potential_upgrade = min(potential_upgrade, 6)

        return (
            self.player_level,
            len(self.treasure_cards),
            self.active_treasure_power,
            self.monster_power,
            self.defense_bonus,
            self.hero_class,
            potential_upgrade,
        )

    def step(self, action, class_bonus=0, item_penalty=0):
        reward = 0
        done = False

        if action == 0:  # Saldır
            # Güç hesabına eksi olarak item_penalty (dezavantaj) eklendi
            total_power = self.player_level + self.active_treasure_power + self.defense_bonus + class_bonus - item_penalty
            if total_power >= self.monster_power:
                self.player_level += 1
                reward = 10
                self.defense_bonus = 0
                if len(self.treasure_cards) < 5:
                    self.treasure_cards.append(self._generate_card())
                if self.player_level >= self.max_level:
                    reward = 1000
                    done = True
                else:
                    self.monster_power = self._spawn_monster()
            else:
                reward = -50
                done = True

        elif action == 1:  # Kaç
            reward = -5
            self.defense_bonus = 0
            self.monster_power = self._spawn_monster()

        elif action == 2:  # En İyi Kartı Giy
            if len(self.treasure_cards) > 0:
                best_idx = self.get_best_card_index()
                if best_idx is not None:
                    card = self.treasure_cards.pop(best_idx)
                    gain = card["power"] - self.equipment[card["slot"]]
                    self.equipment[card["slot"]] = card["power"]
                    reward = 3 + gain
                else:
                    self.treasure_cards.pop(0)
                    reward = -3
                self.active_treasure_power = sum(self.equipment.values())
            else:
                reward = -10

        elif action == 3:  # Savunma
            self.defense_bonus = 3
            reward = -2

        return self._get_state(), reward, done