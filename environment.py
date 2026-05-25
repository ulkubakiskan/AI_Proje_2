import random

# ===== MUNCHKIN PDF KURALLARINA GÖRE ZENGİNLEŞTİRİLMİŞ ENVIRONMENT =====

MONSTERS = [
    {"name": "Saksı Çiçeği",      "emoji": "🪴", "power": 1,  "treasures": 1, "bad_thing": "1 seviye kaybet",    "undead": False},
    {"name": "Salya Sümük",        "emoji": "🦠", "power": 2,  "treasures": 1, "bad_thing": "1 eşya kaybet",      "undead": False},
    {"name": "Uçan Kurbağa",       "emoji": "🐸", "power": 4,  "treasures": 2, "bad_thing": "2 seviye kaybet",    "undead": False},
    {"name": "Zombi Tavşan",       "emoji": "🐇", "power": 5,  "treasures": 2, "bad_thing": "1 eşya kaybet",      "undead": True},
    {"name": "İnternet Trolü",     "emoji": "🧌", "power": 8,  "treasures": 2, "bad_thing": "3 seviye kaybet",    "undead": False},
    {"name": "Vampir Özentisi",    "emoji": "🧛", "power": 10, "treasures": 3, "bad_thing": "Öl",                 "undead": True},
    {"name": "Gıcık Avukat",       "emoji": "👨‍⚖️", "power": 13, "treasures": 3, "bad_thing": "4 seviye kaybet",    "undead": False},
    {"name": "Çürük Kral",         "emoji": "👑", "power": 16, "treasures": 4, "bad_thing": "Öl",                 "undead": True},
    {"name": "Sözlük Trollü",      "emoji": "📚", "power": 20, "treasures": 4, "bad_thing": "Öl",                 "undead": False},
    {"name": "Plütonyum Ejderhası","emoji": "🐉", "power": 25, "treasures": 5, "bad_thing": "Öl",                 "undead": False},
]

CLASSES = ["Savaşçı", "Büyücü", "Hırsız", "Keşiş"]
RACES  = ["İnsan", "Elf", "Cüce", "Buçukluk"]

CURSES = [
    {"name": "Seviye Kaybı",    "effect": "level_down",    "desc": "1 seviye düş!"},
    {"name": "Eşya Laneti",     "effect": "lose_item",     "desc": "En iyi eşyanı kaybet!"},
    {"name": "Güç Zayıflaması", "effect": "power_down",    "desc": "Bu savaşta -2 güç!"},
    {"name": "Korku",           "effect": "must_flee",     "desc": "Kaçmak zorundasın!"},
]

ITEMS = {
    "head":   [("Kese Kağıdı",1),("Teneke Kova",2),("Boynuzlu Kask",3),("Kral Tacı",4),("Mithril Miğfer",5),("Görünmezlik Bandanası",6)],
    "body":   [("Deri Yelek",1),("Dikenli Zırh",2),("Şövalye Zırhı",3),("Mithril Gömlek",4),("Ejderha Pulu Zırh",5),("Gölge Pelerini",6)],
    "hand_1": [("Tahta Sopa",1),("Paslı Kılıç",2),("Cırtlak Kılıç",3),("Alevli Kılıç",4),("Lazer Kılıcı",5),("Sonsuzluk Kılıcı",6)],
    "hand_2": [("Tahta Kapak",1),("Demir Kalkan",2),("Aynalı Kalkan",3),("Ejderha Kalkanı",4),("Kuvvet Alanı",5),("Zaman Kalkanı",6)],
    "feet":   [("Yırtık Çorap",1),("Deri Çizme",2),("Hızlı Bot",3),("Uçan Pabuç",4),("Işınlanma Çizmesi",5),("Kuantum Terlikleri",6)],
}

SLOT_TR = {"head":"Kafa","body":"Gövde","hand_1":"Sağ El","hand_2":"Sol El","feet":"Ayaklar"}

# Sınıf bonusları (canavar ismine göre)
CLASS_BONUSES = {
    ("Savaşçı", "İnternet Trolü"):      3,
    ("Savaşçı", "Sözlük Trollü"):       4,
    ("Büyücü",  "Saksı Çiçeği"):        3,
    ("Büyücü",  "Uçan Kurbağa"):        2,
    ("Hırsız",  "Uçan Kurbağa"):        3,
    ("Hırsız",  "Gıcık Avukat"):        2,
    ("Keşiş",   "Vampir Özentisi"):     10,  # Keşiş vampiri DEF eder!
    ("Keşiş",   "Çürük Kral"):          5,
    ("Keşiş",   "Zombi Tavşan"):        4,
}

# Irk bonusları
RACE_BONUSES = {
    "Elf":       2,   # Her savaşta +2 güç
    "Cüce":      3,   # Büyük eşyalara +3
    "Buçukluk":  2,   # Kaçış bonusu
    "İnsan":     0,
}

# Eşya dezavantajları (ağır zırh kurbağa vs.)
ITEM_PENALTIES = {
    ("Uçan Kurbağa",  "body"):   2,
    ("Salya Sümük",   "hand_1"): 1,
    ("Gıcık Avukat",  "hand_2"): 2,
    ("Sözlük Trollü", "head"):   1,
}


class MunchkinEnvironment:
    """
    PDF kurallarına uygun Munchkin environment:
    - Kaçış zarı mekaniği (5+ = kaçış)
    - Lanet kartları
    - Çoklu canavar desteği (temel)
    - Irk ve sınıf sistemi
    - Kötü Şey sonuçları
    - Yardım mekaniği (AI-vs-AI)
    """

    def __init__(self):
        self.max_level     = 10   # PDF: 10. seviye kazanır
        self.action_space_size = 5
        # 0=Saldır, 1=Kaç, 2=Eşya Giy, 3=Savunma, 4=Yardım Çağır
        self.equipment_slots = list(ITEMS.keys())
        self.reset()

    def _gen_card(self):
        slot = random.choice(self.equipment_slots)
        power = random.randint(1, 6)
        return {"slot": slot, "power": power, "name": ITEMS[slot][power-1][0]}

    def reset(self, hero_class=None, hero_race=None):
        self.player_level  = 1
        self.equipment     = {s: 0 for s in self.equipment_slots}
        self.treasure_cards= [self._gen_card() for _ in range(3)]
        self.active_power  = sum(self.equipment.values())
        self.defense_bonus = 0
        self.curse_power_debuff = 0  # aktif lanet güç azalması

        # Irk & sınıf
        self.hero_class = hero_class if hero_class else random.choice(CLASSES)
        self.hero_race  = hero_race  if hero_race  else random.choice(RACES)

        # Canavar seç (seviyeye uygun)
        self.current_monsters  = [self._spawn_monster()]
        self.second_monster    = None   # Avare canavar
        self.pending_curse     = None   # Aktif lanet
        self.fled_this_turn    = False
        self.steps             = 0
        self.total_kills       = 0
        self.flee_attempts     = 0
        self.curse_events      = 0

        return self._get_state()

    def _spawn_monster(self):
        # Seviyeye uygun canavar: düşük seviyede zayıf, yüksekte güçlü
        candidates = [m for m in MONSTERS if abs(m["power"] - (self.player_level * 2)) <= 5]
        if not candidates:
            candidates = MONSTERS
        m = random.choice(candidates).copy()
        # Olasılıkla güçlendirici kart (Öfkeli)
        if random.random() < 0.15:
            m = m.copy()
            m["power"] += 5
            m["treasures"] += 1
            m["name"] += " (Öfkeli)"
            m["enraged"] = True
        return m

    def _get_total_monster_power(self):
        total = sum(m["power"] for m in self.current_monsters)
        return total

    def _get_player_power(self, extra=0):
        class_bonus = self._get_class_bonus()
        race_bonus  = RACE_BONUSES.get(self.hero_race, 0)
        penalty     = self._get_item_penalty()
        power = (self.player_level + self.active_power + self.defense_bonus
                 + class_bonus + race_bonus - penalty - self.curse_power_debuff + extra)
        return max(1, power)

    def _get_class_bonus(self):
        bonus = 0
        for m in self.current_monsters:
            bonus += CLASS_BONUSES.get((self.hero_class, m["name"].replace(" (Öfkeli)","").strip()), 0)
        return bonus

    def _get_item_penalty(self):
        penalty = 0
        for m in self.current_monsters:
            mn = m["name"].replace(" (Öfkeli)","").strip()
            for slot, val in self.equipment.items():
                if val > 0:
                    penalty += ITEM_PENALTIES.get((mn, slot), 0)
        return penalty

    def get_best_card_index(self):
        best_idx, best_gain = None, 0
        for i, c in enumerate(self.treasure_cards):
            gain = c["power"] - self.equipment[c["slot"]]
            if gain > best_gain:
                best_gain, best_idx = gain, i
        return best_idx

    def has_upgrade_card(self):
        return self.get_best_card_index() is not None

    def _get_state(self):
        monster_power = self._get_total_monster_power()
        player_power  = self._get_player_power()
        power_diff    = max(-8, min(8, player_power - monster_power))
        potential_upg = 0
        bi = self.get_best_card_index()
        if bi is not None:
            c = self.treasure_cards[bi]
            potential_upg = min(6, c["power"] - self.equipment[c["slot"]])

        return (
            self.player_level,
            len(self.treasure_cards),
            self.active_power,
            monster_power,
            self.defense_bonus,
            CLASSES.index(self.hero_class),
            potential_upg,
            power_diff,
        )

    def _apply_bad_thing(self, monster):
        bt = monster.get("bad_thing", "")
        event = ""
        if "Öl" in bt:
            self.player_level = max(1, self.player_level - 2)
            self.equipment    = {s: 0 for s in self.equipment_slots}
            self.active_power = 0
            event = "💀 ÖLÜM! Tüm eşyalar kayboldu!"
        elif "seviye kaybet" in bt:
            n = int(''.join(filter(str.isdigit, bt)) or 1)
            self.player_level = max(1, self.player_level - n)
            event = f"📉 {n} seviye düştün!"
        elif "eşya kaybet" in bt:
            # En güçlü eşyayı kaldır
            best_slot = max(self.equipment, key=self.equipment.get)
            if self.equipment[best_slot] > 0:
                self.equipment[best_slot] = 0
                self.active_power = sum(self.equipment.values())
                event = f"🗑️ {SLOT_TR[best_slot]} eşyan gitti!"
            else:
                event = "😅 Kaybedecek eşyan yoktu!"
        return event

    def _roll_escape(self):
        """PDF: Zar at, 5+ = kaçış başarılı"""
        roll = random.randint(1, 6)
        # Buçukluk +1 kaçış bonusu
        if self.hero_race == "Buçukluk":
            roll += 1
        return roll, roll >= 5

    def step(self, action):
        """
        Aksiyonlar:
        0 = Saldır
        1 = Kaç (zar at!)
        2 = En iyi kartı giy
        3 = Savunma pozisyonu al
        4 = Yardım çağır (AI yardımcı gelir, +3 güç)
        """
        reward = 0
        done   = False
        event  = ""
        self.steps += 1
        self.curse_power_debuff = 0  # her adımda sıfırla

        # Lanet şansı (PDF: kapı tekmeleme)
        if random.random() < 0.08:
            curse = random.choice(CURSES)
            self.curse_events += 1
            if curse["effect"] == "level_down":
                self.player_level = max(1, self.player_level - 1)
                reward -= 5
                event = f"🔮 LANET: {curse['desc']}"
            elif curse["effect"] == "lose_item":
                best_slot = max(self.equipment, key=self.equipment.get)
                if self.equipment[best_slot] > 0:
                    self.equipment[best_slot] = 0
                    self.active_power = sum(self.equipment.values())
                event = f"🔮 LANET: {curse['desc']}"
                reward -= 3
            elif curse["effect"] == "power_down":
                self.curse_power_debuff = 2
                event = f"🔮 LANET: {curse['desc']}"
                reward -= 2
            elif curse["effect"] == "must_flee":
                action = 1
                event = f"🔮 LANET: {curse['desc']} — Kaçmak zorunda!"

        monster_power = self._get_total_monster_power()
        player_power  = self._get_player_power()
        monster       = self.current_monsters[0]

        if action == 0:  # Saldır
            if player_power > monster_power:
                # Kazandı!
                self.total_kills   += len(self.current_monsters)
                treasures_gained    = sum(m["treasures"] for m in self.current_monsters)
                self.player_level  += 1
                reward              = 10 + treasures_gained * 2
                self.defense_bonus  = 0
                # Hazine kazan
                for _ in range(min(treasures_gained, 3)):
                    if len(self.treasure_cards) < 6:
                        self.treasure_cards.append(self._gen_card())
                event = f"⚔️ Zafer! {'+'.join(m['emoji'] for m in self.current_monsters)} öldürüldü! +{treasures_gained} hazine"
                if self.player_level >= self.max_level:
                    reward = 500
                    done   = True
                    event += " 🏆 OYUN KAZANILDI!"
                else:
                    self.current_monsters = [self._spawn_monster()]
            else:
                # Kaybetti — PDF: kaçış zarunlu
                reward = -20
                done   = True
                bt_event = self._apply_bad_thing(monster)
                event  = f"💥 Savaş kaybedildi! {bt_event}"

        elif action == 1:  # Kaç
            roll, success = self._roll_escape()
            self.flee_attempts += 1
            if success:
                reward = -3
                self.defense_bonus   = 0
                self.current_monsters = [self._spawn_monster()]
                event = f"🏃 Kaçış başarılı! (Zar: {roll}) Yeni canavar geliyor..."
            else:
                # Kaçamadı — Kötü Şey
                bt_event = self._apply_bad_thing(monster)
                reward   = -15
                done     = True
                event    = f"😱 Kaçış başarısız! (Zar: {roll}) {bt_event}"

        elif action == 2:  # Eşya Giy
            bi = self.get_best_card_index()
            if bi is not None:
                card = self.treasure_cards.pop(bi)
                gain = card["power"] - self.equipment[card["slot"]]
                self.equipment[card["slot"]] = card["power"]
                self.active_power = sum(self.equipment.values())
                reward = 2 + gain
                event  = f"🎒 {card['name']} giyildi! (+{gain} güç)"
            else:
                reward = -2
                event  = "🎒 Yükseltecek kart yok."

        elif action == 3:  # Savunma
            self.defense_bonus = 3
            reward = -1
            event  = "🛡️ Savunma pozisyonu! (+3 güç sonraki saldırıda)"

        elif action == 4:  # Yardım Çağır (PDF mekanik)
            # Yardımcı: +3 güç, ama hazineyi paylaşırsın
            new_power = self._get_player_power(extra=3)
            if new_power > monster_power:
                self.total_kills += len(self.current_monsters)
                treasures = sum(m["treasures"] for m in self.current_monsters)
                shared    = max(1, treasures // 2)
                self.player_level += 1
                reward = 5 + shared  # azaltılmış ödül
                self.defense_bonus = 0
                for _ in range(shared):
                    if len(self.treasure_cards) < 6:
                        self.treasure_cards.append(self._gen_card())
                event = f"🤝 Yardımla zafer! Hazine paylaşıldı (+{shared})"
                if self.player_level >= self.max_level:
                    reward = 400
                    done   = True
                    event += " 🏆 KAZANILDI!"
                else:
                    self.current_monsters = [self._spawn_monster()]
            else:
                reward = -5
                event  = "🤝 Yardım yetmedi, kaçış gerekli!"
                # Zorla kaç
                roll, success = self._roll_escape()
                if not success:
                    bt_event = self._apply_bad_thing(monster)
                    reward   = -12
                    done     = True
                    event   += f" Kaçış başarısız (Zar:{roll}) {bt_event}"

        # Avare canavar (küçük olasılık — PDF mekanik)
        if not done and random.random() < 0.07 and len(self.current_monsters) < 2:
            wanderer = self._spawn_monster()
            wanderer["name"] = "Avare " + wanderer["name"]
            self.current_monsters.append(wanderer)
            reward -= 3
            event += f" ⚠️ Avare {wanderer['emoji']} {wanderer['name']} savaşa katıldı!"

        state = self._get_state()
        return state, reward, done, event

    def get_status_dict(self):
        """Frontend için durum özeti"""
        bi = self.get_best_card_index()
        cards_fmt = []
        for i, c in enumerate(self.treasure_cards):
            gain = c["power"] - self.equipment[c["slot"]]
            cards_fmt.append({
                "name":       c["name"],
                "power":      c["power"],
                "slot":       SLOT_TR[c["slot"]],
                "is_upgrade": gain > 0,
                "gain":       gain,
                "is_best":    i == bi,
            })

        equip_fmt = {}
        for slot, val in self.equipment.items():
            if val > 0:
                name = ITEMS[slot][val-1][0]
                equip_fmt[SLOT_TR[slot]] = f"{name} (+{val})"
            else:
                equip_fmt[SLOT_TR[slot]] = "Boş"

        return {
            "player_level":   self.player_level,
            "player_power":   self._get_player_power(),
            "active_power":   self.active_power,
            "defense_bonus":  self.defense_bonus,
            "class_bonus":    self._get_class_bonus(),
            "item_penalty":   self._get_item_penalty(),
            "race_bonus":     RACE_BONUSES.get(self.hero_race, 0),
            "hero_class":     self.hero_class,
            "hero_race":      self.hero_race,
            "monsters":       self.current_monsters,
            "monster_power":  self._get_total_monster_power(),
            "treasure_cards": cards_fmt,
            "equipment":      equip_fmt,
            "total_kills":    self.total_kills,
            "flee_attempts":  self.flee_attempts,
            "curse_events":   self.curse_events,
            "steps":          self.steps,
        }
