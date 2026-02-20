import cv2
import numpy as np
import winsound
from enum import Enum
from loguru import logger

class GameState(Enum):
    EXPLORING = "exploring"
    IN_BATTLE = "in_battle"
    SHINY_FOUND = "shiny_found"
    UNKNOWN = "unknown"

from ..utils.geometry import crop_roi_safe

class GameStateDetector:
    def __init__(self, screen_capture, ocr_engine, config):
        self.cap = screen_capture
        self.ocr = ocr_engine
        self.rois = config.get('rois', {})
        self.cfg_detection = config.get('detection', {})
        self.templates = self._load_templates(config)

    def _load_templates(self, config):
        # Carrega imagem de shiny, talk e botões de batalha
        assets_dir = config.get('assets', {}).get('templates_dir', 'assets/templates/')
        shiny_path = assets_dir + config.get('assets', {}).get('shiny_image', 'shiny.png')
        talk_path = assets_dir + config.get('assets', {}).get('talk_image', 'talk.png')
        goto_path = assets_dir + config.get('assets', {}).get('goto_image', 'goto.png')
        fight_path = assets_dir + config.get('assets', {}).get('fight_image', 'fight.png')
        bag_path = assets_dir + config.get('assets', {}).get('bag_image', 'bag.png')
        pokemon_path = assets_dir + config.get('assets', {}).get('pokemon_image', 'pokemon.png')
        run_path = assets_dir + config.get('assets', {}).get('run_image', 'run.png')
        return {
            'shiny': cv2.imread(shiny_path),
            'talk': cv2.imread(talk_path),
            'goto': cv2.imread(goto_path),
            'fight': cv2.imread(fight_path),
            'bag': cv2.imread(bag_path),
            'pokemon': cv2.imread(pokemon_path),
            'run': cv2.imread(run_path),
        }

    def detect_state(self, image):
        # 1. Verifica SHINY (Prioridade Absoluta)
        if self._detect_shiny(image):
            return GameState.SHINY_FOUND

        # 2. Verifica Botões de Batalha (qualquer um dos 4) via template matching
        # em uma única região ampla de combate (battle_area)
        battle_area = self.cfg_detection.get('battle_area')
        if battle_area and isinstance(battle_area, (list, tuple)) and len(battle_area) == 4:
            x1, y1, x2, y2 = battle_area
            battle_roi = image[y1:y2, x1:x2]
        else:
            battle_roi = image

        battle_templates = {
            'fight': 'fight',
            'items': 'bag',
            'pokemon': 'pokemon',
            'run': 'run',
        }

        battle_thresh = float(self.cfg_detection.get('battle_button_threshold', 0.75))

        for name, tpl_key in battle_templates.items():
            template = self.templates.get(tpl_key)
            if template is None:
                continue

            try:
                res = cv2.matchTemplate(battle_roi, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)
            except cv2.error as e:
                logger.error(f"Erro em matchTemplate para {tpl_key}: {e}")
                continue

            if max_val >= battle_thresh:
                logger.debug(
                    f"Botão de batalha '{name}' detectado com score={max_val:.3f} (threshold={battle_thresh})"
                )
                return GameState.IN_BATTLE

        return GameState.EXPLORING

    def _detect_shiny(self, image):
        template = self.templates.get('shiny')
        if template is None:
            return False

        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        # Threshold configurável via settings.yaml (fallback 0.85)
        shiny_thresh = float(self.cfg_detection.get('shiny_threshold', 0.85))

        if max_val >= shiny_thresh:
            logger.info(f"Template de SHINY detectado com score={max_val:.3f} (threshold={shiny_thresh})")
            return True

        return False

    def get_battle_info(self, image):
        """Extrai nome do inimigo, nome do player e HP."""
        # Nome do inimigo
        enemy_name_img = crop_roi_safe(image, self.rois.get('enemy_name'))
        enemy_name_raw = self.ocr.extract_text_optimized(
            enemy_name_img,
            whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz- ",
            invert_for_white_text=True,
        )
        enemy_name = enemy_name_raw.replace("Lv", "").strip()

        # Nome do Pokémon do player (HUD)
        player_name_img = crop_roi_safe(image, self.rois.get('player_name'))
        player_name_raw = self.ocr.extract_text_optimized(
            player_name_img,
            whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz- ",
            invert_for_white_text=True,
        )
        player_name = player_name_raw.replace("Lv", "").strip()
        
        # Detectar HP do player (porcentagem baseada em cor da barra)
        player_hp_percentage = self._get_hp_percentage(image, 'player_hp_bar')
        
        # Detectar HP do inimigo (porcentagem baseada em cor da barra)
        enemy_hp_percentage = self._get_hp_percentage(image, 'enemy_hp_bar')

        return {
            "enemy_name": enemy_name,
            "player_name": player_name,
            "player_hp_percentage": player_hp_percentage,
            "enemy_hp_percentage": enemy_hp_percentage,
            "player_hp_critical": player_hp_percentage < 25 if player_hp_percentage is not None else False,
            "player_hp_low": player_hp_percentage < 50 if player_hp_percentage is not None else False,
        }
    
    def _get_hp_percentage(self, image, hp_bar_roi_key):
        """
        Calcula a porcentagem de HP baseado na cor da barra de HP.
        
        Args:
            image: Imagem da tela
            hp_bar_roi_key: Chave da ROI no config (ex: 'player_hp_bar' ou 'enemy_hp_bar')
            
        Returns:
            Porcentagem de HP (0-100) ou None se ROI não existir
        """
        hp_roi = self.rois.get(hp_bar_roi_key)
        if not hp_roi:
            return None
        
        hp_bar_img = crop_roi_safe(image, hp_roi)
        if hp_bar_img is None or hp_bar_img.size == 0:
            return None
        
        # Converter para HSV para melhor detecção de cor
        hsv = cv2.cvtColor(hp_bar_img, cv2.COLOR_BGR2HSV)
        
        # Definir ranges de cor para HP (verde, amarelo, vermelho)
        # Verde: HP alto (> 50%)
        lower_green = np.array([40, 50, 50])
        upper_green = np.array([80, 255, 255])
        
        # Amarelo: HP médio (25-50%)
        lower_yellow = np.array([20, 50, 50])
        upper_yellow = np.array([40, 255, 255])
        
        # Vermelho: HP baixo (< 25%)
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        
        # Criar máscaras
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        # Contar pixels de cada cor
        green_pixels = cv2.countNonZero(mask_green)
        yellow_pixels = cv2.countNonZero(mask_yellow)
        red_pixels = cv2.countNonZero(mask_red)
        
        total_colored_pixels = green_pixels + yellow_pixels + red_pixels
        
        if total_colored_pixels == 0:
            return None
        
        # Calcular largura da barra preenchida
        # Assume que a barra é horizontal
        height, width = hp_bar_img.shape[:2]
        
        # Encontrar a largura efetiva da cor (do lado esquerdo)
        combined_mask = cv2.bitwise_or(mask_green, cv2.bitwise_or(mask_yellow, mask_red))
        
        # Procurar a coluna mais à direita com pixels coloridos
        rightmost_col = 0
        for col in range(width):
            if np.any(combined_mask[:, col]):
                rightmost_col = col
        
        # Calcular porcentagem
        percentage = (rightmost_col / width) * 100
        
        # Ajustar baseado na cor predominante para maior precisão
        if green_pixels > yellow_pixels and green_pixels > red_pixels:
            # HP alto: 50-100%
            percentage = max(50, percentage)
        elif yellow_pixels > green_pixels and yellow_pixels > red_pixels:
            # HP médio: 25-50%
            percentage = max(25, min(50, percentage))
        elif red_pixels > 0:
            # HP baixo: 0-25%
            percentage = min(25, percentage)
        
        return round(percentage, 1)
