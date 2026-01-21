import cv2
import numpy as np

from src.perception.game_state_detector import GameStateDetector, GameState
from src.perception.ocr_engine import OCREngine
from src.perception.screen_capture import ScreenCapture


class DummyScreen(ScreenCapture):
    """ScreenCapture fake que devolve sempre a mesma imagem."""

    def __init__(self, image):
        self._image = image

    def capture(self):  # override
        return self._image


def test_detect_state_returns_shiny_found_when_template_present():
    """Garante que detect_state => SHINY_FOUND quando shiny.png está na tela."""
    # Carrega a mesma imagem usada como template de shiny
    cfg = {
        "assets": {
            # Usa o caminho real relativo a partir da raiz do projeto
            "templates_dir": "PokeBot_Pro/assets/templates/",
            "shiny_image": "shiny.png",
            "talk_image": "talk.png",
            "fight_image": "fight.png",
            "bag_image": "bag.png",
            "pokemon_image": "pokemon.png",
            "run_image": "run.png",
        },
        "detection": {
            "shiny_threshold": 0.5,  # threshold baixo só para o teste
        },
        "rois": {},
        "ocr": {"tesseract_path": "tesseract"},
    }
    shiny_path = cfg["assets"]["templates_dir"] + cfg["assets"]["shiny_image"]
    shiny_img = cv2.imread(shiny_path)
    assert shiny_img is not None, f"shiny.png não encontrado no caminho configurado para o teste: {shiny_path}"

    # Cria uma "tela" que é exatamente o shiny
    screen = DummyScreen(shiny_img)
    ocr = OCREngine(cfg["ocr"]["tesseract_path"])
    detector = GameStateDetector(screen, ocr, cfg)

    state = detector.detect_state(shiny_img)

    assert state == GameState.SHINY_FOUND
