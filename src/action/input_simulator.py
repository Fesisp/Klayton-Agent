import pyautogui
import time
import cv2
import numpy as np
import os
import random
from scipy import interpolate
from ..utils.geometry import normalize_roi, get_safe_random_point

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
            self.human_click(x, y)
        else:
            if self.move_duration and self.move_duration > 0:
                pyautogui.moveTo(x, y, duration=self.move_duration)
                pyautogui.click()
            else:
                pyautogui.click(x, y)
    
    def human_click(self, x, y):
        """Simula clique humano com movimento em curva Bezier e delays randômicos."""
        # 1. Move o mouse de forma curva até o alvo
        self._bezier_move(x, y)
        
        # 2. Pequena pausa antes de clicar (jitter)
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
        
        # 3. Clica
        pyautogui.click()
        
        # 4. Pequeno delay pós-clique
        time.sleep(random.uniform(0.02, 0.08))
    
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
        
        actions = [
            lambda: pyautogui.press('space'),  # Pressiona espaço
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
        slot_map = {
            0: 'slot_1',
            1: 'slot_2',
            2: 'slot_3',
            3: 'slot_4',
        }
        key = slot_map.get(slot_index)
        if not key:
            return
        moves_rois = self.rois.get('moves', {})
        coords = moves_rois.get(key)
        
        # Simplificado usando função utilitária
        cx, cy = get_safe_random_point(coords, 0.2)
        
        self.click(cx, cy)

    def click_fight_button(self, screen_img=None):
        """Clica no botão FIGHT usando o template fight.png."""
        self._click_template(self.fight_template, 'fight_threshold', screen_img)


    def click_pokemon_button(self, screen_img=None):
        """Clica no botão POKEMON usando o template pokemon.png."""
        self._click_template(self.pokemon_template, 'pokemon_threshold', screen_img)


    def click_run_button(self, screen_img=None):
        """Clica no botão RUN usando o template run.png."""
        self._click_template(self.run_template, 'run_threshold', screen_img)


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