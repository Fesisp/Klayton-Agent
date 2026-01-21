import yaml
import sys
from pathlib import Path

# Add the project root to the python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.perception.screen_capture import ScreenCapture
from src.perception.ocr_engine import OCREngine
from src.perception.game_state_detector import GameStateDetector
from src.action.input_simulator import InputSimulator
from src.knowledge.pokemon_database import PokemonDatabase
from src.knowledge.team_manager import TeamManager
from src.decision.battle_strategy import BattleStrategy
from src.core.bot_controller import BotController

def load_config():
    config_path = ROOT_DIR / 'config' / 'settings.yaml'
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

try:
    from loguru import logger
except ImportError:
    class logger:
        @staticmethod
        def error(msg): print(f"ERROR: {msg}")
        @staticmethod
        def exception(msg): print(f"EXCEPTION: {msg}")

def setup_logging():
    """Configura loguru para salvar logs em arquivo com rotação."""
    try:
        from loguru import logger
        log_dir = ROOT_DIR / 'logs'
        log_dir.mkdir(exist_ok=True)
        logger.add(
            str(log_dir / "pokebot_{time}.log"), 
            rotation="5 MB", 
            retention="1 week",
            level="DEBUG"
        )
    except Exception:
        pass

def main():
    try:
        setup_logging()
        config = load_config()
        
        # Initialize components
        screen = ScreenCapture()
        ocr = OCREngine(config['ocr']['tesseract_path'])
        detector = GameStateDetector(screen, ocr, config)
        input_sim = InputSimulator(config)
        db = PokemonDatabase()
        team_mgr = TeamManager()
        strategy = BattleStrategy(db, team_mgr, config)
        
        components = {
            'screen': screen,
            'detector': detector,
            'input': input_sim,
            'ocr': ocr,
            'strategy': strategy,
            'team_mgr': team_mgr
        }
        
        bot = BotController(config, components)
        bot.run()
    except Exception as e:
        logger.exception(f"Fatal error in main loop: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()