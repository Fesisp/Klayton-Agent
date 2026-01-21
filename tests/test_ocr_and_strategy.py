from src.perception.ocr_engine import OCREngine
from src.decision.battle_strategy import BattleStrategy
from src.knowledge.team_manager import TeamManager


def test_clean_move_name_basic():
    engine = OCREngine(tesseract_path="tesseract")
    raw = "Thunderbolt  23/25"
    cleaned = engine.clean_move_name(raw)
    assert cleaned.lower() == "thunderbolt"


class DummyDb:
    def get_pokemon_types(self, name: str):
        if name.lower() == "gyarados":
            return ["water", "flying"]
        if name.lower() == "pikachu":
            return ["electric"]
        return ["normal"]

    def get_move_data(self, move_key: str):
        key = move_key.strip().lower()
        if key == "thunderbolt":
            # type_id 13: elétrico (valor arbitrário apenas para o teste)
            return {"type_id": 13, "power": 90, "category_id": 3}
        if key == "tackle":
            return {"type_id": 1, "power": 40, "category_id": 2}
        return {"type_id": 1, "power": 40, "category_id": 2}

    def get_type_multiplier(self, type_id, enemy_types):
        # elétrico contra água/voador é super efetivo
        if type_id == 13 and "water" in enemy_types:
            return 2.0
        return 1.0


def test_battle_strategy_prefers_super_effective():
    db = DummyDb()
    team = TeamManager()

    team.known_moves["pikachu"] = ["Thunderbolt", "Tackle"]

    strat = BattleStrategy(db, team)

    best_idx = strat.get_best_move("pikachu", "Gyarados")
    assert best_idx == 0


if __name__ == "__main__":
    print("Running tests...")
    try:
        test_clean_move_name_basic()
        print("test_clean_move_name_basic: PASS")
    except Exception as e:
        print(f"test_clean_move_name_basic: FAIL ({e})")

    try:
        test_battle_strategy_prefers_super_effective()
        print("test_battle_strategy_prefers_super_effective: PASS")
    except Exception as e:
        print(f"test_battle_strategy_prefers_super_effective: FAIL ({e})")
