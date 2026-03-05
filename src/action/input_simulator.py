import pyautogui
import time
import cv2
import numpy as np
import os
import random
try:
    import pydirectinput
except Exception:
    pydirectinput = None
from scipy import interpolate
from ..utils.geometry import normalize_roi, get_safe_random_point
from ..utils.window_handler import WindowHandler
try:
    from loguru import logger
except Exception:
    import logging
    logger = logging.getLogger(__name__)


def execute_human_action(x, y, label="Botão"):
    """Clica com jitter de pixels e delay variável (curva gaussiana)."""
    target_x = x + random.randint(-3, 3)
    target_y = y + random.randint(-3, 3)

    mover = pydirectinput if pydirectinput is not None else pyautogui
    mover.moveTo(target_x, target_y, duration=random.uniform(0.15, 0.4))

    reaction_time = abs(random.gauss(0.2, 0.05))
    time.sleep(reaction_time)

    mover.click()
    print(f"Ação executada: {label} em {target_x},{target_y}")

class InputSimulator:
    def __init__(self, config=None):
        # Desabilita o fail-safe para evitar paradas bruscas se o mouse for para o canto
        # CUIDADO: Isso impede que você pare o bot movendo o mouse para o canto!
        pyautogui.FAILSAFE = False
        self.cfg = config or {}
        self.rois = self.cfg.get('rois', {})
        self.move_duration = float(self.cfg.get('input', {}).get('mouse_move_duration', 0.0))
        
        # Configurações de humanização
        input_cfg = self.cfg.get('input', {})
        self.use_human_movement = input_cfg.get('use_human_movement', True)
        self.min_delay = float(input_cfg.get('min_delay', 0.05))
        self.max_delay = float(input_cfg.get('max_delay', 0.15))
        self.min_move_duration = float(input_cfg.get('min_move_duration', 0.2))
        self.max_move_duration = float(input_cfg.get('max_move_duration', 0.5))
        self.idle_action_chance = float(input_cfg.get('idle_action_chance', 0.05))
        self.last_idle_time = time.time()
        window_title = self.cfg.get('screen', {}).get('window_title', 'PokeOne')
        self.win_handler = WindowHandler(window_title=window_title)
        
        # Preload templates to avoid IO on every click
        assets_dir = self.cfg.get('assets', {}).get('templates_dir', '')
        
        # Fight
        fight_img_name = self.cfg.get('assets', {}).get('fight_image', 'fight.png')
        self.fight_template = None
        if assets_dir and fight_img_name:
            import os
            path = os.path.join(assets_dir, fight_img_name)
            if os.path.exists(path):
                self.fight_template = cv2.imread(path)

        # Pokemon
        poke_img_name = self.cfg.get('assets', {}).get('pokemon_image', 'pokemon.png')
        self.pokemon_template = None
        if assets_dir and poke_img_name:
            import os
            path = os.path.join(assets_dir, poke_img_name)
            if os.path.exists(path):
                self.pokemon_template = cv2.imread(path)

        # Run
        run_img_name = self.cfg.get('assets', {}).get('run_image', 'run.png')
        self.run_template = None
        if assets_dir and run_img_name:
            import os
            path = os.path.join(assets_dir, run_img_name)
            if os.path.exists(path):
                self.run_template = cv2.imread(path)

    def click(self, x, y):
        """Clique padrão (mantido para compatibilidade)."""
        if self.use_human_movement:
            self.humanized_click(x, y)
        else:
            if self.move_duration and self.move_duration > 0:
                pyautogui.moveTo(x, y, duration=self.move_duration)
                pyautogui.click()
            else:
                pyautogui.click(x, y)
    
    def humanized_click(self, x, y, delay_min=None, delay_max=None):
        """
        Clique humanizado com variância gaussiana e jitter de coordenadas.
        
        SEGURANÇA ANTI-CHEAT:
        - Distribuição Gaussiana para delays (tempo de reação humano)
        - Jitter de 2 pixels nas coordenadas (imprecisão natural)
        - Curva Bezier suave para movimento do mouse
        
        Args:
            x, y: Coordenadas alvo
            delay_min: Delay mínimo em segundos (default: 0.1s)
            delay_max: Delay máximo em segundos (default: 0.3s)
        """
        try:
            execute_human_action(x, y)
        except Exception:
            if delay_min is None:
                delay_min = self.min_delay
            if delay_max is None:
                delay_max = self.max_delay

            jitter_x = x + random.randint(-2, 2)
            jitter_y = y + random.randint(-2, 2)

            self._bezier_move(jitter_x, jitter_y)

            mean_delay = (delay_min + delay_max) / 2
            sigma = (delay_max - delay_min) / 6

            actual_delay = abs(random.gauss(mean_delay, sigma))
            actual_delay = max(delay_min, min(actual_delay, delay_max))

            time.sleep(actual_delay)
            pyautogui.click()

            post_click_delay = abs(random.gauss(0.05, 0.015))
            time.sleep(max(0.01, post_click_delay))
    
    def human_click(self, x, y):
        """Alias para compatibilidade com código antigo."""
        self.humanized_click(x, y)

    def click_relative(self, rel_x, rel_y):
        """Clica em posição baseada na porcentagem da janela detectada."""
        rect = self.win_handler.get_window_rect()
        if rect:
            real_x, real_y = self.win_handler.get_relative_coords(rel_x, rel_y, rect)
            execute_human_action(real_x, real_y, label=f"Clique Relativo {rel_x},{rel_y}")
            return True
        return False
    
    def press_directional_key(self, key):
        """Pressiona tecla direcional (W/A/S/D) para movimento.
        
        Usado para micro-movimentação de escape em obstáculos.
        
        Args:
            key: 'w', 'a', 's', 'd' (cima, esquerda, baixo, direita)
        """
        key = key.lower()
        if key not in ['w', 'a', 's', 'd']:
            logger.warning(f"Tecla inválida: {key}. Use W/A/S/D.")
            return
        
        # Pressiona e solta tecla com duração curta (~0.1s)
        pyautogui.keyDown(key)
        time.sleep(0.1)
        pyautogui.keyUp(key)
        
        # Pequeno delay após movimento
        time.sleep(0.05)
    
    def _bezier_move(self, target_x, target_y):
        """Move o mouse em uma curva Bezier suave até o alvo."""
        current_pos = pyautogui.position()
        start_x, start_y = current_pos
        
        # Pontos de controle para curva Bezier quadrática
        # Adiciona aleatoriedade ao ponto de controle
        mid_x = (start_x + target_x) / 2 + random.randint(-20, 20)
        mid_y = (start_y + target_y) / 2 + random.randint(-20, 20)
        
        # Pontos da curva Bezier: início, controle, fim
        points = np.array([[start_x, start_y], [mid_x, mid_y], [target_x, target_y]])
        
        # Criar curva Bezier usando interpolação
        t = np.linspace(0, 1, num=random.randint(15, 25))
        
        # Bezier quadrática: B(t) = (1-t)²P₀ + 2(1-t)tP₁ + t²P₂
        curve = np.array([
            (1-ti)**2 * points[0] + 2*(1-ti)*ti * points[1] + ti**2 * points[2]
            for ti in t
        ])
        
        # Move o mouse ao longo da curva
        duration = random.uniform(self.min_move_duration, self.max_move_duration)
        step_delay = duration / len(curve)
        
        for point in curve:
            pyautogui.moveTo(int(point[0]), int(point[1]))
            time.sleep(step_delay)
    
    def perform_idle_action(self):
        """Executa ações aleatórias para simular jogador real entediado."""
        # Só executa se passou tempo suficiente desde a última ação idle
        if time.time() - self.last_idle_time < 10:
            return
        
        if random.random() > self.idle_action_chance:
            return
        
        # Ações que NÃO movem o personagem
        actions = [
            lambda: self._random_camera_move(),  # Move câmera
            lambda: time.sleep(random.uniform(0.5, 1.5)),  # Apenas pausa
        ]
        
        action = random.choice(actions)
        action()
        self.last_idle_time = time.time()
    
    def _random_camera_move(self):
        """Simula movimento aleatório de câmera."""
        # Move mouse para uma posição aleatória (simula olhar ao redor)
        current_pos = pyautogui.position()
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-50, 50)
        
        new_x = max(0, min(current_pos[0] + offset_x, pyautogui.size()[0]))
        new_y = max(0, min(current_pos[1] + offset_y, pyautogui.size()[1]))
        
        self._bezier_move(new_x, new_y)
        time.sleep(random.uniform(0.1, 0.3))

    def press(self, key):
        pyautogui.press(key)
    
    def click_in_slot(self, slot_index):
        """Clica aproximadamente no centro de um dos 4 slots de ataque (0-3)."""
        if slot_index not in [0, 1, 2, 3]:
            return

        moves_rois = self.rois.get('moves', {})
        coords = None

        if isinstance(moves_rois, (list, tuple)):
            if slot_index < len(moves_rois):
                coords = moves_rois[slot_index]
        elif isinstance(moves_rois, dict):
            slot_map = {
                0: 'slot_1',
                1: 'slot_2',
                2: 'slot_3',
                3: 'slot_4',
            }
            key = slot_map.get(slot_index)
            coords = moves_rois.get(key)

        if not coords:
            logger.warning(f"ROI de move não encontrada para slot {slot_index}")
            return
        
        # Simplificado usando função utilitária
        cx, cy = get_safe_random_point(coords, 0.2)
        
        self.click(cx, cy)
    
    def humanized_click_in_slot(self, slot_index, delay_min=0.1, delay_max=0.3):
        """
        Clica em um slot de movimento com humanização completa.
        
        SEGURANÇA ANTI-CHEAT:
        - Variância Gaussiana no delay
        - Jitter nas coordenadas
        - Curva Bezier no movimento
        
        Args:
            slot_index: Índice do slot (0-3)
            delay_min: Delay mínimo em segundos
            delay_max: Delay máximo em segundos
        """
        if slot_index not in [0, 1, 2, 3]:
            return

        moves_rois = self.rois.get('moves', {})
        coords = None

        if isinstance(moves_rois, (list, tuple)):
            if slot_index < len(moves_rois):
                coords = moves_rois[slot_index]
        elif isinstance(moves_rois, dict):
            slot_map = {
                0: 'slot_1',
                1: 'slot_2',
                2: 'slot_3',
                3: 'slot_4',
            }
            key = slot_map.get(slot_index)
            coords = moves_rois.get(key)

        if not coords:
            logger.warning(f"ROI de move não encontrada para slot {slot_index}")
            return
        
        # Ponto aleatório dentro do slot
        cx, cy = get_safe_random_point(coords, 0.2)
        
        # Clique humanizado com curva Bezier e delay Gaussiano
        self.humanized_click(cx, cy, delay_min=delay_min, delay_max=delay_max)

    def click_fight_button(self, screen_img=None):
        """Clica no botão FIGHT usando o template fight.png."""
        clicked = self._click_template(self.fight_template, 'fight_threshold', screen_img)
        if not clicked:
            rel = self.rois.get('fight_button_rel')
            if isinstance(rel, dict) and 'x' in rel and 'y' in rel:
                return self.click_relative(rel['x'], rel['y'])
        return clicked


    def click_pokemon_button(self, screen_img=None):
        """Clica no botão POKEMON usando o template pokemon.png."""
        clicked = self._click_template(self.pokemon_template, 'pokemon_threshold', screen_img)
        if not clicked:
            rel = self.rois.get('pokemon_button_rel')
            if isinstance(rel, dict) and 'x' in rel and 'y' in rel:
                return self.click_relative(rel['x'], rel['y'])
        return clicked


    def click_run_button(self, screen_img=None):
        """Clica no botão RUN usando o template run.png."""
        clicked = self._click_template(self.run_template, 'run_threshold', screen_img)
        if not clicked:
            rel = self.rois.get('run_button_rel')
            if isinstance(rel, dict) and 'x' in rel and 'y' in rel:
                return self.click_relative(rel['x'], rel['y'])
        return clicked


    def _click_template(self, template, threshold_key, screen_img=None, margin_pct=0.2):
        """
        Generic helper to find and click a template.
        """
        if template is None:
            return False

        if screen_img is not None:
            screenshot = screen_img
        else:
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        thresh = float(self.cfg.get('detection', {}).get(threshold_key, 0.85))
        if max_val < thresh:
            return False

        h, w = template.shape[:2]
        x, y = max_loc
        
        # Constrói ROI [x, y, w, h] que será normalizada na função utilitária
        roi = [x, y, w, h]
        cx, cy = get_safe_random_point(roi, margin_pct)

        self.click(cx, cy)
        return True