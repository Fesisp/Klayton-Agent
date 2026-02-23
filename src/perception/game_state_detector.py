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

    def find_player_name(self, frame, nickname):
        """
        Procura o nickname de um jogador no frame usando template matching ou OCR.
        
        Args:
            frame: Frame capturado da tela
            nickname: Nome do jogador a ser procurado
            
        Returns:
            tuple: (x, y) coordenadas do centro do nome encontrado, ou None se não encontrado
        """
        import pytesseract
        
        # 1. Tenta template matching se houver template do nome
        template_path = os.path.join('assets', 'templates', f'name_{nickname.lower()}.png')
        if os.path.exists(template_path):
            template = cv2.imread(template_path)
            result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.8:  # 80% de confiança
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y)
        
        # 2. Fallback: OCR na região central onde nomes flutuantes aparecem
        h, w = frame.shape[:2]
        roi = frame[int(h*0.3):int(h*0.6), int(w*0.3):int(w*0.7)]
        
        # Preprocessamento para OCR
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # OCR
        text = pytesseract.image_to_string(thresh, config='--psm 11')
        
        # Procura o nickname no texto extraído
        if nickname.lower() in text.lower():
            # Tenta pegar posição mais precisa com image_to_boxes
            boxes = pytesseract.image_to_boxes(thresh)
            for box in boxes.splitlines():
                parts = box.split()
                if len(parts) >= 5 and parts[0].lower() in nickname.lower():
                    x = int(parts[1]) + int(w*0.3)
                    y = h - int(parts[2]) + int(h*0.3)  # Ajuste de coordenada Y
                    return (x, y)
        
        return None

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

        # Nível do inimigo (se disponível)
        enemy_level_img = crop_roi_safe(image, self.rois.get('enemy_level'))
        enemy_level_raw = self.ocr.extract_text_optimized(
            enemy_level_img,
            whitelist="0123456789",
            invert_for_white_text=True,
        )
        enemy_level_digits = "".join([c for c in enemy_level_raw if c.isdigit()])
        enemy_level = int(enemy_level_digits) if enemy_level_digits else None

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
            "enemy_level": enemy_level,
            "player_name": player_name,
            "player_hp_percentage": player_hp_percentage,
            "enemy_hp_percentage": enemy_hp_percentage,
            "player_hp_critical": player_hp_percentage < 25 if player_hp_percentage is not None else False,
            "player_hp_low": player_hp_percentage < 50 if player_hp_percentage is not None else False,
        }
    
    def get_hp_ratio(self, image, side='player'):
        """
        Calcula a razão de HP (0.0 a 1.0) baseado na proporção de pixels coloridos na barra de HP.
        Método mais rápido e confiável que OCR.
        
        Args:
            image: Imagem da tela completa
            side: 'player' ou 'enemy'
            
        Returns:
            float: Razão de HP (0.0 a 1.0) ou None se ROI não existir
        """
        # Determina qual ROI usar
        roi_key = f'hp_{side}' if side in ['player', 'enemy'] else f'{side}_hp_bar'
        hp_roi = self.rois.get(roi_key)
        
        if not hp_roi:
            return None
        
        hp_bar_img = crop_roi_safe(image, hp_roi)
        if hp_bar_img is None or hp_bar_img.size == 0:
            return None
        
        # Converter para HSV para melhor detecção de cor
        hsv = cv2.cvtColor(hp_bar_img, cv2.COLOR_BGR2HSV)
        
        # Ranges de cor para HP (verde, amarelo, vermelho)
        # Verde: HP alto
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([85, 255, 255])
        
        # Amarelo: HP médio
        lower_yellow = np.array([15, 40, 40])
        upper_yellow = np.array([40, 255, 255])
        
        # Vermelho: HP baixo (precisa de 2 ranges devido ao wrap do hue)
        lower_red1 = np.array([0, 40, 40])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([165, 40, 40])
        upper_red2 = np.array([180, 255, 255])
        
        # Criar máscaras
        mask_green = cv2.inRange(hsv, lower_green, upper_green)
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
        
        # Combinar todas as máscaras (qualquer cor de HP)
        combined_mask = cv2.bitwise_or(mask_green, cv2.bitwise_or(mask_yellow, mask_red))
        
        # Contar colunas com pixels de HP (proporção da largura)
        columns_with_hp = np.any(combined_mask, axis=0)
        total_hp_pixels = int(np.count_nonzero(columns_with_hp))

        # Largura da barra = máximo de pixels possível
        _, width = hp_bar_img.shape[:2]

        # Calcular razão (0.0 a 1.0) baseado em contagem de colunas
        hp_ratio = total_hp_pixels / width if width > 0 else 0.0
        
        # Clamp entre 0 e 1
        hp_ratio = max(0.0, min(1.0, hp_ratio))
        
        return hp_ratio
    
    def _get_hp_percentage(self, image, hp_bar_roi_key):
        """
        Calcula a porcentagem de HP baseado na cor da barra de HP.
        Wrapper para get_hp_ratio que retorna porcentagem (0-100).
        
        Args:
            image: Imagem da tela
            hp_bar_roi_key: Chave da ROI no config (ex: 'player_hp_bar' ou 'enemy_hp_bar')
            
        Returns:
            Porcentagem de HP (0-100) ou None se ROI não existir
        """
        # Extrai 'player' ou 'enemy' do nome da chave
        if 'player' in hp_bar_roi_key:
            side = 'player'
        elif 'enemy' in hp_bar_roi_key:
            side = 'enemy'
        else:
            # Fallback para método antigo se não reconhecer
            return None
        
        hp_ratio = self.get_hp_ratio(image, side)
        if hp_ratio is None:
            return None
        
        # Converter razão para porcentagem
        percentage = hp_ratio * 100
        
        return round(percentage, 1)
    
    def find_player_name(self, image, player_name):
        """
        Localiza o nome do jogador principal na tela usando OCR.
        Útil para o modo FOLLOW onde o bot precisa seguir outro personagem.
        
        Args:
            image: Imagem da tela completa
            player_name: Nome do jogador a procurar (ex: "FelipeSpinola")
            
        Returns:
            tuple: (x, y) posição central do nome encontrado, ou None se não encontrado
        """
        if not player_name:
            return None
        
        # Configurações de busca
        follow_cfg = self.cfg.get('follow_settings', {})
        min_confidence = float(follow_cfg.get('min_confidence', 0.7))
        
        # ROI de busca (área ao redor do centro da tela)
        # Foca na área onde o personagem estaria visível
        screen_h, screen_w = image.shape[:2]
        search_margin = 400  # pixels ao redor do centro
        
        x1 = max(0, (screen_w // 2) - search_margin)
        y1 = max(0, (screen_h // 2) - search_margin)
        x2 = min(screen_w, (screen_w // 2) + search_margin)
        y2 = min(screen_h, (screen_h // 2) + search_margin)
        
        search_area = image[y1:y2, x1:x2]
        
        # Tenta detectar texto na área de busca
        try:
            # Extrai todo o texto da área
            text = self.ocr.extract_text_optimized(
                search_area,
                whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0-9 ",
                invert_for_white_text=True
            )
            
            # Verifica se o nome do jogador está no texto detectado
            text_lower = text.lower()
            player_name_lower = player_name.lower()
            
            if player_name_lower in text_lower:
                # Nome encontrado! Agora precisa localizar coordenadas exatas
                # Para simplicidade, retorna centro da área de busca
                # TODO: Implementar localização precisa usando pytesseract.image_to_data
                
                center_x = x1 + (x2 - x1) // 2
                center_y = y1 + (y2 - y1) // 2
                
                logger.debug(f"[FOLLOW] Nome '{player_name}' detectado próximo a ({center_x}, {center_y})")
                return (center_x, center_y)
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao procurar nome do jogador: {e}")
            return None
