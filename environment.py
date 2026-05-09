import random


class RPGEnvironment:
    def __init__(self):
        self.max_level = 30
        self.action_space_size = 4
        self.equipment_slots = ["head", "body", "hand_1", "hand_2", "feet"]
        self.reset()

    def _generate_card(self):
        return {"slot": random.choice(self.equipment_slots), "power": random.randint(1, 4)}

    def reset(self):
        self.player_level = 1
        self.treasure_cards = [self._generate_card() for _ in range(3)]
        self.equipment = {
            "head": 0,
            "body": 0,
            "hand_1": 0,
            "hand_2": 0,
            "feet": 0
        }
        self.active_treasure_power = 0
        self.defense_bonus = 0
        self.monster_power = self._spawn_monster()
        return self._get_state()

    def _spawn_monster(self):
        return max(1, self.player_level + random.randint(-1, 3))

    def _get_state(self):
        return (self.player_level, len(self.treasure_cards), self.active_treasure_power, self.monster_power,
                self.defense_bonus)

    # DİKKAT: class_bonus parametresi eklendi!
    def step(self, action, class_bonus=0):
        reward = 0
        done = False

        if action == 0:
            # Sınıf avantajı (class_bonus) toplam güce ekleniyor!
            total_power = self.player_level + self.active_treasure_power + self.defense_bonus + class_bonus
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

        elif action == 1:
            reward = -5
            self.defense_bonus = 0
            self.monster_power = self._spawn_monster()

        elif action == 2:
            if len(self.treasure_cards) > 0:
                card = self.treasure_cards.pop(0)
                new_card_power = card["power"]
                slot = card["slot"]

                if new_card_power > self.equipment[slot]:
                    self.equipment[slot] = new_card_power
                    reward = 5
                else:
                    reward = -2

                self.active_treasure_power = sum(self.equipment.values())
            else:
                reward = -10

        elif action == 3:
            self.defense_bonus = 3
            reward = -2

        return self._get_state(), reward, done